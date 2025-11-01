# NarratoAI

> AIを活用した自動ビデオナレーション・編集ツール

<div align="center">

![Version](https://img.shields.io/badge/version-0.7.4-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-green.svg)
![License](https://img.shields.io/badge/license-Modified%20MIT-lightgrey.svg)

**自動化AIビデオナレーションツール**  
ビデオ分析 → スクリプト生成 → スマート編集 → 音声・字幕 → 最終出力

[English](README-en.md) | [简体中文](README.md) | [日本語](README-ja.md)

</div>

---

## 📋 概要

NarratoAIは大規模言語モデル（LLM）を活用した自動ビデオナレーションツールです。ナレーション付きビデオを作成するためのエンドツーエンドソリューションを提供します：

1. **インテリジェントなビデオ分析**: ビジョンモデルを使用してビデオフレームを分析し、コンテンツを理解
2. **プロフェッショナルなスクリプト生成**: ビデオコンテンツに基づいてナレーションスクリプトを自動生成
3. **スマートなビデオ編集**: スクリプトに従ってビデオセグメントを自動クリップ
4. **マルチエンジンTTS**: Edge TTS、Azure、Tencent Cloudなどをサポート
5. **自動字幕生成**: SRT形式の字幕ファイルを生成
6. **ワンクリック出力**: ビデオ、オーディオ、BGM、字幕を最終出力にマージ

---

## ✨ 機能

- **複数のビデオタイプ**: 映画解説、ショートドラマ、動物世界、料理、ドキュメンタリーなど
- **ビジョンモデル統合**: Gemini、OpenAI、Qwen VLなどのビジョンモデルをサポート
- **テキストモデル統合**: DeepSeek、GPT、Gemini、Qwenなどのテキストモデルをサポート
- **複数のTTSエンジン**: Edge TTS（無料）、Azure、Tencent Cloud、Qwen TTS、SoulVoice
- **Web UI**: 使いやすいStreamlitベースのインターフェース
- **Dockerサポート**: すぐに使えるDockerデプロイメント

---

## 🚀 クイックスタート

### 前提条件

- Python 3.12+
- FFmpeg
- LLMサービスのAPIキー（ビジョンとテキストモデル）

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/jianjieyiban/narratoai-0-7-4.git
cd narratoai-0-7-4

# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt

# 設定ファイルをコピーして設定
cp config.example.toml config.toml
# config.tomlにAPIキーを設定

# アプリケーションを起動
streamlit run webui.py --server.maxUploadSize=2048
```

ブラウザで `http://localhost:8501` にアクセスしてください。

### Dockerデプロイメント

```bash
docker-compose up -d
```

---

## ⚙️ 設定

`config.toml`を編集して設定：

- **ビジョンモデル**: ビデオフレーム分析用
  - 例: `gemini/gemini-2.0-flash-lite`
- **テキストモデル**: スクリプト生成用
  - 例: `deepseek/deepseek-chat`
- **TTSエンジン**: 音声合成用
  - オプション: `edge_tts`, `azure_speech`, `tencent_tts`など

詳細なドキュメントについては、[`README.md`](README.md)（中国語）を参照してください。

---

## 📖 ドキュメント

詳細なドキュメントについては、以下を参照してください：
- [README.md](README.md) - 完全なドキュメント（中国語）
- [設定ガイド](配置说明.md) - 設定ガイド

---

## 🤖 サポートされているモデル

### ビジョンモデル
- Gemini: `gemini-2.0-flash-lite`, `gemini-1.5-pro`
- OpenAI: `gpt-4o`, `gpt-4o-mini`
- Qwen: `qwen2.5-vl-32b-instruct`

### テキストモデル
- DeepSeek: `deepseek-chat`, `deepseek-reasoner`
- OpenAI: `gpt-4o`, `gpt-4o-mini`
- Gemini: `gemini-2.0-flash`
- Qwen: `qwen-plus`, `qwen-turbo`

### TTSエンジン
- Edge TTS（無料）
- Azure Speech
- Tencent Cloud TTS
- Qwen TTS
- SoulVoice

---

## 📝 ライセンス

修正MITライセンス - 学習と研究目的のみ、商用利用不可。

詳細は[`LICENSE`](LICENSE)ファイルを参照してください。

---

## 🔗 リンク

- **リポジトリ**: https://github.com/jianjieyiban/narratoai-0-7-4
- **Issues**: https://github.com/jianjieyiban/narratoai-0-7-4/issues
- **Pull Requests**: https://github.com/jianjieyiban/narratoai-0-7-4/pulls

---

**バージョン**: 0.7.4  
**最終更新**: 2025-11-01
