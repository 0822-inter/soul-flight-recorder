"""
Soul Flight Recorder (SFR) — Streamlit UI
実行: streamlit run app.py
"""

from __future__ import annotations

import os
import uuid

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Streamlit Cloud の Secrets にも対応（ローカルでは secrets.toml がなくてもOK）
try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

# ------------------------------------------------------------------ #
# DB 初期化（起動時1回）
# ------------------------------------------------------------------ #

from src.db import init_db
init_db()

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
# インタビュー用セッションID（ブラウザセッション中は固定）
if "interview_session_id" not in st.session_state:
    st.session_state.interview_session_id = str(uuid.uuid4())
# インタビュー履歴キャッシュ（DB再読み込みを減らすため）
if "interview_history" not in st.session_state:
    st.session_state.interview_history = []
# 手動フェーズ管理（0=ICEBREAK, 1=EXPLORE, 2=PATTERN, 3=FUTURE）
if "interview_phase_idx" not in st.session_state:
    st.session_state.interview_phase_idx = 0
# まとめキャッシュ
if "interview_summary" not in st.session_state:
    st.session_state.interview_summary = ""


# ------------------------------------------------------------------ #
# サイドバー
# ------------------------------------------------------------------ #

with st.sidebar:
    # ── 言語スイッチ ──
    lang_display = st.radio(
        "Language / 言語",
        options=["日本語", "English"],
        horizontal=True,
        key="lang_display",
    )
    lang = "ja" if lang_display == "日本語" else "en"

    st.divider()

    # ── API Key ──
    st.header("🔑 API Key")
    api_key = st.text_input(
        "Groq API Key",
        value=os.environ.get("GROQ_API_KEY", ""),
        type="password",
        help=".env ファイルに GROQ_API_KEY=... と書いておくと自動入力されます",
    )
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key

    st.divider()

    # ── データ管理（既存機能） ──
    st.header("📁 データ管理" if lang == "ja" else "📁 Data")

    data_dir = st.text_input(
        "データディレクトリ" if lang == "ja" else "Data directory",
        value="data/raw",
    )
    force_rebuild = st.checkbox(
        "インデックスを再構築" if lang == "ja" else "Rebuild index",
        value=False,
    )

    if st.button(
        "🔄 インデックス構築 / 更新" if lang == "ja" else "🔄 Build / Update Index",
        use_container_width=True,
    ):
        if not api_key:
            st.error("Groq API Key を入力してください" if lang == "ja" else "Please enter your Groq API Key")
        else:
            with st.spinner("インデックスを構築中..." if lang == "ja" else "Building index..."):
                from src.vectorstore import build_index
                from src.analyzer import SFRAnalyzer

                st.session_state.store = build_index(
                    data_dir=data_dir, force=force_rebuild
                )
                st.session_state.analyzer = SFRAnalyzer(st.session_state.store)
                st.session_state.indexed = True
            st.success(
                f"完了！ {st.session_state.store.count()} チャンクをインデックス済み"
                if lang == "ja"
                else f"Done! {st.session_state.store.count()} chunks indexed"
            )

    if st.session_state.indexed:
        st.info(
            f"インデックス済み: {st.session_state.store.count()} チャンク"
            if lang == "ja"
            else f"Indexed: {st.session_state.store.count()} chunks"
        )

    st.divider()
    st.caption(
        "📝 `data/raw/` に .txt / .md ファイルを追加して\n「インデックス構築」を押すと記憶が増えます"
        if lang == "ja"
        else "📝 Add .txt / .md files to `data/raw/`\nthen press Build Index."
    )


# ------------------------------------------------------------------ #
# メインエリア：タブ構成
# ------------------------------------------------------------------ #

if lang == "ja":
    tab_labels = ["🎤 インタビュー", "🔥 強み分析", "📊 感情マップ", "🚀 未来ビジョン", "💬 対話コーチング"]
else:
    tab_labels = ["🎤 Interview", "🔥 Strengths", "📊 Emotion Map", "🚀 Future Vision", "💬 Coaching"]

tab_interview, tab1, tab2, tab3, tab4 = st.tabs(tab_labels)

def _require_index():
    if not st.session_state.indexed:
        msg = (
            "サイドバーで **インデックス構築** を実行してください。\n\n"
            "`data/raw/` にテキストファイルを置き、API Key を入力後にボタンを押します。"
            if lang == "ja"
            else "Please run **Build Index** in the sidebar.\n\n"
            "Add text files to `data/raw/` and click the button after entering your API Key."
        )
        st.warning(msg)
        return False
    return True


# ------------------------------------------------------------------ #
# Tab 0: インタビュー
# ------------------------------------------------------------------ #

with tab_interview:
    from src.db import (
        create_session, save_message, get_messages,
        user_turn_count, clear_session_messages,
    )
    from src.interview import InterviewEngine, PHASE_LABELS, Phase

    if lang == "ja":
        st.subheader("🎤 AIインタビュー")
        st.write("質問に答えていくだけで、あなたの「本当にやりたいこと」が見えてきます。")
    else:
        st.subheader("🎤 AI Interview")
        st.write("Just answer the questions — your true passions and strengths will emerge naturally.")

    session_id = st.session_state.interview_session_id
    create_session(session_id, lang)

    # DB から履歴取得
    db_history = get_messages(session_id)
    st.session_state.interview_history = db_history

    # ── フェーズ（手動管理） ──
    phases_list = list(Phase)
    phase_idx = st.session_state.interview_phase_idx
    current_phase = phases_list[phase_idx]
    phase_labels = PHASE_LABELS[lang]

    # フェーズインジケーター + 「次のフェーズへ」ボタン
    indicator_cols = st.columns(len(phases_list) + 1)
    for i, (col, ph) in enumerate(zip(indicator_cols[:len(phases_list)], phases_list)):
        label = phase_labels[ph]
        if i < phase_idx:
            col.success(label)
        elif i == phase_idx:
            col.info(f"**{label}**")
        else:
            col.markdown(f"<span style='color:gray'>{label}</span>", unsafe_allow_html=True)

    with indicator_cols[-1]:
        next_label = "次のフェーズへ →" if lang == "ja" else "Next Phase →"
        next_disabled = phase_idx >= len(phases_list) - 1
        if st.button(next_label, disabled=next_disabled, key="btn_next_phase"):
            st.session_state.interview_phase_idx += 1
            st.rerun()

    st.divider()

    # ── レイアウト: チャット | まとめ ──
    chat_col, summary_col = st.columns([3, 2])

    with summary_col:
        summary_title = "📋 これまでのまとめ" if lang == "ja" else "📋 Summary So Far"
        st.markdown(f"**{summary_title}**")

        update_label = "まとめを更新" if lang == "ja" else "Update Summary"
        if st.button(update_label, key="btn_summary", use_container_width=True):
            if not api_key:
                st.error("API Key が必要です" if lang == "ja" else "API Key required")
            elif not st.session_state.interview_history:
                st.info("まだ会話がありません" if lang == "ja" else "No conversation yet")
            else:
                engine = InterviewEngine(api_key=api_key)
                summary_area = st.empty()
                full_summary = ""
                with st.spinner("まとめを生成中..." if lang == "ja" else "Generating summary..."):
                    for chunk in engine.stream_summary(
                        history=[{"role": m["role"], "content": m["content"]}
                                 for m in st.session_state.interview_history],
                        lang=lang,
                    ):
                        full_summary += chunk
                        summary_area.markdown(full_summary + "▌")
                summary_area.markdown(full_summary)
                st.session_state.interview_summary = full_summary

        if st.session_state.interview_summary:
            st.markdown(st.session_state.interview_summary)
        else:
            placeholder_text = (
                "「まとめを更新」ボタンを押すと、\nここに会話のまとめが表示されます。"
                if lang == "ja"
                else "Press 'Update Summary' to see\na summary of your conversation here."
            )
            st.caption(placeholder_text)

    with chat_col:
        # チャット履歴の表示
        for msg in st.session_state.interview_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # 初回: AIから先に挨拶を出す
        if len(st.session_state.interview_history) == 0:
            if not api_key:
                st.info(
                    "サイドバーに Groq API Key を入力するとインタビューが始まります。"
                    if lang == "ja"
                    else "Enter your Groq API Key in the sidebar to start the interview."
                )
            else:
                engine = InterviewEngine(api_key=api_key)
                with st.chat_message("assistant"):
                    response_area = st.empty()
                    full_response = ""
                    for chunk in engine.stream_response(history=[], lang=lang, phase=current_phase):
                        full_response += chunk
                        response_area.markdown(full_response + "▌")
                    response_area.markdown(full_response)
                save_message(session_id, "assistant", full_response, current_phase.value)
                st.rerun()

        # ユーザー入力
        placeholder = "ここに答えを入力してください..." if lang == "ja" else "Type your answer here..."
        if user_input := st.chat_input(placeholder):
            if not api_key:
                st.error("Groq API Key を入力してください" if lang == "ja" else "Please enter your Groq API Key")
            else:
                save_message(session_id, "user", user_input, current_phase.value)
                with st.chat_message("user"):
                    st.markdown(user_input)

                updated_history = get_messages(session_id)
                engine = InterviewEngine(api_key=api_key)
                with st.chat_message("assistant"):
                    response_area = st.empty()
                    full_response = ""
                    for chunk in engine.stream_response(
                        history=[{"role": m["role"], "content": m["content"]} for m in updated_history],
                        lang=lang,
                        phase=current_phase,
                    ):
                        full_response += chunk
                        response_area.markdown(full_response + "▌")
                    response_area.markdown(full_response)

                save_message(session_id, "assistant", full_response, current_phase.value)
                st.rerun()

        # リセットボタン
        if st.session_state.interview_history:
            st.divider()
            reset_label = "🗑️ インタビューをリセット" if lang == "ja" else "🗑️ Reset Interview"
            if st.button(reset_label, key="btn_interview_reset"):
                clear_session_messages(session_id)
                st.session_state.interview_history = []
                st.session_state.interview_phase_idx = 0
                st.session_state.interview_summary = ""
                st.rerun()


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
