# Fun-ASR 语音识别批量处理系统

基于 Fun-ASR-Nano-2512 模型的本地语音识别批量处理系统，支持文件夹批量识别、实时进度显示和 Markdown 结果导出。

## 功能特点

- 🎙️ **本地识别** - 所有文件在本地处理，无需上传到服务器
- 📁 **批量处理** - 支持整个文件夹的音频文件批量识别
- 📊 **实时进度** - 显示识别进度和当前处理文件
- 📝 **结果导出** - 自动生成 Markdown 格式的识别结果文件
- 🌐 **Web 界面** - 简洁易用的网页界面

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python backend/app.py
```

### 3. 访问界面

打开浏览器访问: `http://127.0.0.1:5000`

## 使用说明

1. **选择文件夹**
   - 在输入框中输入音频文件夹的本地路径
   - Windows 示例: `C:\Users\用户名\Documents\音频文件`
   - Mac/Linux 示例: `/Users/用户名/Documents/音频文件`

2. **扫描文件**
   - 点击"扫描文件夹"按钮获取音频文件列表

3. **开始识别**
   - 点击"开始识别"按钮进行批量语音识别
   - 实时查看处理进度

4. **导出结果**
   - 识别完成后点击"导出结果"
   - 结果文件保存到 `outputs/` 目录

## 支持的音频格式

- WAV (.wav)
- MP3 (.mp3)
- M4A (.m4a)
- FLAC (.flac)
- OGG (.ogg)
- WMA (.wma)
- AAC (.aac)

## 项目结构

```
AudioProcessingSystem/
├── backend/
│   ├── app.py                 # Flask 主应用
│   ├── asr_engine.py          # ASR 引擎封装
│   ├── audio_processor.py     # 音频处理模块
│   ├── result_exporter.py     # 结果导出模块
│   └── utils/
│       └── config.py          # 配置文件
├── frontend/
│   ├── index.html             # 主页面
│   ├── css/
│   │   └── style.css          # 样式文件
│   └── js/
│       └── app.js             # 前端逻辑
├── models/                    # 模型存储目录
├── outputs/                   # 输出结果目录
├── requirements.txt           # Python 依赖
└── README.md                  # 本文件
```

## 系统要求

- Python 3.8+
- 足够的内存用于模型加载（建议 4GB+）

## 常见问题

### 模型下载失败

首次运行时，Fun-ASR 会自动下载模型。如果下载失败，可以手动下载并放置到 `models/` 目录。

### 识别速度慢

识别速度取决于:
- 音频文件长度
- CPU/GPU 性能
- 是否启用 GPU 加速

如有 GPU，可在 `backend/asr_engine.py` 中取消注释 `device="cuda"`。

## 技术栈

- **后端**: Python + Flask
- **前端**: HTML + CSS + JavaScript
- **AI 模型**: Fun-ASR (paraformer-zh)

## 许可证

MIT License
