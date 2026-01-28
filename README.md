# AudioProcessingSystem

<div align="center">

![Fun-ASR](https://img.shields.io/badge/Fun--ASR-语音识别-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![Flask](https://img.shields.io/badge/Flask-3.0+-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

**基于 Fun-ASR 的本地语音识别批量处理系统**

现代化 Web 界面 · 本地处理 · 实时进度 · Markdown 导出

[功能特性](#功能特性) · [快速开始](#快速开始) · [使用说明](#使用说明) · [API 文档](#api-接口)

</div>

---

## 功能特性

### 核心功能
- **本地识别** - 所有音频文件在本地处理，无需上传到云端服务器，确保数据隐私
- **批量处理** - 支持扫描整个文件夹，批量处理多个音频文件
- **实时进度** - 显示识别进度条、当前处理文件和预计剩余时间
- **说话人分离** - 支持多人对话场景的说话人识别与分离（可选）
- **GPU 加速** - 支持 CUDA 加速，大幅提升识别速度（需 NVIDIA 显卡）
- **结果导出** - 自动生成 Markdown 格式的识别结果文件
- **汇总报告** - 生成包含所有识别结果的汇总文件

### 界面特点
- 现代化深色主题设计
- 响应式布局，支持移动端访问
- 直观的可视化进度显示
- 文件状态实时更新
- 优雅的加载动画和提示消息

---

## 快速开始

### 环境要求

- **Python**: 3.8 或更高版本
- **操作系统**: Windows / macOS / Linux
- **内存**: 建议 4GB 以上（模型加载需要）
- **GPU**（可选）: NVIDIA 显卡 + CUDA Toolkit（用于加速）

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/yourusername/AudioProcessingSystem.git
cd AudioProcessingSystem
```

2. **创建虚拟环境**（推荐）
```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

### 启动服务

**方式一：使用启动脚本**

```bash
# macOS / Linux
./start.sh

# Windows
start.bat
```

**方式二：直接运行**

```bash
python backend/app.py
```

启动成功后，终端会显示：

```
==================================================
Fun-ASR 语音识别批量处理系统
==================================================
服务器地址: http://127.0.0.1:5000
输出目录: /path/to/AudioProcessingSystem/outputs
==================================================

正在预加载模型...
模型加载完成！
```

### 访问界面

打开浏览器访问：**http://127.0.0.1:5000**

---

## 使用说明

### 1. 选择音频文件夹

在网页顶部输入框中输入音频文件夹的本地路径：

**Windows 示例:**
```
C:\Users\用户名\Documents\音频文件
```

**macOS/Linux 示例:**
```
/Users/用户名/Documents/音频文件
```

或点击 **"选择文件夹"** 按钮直接选择文件夹。

### 2. 扫描音频文件

点击 **"扫描"** 按钮，系统会自动扫描文件夹中的所有音频文件。

**支持的音频格式:**
- WAV (.wav)
- MP3 (.mp3)
- M4A (.m4a)
- FLAC (.flac)
- OGG (.ogg)
- WMA (.wma)
- AAC (.aac)

### 3. 配置处理选项

**处理设备:**
- **CPU** - 使用处理器进行识别（兼容性好）
- **GPU** - 使用显卡加速（需要 NVIDIA CUDA）

**高级选项:**
- **说话人分离** - 启用后会识别并标注不同说话人（适用于多人对话场景）

### 4. 开始识别

点击 **"开始识别"** 按钮，系统会：

1. 加载 Fun-ASR 模型
2. 逐个处理音频文件
3. 实时更新处理进度
4. 显示识别结果

### 5. 导出结果

识别完成后，点击 **"导出结果"** 按钮：

- 每个音频文件生成对应的 `.md` 文件
- 生成汇总文件 `summary.md`
- 默认保存到 `outputs/` 目录

---

## API 接口

### 扫描文件夹

```http
POST /api/scan-folder
Content-Type: application/json

{
  "folder_path": "/path/to/audio/folder"
}
```

**响应:**
```json
{
  "success": true,
  "files": [
    {
      "name": "audio1.wav",
      "path": "/full/path/to/audio1.wav",
      "size": "3.2 MB",
      "status": "pending"
    }
  ],
  "count": 1
}
```

### 开始识别

```http
POST /api/start-recognition
Content-Type: application/json

{
  "files": [...],
  "device": "cpu",
  "speaker_diarization": false
}
```

**响应:**
```json
{
  "success": true,
  "message": "开始识别 10 个音频文件 (使用 CPU)"
}
```

### 获取进度

```http
GET /api/progress
```

**响应:**
```json
{
  "is_processing": true,
  "current_index": 5,
  "total": 10,
  "current_file": "audio5.wav",
  "results": [...]
}
```

### 导出结果

```http
POST /api/export-results
Content-Type: application/json

{
  "results": [...],
  "output_dir": "/custom/output/path"
}
```

### 模型状态

```http
GET /api/model-status
```

### 设备状态

```http
GET /api/device-status
```

### 停止识别

```http
POST /api/stop-recognition
```

---

## 项目结构

```
AudioProcessingSystem/
├── backend/
│   ├── app.py                 # Flask 主应用
│   ├── asr_engine.py          # ASR 引擎封装
│   ├── audio_processor.py     # 音频处理模块
│   ├── result_exporter.py     # 结果导出模块
│   └── utils/
│       ├── __init__.py
│       └── config.py          # 配置文件
├── frontend/
│   ├── index.html             # 主页面
│   ├── css/
│   │   └── style.css          # 样式文件（深色主题）
│   └── js/
│       └── app.js             # 前端逻辑
├── models/                    # 模型存储目录（自动下载）
├── outputs/                   # 输出结果目录
├── requirements.txt           # Python 依赖
├── start.sh                   # Linux/macOS 启动脚本
├── start.bat                  # Windows 启动脚本
└── README.md                  # 本文件
```

---

## 技术栈

| 类别 | 技术 |
|------|------|
| **后端框架** | Flask 3.0+ |
| **AI 模型** | Fun-ASR (paraformer-zh) |
| **深度学习** | PyTorch 2.0+ |
| **音频处理** | librosa, soundfile |
| **前端** | 原生 HTML/CSS/JavaScript |
| **样式** | CSS Grid + Flexbox |

---

## 常见问题

### 模型下载失败怎么办？

首次运行时，Fun-ASR 会自动从 ModelScope 下载模型。如果下载失败：

1. 检查网络连接
2. 使用镜像源：设置环境变量 `MODELSCOPE_CACHE`
3. 手动下载模型文件到 `models/` 目录

### 识别速度慢？

识别速度取决于以下因素：
- 音频文件时长
- CPU/GPU 性能
- 是否启用 GPU 加速

**建议:**
- 有 NVIDIA 显卡时选择 GPU 模式
- 批量处理时避免同时运行其他大型程序

### 浏览器无法访问？

检查以下项：
1. 确认后端服务已启动
2. 检查端口 5000 是否被占用
3. 尝试访问 `http://127.0.0.1:5000` 或 `http://localhost:5000`

### 说话人分离功能不工作？

说话人分离需要额外的模型支持，确保：
1. 网络连接正常（需下载说话人分离模型）
2. 音频文件包含多人对话
3. 音频质量良好

---

## 结果文件格式

### 单个音频结果

```markdown
# 音频识别结果

**文件名**: meeting_20240129.wav
**识别时间**: 2024-01-29 14:30:00
**文件大小**: 15.2 MB
**音频时长**: 00:05:23
**处理耗时**: 12.3 秒

## 识别文本

大家好，欢迎参加今天的会议。今天我们主要讨论项目进展情况...

## 元数据
- 采样率: 16000 Hz
- 声道: 单声道
- 格式: WAV
```

### 说话人分离格式

```markdown
# 音频识别结果（说话人分离）

**文件名**: interview.wav
**识别时间**: 2024-01-29 14:30:00

## 说话人 0
请问您能介绍一下这个项目吗？

## 说话人 1
当然，这是一个基于 Fun-ASR 的语音识别系统...

## 说话人 0
听起来很有意思！
```

---

## 开发

### 运行开发模式

```bash
# 设置 Flask 开发模式
export FLASK_ENV=development
export FLASK_DEBUG=1

# 启动服务
python backend/app.py
```

### 修改配置

编辑 `backend/utils/config.py`:

```python
FLASK_CONFIG = {
    'host': '127.0.0.1',    # 服务器地址
    'port': 5000,           # 端口号
    'debug': False,         # 调试模式
    'threaded': True        # 多线程
}
```

---

## 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 致谢

- [Fun-ASR](https://github.com/alibaba-damo-academy/FunASR) - 阿里达摩院开源的语音识别工具
- [ModelScope](https://modelscope.cn/) - 魔搭社区模型库

---

<div align="center">

**如果这个项目对你有帮助，请给一个 Star ⭐**

Made with ❤️ by [Your Name]

</div>
