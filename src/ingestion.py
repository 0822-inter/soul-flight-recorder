"""
テキストデータの読み込みとチャンク分割モジュール
data/raw/ 以下の .txt / .md ファイルを読み込み、重複チャンクに分割する
"""

from __future__ import annotations

import glob
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TextChunk:
    """分割済みテキストの単一チャンク"""
    content: str
    source: str          # ファイル名
    chunk_index: int
    metadata: dict = field(default_factory=dict)

    @property
    def doc_id(self) -> str:
        return f"{Path(self.source).stem}_chunk{self.chunk_index}"


def load_text_files(data_dir: str = "data/raw") -> list[dict]:
    """data/raw/ 以下の全テキストファイルを読み込む"""
    docs = []
    patterns = [f"{data_dir}/**/*.txt", f"{data_dir}/**/*.md"]
    for pattern in patterns:
        for filepath in glob.glob(pattern, recursive=True):
            try:
                text = Path(filepath).read_text(encoding="utf-8")
                docs.append({"content": text, "source": filepath})
                print(f"  [OK] {filepath} ({len(text)} chars)")
            except Exception as e:
                print(f"  [NG] {filepath}: {e}")
    return docs


def split_into_chunks(
    text: str,
    chunk_size: int = 400,
    overlap: int = 80,
) -> list[str]:
    """
    テキストを意味のある単位でチャンク分割する。
    - まず空行・見出し行で段落分割を試みる
    - 段落が chunk_size を超える場合は文字数でさらに分割
    """
    # --- 段落単位で分割 ---
    paragraphs: list[str] = []
    current: list[str] = []

    for line in text.split("\n"):
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            if current:
                paragraphs.append("\n".join(current).strip())
                current = []
            if stripped.startswith("#"):
                current.append(line)
        else:
            current.append(line)
    if current:
        paragraphs.append("\n".join(current).strip())

    # --- 段落をチャンクに結合（オーバーラップ付き） ---
    chunks: list[str] = []
    buf = ""
    for para in paragraphs:
        if not para:
            continue
        if len(buf) + len(para) > chunk_size and buf:
            chunks.append(buf.strip())
            # オーバーラップ: 前チャンクの末尾 overlap 文字を引き継ぐ
            buf = buf[-overlap:] + "\n" + para
        else:
            buf = (buf + "\n" + para).strip()

    if buf.strip():
        chunks.append(buf.strip())

    # --- 空チャンクを除去し、最低文字数を保証 ---
    return [c for c in chunks if len(c) >= 30]


def build_chunks(data_dir: str = "data/raw") -> list[TextChunk]:
    """全ファイルを読み込み、チャンクリストを返す"""
    docs = load_text_files(data_dir)
    all_chunks: list[TextChunk] = []

    for doc in docs:
        raw_chunks = split_into_chunks(doc["content"])
        for idx, chunk_text in enumerate(raw_chunks):
            all_chunks.append(
                TextChunk(
                    content=chunk_text,
                    source=doc["source"],
                    chunk_index=idx,
                    metadata={"source": doc["source"]},
                )
            )

    print(f"\n合計 {len(all_chunks)} チャンク生成（{len(docs)} ファイル）")
    return all_chunks


if __name__ == "__main__":
    chunks = build_chunks()
    for c in chunks[:3]:
        print(f"\n--- {c.doc_id} ---\n{c.content[:120]}...")
