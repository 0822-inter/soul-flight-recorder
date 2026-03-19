"""
Gemini (Google AI Studio) による自己分析モジュール
RAGで関連記憶を引いて、強み・関心・感情パターンを抽出する
"""

from __future__ import annotations

import os
from typing import Generator

from groq import Groq
from dotenv import load_dotenv

from src.vectorstore import MemoryStore

load_dotenv()

SYSTEM_PROMPT = """\
あなたは「Soul Flight Recorder (SFR)」というAIコーチです。
ユーザーの過去の経験・日記・メモを読み込み、
客観的かつ温かみのある視点で「自己理解」を深めるサポートをします。

分析する際は以下を意識してください：
1. 事実の列挙ではなく、**感情の振れ幅（ワクワク・モヤモヤ・没頭感）** に注目する
2. ユーザーが気づいていないパターンや強みを引き出す
3. 断定ではなく「問いかけ」を交えて、本人が内省できるよう促す
4. 引用する際は「あの時、〇〇と感じていた」のように過去の記録に基づく

出力は日本語で、読みやすいマークダウン形式で。\
"""

MODEL_NAME = "llama-3.3-70b-versatile"


def _format_context(hits: list[dict]) -> str:
    """検索結果をプロンプト用文字列に整形"""
    if not hits:
        return "（関連する記録が見つかりませんでした）"
    lines = []
    for i, h in enumerate(hits, 1):
        lines.append(f"[記録 {i}] (関連度: {h['score']})\n{h['content']}")
    return "\n\n".join(lines)


class SFRAnalyzer:
    """RAG + Gemini で自己分析を行うクラス"""

    def __init__(self, store: MemoryStore):
        self.store = store
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    def _stream(self, prompt: str) -> Generator[str, None, None]:
        """Groq にプロンプトを送りストリーミングで返す"""
        stream = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )
        for chunk in stream:
            text = chunk.choices[0].delta.content
            if text:
                yield text

    # ------------------------------------------------------------------ #
    # 強み・関心の抽出（ストリーミング）
    # ------------------------------------------------------------------ #

    def extract_strengths_stream(self) -> Generator[str, None, None]:
        hits = self.store.search("強み ワクワク 没頭 好き 達成感 楽しい", n_results=6)
        context = _format_context(hits)
        prompt = f"""\
以下はユーザーのこれまでの経験・活動・感情に関する記録です。

---
{context}
---

上記の記録を分析して、以下の形式で出力してください：

## 🔥 ワクワクのパターン（Excitement Map）
どんな状況・行動で感情が最も高まっているか、具体的に引用しながら説明。

## 💪 潜在的な強み（Strength Profile）
経験から読み取れる能力・資質を3〜5個、それぞれ根拠となる体験とともに。

## 🎯 関心の核心（Core Interest）
様々な活動の奥にある「共通のテーマ」は何か？

## 💭 問いかけ（Reflection Questions）
自己理解をさらに深めるための問いを2〜3個。\
"""
        yield from self._stream(prompt)

    # ------------------------------------------------------------------ #
    # 感情タイムライン分析（ストリーミング）
    # ------------------------------------------------------------------ #

    def analyze_emotion_timeline_stream(self) -> Generator[str, None, None]:
        hits = self.store.search("感じたこと 嬉しい しんどい 達成感 モヤモヤ 刺激", n_results=8)
        context = _format_context(hits)
        prompt = f"""\
以下の記録から、各活動における感情の強度を分析してください。

---
{context}
---

## 📊 感情マッピング（Emotion Mapping）
各活動について以下を評価してください：
- **没頭度** (1-5): どれだけ時間を忘れて集中できたか
- **ワクワク度** (1-5): 取り組む前・最中の高揚感
- **達成感** (1-5): 完了後の充実感
- **モヤモヤ度** (1-5): 違和感・葛藤の大きさ（大きいほど要注意）

表形式で整理した後、「最もエネルギーが湧いていた活動」と「そうでない活動」の
違いについて考察してください。\
"""
        yield from self._stream(prompt)

    # ------------------------------------------------------------------ #
    # カスタムクエリ（RAG チャット）
    # ------------------------------------------------------------------ #

    def chat_stream(
        self,
        user_input: str,
        history: list[dict] | None = None,
    ) -> Generator[str, None, None]:
        hits = self.store.search(user_input, n_results=4)
        context = _format_context(hits)

        # Gemini の history 形式に変換
        gemini_history = []
        for msg in (history or []):
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg["content"]]})

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in (history or []):
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": f"""\
【参照できる過去の記録】
{context}

【ユーザーの質問・相談】
{user_input}"""})

        stream = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            text = chunk.choices[0].delta.content
            if text:
                yield text

    # ------------------------------------------------------------------ #
    # 将来像の描画（ストリーミング）
    # ------------------------------------------------------------------ #

    def generate_future_vision_stream(self) -> Generator[str, None, None]:
        hits = self.store.search("やりたいこと 悩み 将来 可能性 ロボット AI", n_results=6)
        context = _format_context(hits)
        prompt = f"""\
以下の記録を読んだうえで、「等身大の5年後ビジョン」を一緒に描いてください。

---
{context}
---

## 🚀 等身大の未来予想図（Future Vision Map）

現実的でありながら、このユーザーが「やりたくてたまらない」と感じるような
5年後のシナリオを描いてください。

条件：
- 現在の強み・関心を踏まえる
- 「研究者 / エンジニア / 起業家」などの固定ラベルに縛られない
- 具体的な活動内容（何を作っているか、誰と関わっているか）を描く
- ポジティブな可能性を示しながら、「その実現に向けた最初の一歩」も提案する\
"""
        yield from self._stream(prompt)


if __name__ == "__main__":
    from src.vectorstore import build_index

    store = build_index()
    analyzer = SFRAnalyzer(store)

    print("=== 強み抽出 ===\n")
    for chunk in analyzer.extract_strengths_stream():
        print(chunk, end="", flush=True)
    print("\n")
