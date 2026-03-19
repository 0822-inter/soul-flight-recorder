"""
Soul Flight Recorder (SFR) — Streamlit UI
実行: streamlit run app.py
"""

from __future__ import annotations

import os
import time

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Streamlit Cloud の Secrets にも対応
if "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

# ------------------------------------------------------------------ #
# ページ設定
# ------------------------------------------------------------------ #

st.set_page_config(
    page_title="Soul Flight Recorder",
    page_icon="🛸",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🛸 Soul Flight Recorder")
st.caption("自分の経験・感情を記録し、内側にある「本当にやりたいこと」を見つけるAI")

# ------------------------------------------------------------------ #
# セッション状態の初期化
# ------------------------------------------------------------------ #

if "store" not in st.session_state:
    st.session_state.store = None
if "analyzer" not in st.session_state:
    st.session_state.analyzer = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "indexed" not in st.session_state:
    st.session_state.indexed = False


# ------------------------------------------------------------------ #
# サイドバー：インデックス管理
# ------------------------------------------------------------------ #

with st.sidebar:
    st.header("📁 データ管理")

    api_key = st.text_input(
        "Groq API Key",
        value=os.environ.get("GROQ_API_KEY", ""),
        type="password",
        help=".env ファイルに GROQ_API_KEY=... と書いておくと自動入力されます",
    )
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key

    st.divider()

    data_dir = st.text_input("データディレクトリ", value="data/raw")
    force_rebuild = st.checkbox("インデックスを再構築", value=False)

    if st.button("🔄 インデックス構築 / 更新", use_container_width=True):
        if not api_key:
            st.error("Google AI Studio の API Key を入力してください")
        else:
            with st.spinner("データを読み込んでインデックスを構築中..."):
                from src.vectorstore import build_index
                from src.analyzer import SFRAnalyzer

                st.session_state.store = build_index(
                    data_dir=data_dir, force=force_rebuild
                )
                st.session_state.analyzer = SFRAnalyzer(st.session_state.store)
                st.session_state.indexed = True
            st.success(
                f"完了！ {st.session_state.store.count()} チャンクをインデックス済み"
            )

    if st.session_state.indexed:
        st.info(f"インデックス済み: {st.session_state.store.count()} チャンク")

    st.divider()
    st.caption(
        "📝 `data/raw/` に .txt / .md ファイルを追加して\n"
        "「インデックス構築」を押すと記憶が増えます"
    )


# ------------------------------------------------------------------ #
# メインエリア：タブ構成
# ------------------------------------------------------------------ #

tab1, tab2, tab3, tab4 = st.tabs(
    ["🔥 強み分析", "📊 感情マップ", "🚀 未来ビジョン", "💬 対話コーチング"]
)

def _require_index():
    if not st.session_state.indexed:
        st.warning(
            "サイドバーで **インデックス構築** を実行してください。\n\n"
            "`data/raw/` にテキストファイルを置き、API Key を入力後にボタンを押します。"
        )
        return False
    return True


# ------------------------------------------------------------------ #
# Tab 1: 強み・関心の抽出
# ------------------------------------------------------------------ #

with tab1:
    st.subheader("🔥 強み・関心の抽出")
    st.write(
        "過去の経験記録から「ワクワクのパターン」と「潜在的な強み」を抽出します。"
    )

    if st.button("分析スタート", key="btn_strength", use_container_width=True):
        if _require_index():
            result_area = st.empty()
            full_text = ""
            with st.spinner("Claude が分析中..."):
                for chunk in st.session_state.analyzer.extract_strengths_stream():
                    full_text += chunk
                    result_area.markdown(full_text + "▌")
            result_area.markdown(full_text)


# ------------------------------------------------------------------ #
# Tab 2: 感情マップ
# ------------------------------------------------------------------ #

with tab2:
    st.subheader("📊 感情マッピング")
    st.write(
        "各活動での没頭度・ワクワク度・達成感・モヤモヤ度を分析します。"
    )

    if st.button("感情マップを生成", key="btn_emotion", use_container_width=True):
        if _require_index():
            result_area = st.empty()
            full_text = ""
            with st.spinner("感情パターンを解析中..."):
                for chunk in st.session_state.analyzer.analyze_emotion_timeline_stream():
                    full_text += chunk
                    result_area.markdown(full_text + "▌")
            result_area.markdown(full_text)


# ------------------------------------------------------------------ #
# Tab 3: 未来ビジョン
# ------------------------------------------------------------------ #

with tab3:
    st.subheader("🚀 等身大の未来予想図")
    st.write(
        "強みと関心を統合した「5年後のビジョン」と「最初の一歩」を描きます。"
    )

    if st.button("ビジョンを生成", key="btn_vision", use_container_width=True):
        if _require_index():
            result_area = st.empty()
            full_text = ""
            with st.spinner("未来像を描いています..."):
                for chunk in st.session_state.analyzer.generate_future_vision_stream():
                    full_text += chunk
                    result_area.markdown(full_text + "▌")
            result_area.markdown(full_text)


# ------------------------------------------------------------------ #
# Tab 4: 対話コーチング（マルチターン RAG チャット）
# ------------------------------------------------------------------ #

with tab4:
    st.subheader("💬 自己理解コーチング")
    st.write(
        "過去の記録を参照しながら、あなたの問いに答えます。\n"
        "「自分の強みって何？」「なぜあの活動が楽しかったの？」など自由に聞いてみてください。"
    )

    # チャット履歴の表示
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ユーザー入力
    if prompt := st.chat_input("何でも聞いてみてください..."):
        if not _require_index():
            pass
        elif not api_key:
            st.error("API Key を入力してください")
        else:
            # ユーザーメッセージ表示
            with st.chat_message("user"):
                st.markdown(prompt)

            # AI 応答（ストリーミング）
            with st.chat_message("assistant"):
                response_area = st.empty()
                full_response = ""

                for chunk in st.session_state.analyzer.chat_stream(
                    user_input=prompt,
                    history=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.chat_history
                    ],
                ):
                    full_response += chunk
                    response_area.markdown(full_response + "▌")

                response_area.markdown(full_response)

            # 履歴に追加
            st.session_state.chat_history.append(
                {"role": "user", "content": prompt}
            )
            st.session_state.chat_history.append(
                {"role": "assistant", "content": full_response}
            )

    if st.session_state.chat_history:
        if st.button("🗑️ 会話をリセット", key="btn_reset"):
            st.session_state.chat_history = []
            st.rerun()
