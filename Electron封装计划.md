# Electron 封装语音识别系统实施计划

## 项目概述

将现有的 Flask + Fun-ASR 语音识别系统封装为跨平台桌面应用，支持 Windows 和 macOS。

**重要变更**: 模型文件不打包进安装包，应用启动时自动下载。

## 技术方案

**核心架构**: Electron (前端) + PyInstaller 打包的 Python 可执行文件 (后端)

- Electron 通过 `child_process` 启动 Python 后端
- 前端通过 HTTP 请求与 `localhost:5000` 的 Flask API 通信
- 使用 `electron-builder` 打包分发
- **模型文件**: 首次启动时从 ModelScope 自动下载

---

## 实施步骤

### 第一阶段: 创建 Electron 项目结构

**1. 创建 electron 目录和核心文件**

创建以下新文件：
- `electron/main.js` - Electron 主进程
- `electron/preload.js` - 预加载脚本
- `electron/package.json` - 依赖配置
- `electron-builder.json` - 打包配置

**2. main.js 核心功能**
```javascript
const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let pythonProcess = null;

function createWindow() {
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false
        }
    });
    win.loadFile('../frontend/index.html');
    return win;
}

function startPythonBackend() {
    const isDev = process.env.NODE_ENV === 'development';
    const pythonExe = isDev
        ? 'python'  // 开发环境使用系统 Python
        : path.join(process.resourcesPath, 'python-dist', 'app');  // 生产环境

    const script = isDev
        ? 'backend/app.py'
        : null;  // 生产环境已打包

    const args = isDev ? [script, '--electron'] : ['--electron'];

    pythonProcess = spawn(pythonExe, args, {
        cwd: isDev ? path.join(__dirname, '..') : undefined
    });

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Python: ${data}`);
    });

    pythonProcess.on('error', (error) => {
        console.error('Python 启动失败:', error);
    });

    pythonProcess.on('exit', (code) => {
        console.log(`Python 进程退出，代码: ${code}`);
    });
}

app.whenReady().then(() => {
    createWindow();
    startPythonBackend();
});

app.on('before-quit', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
});
```

**3. preload.js 安全隔离**
```javascript
const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    getPlatform: () => process.platform,
    isElectron: () => true,
    openExternal: (url) => require('electron').shell.openExternal(url)
});
```

---

### 第二阶段: 修改现有代码

**修改 `backend/app.py`**
```python
# 添加 Electron 环境检测
import sys
import os

IS_ELECTRON = '--electron' in sys.argv or os.environ.get('ELECTRON_RUN') == '1'

if IS_ELECTRON:
    FLASK_CONFIG = {
        'host': '127.0.0.1',
        'port': 5000,
        'debug': False,
        'threaded': True,
    }
else:
    FLASK_CONFIG = {
        'host': '0.0.0.0',
        'port': 5000,
        'debug': True,
        'threaded': True,
    }

# 添加启动完成信号
def main():
    print("FLASK_SERVER_READY")  # Electron 检测此信号
    # ... 其余代码
```

**修改 `frontend/js/app.js`**
```javascript
// 第 7 行附近添加
const API_BASE = (window.electronAPI && window.electronAPI.isElectron())
    ? 'http://127.0.0.1:5000/api'  // Electron 环境
    : '/api';  // 浏览器环境
```

**修改 `backend/utils/config.py`**
```python
import platform
import os
from pathlib import Path

# 跨平台用户数据目录
if platform.system() == 'Windows':
    USER_DATA_DIR = Path(os.environ.get('APPDATA', '.')) / 'AudioProcessingSystem'
elif platform.system() == 'Darwin':  # macOS
    USER_DATA_DIR = Path.home() / 'Library' / 'AudioProcessingSystem'
else:  # Linux
    USER_DATA_DIR = Path.home() / '.local' / 'share' / 'AudioProcessingSystem'

# 确保目录存在
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

MODELS_DIR = USER_DATA_DIR / 'models'
OUTPUT_DIR = USER_DATA_DIR / 'outputs'

MODELS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
```

---

### 第三阶段: 添加模型下载功能

**新建 `backend/model_downloader.py`**
```python
import os
from pathlib import Path
from funasr import AutoModel
from .utils.config import MODELS_DIR

class ModelDownloader:
    """模型下载管理器"""

    MODELS = {
        'paraformer-zh': 'damo/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch',
        'cam++': 'damo/speech_campplus_sv_zh-cn_16k-common',
    }

    @staticmethod
    def check_model_exists(model_name: str) -> bool:
        """检查模型是否已存在"""
        model_path = MODELS_DIR / model_name
        return model_path.exists() and any(model_path.iterdir())

    @staticmethod
    def download_model(model_name: str, callback=None):
        """下载模型"""
        if ModelDownloader.check_model_exists(model_name):
            return True

        model_id = ModelDownloader.MODELS.get(model_name)
        if not model_id:
            raise ValueError(f"未知模型: {model_name}")

        try:
            # 设置缓存目录
            os.environ['MODELSCOPE_CACHE'] = str(MODELS_DIR)

            # 下载并加载模型（首次会自动下载）
            model = AutoModel(
                model=model_id,
                cache_dir=str(MODELS_DIR)
            )

            if callback:
                callback(100, model_name)

            return True
        except Exception as e:
            print(f"模型下载失败: {e}")
            return False

    @staticmethod
    def get_download_status():
        """获取模型下载状态"""
        status = {}
        for name in ModelDownloader.MODELS:
            status[name] = ModelDownloader.check_model_exists(name)
        return status
```

**修改 `backend/app.py` 添加模型下载接口**
```python
from backend.model_downloader import ModelDownloader

@app.route('/api/model-status', methods=['GET'])
def model_status():
    """获取模型状态（包括是否需要下载）"""
    try:
        status = ModelDownloader.get_download_status()
        return jsonify({
            "loaded": get_asr_engine().is_loaded,
            "models": status,
            "models_dir": str(MODELS_DIR)
        })
    except Exception as e:
        return jsonify({"loaded": False, "error": str(e)}), 500

@app.route('/api/download-model', methods=['POST'])
def download_model():
    """下载模型"""
    data = request.get_json()
    model_name = data.get('model', 'paraformer-zh')

    def download_progress(percent, model):
        # 可以通过 WebSocket 或 SSE 推送进度
        pass

    success = ModelDownloader.download_model(model_name, download_progress)

    return jsonify({
        "success": success,
        "model": model_name
    })
```

---

### 第四阶段: Python 打包

**1. 创建 PyInstaller 配置文件**
```python
# backend/app.spec
a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 不打包 models 目录！
        ('../utils', 'backend/utils'),
    ],
    hiddenimports=[
        'funasr',
        'modelscope',
        'torch',
        'torchaudio',
        'librosa',
        'soundfile',
        'backend.model_downloader',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'IPython', 'PIL'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

**2. 打包命令**
```bash
# Windows
pyinstaller backend/app.spec --onefile --clean

# macOS
pyinstaller backend/app.spec --onefile --clean
```

---

### 第五阶段: Electron 打包配置

**electron-builder.json:**
```json
{
  "appId": "com.audio.app",
  "productName": "语音识别助手",
  "directories": {
    "output": "dist"
  },
  "files": [
    "electron/**/*",
    "frontend/**/*",
    "python-dist/**/*"
  ],
  "extraResources": [
    {
      "from": "python-dist/app.exe",
      "to": "python-dist/app.exe",
      "unpack": true
    }
  ],
  "win": {
    "target": [
      {
        "target": "nsis",
        "arch": ["x64"]
      }
    ],
    "icon": "assets/icon.ico"
  },
  "mac": {
    "target": ["dmg"],
    "icon": "assets/icon.icns",
    "category": "public.app-category.utilities",
    "hardenedRuntime": true
  },
  "nsis": {
    "oneClick": false,
    "allowToChangeInstallationDirectory": true,
    "installerIcon": "assets/icon.ico",
    "uninstallerIcon": "assets/icon.ico",
    "createDesktopShortcut": true,
    "createStartMenuShortcut": true
  }
}
```

---

### 第六阶段: 前端启动页优化

**修改 `frontend/index.html` 添加模型下载提示**

在主界面前添加一个启动检查页，当模型未下载时显示下载提示：

```javascript
// 添加到 app.js
async function checkModelsBeforeStart() {
    const response = await fetch('http://127.0.0.1:5000/api/model-status');
    const data = await response.json();

    if (!data.models['paraformer-zh']) {
        // 显示模型下载对话框
        showModelDownloadDialog();
    }
}

function showModelDownloadDialog() {
    const modal = document.createElement('div');
    modal.className = 'model-download-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <h2>📥 首次使用需要下载模型</h2>
            <p>语音识别模型约 2GB，请确保网络连接稳定。</p>
            <div class="progress-bar">
                <div class="progress-fill"></div>
            </div>
            <p class="status">准备下载...</p>
            <button class="download-btn">开始下载</button>
        </div>
    `;
    document.body.appendChild(modal);
}
```

---

### 第七阶段: 构建和测试

**完整构建流程:**
```bash
# 1. 安装 Electron 依赖
cd electron
npm install

# 2. 打包 Python（不包含模型）
cd ..
pyinstaller backend/app.spec --onefile --clean

# 3. 复制 Python 可执行文件
# Windows
copy dist\app.exe electron\python-dist\

# macOS
cp dist/app electron/python-dist/

# 4. 打包 Electron
cd electron
npm run build:windows  # 或 npm run build:mac
```

---

## 关键文件清单

### 新增文件

| 文件 | 说明 |
|------|------|
| `electron/main.js` | Electron 主进程入口 |
| `electron/preload.js` | 预加载脚本 |
| `electron/package.json` | Electron 依赖 |
| `electron-builder.json` | 打包配置 |
| `backend/app.spec` | PyInstaller 配置 |
| `backend/model_downloader.py` | 模型下载管理器 |

### 修改文件

| 文件 | 修改内容 |
|------|----------|
| `backend/app.py` | 添加 Electron 环境检测、模型下载接口 |
| `frontend/js/app.js` | 修改 API_BASE 路径、添加模型检查 |
| `frontend/index.html` | 添加模型下载对话框样式 |
| `backend/utils/config.py` | 添加用户数据目录配置 |
| `frontend/css/style.css` | 添加模型下载对话框样式 |

---

## 启动流程

### 首次启动
```
用户启动应用
    ↓
Electron 启动 Python 后端
    ↓
前端检测模型状态
    ↓
[模型未下载] → 显示下载对话框 → 用户确认 → 后台下载 → 下载完成
    ↓
进入主界面
```

### 后续启动
```
用户启动应用
    ↓
Electron 启动 Python 后端
    ↓
检测模型已存在 → 直接进入主界面
```

---

## 验证测试

### 功能测试
- [ ] 应用启动后 Python 后端正常运行
- [ ] 首次启动正确检测模型不存在
- [ ] 模型下载功能正常工作
- [ ] 下载进度正确显示
- [ ] 下载完成后模型可用
- [ ] 前端能成功调用 API
- [ ] 文件夹扫描功能正常
- [ ] 语音识别功能正常
- [ ] 结果导出功能正常

### 跨平台测试
- [ ] Windows 10/11 安装和运行
- [ ] macOS 安装和运行

### 性能测试
- [ ] 安装包大小 < 1GB
- [ ] 启动时间 < 10 秒（不含下载）
- [ ] 内存占用 < 4GB
- [ ] 识别速度与原版一致

### 模型下载测试
- [ ] 断点续传支持
- [ ] 下载失败重试机制
- [ ] 网络异常处理
- [ ] 磁盘空间不足提示

---

## 预期成果

| 平台 | 格式 | 大小 |
|------|------|------|
| Windows | NSIS 安装程序 | ~500MB |
| macOS | DMG 镜像 | ~600MB |

**用户数据占用**（首次启动后）:
- 模型文件: ~2GB
- 输出文件: 根据使用情况

---

## 风险和注意事项

| 风险 | 缓解措施 |
|------|----------|
| 模型下载失败 | 添加重试机制，提供手动下载链接 |
| 网络不稳定 | 实现断点续传 |
| 下载时间过长 | 显示详细进度和预计剩余时间 |
| ModelScope 访问慢 | 提供国内镜像备用地址 |
| 磁盘空间不足 | 下载前检查可用空间 |
| PyTorch 打包失败 | 使用官方 wheel 包，测试 --hidden-import |
| Windows 杀软误报 | 申请代码签名证书 |
| macOS Gatekeeper | 进行公证 (notarization) |

---

**文档版本**: v2.0
**更新日期**: 2024-01-29
**更新内容**: 模型改为运行时下载，大幅减小安装包体积
