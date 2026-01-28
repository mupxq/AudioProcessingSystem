/**
 * Fun-ASR 语音识别批量处理系统 - 前端逻辑
 */

// API 基础路径
const API_BASE = '/api';

// 全局状态
const state = {
    files: [],
    results: [],
    isProcessing: false,
    progressInterval: null,
    device: 'cpu',  // 当前选择的设备
    cudaAvailable: false  // CUDA 是否可用
};

// DOM 元素
const elements = {
    folderPath: document.getElementById('folderPath'),
    scanBtn: document.getElementById('scanBtn'),
    startBtn: document.getElementById('startBtn'),
    stopBtn: document.getElementById('stopBtn'),
    exportBtn: document.getElementById('exportBtn'),
    clearBtn: document.getElementById('clearBtn'),
    fileCount: document.getElementById('fileCount'),
    filesTableBody: document.getElementById('filesTableBody'),
    progressSection: document.getElementById('progressSection'),
    progressFill: document.getElementById('progressFill'),
    progressText: document.getElementById('progressText'),
    currentFile: document.getElementById('currentFile'),
    resultsSection: document.getElementById('resultsSection'),
    resultsList: document.getElementById('resultsList'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    loadingText: document.getElementById('loadingText'),
    toast: document.getElementById('toast'),
    gpuOption: document.getElementById('gpuOption'),
    deviceStatus: document.getElementById('deviceStatus')
};

// ==================== API 调用 ====================

/**
 * 扫描文件夹
 */
async function scanFolder(folderPath) {
    try {
        const response = await fetch(`${API_BASE}/scan-folder`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ folder_path: folderPath })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || '扫描失败');
        }

        return data;
    } catch (error) {
        throw error;
    }
}

/**
 * 开始识别
 */
async function startRecognition(files, device = 'cpu') {
    try {
        const response = await fetch(`${API_BASE}/start-recognition`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ files, device })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || '启动识别失败');
        }

        return data;
    } catch (error) {
        throw error;
    }
}

/**
 * 获取设备状态
 */
async function getDeviceStatus() {
    try {
        const response = await fetch(`${API_BASE}/device-status`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('获取设备状态失败:', error);
        return { cuda_available: false, current_device: 'cpu' };
    }
}

/**
 * 停止识别
 */
async function stopRecognition() {
    try {
        const response = await fetch(`${API_BASE}/stop-recognition`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('停止识别失败:', error);
    }
}

/**
 * 获取进度
 */
async function getProgress() {
    try {
        const response = await fetch(`${API_BASE}/progress`);
        return await response.json();
    } catch (error) {
        console.error('获取进度失败:', error);
        return null;
    }
}

/**
 * 导出结果
 */
async function exportResults(results) {
    try {
        const response = await fetch(`${API_BASE}/export-results`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ results })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || '导出失败');
        }

        return data;
    } catch (error) {
        throw error;
    }
}

// ==================== UI 操作 ====================

/**
 * 显示提示消息
 */
function showToast(message, type = 'info') {
    elements.toast.textContent = message;
    elements.toast.className = `toast ${type} show`;

    setTimeout(() => {
        elements.toast.classList.remove('show');
    }, 3000);
}

/**
 * 显示/隐藏加载遮罩
 */
function setLoading(show, text = '正在处理...') {
    elements.loadingText.textContent = text;
    elements.loadingOverlay.style.display = show ? 'flex' : 'none';
}

/**
 * 更新文件列表表格
 */
function updateFilesTable() {
    const tbody = elements.filesTableBody;
    tbody.innerHTML = '';

    if (state.files.length === 0) {
        tbody.innerHTML = `
            <tr class="empty-row">
                <td colspan="5" class="empty-text">
                    请先扫描文件夹获取音频文件列表
                </td>
            </tr>
        `;
        elements.fileCount.textContent = '0';
        return;
    }

    elements.fileCount.textContent = state.files.length;

    state.files.forEach((file, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${index + 1}</td>
            <td>
                <div class="file-name">${file.name}</div>
                <div class="file-path">${file.path}</div>
            </td>
            <td>${file.size_mb} MB</td>
            <td>
                <span class="status-badge status-${file.status}">
                    ${getStatusText(file.status)}
                </span>
            </td>
            <td>
                ${file.status === 'completed' && file.result ?
                    '<button class="btn btn-secondary" onclick="previewResult(' + index + ')" style="padding: 6px 12px; font-size: 12px;">查看</button>' :
                    '-'}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

/**
 * 获取状态文本
 */
function getStatusText(status) {
    const statusMap = {
        pending: '待处理',
        processing: '处理中',
        completed: '已完成',
        failed: '失败'
    };
    return statusMap[status] || status;
}

/**
 * 更新进度条
 */
function updateProgress(progressData) {
    const { current_index, total, current_file } = progressData;

    const percentage = total > 0 ? (current_index / total) * 100 : 0;
    elements.progressFill.style.width = `${percentage}%`;
    elements.progressText.textContent = `${current_index} / ${total}`;
    elements.currentFile.textContent = current_file || '-';

    // 更新文件列表中的状态
    if (progressData.results && progressData.results.length > 0) {
        progressData.results.forEach((result, index) => {
            if (state.files[index]) {
                state.files[index].status = result.success ? 'completed' : 'failed';
                state.files[index].result = result;
            }
        });
        updateFilesTable();
    }
}

/**
 * 添加结果预览
 */
function addResultPreview(result, index) {
    const file = state.files[index];
    if (!file) return;

    const resultItem = document.createElement('div');
    resultItem.className = `result-item ${result.success ? 'success' : 'failed'}`;

    if (result.success) {
        resultItem.innerHTML = `
            <div class="result-header">
                <div class="result-file-name">${file.name}</div>
                <div class="result-status success">成功</div>
            </div>
            <div class="result-text">${result.text || '(空)'}</div>
        `;
    } else {
        resultItem.innerHTML = `
            <div class="result-header">
                <div class="result-file-name">${file.name}</div>
                <div class="result-status failed">失败</div>
            </div>
            <div class="result-error">${result.error || '未知错误'}</div>
        `;
    }

    elements.resultsList.appendChild(resultItem);
}

/**
 * 预览单个结果
 */
window.previewResult = function(index) {
    const file = state.files[index];
    if (!file || !file.result) return;

    elements.resultsSection.style.display = 'block';
    elements.resultsList.innerHTML = '';

    addResultPreview(file.result, index);

    // 滚动到结果区
    elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
};

/**
 * 更新按钮状态
 */
function updateButtons() {
    const hasFiles = state.files.length > 0;

    elements.startBtn.disabled = !hasFiles || state.isProcessing;
    elements.exportBtn.disabled = state.results.length === 0;
    elements.clearBtn.disabled = !hasFiles || state.isProcessing;

    if (state.isProcessing) {
        elements.startBtn.style.display = 'none';
        elements.stopBtn.style.display = 'inline-flex';
    } else {
        elements.startBtn.style.display = 'inline-flex';
        elements.stopBtn.style.display = 'none';
    }
}

// ==================== 事件处理 ====================

/**
 * 扫描文件夹按钮点击
 */
elements.scanBtn.addEventListener('click', async () => {
    const folderPath = elements.folderPath.value.trim();

    if (!folderPath) {
        showToast('请输入文件夹路径', 'error');
        return;
    }

    setLoading(true, '正在扫描文件夹...');

    try {
        const data = await scanFolder(folderPath);

        state.files = data.files.map(f => ({
            ...f,
            status: 'pending',
            result: null
        }));
        state.results = [];

        updateFilesTable();
        updateButtons();

        // 隐藏结果区
        elements.resultsSection.style.display = 'none';

        showToast(`找到 ${data.count} 个音频文件`, 'success');
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        setLoading(false);
    }
});

/**
 * 开始识别按钮点击
 */
elements.startBtn.addEventListener('click', async () => {
    if (state.files.length === 0) {
        showToast('请先扫描文件夹', 'error');
        return;
    }

    // 获取选中的设备
    const selectedDevice = document.querySelector('input[name="device"]:checked').value;

    // 如果选择 GPU 但不可用，提示用户
    if (selectedDevice === 'cuda' && !state.cudaAvailable) {
        showToast('GPU (CUDA) 不可用，请使用 CPU 模式', 'error');
        return;
    }

    try {
        await startRecognition(state.files, selectedDevice);

        state.isProcessing = true;
        elements.progressSection.style.display = 'block';
        elements.resultsSection.style.display = 'block';
        elements.resultsList.innerHTML = '';

        updateButtons();

        // 开始轮询进度
        state.progressInterval = setInterval(async () => {
            const progressData = await getProgress();

            if (progressData) {
                updateProgress(progressData);

                // 保存结果
                if (progressData.results) {
                    state.results = progressData.results;
                }

                // 检查是否完成
                if (!progressData.is_processing) {
                    clearInterval(state.progressInterval);
                    state.isProcessing = false;

                    // 显示所有结果
                    elements.resultsList.innerHTML = '';
                    state.results.forEach((result, index) => {
                        addResultPreview(result, index);
                    });

                    updateButtons();
                    showToast('识别完成！', 'success');
                }
            }
        }, 500);

    } catch (error) {
        state.isProcessing = false;
        updateButtons();
        showToast(error.message, 'error');
    }
});

/**
 * 停止识别按钮点击
 */
elements.stopBtn.addEventListener('click', async () => {
    if (confirm('确定要停止识别吗？')) {
        await stopRecognition();

        if (state.progressInterval) {
            clearInterval(state.progressInterval);
        }

        state.isProcessing = false;
        updateButtons();
        showToast('识别已停止', 'info');
    }
});

/**
 * 导出结果按钮点击
 */
elements.exportBtn.addEventListener('click', async () => {
    if (state.results.length === 0) {
        showToast('没有可导出的结果', 'error');
        return;
    }

    setLoading(true, '正在导出结果...');

    try {
        const data = await exportResults(state.results);

        showToast(
            `成功导出 ${data.exported_count} 个文件到 ${data.output_dir}`,
            'success'
        );

        elements.exportBtn.disabled = true;
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        setLoading(false);
    }
});

/**
 * 清空列表按钮点击
 */
elements.clearBtn.addEventListener('click', () => {
    if (confirm('确定要清空列表吗？')) {
        state.files = [];
        state.results = [];

        elements.filesTableBody.innerHTML = `
            <tr class="empty-row">
                <td colspan="5" class="empty-text">
                    请先扫描文件夹获取音频文件列表
                </td>
            </tr>
        `;
        elements.fileCount.textContent = '0';
        elements.progressSection.style.display = 'none';
        elements.resultsSection.style.display = 'none';

        updateButtons();
        showToast('列表已清空', 'info');
    }
});

/**
 * 输入框回车键支持
 */
elements.folderPath.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        elements.scanBtn.click();
    }
});

// ==================== 初始化 ====================

/**
 * 检测设备状态
 */
async function checkDeviceStatus() {
    const status = await getDeviceStatus();
    state.cudaAvailable = status.cuda_available;

    const statusText = elements.deviceStatus.querySelector('.status-text');

    if (status.cuda_available) {
        elements.deviceStatus.className = 'device-status cuda-available';
        statusText.textContent = 'GPU 可用';
        if (status.cuda_device_name) {
            statusText.textContent += ` (${status.cuda_device_name})`;
        }
    } else {
        elements.deviceStatus.className = 'device-status cuda-unavailable';
        statusText.textContent = 'GPU 不可用，仅支持 CPU 模式';
        elements.gpuOption.classList.add('disabled');
        elements.gpuOption.querySelector('input').disabled = true;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    updateButtons();
    checkDeviceStatus();  // 检测设备状态
    console.log('Fun-ASR 语音识别系统已加载');
});
