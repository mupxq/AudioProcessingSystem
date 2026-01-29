/**
 * Fun-ASR 语音识别批量处理系统 - 前端逻辑
 * Modern Dark Dashboard Theme
 */

// API 基础路径
const API_BASE = '/api';

// 全局状态
const state = {
    files: [],
    results: [],
    isProcessing: false,
    progressInterval: null,
    device: 'cpu',
    cudaAvailable: false
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
    progressPercentage: document.getElementById('progressPercentage'),
    progressText: document.getElementById('progressText'),
    currentFile: document.getElementById('currentFile'),
    resultsSection: document.getElementById('resultsSection'),
    resultsList: document.getElementById('resultsList'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    loadingText: document.getElementById('loadingText'),
    toast: document.getElementById('toast'),
    toastIcon: document.querySelector('.toast-icon'),
    toastMessage: document.querySelector('.toast-message'),
    gpuOption: document.getElementById('gpuOption'),
    deviceStatus: document.getElementById('deviceStatus'),
    speakerDiarization: document.getElementById('speakerDiarization')
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
async function startRecognition(files, device = 'cpu', speakerDiarization = false) {
    try {
        const response = await fetch(`${API_BASE}/start-recognition`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                files,
                device,
                speaker_diarization: speakerDiarization
            })
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
    elements.toastMessage.textContent = message;
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
                    <span class="empty-icon">📭</span>
                    <span class="empty-label">请先扫描文件夹获取音频文件列表</span>
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
                    `<button class="action-btn action-btn-secondary" onclick="previewResult(${index})" style="padding: 6px 12px; font-size: 11px; min-width: auto;">查看</button>` :
                    '<span style="color: var(--text-muted);">—</span>'}
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

    const percentage = total > 0 ? Math.round((current_index / total) * 100) : 0;
    elements.progressFill.style.width = `${percentage}%`;
    elements.progressPercentage.textContent = `${percentage}%`;
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
        const hasSpeakers = result.speaker_diarization_enabled && result.sentences && result.sentences.length > 0;

        let contentHtml = `
            <div class="result-header">
                <div class="result-file-name">${file.name}</div>
                <div class="result-status success">成功</div>
            </div>
        `;

        if (hasSpeakers) {
            const speakerCount = result.speaker_count || 0;
            const speakers = result.speakers || [];

            const speakerNames = {};
            for (let i = 0; i < speakers.length; i++) {
                speakerNames[speakers[i]] = `说话人${String.fromCharCode(65 + i)}`;
            }

            contentHtml += `
                <div class="speaker-info">
                    <strong>检测到 ${speakerCount} 位说话人</strong>
                </div>
                <div class="result-text">
            `;

            const speakerText = {};
            result.sentences.forEach(sentence => {
                const speaker = sentence.speaker || 'unknown';
                if (!speakerText[speaker]) {
                    speakerText[speaker] = [];
                }
                speakerText[speaker].push(sentence);
            });

            for (const [speaker, sentences] of Object.entries(speakerText)) {
                const speakerName = speakerNames[speaker] || speaker;
                contentHtml += `<div class="speaker-section"><strong>${speakerName}:</strong>`;

                sentences.forEach(sentence => {
                    const startTime = (sentence.start / 1000).toFixed(1);
                    const endTime = (sentence.end / 1000).toFixed(1);
                    contentHtml += `<div class="speaker-sentence">[${startTime}s - ${endTime}s] ${sentence.text}</div>`;
                });

                contentHtml += `</div>`;
            }

            contentHtml += `</div>`;
            contentHtml += `<div class="result-text-full"><strong>完整文本:</strong> ${result.text || '(空)'}</div>`;
        } else {
            contentHtml += `
                <div class="result-text">${result.text || '(空)'}</div>
            `;
        }

        resultItem.innerHTML = contentHtml;
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
        showToast('请输入或选择文件夹路径', 'error');
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

    const selectedDevice = document.querySelector('input[name="device"]:checked').value;

    if (selectedDevice === 'cuda' && !state.cudaAvailable) {
        showToast('GPU (CUDA) 不可用，请使用 CPU 模式', 'error');
        return;
    }

    const speakerDiarization = elements.speakerDiarization.checked;

    try {
        await startRecognition(state.files, selectedDevice, speakerDiarization);

        state.isProcessing = true;
        elements.progressSection.style.display = 'block';
        elements.resultsSection.style.display = 'block';
        elements.resultsList.innerHTML = '';

        updateButtons();

        state.progressInterval = setInterval(async () => {
            const progressData = await getProgress();

            if (progressData) {
                updateProgress(progressData);

                if (progressData.results) {
                    state.results = progressData.results;
                }

                if (!progressData.is_processing) {
                    clearInterval(state.progressInterval);
                    state.isProcessing = false;

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
                    <span class="empty-icon">📭</span>
                    <span class="empty-label">请先扫描文件夹获取音频文件列表</span>
                </td>
            </tr>
        `;
        elements.fileCount.textContent = '0';
        elements.progressSection.style.display = 'none';
        elements.resultsSection.style.display = 'none';

        elements.folderPath.value = '';

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
    checkDeviceStatus();
    console.log('Fun-ASR 语音识别系统已加载');
});
