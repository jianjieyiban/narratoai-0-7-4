# NarratoAI

> 基于大语言模型的自动化影视解说视频生成工具

<div align="center">

![Version](https://img.shields.io/badge/version-0.7.4-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-green.svg)
![License](https://img.shields.io/badge/license-Modified%20MIT-lightgrey.svg)

**一站式 AI 影视解说视频生成工具**  
自动分析视频内容 → 生成专业解说文案 → 智能剪辑 → 配音字幕 → 成品输出

</div>

---

## 📋 目录

- [项目简介](#项目简介)
- [核心功能](#核心功能)
- [技术架构](#技术架构)
- [系统要求](#系统要求)
- [快速开始](#快速开始)
  - [方式一：本地运行](#方式一本地运行)
  - [方式二：Docker 部署](#方式二docker-部署)
- [配置说明](#配置说明)
- [使用指南](#使用指南)
- [项目结构](#项目结构)
- [支持的模型](#支持的模型)
- [常见问题](#常见问题)
- [许可证](#许可证)

---

## 🎯 项目简介

NarratoAI 是一个基于大语言模型的自动化影视解说视频生成工具，通过 AI 技术实现从视频分析到成品输出的全流程自动化：

1. **智能视频分析**：使用视觉大模型分析视频关键帧，理解视频内容
2. **专业文案生成**：基于视频内容自动生成符合自媒体平台标准的解说文案
3. **智能视频剪辑**：根据文案自动裁剪视频片段，保留精彩内容
4. **多引擎配音**：支持 Edge TTS、Azure、腾讯云等多种 TTS 引擎
5. **自动字幕生成**：自动生成字幕文件，支持 SRT 格式
6. **一键合成输出**：自动合并视频、配音、背景音乐和字幕，输出最终视频

---

## ✨ 核心功能

### 视频内容分析
- 自动提取视频关键帧
- 使用视觉大模型分析画面内容（动物、人物、场景、动作等）
- 生成详细的画面描述和时间轴信息
- 支持多种视频格式（MP4、AVI、MOV 等）

### 智能文案生成
支持多种视频类型的专业解说文案生成：
- **影视解说**：电影、电视剧深度解读
- **短剧解说**：快节奏剧情梳理
- **动物世界**：自然纪录片风格
- **野外美食**：美食制作过程讲解
- **影视混剪**：主题混剪视频
- **通用纪录片**：各类纪录片解说

### 视频剪辑功能
- 根据文案自动裁剪视频片段
- 支持保留原声（OST）或替换为配音
- 自动处理视频时长与音频同步
- 支持添加背景音乐

### 语音合成（TTS）
支持多种 TTS 引擎：
- **Edge TTS**：免费、无需 API Key
- **Azure Speech**：高质量语音合成
- **腾讯云 TTS**：中文优化
- **SoulVoice**：语音克隆
- **Qwen TTS**：通义千问语音合成

### 字幕生成
- 自动生成 SRT 字幕文件
- 支持自定义字体、颜色、大小
- 自动同步视频时间轴
- 支持多语言字幕

---

## 🏗️ 技术架构

### 核心技术栈

- **前端框架**：Streamlit（Web UI）
- **视频处理**：FFmpeg、MoviePy
- **音频处理**：Pydub、Edge TTS
- **AI 服务**：LiteLLM（统一 LLM 接口）
- **视觉模型**：支持 Gemini、OpenAI、Qwen VL 等
- **文本模型**：支持 DeepSeek、GPT、Gemini、Qwen 等

### 项目架构

```
NarratoAI/
├── app/                    # 核心应用代码
│   ├── config/            # 配置管理
│   ├── models/            # 数据模型
│   ├── services/          # 业务服务层
│   │   ├── llm/          # LLM 服务（统一接口）
│   │   ├── prompts/      # 提示词管理
│   │   └── ...           # 其他服务
│   └── utils/             # 工具函数
├── webui/                  # Web UI 界面
│   ├── components/        # UI 组件
│   ├── tools/             # 业务工具
│   └── utils/             # UI 工具
├── resource/              # 资源文件
│   ├── videos/           # 视频文件
│   ├── scripts/           # 生成的脚本
│   └── templates/         # 模板文件
├── storage/               # 存储目录
│   ├── temp/             # 临时文件
│   └── tasks/            # 任务输出
└── docs/                  # 文档
```

---

## 💻 系统要求

### 最低配置
- **操作系统**：Windows 10/11、macOS 11.0+、Linux
- **CPU**：4 核或以上（推荐 8 核）
- **内存**：8GB 或以上（推荐 16GB）
- **存储空间**：至少 5GB 可用空间
- **Python**：3.12 或更高版本

### 必需软件
- Python 3.12+
- FFmpeg（用于视频处理）
- Git（可选，用于克隆仓库）

### 可选软件
- Docker（用于容器化部署）
- CUDA（用于 GPU 加速，非必需）

---

## 🚀 快速开始

### 方式一：本地运行

#### 1. 克隆仓库

```bash
git clone https://github.com/jianjieyiban/narratoai-0-7-4.git
cd narratoai-0-7-4
```

#### 2. 创建虚拟环境（推荐）

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 配置应用

复制示例配置文件：
```bash
cp config.example.toml config.toml
```

编辑 `config.toml`，配置你的 API 密钥：
- 视觉模型 API Key（如 Gemini、Qwen VL 等）
- 文本模型 API Key（如 DeepSeek、OpenAI 等）
- TTS 服务配置（如需要）

#### 5. 启动应用

```bash
streamlit run webui.py --server.maxUploadSize=2048
```

#### 6. 访问应用

在浏览器中打开：`http://localhost:8501`

---

### 方式二：Docker 部署

#### 1. 克隆仓库

```bash
git clone https://github.com/jianjieyiban/narratoai-0-7-4.git
cd narratoai-0-7-4
```

#### 2. 配置应用

复制并编辑配置文件：
```bash
cp config.example.toml config.toml
# 编辑 config.toml，配置你的 API 密钥
```

#### 3. 构建并启动容器

```bash
docker-compose up -d
```

或使用一键部署脚本：
```bash
./docker-deploy.sh
```

#### 4. 访问应用

在浏览器中打开：`http://localhost:8501`

#### 5. 查看日志

```bash
docker-compose logs -f
```

#### 6. 停止服务

```bash
docker-compose down
```

---

## ⚙️ 配置说明

### 配置文件结构

配置文件 `config.toml` 采用 TOML 格式，主要包含以下部分：

#### 应用配置

```toml
[app]
project_version = "0.7.4"
llm_vision_timeout = 120      # 视觉模型超时时间（秒）
llm_text_timeout = 180     # 文本模型超时时间（秒）
llm_max_retries = 3           # API 重试次数
```

#### LLM 配置

使用 LiteLLM 统一接口，支持 100+ 模型提供商：

```toml
[app]
# 视觉模型配置
vision_llm_provider = "litellm"
vision_litellm_model_name = "gemini/gemini-2.0-flash-lite"
vision_litellm_api_key = "your-api-key"
vision_litellm_base_url = ""  # 可选

# 文本模型配置
text_llm_provider = "litellm"
text_litellm_model_name = "deepseek/deepseek-chat"
text_litellm_api_key = "your-api-key"
text_litellm_base_url = ""  # 可选
```

#### TTS 配置

```toml
[ui]
tts_engine = "edge_tts"  # 可选：edge_tts, azure_speech, tencent_tts, soulvoice, tts_qwen
edge_voice_name = "zh-CN-YunxiNeural-Male"
edge_volume = 100
edge_rate = 1.0
edge_pitch = 0
```

#### 视频处理配置

```toml
[frames]
frame_interval_input = 3      # 关键帧提取间隔（秒）
vision_batch_size = 10       # 视觉模型单次处理的帧数
```

### API Key 获取

#### 视觉模型
- **Gemini**：https://makersuite.google.com/app/apikey
- **OpenAI**：https://platform.openai.com/api-keys
- **Qwen（阿里）**：https://bailian.console.aliyun.com/?tab=model#/api-key

#### 文本模型
- **DeepSeek**：https://platform.deepseek.com/api_keys
- **OpenAI**：https://platform.openai.com/api-keys
- **Gemini**：https://makersuite.google.com/app/apikey
- **Qwen**：https://bailian.console.aliyun.com/?tab=model#/api-key

#### TTS 服务
- **Azure Speech**：https://portal.azure.com
- **腾讯云 TTS**：https://console.cloud.tencent.com/cam/capi
- **Qwen TTS**：https://bailian.console.aliyun.com/?tab=model#/api-key

---

## 📖 使用指南

### 基本流程

1. **上传视频**
   - 点击"上传视频"按钮，选择要处理的视频文件
   - 支持 MP4、AVI、MOV 等常见格式

2. **生成脚本**
   - 选择视频类型（影视解说、动物世界等）
   - 点击"AI生成画面解说脚本"
   - 等待视频分析和文案生成完成

3. **编辑脚本（可选）**
   - 在脚本编辑器中修改生成的文案
   - 调整时间轴和片段内容

4. **配置参数**
   - **音频设置**：选择 TTS 引擎、语音、音量等
   - **字幕设置**：配置字体、颜色、大小等
   - **视频设置**：背景音乐、原声保留等

5. **生成视频**
   - 点击"生成视频"按钮
   - 等待处理完成（可能需要几分钟到几十分钟）
   - 下载生成的视频文件

### 高级功能

#### 视频类型选择

根据视频内容选择对应的类型，系统会使用相应的提示词模板：
- **影视解说**：适合电影、电视剧
- **短剧解说**：适合快节奏短剧
- **动物世界**：适合自然纪录片
- **野外美食**：适合美食制作视频
- **影视混剪**：适合多部影片混剪
- **通用纪录片**：其他类型纪录片

#### 原声策略（OST）

- **OST=0**：完全替换为配音（适合影视解说）
- **OST=1**：部分保留原声（适合短剧关键片段）
- **OST=2**：保留环境音（适合动物世界、美食视频）

#### 批量处理

可以将多个视频依次上传处理，每个视频会生成独立的脚本和输出文件。

---

## 📁 项目结构

```
narratoai-0-7-4/
│
├── app/                          # 核心应用代码
│   ├── config/                   # 配置管理模块
│   │   ├── config.py            # 主配置加载
│   │   ├── audio_config.py       # 音频配置
│   │   └── ffmpeg_config.py       # FFmpeg 配置
│   │
│   ├── models/                   # 数据模型
│   │   ├── schema.py            # 数据结构定义
│   │   ├── const.py             # 常量定义
│   │   └── exception.py         # 异常定义
│   │
│   ├── services/                # 业务服务层
│   │   ├── llm/                 # LLM 服务
│   │   │   ├── manager.py       # 服务管理器
│   │   │   ├── litellm_provider.py  # LiteLLM 提供商
│   │   │   └── unified_service.py   # 统一服务接口
│   │   │
│   │   ├── prompts/             # 提示词管理
│   │   │   ├── registry.py      # 提示词注册表
│   │   │   ├── manager.py       # 提示词管理器
│   │   │   ├── documentary/     # 纪录片提示词
│   │   │   ├── animal_world/    # 动物世界提示词
│   │   │   ├── movie_commentary/ # 影视解说提示词
│   │   │   └── ...              # 其他类型提示词
│   │   │
│   │   ├── generate_narration_script.py  # 文案生成服务
│   │   ├── voice.py             # 语音合成服务
│   │   ├── clip_video.py        # 视频剪辑服务
│   │   ├── generate_video.py    # 视频生成服务
│   │   ├── subtitle_merger.py   # 字幕合并服务
│   │   └── ...                  # 其他服务
│   │
│   └── utils/                    # 工具函数
│       ├── video_processor.py   # 视频处理工具
│       ├── script_generator.py  # 脚本生成工具
│       ├── check_script.py      # 脚本验证工具
│       └── ffmpeg_utils.py      # FFmpeg 工具
│
├── webui/                        # Web UI 界面
│   ├── components/              # UI 组件
│   │   ├── video_settings.py    # 视频设置
│   │   ├── audio_settings.py    # 音频设置
│   │   ├── subtitle_settings.py # 字幕设置
│   │   ├── script_settings.py   # 脚本设置
│   │   └── system_settings.py   # 系统设置
│   │
│   ├── tools/                   # 业务工具
│   │   ├── generate_script_docu.py  # 纪录片脚本生成
│   │   └── generate_script_short.py  # 短剧脚本生成
│   │
│   └── utils/                    # UI 工具
│       ├── cache.py             # 缓存管理
│       └── file_utils.py        # 文件工具
│
├── resource/                     # 资源文件
│   ├── videos/                  # 视频文件目录
│   ├── scripts/                 # 生成的脚本目录
│   ├── templates/               # 脚本模板
│   ├── fonts/                   # 字体文件
│   └── songs/                   # 背景音乐目录
│
├── storage/                      # 存储目录
│   ├── temp/                    # 临时文件
│   │   ├── keyframes/           # 关键帧缓存
│   │   ├── analysis/            # 分析结果
│   │   └── clip_video_unified/  # 剪辑片段
│   │
│   └── tasks/                   # 任务输出
│       └── <task_id>/           # 任务目录
│           ├── combined.mp4     # 最终视频
│           ├── merger_audio.mp3 # 合并的音频
│           └── merged_subtitle_*.srt  # 合并的字幕
│
├── docs/                         # 文档目录
│   ├── LLM_SERVICE_GUIDE.md     # LLM 服务指南
│   ├── prompt_management_system.md  # 提示词管理系统
│   └── ...                      # 其他文档
│
├── config.example.toml           # 配置文件示例
├── requirements.txt             # Python 依赖
├── Dockerfile                   # Docker 镜像定义
├── docker-compose.yml           # Docker Compose 配置
├── webui.py                     # Streamlit 主程序
└── README.md                    # 本文件
```

---

## 🤖 支持的模型

### 视觉模型（视频理解）

| 提供商 | 模型名称 | 推荐度 | 说明 |
|--------|---------|--------|------|
| Gemini | gemini-2.0-flash-lite | ⭐⭐⭐⭐⭐ | 速度快、成本低、推荐 |
| Gemini | gemini-1.5-pro | ⭐⭐⭐⭐ | 高精度、适合复杂场景 |
| OpenAI | gpt-4o | ⭐⭐⭐⭐ | 高质量、成本较高 |
| OpenAI | gpt-4o-mini | ⭐⭐⭐ | 性价比高 |
| Qwen | qwen2.5-vl-32b-instruct | ⭐⭐⭐⭐ | 中文优化、性能优秀 |
| SiliconFlow | Qwen2.5-VL-32B-Instruct | ⭐⭐⭐ | 国内访问快 |

### 文本模型（文案生成）

| 提供商 | 模型名称 | 推荐度 | 说明 |
|--------|---------|--------|------|
| DeepSeek | deepseek-chat | ⭐⭐⭐⭐⭐ | 性价比极高、中文优秀 |
| DeepSeek | deepseek-reasoner | ⭐⭐⭐⭐ | 推理能力强、适合复杂任务 |
| Gemini | gemini-2.0-flash | ⭐⭐⭐⭐ | 速度快、成本低 |
| OpenAI | gpt-4o | ⭐⭐⭐⭐ | 高质量 |
| OpenAI | gpt-4o-mini | ⭐⭐⭐ | 性价比高 |
| Qwen | qwen-plus | ⭐⭐⭐⭐ | 中文优化 |
| Qwen | qwen-turbo | ⭐⭐⭐ | 速度快 |

### TTS 引擎

| 引擎 | 免费 | 质量 | 说明 |
|------|------|------|------|
| Edge TTS | ✅ | ⭐⭐⭐ | 免费、无需 API Key、推荐 |
| Azure Speech | ❌ | ⭐⭐⭐⭐⭐ | 高质量、需付费 |
| 腾讯云 TTS | ❌ | ⭐⭐⭐⭐ | 中文优化、需付费 |
| Qwen TTS | ❌ | ⭐⭐⭐⭐ | 中文自然、需付费 |
| SoulVoice | ❌ | ⭐⭐⭐⭐⭐ | 语音克隆、需付费 |

---

## ❓ 常见问题

### 安装问题

**Q: 安装依赖时遇到 `pyaudioop` 错误？**  
A: Python 3.13+ 已移除 `audioop` 模块，请安装 `audioop-lts`：
```bash
pip install audioop-lts>=0.2.0
```

**Q: FFmpeg 未找到错误？**  
A: 请确保已安装 FFmpeg 并将其添加到系统 PATH。Windows 用户可下载 FFmpeg 并添加到环境变量。

**Q: Docker 启动失败？**  
A: 检查 Docker 服务是否运行，端口 8501 是否被占用，以及配置文件是否正确。

### 使用问题

**Q: 生成的文案与视频内容不匹配？**  
A: 检查视频类型选择是否正确，确保视觉模型 API Key 配置正确，尝试使用更高质量的视觉模型（如 gemini-1.5-pro）。

**Q: 视频生成时间过长？**  
A: 可以通过以下方式优化：
- 使用更快的模型（如 gemini-2.0-flash-lite）
- 减小 `vision_batch_size`（但会增加 API 调用次数）
- 减少视频时长或关键帧数量

**Q: 字幕与语音不同步？**  
A: 确保使用了最新版本的代码，系统会自动处理音视频同步。如仍有问题，检查生成的音频时长是否正确。

**Q: 如何清理缓存和临时文件？**  
A: 在 Web UI 的"系统设置"面板中，点击"一键清理所有缓存"按钮，或手动删除以下目录：
- `storage/temp/keyframes/`
- `storage/temp/analysis/`
- `storage/temp/clip_video_unified/`

### API 问题

**Q: API 调用失败或超时？**  
A: 
- 检查 API Key 是否正确配置
- 检查网络连接和代理设置
- 尝试增加超时时间（`llm_vision_timeout`、`llm_text_timeout`）
- 检查 API 配额和余额

**Q: 如何切换不同的模型提供商？**  
A: 在 `config.toml` 中修改 `vision_litellm_model_name` 和 `text_litellm_model_name`，格式为 `provider/model-name`。

---

## 📝 许可证

本项目采用 Modified MIT License，仅供学习和研究使用，不得商用。

详见 [`LICENSE`](LICENSE) 文件。

---

## 🔗 相关文档

- [生成素材存储与清理说明](生成素材存储与清理说明.md)
- [2025年热门解说博主经验整合说明](2025年热门解说博主经验整合说明.md)
- [配置说明](配置说明.md)

---

## 📧 反馈与支持

如有问题或建议，欢迎：
- 提交 [Issue](https://github.com/jianjieyiban/narratoai-0-7-4/issues)
- 提交 [Pull Request](https://github.com/jianjieyiban/narratoai-0-7-4/pulls)

---

**版本**: 0.7.4  
**最后更新**: 2025-11-01
