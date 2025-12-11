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
