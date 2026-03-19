# 🛸 Soul Flight Recorder (SFR)

> 自分の経験・感情を記録し、内側にある「本当にやりたいこと」を見つけるAI自己分析ツール

---

## 💡 背景

宇宙イベントの運営、ロボコン、海外ハッカソン——多くの挑戦を経るうちに、ふと気づいた。

**「自分は本当に何がしたいんだろう？」**

活動の数が増えるほど、逆に自分の軸が見えにくくなる。そんな経験から生まれたのが Soul Flight Recorder です。

過去の日記・活動ログ・技術メモをAIに読み込ませることで、「あの時どう感じていたか」を引用しながら自己分析を行います。単なる経歴整理ではなく、**感情の振れ幅からやりたいことの核心を探る**ツールです。

---

## ✨ 機能

| タブ | 機能 |
|------|------|
| 🔥 強み分析 | ワクワクのパターン・潜在的強み・関心の核心を抽出 |
| 📊 感情マップ | 活動別に没頭度・ワクワク度・達成感・モヤモヤ度を評価 |
| 🚀 未来ビジョン | 等身大の5年後シナリオと最初の一歩を生成 |
| 💬 コーチング | 記憶を参照しながら対話で内省を深めるRAGチャット |

---

## 🛠 技術スタック

- **LLM**: [Groq](https://console.groq.com) (Llama 3.3 70B)
- **RAG**: ChromaDB × sentence-transformers (`paraphrase-multilingual-MiniLM-L12-v2`)
- **UI**: Streamlit
- **環境**: Python 3.11

---

## 🚀 ローカルで動かす

### 1. リポジトリをクローン

```bash
git clone https://github.com/0822-inter/soul-flight-recorder.git
cd soul-flight-recorder
```

### 2. 依存関係をインストール

```bash
pip install -r requirements.txt
```

### 3. APIキーを設定

[console.groq.com](https://console.groq.com) で無料のAPIキーを取得し、`.env` ファイルを作成：

```bash
cp .env.example .env
# .env を編集して GROQ_API_KEY=gsk_... を記入
```

### 4. 自分のデータを追加（任意）

`data/raw/` に `.txt` または `.md` ファイルを置く。

```
data/raw/
├── diary.txt        # 日記
├── hackathon.md     # 活動振り返り
└── tech_notes.txt   # 技術メモ
```

### 5. 起動

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` が開きます。サイドバーの「インデックス構築」を押してスタート。

---

## 📁 ディレクトリ構成

```
soul-flight-recorder/
├── app.py               # Streamlit UI
├── src/
│   ├── ingestion.py     # テキスト読み込み・チャンク分割
│   ├── vectorstore.py   # ChromaDB ラッパー
│   └── analyzer.py      # RAG × LLM 分析
├── data/raw/            # 自分のテキストデータ置き場
├── requirements.txt
└── .env.example
```

---

## 🙋 作者

**Saito** — 九州工業大学 知能制御工学専攻 2年

ロボット制御・VLAモデル・宇宙イベント運営など幅広く活動しながら、「AI × ロボティクス」の交差点を探っています。

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://linkedin.com/in/YOUR_LINKEDIN)
[![GitHub](https://img.shields.io/badge/GitHub-0822--inter-black)](https://github.com/0822-inter)
