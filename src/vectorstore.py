"""
ベクトルストア管理モジュール
sentence-transformers (多言語対応) + ChromaDB でローカルに保存
"""

from __future__ import annotations

import os
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from src.ingestion import TextChunk, build_chunks

# 多言語対応モデル（日本語・英語どちらも OK）
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"  # 軽量版（約120MB、精度はほぼ同等）
COLLECTION_NAME = "sfr_memories"
DB_DIR = "db/chroma"


class MemoryStore:
    """Soul Flight Recorder 用ベクトルストア"""

    def __init__(
        self,
        db_dir: str = DB_DIR,
        embed_model: str = EMBED_MODEL,
        collection_name: str = COLLECTION_NAME,
    ):
        self.embedder = SentenceTransformer(embed_model)

        Path(db_dir).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=db_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------ #
    # インデックス構築
    # ------------------------------------------------------------------ #

    def index_chunks(self, chunks: list[TextChunk], batch_size: int = 64) -> None:
        """チャンクリストをエンベッドして ChromaDB に保存する"""
        if not chunks:
            print("チャンクが空です")
            return

        texts = [c.content for c in chunks]
        ids = [c.doc_id for c in chunks]
        metadatas = [c.metadata for c in chunks]

        print(f"\nエンベッド中 ({len(texts)} チャンク)...")
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_ids = ids[i : i + batch_size]
            batch_meta = metadatas[i : i + batch_size]
            embeddings = self.embedder.encode(
                batch_texts, normalize_embeddings=True
            ).tolist()

            self.collection.upsert(
                ids=batch_ids,
                documents=batch_texts,
                embeddings=embeddings,
                metadatas=batch_meta,
            )
            print(f"  {i + len(batch_texts)}/{len(texts)} 完了")

        print(f"インデックス完了。総チャンク数: {self.collection.count()}")

    # ------------------------------------------------------------------ #
    # 検索
    # ------------------------------------------------------------------ #

    def search(
        self,
        query: str,
        n_results: int = 5,
    ) -> list[dict]:
        """クエリに関連するチャンクを検索して返す"""
        query_emb = self.embedder.encode(
            [query], normalize_embeddings=True
        ).tolist()

        results = self.collection.query(
            query_embeddings=query_emb,
            n_results=min(n_results, self.collection.count() or 1),
            include=["documents", "metadatas", "distances"],
        )

        hits = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metas, dists):
            hits.append(
                {
                    "content": doc,
                    "source": meta.get("source", ""),
                    "score": round(1 - dist, 4),  # コサイン類似度
                }
            )
        return hits

    def count(self) -> int:
        return self.collection.count()

    def clear(self) -> None:
        """コレクションを全削除して再作成"""
        self.client.delete_collection(COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        print("ベクトルストアをクリアしました")


def build_index(data_dir: str = "data/raw", force: bool = False) -> MemoryStore:
    """データを読み込んでインデックスを構築する。force=True で再構築"""
    store = MemoryStore()

    if store.count() > 0 and not force:
        print(f"既存インデックスを使用 ({store.count()} チャンク)")
        return store

    print("インデックスを新規構築します...")
    chunks = build_chunks(data_dir)
    store.index_chunks(chunks)
    return store


if __name__ == "__main__":
    store = build_index(force=True)
    hits = store.search("ワクワクした経験")
    for h in hits:
        print(f"\n[score={h['score']}] {h['content'][:100]}...")
