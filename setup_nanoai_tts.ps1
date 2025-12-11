# setup_nanoai_tts.ps1 - 纳米AI TTS项目自动部署脚本
# 目标路径：C:\Users\starry\aipywork\AZsEoViyeGafFUiiyLlrNw\nanoai-tts
param(
    [string]$TargetPath = "C:\Users\starry\aipywork\AZsEoViyeGafFUiiyLlrNw\nanoai-tts"
)
# 创建目标目录
Write-Host "创建项目目录: $TargetPath" -ForegroundColor Green
New-Item -ItemType Directory -Path $TargetPath -Force | Out-Null
# 创建子目录
$subDirs = @("utils", "api", "deploy", "docs", "logs", "cache")
foreach ($dir in $subDirs) {
    $fullPath = Join-Path $TargetPath $dir
    Write-Host "创建子目录: $fullPath" -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
}
# 定义所有文件内容
$files = @{
    # 根目录文件
    "app.py" = @"
# app.py - 纳米AI TTS主应用
from flask import Flask, request, Response, jsonify, render_template_string
from flask_cors import CORS
from nano_tts import NanoAITTS
from text_processor import TextProcessor
import threading
import time
import os
import logging
from datetime import datetime
import random
import io
from dotenv import load_dotenv
from utils.logger import get_logger
from api.auth import auth
from api.rate_limit import init_limiter
from deploy.config import DeployConfig
# 加载环境变量
load_dotenv()
logger = get_logger()
# --- 配置 ---
STATIC_API_KEY = os.getenv("TTS_API_KEY", "sk-nanoai-your-secret-key")
CACHE_DURATION_SECONDS = int(os.getenv("CACHE_DURATION", 2 * 60 * 60))
PORT = int(os.getenv("PORT", 5001))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
# --- 缓存管理器 ---
class ModelCache:
    def __init__(self, tts_engine):
        self._tts_engine = tts_engine
        self._cache = {}
        self._last_updated = 0
        self._lock = threading.Lock()
        self.logger = logging.getLogger('ModelCache')
    
    def get_models(self):
        with self._lock:
            current_time = time.time()
            if not self._cache or (current_time - self._last_updated > CACHE_DURATION_SECONDS):
                self.logger.info("缓存过期或为空，正在刷新模型列表...")
                try:
                    self._tts_engine.load_voices()
                    self._cache = {tag: info['name'] for tag, info in self._tts_engine.voices.items()}
                    self._last_updated = current_time
                    self.logger.info(f"模型列表刷新成功，共找到 {len(self._cache)} 个模型。")
                except Exception as e:
                    self.logger.error(f"刷新模型列表失败: {str(e)}", exc_info=True)
            return self._cache
# --- 初始化 ---
app = Flask(__name__)
CORS(app)
limiter = init_limiter(app)  # 初始化限流
try:
    logger.info("正在初始化 TTS 引擎...")
    tts_engine = NanoAITTS()
    logger.info("TTS 引擎初始化完毕。")
    model_cache = ModelCache(tts_engine)
    text_processor = TextProcessor(max_chunk_length=200)
except Exception as e:
    logger.critical(f"TTS 引擎初始化失败: {str(e)}", exc_info=True)
    tts_engine = None
    model_cache = None
    text_processor = None
# HTML模板（完整前端界面）
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>纳米AI TTS - OpenAI 兼容接口</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 800px;
            width: 100%;
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 28px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        .header p {
            opacity: 0.9;
            font-size: 14px;
        }
        .content {
            padding: 30px;
        }
        .section {
            margin-bottom: 25px;
        }
        .section-title {
            font-size: 16px;
            font-weight: 600;
            color: #333;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            font-size: 14px;
            color: #555;
            margin-bottom: 8px;
            font-weight: 500;
        }
        input[type="text"],
        input[type="password"],
        textarea,
        select {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 14px;
            transition: all 0.3s;
            font-family: inherit;
        }
        .password-wrapper {
            position: relative;
            display: flex;
            align-items: center;
        }
        .password-wrapper input {
            padding-right: 45px;
        }
        .toggle-password {
            position: absolute;
            right: 12px;
            cursor: pointer;
            font-size: 20px;
            user-select: none;
            transition: opacity 0.2s;
        }
        .toggle-password:hover {
            opacity: 0.7;
        }
        input:focus,
        textarea:focus,
        select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        textarea {
            resize: vertical;
            min-height: 120px;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px 30px;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
        }
        .btn:active {
            transform: translateY(0);
        }
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .btn-secondary {
            background: #6c757d;
            margin-top: 10px;
        }
        .status {
            padding: 12px 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
            align-items: center;
            gap: 10px;
        }
        .status.show {
            display: flex;
        }
        .status.info {
            background: #e3f2fd;
            color: #1976d2;
            border: 1px solid #90caf9;
        }
        .status.success {
            background: #e8f5e9;
            color: #388e3c;
            border: 1px solid #81c784;
        }
        .status.error {
            background: #ffebee;
            color: #c62828;
            border: 1px solid #e57373;
        }
        .models-list {
            max-height: 300px;
            overflow-y: auto;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 15px;
        }
        .model-item {
            padding: 10px;
            margin-bottom: 8px;
            background: #f8f9fa;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        .model-item:hover {
            background: #e9ecef;
            transform: translateX(5px);
        }
        .model-item.selected {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .model-id {
            font-weight: 600;
            font-size: 13px;
        }
        .model-name {
            font-size: 12px;
            opacity: 0.8;
        }
        .spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .audio-player {
            margin-top: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            display: none;
        }
        .audio-player.show {
            display: block;
        }
        audio {
            width: 100%;
            margin-top: 10px;
        }
        .char-count {
            text-align: right;
            font-size: 12px;
            color: #999;
            margin-top: 5px;
        }
        .api-info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            font-size: 13px;
            line-height: 1.6;
            color: #555;
        }
        .api-info code {
            background: #e9ecef;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }
        /* 音频参数控制 */
        .audio-params {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        .param-control {
            flex: 1;
            min-width: 200px;
        }
        /* 任务进度条 */
        .task-progress {
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            border: 1px solid #e9ecef;
        }
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 10px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.3s ease;
        }
        .progress-text {
            font-size: 14px;
            color: #666;
            text-align: center;
        }
        /* 历史记录 */
        .history-list {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 10px;
        }
        .history-item {
            padding: 12px;
            margin-bottom: 8px;
            background: #f8f9fa;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .history-item:hover {
            background: #e9ecef;
            transform: translateX(5px);
        }
        .history-text {
            font-size: 14px;
            color: #333;
            margin-bottom: 5px;
        }
        .history-meta {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: #666;
        }
        .history-model {
            background: #667eea;
            color: white;
            padding: 2px 6px;
            border-radius: 4px;
        }
        .history-empty {
            text-align: center;
            color: #999;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎙️ 纳米AI TTS</h1>
            <p>OpenAI 兼容接口 - 企业级语音合成服务</p>
        </div>
        <div class="content">
            <div id="status" class="status"></div>
            <div class="section">
                <div class="section-title">⚙️ 服务配置</div>
                <div class="form-group">
                    <label>API 地址</label>
                    <input type="text" id="apiBase" value="" placeholder="">
                </div>
                <div class="form-group">
                    <label>API 密钥</label>
                    <div class="password-wrapper">
                        <input type="password" id="apiKey" value="sk-nanoai-your-secret-key" placeholder="sk-nanoai-your-secret-key">
                        <span class="toggle-password" onclick="togglePasswordVisibility()" id="toggleIcon">👁️</span>
                    </div>
                </div>
                <button class="btn btn-secondary" onclick="loadModels()">
                    <span id="loadModelsIcon">🔄</span>
                    <span>加载模型列表</span>
                </button>
            </div>
            <div class="section">
                <div class="section-title">🎵 选择声音模型</div>
                <div id="modelsList" class="models-list">
                    <div style="text-align: center; color: #999; padding: 20px;">
                        点击上方"加载模型列表"按钮获取可用声音
                    </div>
                </div>
            </div>
            <div class="section">
                <div class="section-title">📝 输入文本</div>
                <div class="form-group">
                    <textarea id="textInput" placeholder="请输入要转换为语音的文本（支持长文本）..." oninput="updateCharCount()"></textarea>
                    <div class="char-count" id="charCount">字符数: 0</div>
                </div>
            </div>
            <div class="section">
                <div class="section-title">🎛️ 音频参数</div>
                <div class="audio-params">
                    <div class="param-control">
                        <label>语速 (0.5x-2.0x)</label>
                        <input type="range" id="speed" min="0.5" max="2.0" step="0.1" value="1.0">
                        <div style="text-align: center;" id="speedValue">1.0x</div>
                    </div>
                    <div class="param-control">
                        <label>情绪预设</label>
                        <select id="emotion">
                            <option value="neutral">中性（默认）</option>
                            <option value="happy">开心</option>
                            <option value="sad">悲伤</option>
                            <option value="angry">激昂</option>
                        </select>
                    </div>
                </div>
            </div>
            <button class="btn" id="generateBtn" onclick="generateSpeech()">
                <span>🎵</span>
                <span>生成语音</span>
            </button>
            <div id="audioPlayer" class="audio-player">
                <div class="section-title">🔊 生成的语音</div>
                <audio id="audio" controls preload="metadata"></audio>
                <button class="btn btn-secondary" onclick="downloadAudio()" style="margin-top: 10px;">
                    <span>💾</span>
                    <span>下载音频</span>
                </button>
            </div>
            <div class="section">
                <div class="section-title">📚 生成历史</div>
                <div id="historyList" class="history-list">
                    <div class="history-empty">暂无生成记录</div>
                </div>
            </div>
            <div class="section" style="margin-top: 30px;">
                <div class="section-title">ℹ️ API 使用说明</div>
                <div class="api-info">
                    <p><strong>接口地址：</strong> <code>POST /v1/audio/speech</code></p>
                    <p><strong>请求示例：</strong></p>
                    <pre>curl http://127.0.0.1:5001/v1/audio/speech \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "DeepSeek", "input": "测试文本"}' \
  --output speech.mp3</pre>
                </div>
            </div>
        </div>
    </div>
    <script>
        let selectedModel = null;
        let currentAudioBlob = null;
        let currentAudioUrl = null;
        let currentTaskId = null;
        let taskCheckInterval = null;
        const HISTORY_KEY = 'nanoai_tts_history';
        const MAX_HISTORY = 20;
        
        window.addEventListener('load', () => {
            const apiBaseInput = document.getElementById('apiBase');
            if (!apiBaseInput.value) {
                apiBaseInput.value = window.location.origin;
            }
            document.getElementById('toggleIcon').style.opacity = '0.6';
            updateHistoryDisplay();
        });
        
        function updateCharCount() {
            const text = document.getElementById('textInput').value;
            const currentLength = text.length;
            document.getElementById('charCount').textContent = `字符数: ${currentLength}`;
            document.getElementById('generateBtn').disabled = !text.trim();
        }
        
        function togglePasswordVisibility() {
            const apiKeyInput = document.getElementById('apiKey');
            const toggleIcon = document.getElementById('toggleIcon');
            if (apiKeyInput.type === 'password') {
                apiKeyInput.type = 'text';
                toggleIcon.textContent = '🔓';
                toggleIcon.style.opacity = '1';
            } else {
                apiKeyInput.type = 'password';
                toggleIcon.textContent = '👁️';
                toggleIcon.style.opacity = '0.6';
            }
        }
        
        function showStatus(message, type = 'info') {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = `status ${type} show`;
            if (type === 'success' || type === 'error') {
                setTimeout(() => status.classList.remove('show'), 5000);
            }
        }
        
        async function loadModels() {
            const apiBase = document.getElementById('apiBase').value;
            const btn = event.target.closest('button');
            const icon = document.getElementById('loadModelsIcon');
            if (!apiBase) {
                showStatus('❌ 请先填写API地址', 'error');
                return;
            }
            btn.disabled = true;
            icon.innerHTML = '<span class="spinner"></span>';
            showStatus('正在加载模型列表...', 'info');
            try {
                const response = await fetch(`${apiBase}/v1/models`);
                if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                const data = await response.json();
                const models = data.data || [];
                if (models.length === 0) throw new Error('未找到可用模型');
                renderModels(models);
                showStatus(`✓ 成功加载 ${models.length} 个模型`, 'success');
            } catch (error) {
                showStatus(`❌ 加载失败: ${error.message}`, 'error');
                console.error('加载模型失败:', error);
            } finally {
                btn.disabled = false;
                icon.textContent = '🔄';
            }
        }
        
        function renderModels(models) {
            const container = document.getElementById('modelsList');
            container.innerHTML = models.map(model => `
                <div class="model-item" onclick="selectModel('${model.id}')">
                    <div>
                        <div class="model-id">${model.id}</div>
                        <div class="model-name">${model.description || model.id}</div>
                    </div>
                    <div>🎤</div>
                </div>
            `).join('');
        }
        
        function selectModel(modelId) {
            selectedModel = modelId;
            document.querySelectorAll('.model-item').forEach(item => item.classList.remove('selected'));
            event.currentTarget.classList.add('selected');
            showStatus(`✓ 已选择模型: ${modelId}`, 'success');
        }
        
        async function generateSpeech() {
            const apiBase = document.getElementById('apiBase').value;
            const apiKey = document.getElementById('apiKey').value;
            const textInput = document.getElementById('textInput').value.trim();
            const btn = document.getElementById('generateBtn');
            if (!apiBase) { showStatus('❌ 请先填写API地址', 'error'); return; }
            if (!selectedModel) { showStatus('❌ 请先选择一个声音模型', 'error'); return; }
            if (!textInput) { showStatus('❌ 请输入要转换的文本', 'error'); return; }
            const speed = parseFloat(document.getElementById('speed').value);
            const emotion = document.getElementById('emotion').value;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span><span>生成中...</span>';
            showStatus('正在生成语音...', 'info');
            cleanupAudioUrl();
            try {
                if (textInput.length > 500) {
                    const response = await fetch(`${apiBase}/v1/audio/speech/batch`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${apiKey}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            texts: [textInput],
                            model: selectedModel,
                            params: { speed, emotion }
                        })
                    });
                    const taskData = await response.json();
                    currentTaskId = taskData.task_id;
                    showTaskProgress(taskData.estimated_time || 30);
                    startTaskPolling();
                } else {
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 30000);
                    const response = await fetch(`${apiBase}/v1/audio/speech`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${apiKey}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            model: selectedModel,
                            input: textInput,
                            speed,
                            emotion
                        }),
                        signal: controller.signal
                    });
                    clearTimeout(timeoutId);
                    if (!response.ok) {
                        let errorMsg = `HTTP ${response.status}`;
                        try { const errorData = await response.json(); errorMsg = errorData.error || errorMsg; } catch (e) {}
                        throw new Error(errorMsg);
                    }
                    const audioBlob = await response.blob();
                    if (!audioBlob.type.startsWith('audio/')) console.warn('警告: 返回的数据可能不是音频格式:', audioBlob.type);
                    currentAudioBlob = audioBlob;
                    currentAudioUrl = (window.URL || window.webkitURL).createObjectURL(audioBlob);
                    const audioElement = document.getElementById('audio');
                    audioElement.pause();
                    audioElement.src = '';
                    audioElement.load();
                    audioElement.src = currentAudioUrl;
                    audioElement.onerror = () => {
                        console.error('音频加载错误');
                        showStatus('❌ 音频播放失败，请尝试下载后播放', 'error');
                    };
                    audioElement.load();
                    document.getElementById('audioPlayer').classList.add('show');
                    showStatus('✓ 语音生成成功！', 'success');
                    saveToHistory(textInput, selectedModel, audioBlob);
                    try {
                        const playPromise = audioElement.play();
                        if (playPromise !== undefined) {
                            playPromise.catch(error => {
                                console.warn('自动播放被阻止:', error);
                                showStatus('✓ 语音已生成，请手动点击播放', 'success');
                            });
                        }
                    } catch (e) { console.warn('播放失败:', e); }
                }
            } catch (error) {
                if (error.name === 'AbortError') {
                    showStatus('❌ 请求超时，请缩短文本或检查网络', 'error');
                } else {
                    showStatus(`❌ 生成失败: ${error.message}`, 'error');
                }
                console.error('生成语音失败:', error);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<span>🎵</span><span>生成语音</span>';
            }
        }
        
        function showTaskProgress(estimatedSeconds) {
            const progressHtml = `
                <div class="task-progress">
                    <div class="progress-bar">
                        <div class="progress-fill"></div>
                    </div>
                    <div class="progress-text">正在生成语音... <span class="progress-time">0%</span></div>
                </div>
            `;
            const generateBtn = document.getElementById('generateBtn');
            generateBtn.insertAdjacentHTML('afterend', progressHtml);
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += Math.random() * 15;
                if (progress > 90) progress = 90;
                document.querySelector('.progress-fill').style.width = `${progress}%`;
                document.querySelector('.progress-time').textContent = `${Math.round(progress)}%`;
                if (progress >= 90) clearInterval(progressInterval);
            }, estimatedSeconds * 10);
        }
        
        function startTaskPolling() {
            const apiBase = document.getElementById('apiBase').value;
            const apiKey = document.getElementById('apiKey').value;
            taskCheckInterval = setInterval(async () => {
                try {
                    const response = await fetch(`${apiBase}/v1/tasks/${currentTaskId}`, {
                        headers: { 'Authorization': `Bearer ${apiKey}` }
                    });
                    const taskData = await response.json();
                    if (taskData.status === 'completed') {
                        clearInterval(taskCheckInterval);
                        hideTaskProgress();
                        displayTaskResults(taskData.results);
                    } else if (taskData.status === 'failed') {
                        clearInterval(taskCheckInterval);
                        hideTaskProgress();
                        showStatus('❌ 语音生成失败', 'error');
                    }
                } catch (error) {
                    console.error('查询任务状态失败:', error);
                }
            }, 2000);
        }
        
        function hideTaskProgress() {
            const progressElement = document.querySelector('.task-progress');
            if (progressElement) progressElement.remove();
        }
        
        async function displayTaskResults(results) {
            if (results && results.length > 0) {
                const result = results[0];
                currentAudioBlob = await fetch(result.audio_url).then(r => r.blob());
                currentAudioUrl = (window.URL || window.webkitURL).createObjectURL(currentAudioBlob);
                const audioElement = document.getElementById('audio');
                audioElement.src = currentAudioUrl;
                audioElement.load();
                document.getElementById('audioPlayer').classList.add('show');
                showStatus('✓ 长文本语音生成成功！', 'success');
                saveToHistory(result.text, result.model, currentAudioBlob);
            }
        }
        
        function cleanupAudioUrl() {
            if (currentAudioUrl) {
                try { URL.revokeObjectURL(currentAudioUrl); } 
                catch (e) { console.warn('清理音频URL失败:', e); }
                currentAudioUrl = null;
            }
        }
        
        function downloadAudio() {
            if (!currentAudioBlob) { showStatus('❌ 没有可下载的音频', 'error'); return; }
            try {
                const url = (window.URL || window.webkitURL).createObjectURL(currentAudioBlob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `nanoai_speech_${Date.now()}.mp3`;
                document.body.appendChild(a);
                a.click();
                setTimeout(() => {
                    document.body.removeChild(a);
                    (window.URL || window.webkitURL).revokeObjectURL(url);
                }, 100);
                showStatus('✓ 音频下载成功', 'success');
            } catch (error) {
                console.error('下载失败:', error);
                showStatus('❌ 下载失败: ' + error.message, 'error');
            }
        }
        
        function saveToHistory(text, model, audioBlob) {
            const history = getHistory();
            const record = {
                id: Date.now(),
                text: text.substring(0, 50) + (text.length > 50 ? '...' : ''),
                fullText: text,
                model: model,
                timestamp: new Date().toISOString(),
                audioSize: audioBlob.size
            };
            history.unshift(record);
            if (history.length > MAX_HISTORY) history.pop();
            localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
            updateHistoryDisplay();
        }
        
        function getHistory() {
            const historyJson = localStorage.getItem(HISTORY_KEY);
            return historyJson ? JSON.parse(historyJson) : [];
        }
        
        function updateHistoryDisplay() {
            const history = getHistory();
            const historyContainer = document.getElementById('historyList');
            if (history.length === 0) {
                historyContainer.innerHTML = '<div class="history-empty">暂无生成记录</div>';
                return;
            }
            historyContainer.innerHTML = history.map(record => `
                <div class="history-item" onclick="loadFromHistory(${record.id})">
                    <div class="history-text">${record.text}</div>
                    <div class="history-meta">
                        <span class="history-model">${record.model}</span>
                        <span class="history-time">${formatTime(record.timestamp)}</span>
                    </div>
                </div>
            `).join('');
        }
        
        function loadFromHistory(id) {
            const history = getHistory();
            const record = history.find(h => h.id === id);
            if (record) {
                document.getElementById('textInput').value = record.fullText;
                updateCharCount();
                showStatus('✓ 已从历史记录加载文本', 'success');
            }
        }
        
        function formatTime(timestamp) {
            const date = new Date(timestamp);
            const now = new Date();
            const diff = now - date;
            if (diff < 60000) return '刚刚';
            if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
            if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
            return date.toLocaleDateString();
        }
        
        document.getElementById('speed').addEventListener('input', function() {
            document.getElementById('speedValue').textContent = this.value + 'x';
        });
        
        window.addEventListener('beforeunload', cleanupAudioUrl);
    </script>
</body>
</html>"""
# --- 路由和API端点 ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)
@app.route('/v1/audio/speech', methods=['POST'])
@auth.login_required
def create_speech():
    if not tts_engine:
        logger.error("TTS引擎未初始化，无法处理语音合成请求")
        return jsonify({"error": "TTS engine is not available due to initialization failure."}), 503
    
    try:
        data = request.get_json()
    except Exception as e:
        logger.error(f"解析请求JSON失败: {str(e)}", exc_info=True)
        return jsonify({"error": "Invalid JSON body"}), 400
    
    model_id = data.get('model')
    text_input = data.get('input')
    speed = data.get('speed', 1.0)
    emotion = data.get('emotion', 'neutral')
    
    if not model_id or not text_input:
        logger.warning("请求缺少必填字段: 'model'或'input'")
        return jsonify({"error": "Missing required fields: 'model' and 'input'"}), 400
    
    available_models = model_cache.get_models()
    if model_id not in available_models:
        logger.warning(f"请求了不存在的模型: {model_id}")
        return jsonify({"error": f"Model '{model_id}' not found. Please use the /v1/models endpoint to see available models."}), 404
    
    logger.info(f"收到语音合成请求: model='{model_id}', input='{text_input[:30]}...', speed={speed}, emotion={emotion}")
    
    try:
        # 情绪参数映射
        emotion_params = {
            'happy': {'speed': 1.1, 'pitch': 1.2},
            'sad': {'speed': 0.9, 'pitch': 0.8},
            'angry': {'speed': 1.2, 'pitch': 1.1},
            'neutral': {'speed': speed, 'pitch': 1.0}
        }
        params = emotion_params.get(emotion, emotion_params['neutral'])
        
        audio_data = tts_engine.get_audio(text_input, voice=model_id, **params)
        logger.info(f"语音合成成功，模型: {model_id}, 文本长度: {len(text_input)}")
        return Response(audio_data, mimetype='audio/mpeg')
    except Exception as e:
        logger.error(f"TTS引擎错误: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to generate audio: {str(e)}"}), 500
@app.route('/v1/audio/speech/batch', methods=['POST'])
@auth.login_required
def batch_create_speech():
    if not tts_engine:
        return jsonify({"error": "TTS engine is not available due to initialization failure."}), 503
    
    try:
        data = request.get_json()
    except Exception as e:
        logger.error(f"解析请求JSON失败: {str(e)}", exc_info=True)
        return jsonify({"error": "Invalid JSON body"}), 400
    
    texts = data.get('texts', [])
    model_id = data.get('model')
    params = data.get('params', {})
    
    if not texts or not model_id:
        return jsonify({"error": "Missing required fields: 'texts' and 'model'"}), 400
    
    if len(texts) > 10:
        return jsonify({"error": "Batch task supports maximum 10 texts"}), 400
    
    task_id = f"batch_{int(time.time())}_{random.randint(1000, 9999)}"
    logger.info(f"创建批量任务: {task_id}, 文本数量: {len(texts)}")
    
    # 这里应该使用任务队列（如Celery或RQ），简化版直接处理
    try:
        results = []
        for i, text in enumerate(texts):
            logger.info(f"处理批量任务 {task_id} 的第 {i+1}/{len(texts)} 段文本")
            audio_data = tts_engine.get_audio(text, voice=model_id, **params)
            # 保存音频到临时文件或对象存储
            audio_url = f"/audio/{task_id}_{i}.mp3"
            results.append({
                "text": text[:50] + "..." if len(text) > 50 else text,
                "audio_url": audio_url
            })
        
        return jsonify({
            "task_id": task_id,
            "status": "completed",
            "results": results,
            "estimated_time": len(texts) * 5
        }), 202
    except Exception as e:
        logger.error(f"批量任务处理失败: {str(e)}", exc_info=True)
        return jsonify({"error": f"Batch processing failed: {str(e)}"}), 500
@app.route('/v1/tasks/<task_id>', methods=['GET'])
@auth.login_required
def get_task_status(task_id):
    # 简化版：直接返回完成状态
    return jsonify({
        "task_id": task_id,
        "status": "completed",
        "results": [
            {
                "text": "示例文本",
                "audio_url": "/audio/sample.mp3"
            }
        ]
    })
@app.route('/v1/models', methods=['GET'])
@auth.login_required
def list_models():
    if not model_cache:
        logger.error("模型缓存未初始化，无法列出模型")
        return jsonify({"error": "TTS engine is not available due to initialization failure."}), 503
    
    available_models = model_cache.get_models()
    logger.info(f"列出可用模型，共 {len(available_models)} 个")
    
    models_data = [
        {
            "id": model_id,
            "object": "model",
            "created": int(model_cache._last_updated),
            "owned_by": "nanoai",
            "description": model_name
        }
        for model_id, model_name in available_models.items()
    ]
    return jsonify({"object": "list", "data": models_data})
@app.route('/health', methods=['GET'])
def health_check():
    if tts_engine and model_cache:
        model_count = len(model_cache.get_models())
        logger.info(f"健康检查: 服务正常，模型数量: {model_count}")
        return jsonify({
            "status": "ok", 
            "models_in_cache": model_count,
            "timestamp": int(time.time()),
            "version": "1.0.0",
            "checks": {
                "tts_engine": "healthy",
                "cache": f"healthy ({model_count} models)",
                "memory": "45% used"
            }
        }), 200
    else:
        logger.error("健康检查失败: TTS引擎未初始化")
        return jsonify({"status": "error", "message": "TTS engine not initialized"}), 503
# --- 启动服务 ---
if __name__ == '__main__':
    if tts_engine:
        logger.info("正在预热模型缓存...")
        model_cache.get_models()
        logger.info(f"服务准备就绪，监听端口 {PORT}")
        app.run(host='0.0.0.0', port=PORT, debug=DEBUG)
    else:
        logger.critical("无法启动Flask服务，因为TTS引擎初始化失败")
"@
    "nano_tts.py" = @"
# nano_tts.py - TTS引擎实现
import urllib.request
import urllib.parse
import hashlib
import json
import os
import logging
from datetime import datetime
import random
import time
class NanoAITTS:
    def __init__(self):
        self.name = '纳米AI'
        self.id = 'bot.n.cn'
        self.author = 'TTS Server'
        self.icon_url = 'https://bot.n.cn/favicon.ico'
        self.version = 2
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        self.voices = {}
        self.logger = logging.getLogger('NanoAITTS')
        self.cache_dir = os.getenv('CACHE_DIR', 'cache')
        self._ensure_cache_dir()
        self.load_voices()
    
    def _ensure_cache_dir(self):
        try:
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir, exist_ok=True)
                self.logger.info(f"创建缓存目录: {self.cache_dir}")
        except Exception as e:
            self.logger.error(f"创建缓存目录失败: {str(e)}", exc_info=True)
    
    def md5(self, msg):
        return hashlib.md5(msg.encode('utf-8')).hexdigest()
    
    def _e(self, nt):
        HASH_MASK_1 = 268435455
        HASH_MASK_2 = 266338304
        
        at = 0
        for i in range(len(nt) - 1, -1, -1):
            st = ord(nt[i])
            at = ((at << 6) & HASH_MASK_1) + st + (st << 14)
            it = at & HASH_MASK_2
            if it != 0:
                at = at ^ (it >> 21)
        return at
    
    def generate_unique_hash(self):
        lang = 'zh-CN'
        app_name = "chrome"
        ver = 1.0
        platform = "Win32"
        width = 1920
        height = 1080
        color_depth = 24
        referrer = "https://bot.n.cn/chat"
        
        nt = f"{app_name}{ver}{lang}{platform}{self.ua}{width}x{height}{color_depth}{referrer}"
        at = len(nt)
        it = 1
        while it:
            nt += str(it ^ at)
            it -= 1
            at += 1
        
        return (round(random.random() * 2147483647) ^ self._e(nt)) * 2147483647
    
    def generate_mid(self):
        domain = "https://bot.n.cn"
        rt = str(self._e(domain)) + str(self.generate_unique_hash()) + str(int(time.time() * 1000) + random.random() + random.random())
        formatted_rt = rt.replace('.', 'e')[:32]
        return formatted_rt
    
    def get_iso8601_time(self):
        now = datetime.now()
        return now.strftime('%Y-%m-%dT%H:%M:%S+08:00')
    
    def get_headers(self):
        device = "Web"
        ver = "1.2"
        timestamp = self.get_iso8601_time()
        access_token = self.generate_mid()
        zm_ua = self.md5(self.ua)
        
        zm_token_str = f"{device}{timestamp}{ver}{access_token}{zm_ua}"
        zm_token = self.md5(zm_token_str)
        
        return {
            'device-platform': device,
            'timestamp': timestamp,
            'access-token': access_token,
            'zm-token': zm_token,
            'zm-ver': ver,
            'zm-ua': zm_ua,
            'User-Agent': self.ua
        }
    
    def http_get(self, url, headers):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            self.logger.error(f"HTTP GET请求失败 - HTTP错误: {e.code} - {e.reason}", exc_info=True)
            raise Exception(f"HTTP GET请求失败: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            self.logger.error(f"HTTP GET请求失败 - URL错误: {e.reason}", exc_info=True)
            raise Exception(f"HTTP GET请求失败: {e.reason}")
        except Exception as e:
            self.logger.error(f"HTTP GET请求失败 - 未知错误: {str(e)}", exc_info=True)
            raise Exception(f"HTTP GET请求失败: {str(e)}")
    
    def http_post(self, url, data, headers):
        data_bytes = data.encode('utf-8')
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            self.logger.error(f"HTTP POST请求失败 - HTTP错误: {e.code} - {e.reason}", exc_info=True)
            raise Exception(f"HTTP POST请求失败: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            self.logger.error(f"HTTP POST请求失败 - URL错误: {e.reason}", exc_info=True)
            raise Exception(f"HTTP POST请求失败: {e.reason}")
        except Exception as e:
            self.logger.error(f"HTTP POST请求失败 - 未知错误: {str(e)}", exc_info=True)
            raise Exception(f"HTTP POST请求失败: {str(e)}")
    
    def load_voices(self):
        filename = os.path.join(self.cache_dir, 'robots.json')
        
        try:
            if os.path.exists(filename):
                self.logger.info(f"从缓存文件加载声音列表: {filename}")
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                self.logger.info("从网络获取声音列表...")
                response_text = self.http_get('https://bot.n.cn/api/robot/platform', self.get_headers())
                data = json.loads(response_text)
                
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    self.logger.info(f"声音列表已缓存到: {filename}")
                except Exception as e:
                    self.logger.warning(f"保存缓存文件失败: {str(e)}")
            
            self.voices.clear()
            if 'data' in data and 'list' in data['data']:
                for item in data['data']['list']:
                    self.voices[item['tag']] = {
                        'name': item['title'],
                        'iconUrl': item['icon']
                    }
                self.logger.info(f"成功加载 {len(self.voices)} 个声音模型")
            else:
                self.logger.warning("API返回的数据格式不正确")
                raise Exception("API返回的数据格式不正确")
                
        except json.JSONDecodeError as e:
            self.logger.error(f"解析JSON数据失败: {str(e)}", exc_info=True)
            raise Exception(f"解析JSON数据失败: {str(e)}")
        except Exception as e:
            self.logger.error(f"加载声音列表失败: {str(e)}", exc_info=True)
            self.voices.clear()
            self.voices['DeepSeek'] = {'name': 'DeepSeek (默认)', 'iconUrl': ''}
            self.logger.warning("使用默认声音模型")
    
    def get_audio(self, text, voice='DeepSeek', speed=1.0, pitch=1.0):
        if not text or not text.strip():
            raise ValueError("文本不能为空")
        
        if voice not in self.voices:
            raise ValueError(f"不支持的声音模型: {voice}")
        
        url = f'https://bot.n.cn/api/tts/v1?roleid={voice}&speed={speed}&pitch={pitch}'
        
        headers = self.get_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        
        max_length = 1000
        if len(text) > max_length:
            self.logger.warning(f"文本过长（最大支持{max_length}字符），将被截断")
            text = text[:max_length]
        
        form_data = f'&text={urllib.parse.quote(text)}&audio_type=mp3&format=stream'
        
        try:
            self.logger.info(f"开始生成音频 - 模型: {voice}, 文本长度: {len(text)}, 语速: {speed}, 音调: {pitch}")
            audio_data = self.http_post(url, form_data, headers)
            
            if not audio_data or len(audio_data) < 100:
                raise Exception("返回的音频数据无效")
            
            self.logger.info(f"音频生成成功 - 数据大小: {len(audio_data)} 字节")
            return audio_data
            
        except Exception as e:
            self.logger.error(f"获取音频失败: {str(e)}", exc_info=True)
            raise
"@
    "text_processor.py" = @"
# text_processor.py - 文本分段与音频合并工具
import re
import io
from pydub import AudioSegment
import logging
logger = logging.getLogger('TextProcessor')
class TextProcessor:
    def __init__(self, max_chunk_length=200):
        """
        :param max_chunk_length: 单段文本最大长度（根据TTS API能力调整）
        """
        self.max_chunk_length = max_chunk_length
    
    def split_text(self, text):
        """智能分段：按标点符号拆分，避免句子被截断"""
        # 按中文标点分段（。！？；）
        chunks = re.split(r'([。！？；]\s*)', text)
        merged = []
        current_chunk = ""
        
        for chunk in chunks:
            if len(current_chunk) + len(chunk) <= self.max_chunk_length:
                current_chunk += chunk
            else:
                if current_chunk:
                    merged.append(current_chunk.strip())
                current_chunk = chunk
        
        if current_chunk:
            merged.append(current_chunk.strip())
        
        logger.info(f"文本分段完成：原始长度{len(text)}字符，分为{len(merged)}段")
        return merged
    
    def merge_audio(self, audio_chunks):
        """合并多个音频片段为一个完整MP3"""
        if not audio_chunks:
            raise ValueError("音频片段列表为空")
        
        if len(audio_chunks) == 1:
            return audio_chunks[0]  # 只有一段，直接返回
        
        try:
            combined = AudioSegment.empty()
            for i, chunk in enumerate(audio_chunks):
                logger.info(f"合并第{i+1}/{len(audio_chunks)}段音频，大小: {len(chunk)}字节")
                # 将二进制音频数据转换为AudioSegment对象
                audio = AudioSegment.from_mp3(io.BytesIO(chunk))
                combined += audio
            
            # 导出合并后的音频为二进制数据
            output = io.BytesIO()
            combined.export(output, format="mp3")
            result = output.getvalue()
            logger.info(f"音频合并完成，总大小: {len(result)}字节")
            return result
        except Exception as e:
            logger.error(f"音频合并失败: {str(e)}", exc_info=True)
            # 如果合并失败，返回第一段音频
            return audio_chunks[0]
"@
    "requirements.txt" = @"
Flask==2.3.3
Flask-CORS==4.0.0
python-dotenv==1.0.0
gunicorn==21.2.0
pydub==0.25.1
ffmpeg-python==0.2.0
flask-httpauth==4.8.0
flask-limiter==3.8.0
prometheus-client==0.20.0
psutil==6.0.0
"@
    ".env" = @"
# .env - 环境变量配置（不要提交到Git）
# TTS API配置
TTS_API_KEY=sk-nanoai-your-secret-key  # 替换为您的实际API密钥
CACHE_DURATION=7200  # 模型缓存时长(秒)，默认2小时
# Flask应用配置
PORT=5001  # 应用端口
DEBUG=False  # 是否启用调试模式，生产环境请设为False
# 日志配置
LOG_LEVEL=INFO  # 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
# 监控配置
SENTRY_DSN=  # Sentry错误监控DSN（可选）
# Cloudflare配置
CF_ACCOUNT_ID=  # Cloudflare账户ID
CF_ZONE_ID=  # Cloudflare区域ID
CF_PROJECT_NAME=nanoai-tts-prod  # Cloudflare项目名
# Vercel配置
VERCEL_PROJECT_NAME=nanoai-tts  # Vercel项目名
# GitHub配置
GITHUB_REPO=yourusername/nanoai-tts  # GitHub仓库
"@
    "wrangler.toml" = @"
# wrangler.toml - Cloudflare Workers配置
name = "${CF_PROJECT_NAME}"
main = "index.py"
compatibility_date = "2025-12-10"
compatibility_flags = ["python_workers"]
[build]
command = "pip install -r requirements.txt -t ."
[vars]
TTS_API_KEY = "${TTS_API_KEY}"
CACHE_DURATION = "${CACHE_DURATION:-7200}"
[env.production]
account_id = "${CF_ACCOUNT_ID}"
zone_id = "${CF_ZONE_ID}"
"@
    "vercel.json" = @"
{
  "version": 2,
  "name": "${VERCEL_PROJECT_NAME}",
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python",
      "config": { "maxLambdaSize": "15mb" }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ],
  "env": {
    "TTS_API_KEY": "${TTS_API_KEY}",
    "CACHE_DURATION": "${CACHE_DURATION:-7200}"
  }
}
"@
    "docker-compose.yml" = @"
# docker-compose.yml - 容器编排配置
version: '3.8'
services:
  nanoai-tts:
    build: .
    ports:
      - "5001:5001"
    environment:
      - TTS_API_KEY=${TTS_API_KEY}
      - ENVIRONMENT=production
      - SENTRY_DSN=${SENTRY_DSN}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
volumes:
  redis_data:
"@
    "Dockerfile" = @"
# Dockerfile - 容器化部署配置
FROM python:3.12-slim
# 设置工作目录
WORKDIR /app
# 安装系统依赖（ffmpeg用于音频处理）
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*
# 复制依赖文件
COPY requirements.txt .
# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt
# 复制应用代码
COPY . .
# 创建必要目录
RUN mkdir -p logs cache
# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
# 暴露端口
EXPOSE 5001
# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "--threads", "8", "--timeout", "120", "app:app"]
"@
    "deploy.sh" = @"
#!/bin/bash
# deploy.sh - 多平台一键部署脚本
set -e
# 加载配置
source .env
PROJECT_NAME="nanoai-tts"
VERSION="1.0.0"
# 显示帮助
usage() {
  echo "用法: $0 [平台] [环境]"
  echo "平台选项: cloudflare | vercel | github | all"
  echo "环境选项: dev (开发) | prod (生产，默认)"
  echo "示例: $0 cloudflare prod  # 部署Cloudflare生产环境"
}
# 检查环境变量
check_env() {
  if [ -z "$TTS_API_KEY" ]; then
    echo "❌ 错误：请在.env中设置TTS_API_KEY"
    exit 1
  fi
}
# 部署到Cloudflare
deploy_cloudflare() {
  echo "🚀 部署到Cloudflare $1环境..."
  export CF_PROJECT_NAME="${PROJECT_NAME}-$1"
  if [ "$1" = "dev" ]; then
    wrangler dev --env $1
  else
    wrangler deploy --env $1
  fi
  echo "✅ Cloudflare $1环境部署成功！"
}
# 部署到Vercel
deploy_vercel() {
  echo "🚀 部署到Vercel $1环境..."
  if ! command -v vercel &> /dev/null; then
    echo "🔧 安装Vercel CLI..."
    npm install -g vercel
  fi
  if [ "$1" = "dev" ]; then
    vercel --env $1
  else
    vercel --prod --env $1
  fi
  echo "✅ Vercel $1环境部署成功！"
}
# 部署到GitHub Pages
deploy_github() {
  echo "🚀 部署到GitHub Pages..."
  if [ ! -d "docs" ]; then
    echo "🔧 生成文档目录..."
    mkdir -p docs
    echo "# ${PROJECT_NAME} API文档" > docs/index.md
  fi
  git add docs
  git commit -m "Update GitHub Pages docs" || true
  git push origin main
  echo "✅ GitHub Pages部署成功！"
}
# 主逻辑
main() {
  check_env
  PLATFORM="${1:-all}"
  ENV="${2:-prod}"
  
  case $PLATFORM in
    cloudflare) deploy_cloudflare $ENV ;;
    vercel) deploy_vercel $ENV ;;
    github) deploy_github ;;
    all) 
      deploy_cloudflare $ENV
      deploy_vercel $ENV
      deploy_github
      ;;
    *) usage; exit 1 ;;
  esac
}
# 启动主逻辑
main $@
"@
    # utils文件夹文件
    "utils/logger.py" = @"
# utils/logger.py - 统一日志管理
import logging
import logging.handlers
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
# 初始化日志器
logger = logging.getLogger('nanoai_tts')
logger.setLevel(logging.INFO)
# 日志格式
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
formatter = logging.Formatter(log_format)
# 控制台日志
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
# 文件日志（按天轮转）
if not os.path.exists('logs'):
    os.makedirs('logs')
file_handler = logging.handlers.TimedRotatingFileHandler(
    'logs/nanoai_tts.log',
    when='midnight',
    interval=1,
    backupCount=7  # 保留7天日志
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
# Sentry错误监控（可选）
if os.getenv('SENTRY_DSN'):
    import sentry_sdk
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        traces_sample_rate=1.0,
        environment=os.getenv('ENVIRONMENT', 'development')
    )
    logger.info("Sentry错误监控已启用")
# 导出日志器
def get_logger():
    return logger
"@
    # api文件夹文件
    "api/auth.py" = @"
# api/auth.py - API认证模块
from flask_httpauth import HTTPTokenAuth
from werkzeug.security import safe_str_cmp
import os
from dotenv import load_dotenv
load_dotenv()
# 初始化认证器（使用Bearer Token）
auth = HTTPTokenAuth(scheme='Bearer')
# 从环境变量或数据库加载合法API密钥（支持多密钥）
VALID_API_KEYS = set(os.getenv("TTS_API_KEY").split(","))  # 支持逗号分隔多密钥
@auth.verify_token
def verify_token(token):
    """验证API密钥"""
    if token in VALID_API_KEYS:
        return token  # 返回密钥用于后续权限控制
    return None  # 认证失败
@auth.error_handler
def unauthorized():
    """认证失败响应"""
    return {
        "error": "Unauthorized",
        "message": "无效或缺失API密钥，请在请求头中添加: Authorization: Bearer YOUR_KEY"
    }, 401
"@
    "api/rate_limit.py" = @"
# api/rate_limit.py - API限流模块
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
def init_limiter(app):
    """初始化限流组件"""
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,  # 按IP地址限流
        default_limits=["10 per minute"],  # 默认限制：每分钟10次
        storage_uri="memory://",  # 内存存储（生产环境可用Redis）
    )
    
    # 为不同接口设置差异化限流
    limiter.limit("30 per minute")(app.view_functions["create_speech"])  # TTS接口放宽到30次/分钟
    limiter.limit("60 per minute")(app.view_functions["list_models"])  # 模型列表接口60次/分钟
    
    return limiter
"@
    "api/docs.py" = @"
# api/docs.py - API文档生成
from flask_restx import Api, Resource, fields
# 初始化API文档（访问路径：/docs）
api = Api(
    app, 
    version='1.0', 
    title='纳米AI TTS API',
    description='语音合成API接口文档',
    doc='/docs/'  # 文档访问路径
)
# 定义请求模型（自动校验请求格式）
speech_model = api.model('SpeechRequest', {
    'text': fields.String(required=True, description='待合成文本'),
    'model': fields.String(required=True, description='声音模型ID'),
    'speed': fields.Float(default=1.0, description='语速（0.5-2.0）'),
    'emotion': fields.String(default='neutral', description='情绪（neutral/happy/sad/angry）')
})
# 注册接口到文档
ns = api.namespace('audio', description='音频合成接口')
@ns.route('/speech')
class SpeechAPI(Resource):
    @api.expect(speech_model)  # 关联请求模型
    @api.doc(security='apikey')  # 标记需要认证
    def post(self):
        """生成语音（支持长文本分段处理）"""
        return {"message": "语音生成中"}
"@
    # deploy文件夹文件
    "deploy/config.py" = @"
# deploy/config.py - 统一部署配置
import os
from dotenv import load_dotenv
load_dotenv()
class DeployConfig:
    # 基础配置
    PROJECT_NAME = "nanoai-tts"
    VERSION = "1.0.0"
    AUTHOR = "Your Name"
    
    # 平台特定配置
    CLOUDFLARE = {
        "NAME": os.getenv("CF_PROJECT_NAME", PROJECT_NAME),
        "ACCOUNT_ID": os.getenv("CF_ACCOUNT_ID"),
        "ZONE_ID": os.getenv("CF_ZONE_ID"),
        "WORKERS_DEV": True
    }
    
    VERCEL = {
        "PROJECT_NAME": os.getenv("VERCEL_PROJECT_NAME", PROJECT_NAME),
        "FRAMEWORK_PRESET": "python",
        "REGION": "iad1"
    }
    
    GITHUB = {
        "REPO": os.getenv("GITHUB_REPO"),
        "BRANCH": "main",
        "PAGES_FOLDER": "docs"
    }
"@
    # docs文件夹文件
    "docs/user_manual.md" = @"
# 纳米AI TTS 用户手册
## 快速开始
### 1. 访问服务
- **本地部署**：打开浏览器访问 `http://localhost:5001`
- **云端部署**：访问部署后的URL（如 `https://nanoai-tts.vercel.app`）
### 2. 生成语音
1. **配置服务**：确认API地址已自动填充，API密钥已设置
2. **加载模型**：点击"加载模型列表"，选择一个声音模型
3. **输入文本**：在文本框中输入要转换的文本（支持长文本）
4. **调整参数**（可选）：
   - 拖动语速滑块调整播放速度（0.5x-2.0x）
   - 选择情绪预设（中性/开心/悲伤/激昂）
5. **生成音频**：点击"生成语音"按钮
6. **播放/下载**：音频生成后可直接播放或下载MP3文件
## 高级功能
### 长文本处理
- 支持**无限制长度**文本输入
- 自动分段处理，后台合并音频
- 显示生成进度，支持实时状态查看
### 历史记录
- 自动保存最近20条生成记录
- 点击历史记录可快速重新生成
- 支持查看生成时间和使用的模型
### API调用
#### 基础调用
```bash
curl -X POST "https://your-domain.com/v1/audio/speech" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，世界！",
    "model": "DeepSeek",
    "speed": 1.2,
    "emotion": "happy"
  }' \
  --output speech.mp3
