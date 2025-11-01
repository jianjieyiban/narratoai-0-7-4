# NarratoAI

> AI-powered automated video narration and editing tool

<div align="center">

![Version](https://img.shields.io/badge/version-0.7.4-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-green.svg)
![License](https://img.shields.io/badge/license-Modified%20MIT-lightgrey.svg)

**Automated AI Video Narration Tool**  
Video Analysis → Script Generation → Smart Editing → Voice-over & Subtitles → Final Output

[English](README-en.md) | [简体中文](README.md) | [日本語](README-ja.md)

</div>

---

## 📋 Overview

NarratoAI is an automated video narration tool powered by Large Language Models (LLMs). It provides an end-to-end solution for creating narrated videos:

1. **Intelligent Video Analysis**: Uses vision models to analyze video frames and understand content
2. **Professional Script Generation**: Automatically generates narration scripts based on video content
3. **Smart Video Editing**: Automatically clips video segments according to scripts
4. **Multi-engine TTS**: Supports Edge TTS, Azure, Tencent Cloud, and more
5. **Automatic Subtitle Generation**: Generates subtitle files in SRT format
6. **One-click Output**: Merges video, audio, BGM, and subtitles into final output

---

## ✨ Features

- **Multiple Video Types**: Movie commentary, short drama, animal world, food, documentary, and more
- **Vision Model Integration**: Supports Gemini, OpenAI, Qwen VL, and other vision models
- **Text Model Integration**: Supports DeepSeek, GPT, Gemini, Qwen, and other text models
- **Multiple TTS Engines**: Edge TTS (free), Azure, Tencent Cloud, Qwen TTS, SoulVoice
- **Web UI**: Easy-to-use Streamlit-based interface
- **Docker Support**: Ready-to-use Docker deployment

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- FFmpeg
- API keys for LLM services (visual and text models)

### Installation

```bash
# Clone repository
git clone https://github.com/jianjieyiban/narratoai-0-7-4.git
cd narratoai-0-7-4

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure
cp config.example.toml config.toml
# Edit config.toml with your API keys

# Start application
streamlit run webui.py --server.maxUploadSize=2048
```

Visit `http://localhost:8501` in your browser.

### Docker Deployment

```bash
docker-compose up -d
```

---

## ⚙️ Configuration

Edit `config.toml` to configure:

- **Vision Model**: For video frame analysis
  - Example: `gemini/gemini-2.0-flash-lite`
- **Text Model**: For script generation
  - Example: `deepseek/deepseek-chat`
- **TTS Engine**: For voice synthesis
  - Options: `edge_tts`, `azure_speech`, `tencent_tts`, etc.

See [`README.md`](README.md) (Chinese) for detailed documentation.

---

## 📖 Documentation

For detailed documentation, please refer to:
- [README.md](README.md) - Full documentation (Chinese)
- [Configuration Guide](配置说明.md) - Configuration guide

---

## 🤖 Supported Models

### Vision Models
- Gemini: `gemini-2.0-flash-lite`, `gemini-1.5-pro`
- OpenAI: `gpt-4o`, `gpt-4o-mini`
- Qwen: `qwen2.5-vl-32b-instruct`

### Text Models
- DeepSeek: `deepseek-chat`, `deepseek-reasoner`
- OpenAI: `gpt-4o`, `gpt-4o-mini`
- Gemini: `gemini-2.0-flash`
- Qwen: `qwen-plus`, `qwen-turbo`

### TTS Engines
- Edge TTS (Free)
- Azure Speech
- Tencent Cloud TTS
- Qwen TTS
- SoulVoice

---

## 📝 License

Modified MIT License - For learning and research use only, no commercial use.

See [`LICENSE`](LICENSE) file for details.

---

## 🔗 Links

- **Repository**: https://github.com/jianjieyiban/narratoai-0-7-4
- **Issues**: https://github.com/jianjieyiban/narratoai-0-7-4/issues
- **Pull Requests**: https://github.com/jianjieyiban/narratoai-0-7-4/pulls

---

**Version**: 0.7.4  
**Last Updated**: 2025-11-01
