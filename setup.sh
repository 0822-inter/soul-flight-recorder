#!/bin/bash
# Soul Flight Recorder セットアップスクリプト

set -e

echo "=== Soul Flight Recorder セットアップ ==="

# 1. Conda 環境を作成
echo "[1/3] Conda 環境を構築中 (name: sfr)..."
conda env create -f environment.yml

# 2. .env ファイルを作成
if [ ! -f .env ]; then
    cp .env.example .env
    echo "[2/3] .env ファイルを作成しました。ANTHROPIC_API_KEY を設定してください。"
else
    echo "[2/3] .env ファイルは既に存在します。"
fi

echo "[3/3] セットアップ完了！"
echo ""
echo "次のステップ："
echo "  1. .env を編集して ANTHROPIC_API_KEY を設定"
echo "  2. conda activate sfr"
echo "  3. streamlit run app.py"
echo ""
echo "自分のデータを追加する場合："
echo "  data/raw/ に .txt または .md ファイルを置く"
echo "  → アプリのサイドバーで「インデックス構築」を実行"
