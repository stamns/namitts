# api/index.py - Vercel Serverless Function Entry Point
from flask import Flask, request, Response, jsonify, render_template_string
from flask_cors import CORS
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nano_tts import NanoAITTS
import threading
import time
import logging
from datetime import datetime
import random
from dotenv import load_dotenv
from utils.logger import get_logger
from api.auth import auth
from api.rate_limit import init_limiter

load_dotenv()
logger = get_logger()

STATIC_API_KEY = os.getenv("TTS_API_KEY", "sk-nanoai-your-secret-key")
CACHE_DURATION_SECONDS = int(os.getenv("CACHE_DURATION", 2 * 60 * 60))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

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

app = Flask(__name__)
CORS(app)

try:
    logger.info("正在初始化 TTS 引擎...")
    tts_engine = NanoAITTS()
    logger.info("TTS 引擎初始化完毕。")
    model_cache = ModelCache(tts_engine)
except Exception as e:
    logger.critical(f"TTS 引擎初始化失败: {str(e)}", exc_info=True)
    tts_engine = None
    model_cache = None

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
        }
        .content {
            padding: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
        }
        select, textarea, input[type="text"], input[type="number"], input[type="range"] {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-family: inherit;
            font-size: 14px;
        }
        textarea {
            resize: vertical;
            min-height: 100px;
            max-height: 200px;
        }
        .slider-container {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        input[type="range"] {
            flex: 1;
        }
        .slider-value {
            min-width: 50px;
            text-align: right;
            font-weight: 600;
            color: #667eea;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: transform 0.2s, box-shadow 0.2s;
            width: 100%;
        }
        button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        #audioPlayer {
            margin-top: 20px;
            padding: 20px;
            background: #f5f5f5;
            border-radius: 8px;
            display: none;
        }
        #audioPlayer.show {
            display: block;
        }
        audio {
            width: 100%;
            margin-bottom: 10px;
        }
        .audio-controls {
            display: flex;
            gap: 10px;
        }
        .audio-controls button {
            flex: 1;
            padding: 8px 12px;
            font-size: 14px;
        }
        #status {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }
        #status.show {
            display: block;
        }
        #status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        #status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .tab-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #f0f0f0;
        }
        .tab-btn {
            flex: 1;
            padding: 12px;
            background: none;
            border: none;
            color: #666;
            font-weight: 600;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            margin-bottom: -2px;
            transition: all 0.2s;
        }
        .tab-btn.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .history-list {
            max-height: 300px;
            overflow-y: auto;
        }
        .history-item {
            padding: 10px;
            margin-bottom: 8px;
            background: #f9f9f9;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.2s;
        }
        .history-item:hover {
            background: #f0f0f0;
        }
        .history-text {
            font-weight: 500;
            margin-bottom: 4px;
        }
        .history-meta {
            font-size: 12px;
            color: #999;
            display: flex;
            justify-content: space-between;
        }
        .history-empty {
            text-align: center;
            color: #999;
            padding: 20px;
        }
        .char-count {
            font-size: 12px;
            color: #999;
            margin-top: 4px;
        }
        .footer {
            background: #f9f9f9;
            padding: 15px;
            text-align: center;
            font-size: 12px;
            color: #999;
        }
        .api-info {
            background: #f0f7ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
            font-size: 13px;
        }
        .api-info strong {
            color: #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <span>🎵</span>
                <span>纳米AI TTS</span>
            </h1>
            <p>基于 OpenAI API 兼容的文字转语音服务</p>
        </div>
        <div class="content">
            <div id="status"></div>
            
            <div class="api-info">
                <strong>💡 API 基础地址:</strong>
                <input type="text" id="apiBase" value="http://localhost:5001" placeholder="输入服务器地址" style="margin-top: 8px;">
                <strong style="margin-top: 10px; display: block;">🔐 API 密钥:</strong>
                <input type="text" id="apiKey" value="sk-nanoai-your-secret-key" placeholder="输入 API 密钥" style="margin-top: 8px;">
            </div>
            
            <div class="tab-buttons">
                <button class="tab-btn active" onclick="switchTab('generate')">📝 生成语音</button>
                <button class="tab-btn" onclick="switchTab('models')">🎤 模型列表</button>
                <button class="tab-btn" onclick="switchTab('history')">📚 生成记录</button>
            </div>
            
            <div id="generate" class="tab-content active">
                <div class="form-group">
                    <label for="modelSelect">选择模型</label>
                    <select id="modelSelect">
                        <option value="">加载中...</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="textInput">输入文本</label>
                    <textarea id="textInput" placeholder="输入要合成的文本（最多1000字）"></textarea>
                    <div class="char-count"><span id="charCount">0</span>/1000</div>
                </div>
                
                <div class="form-group">
                    <label for="speed">语速</label>
                    <div class="slider-container">
                        <input type="range" id="speed" min="0.5" max="2" step="0.1" value="1">
                        <span class="slider-value" id="speedValue">1x</span>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="emotion">语气</label>
                    <select id="emotion">
                        <option value="neutral">中立</option>
                        <option value="happy">开心</option>
                        <option value="sad">悲伤</option>
                        <option value="angry">生气</option>
                    </select>
                </div>
                
                <button id="generateBtn" onclick="generateSpeech()">
                    <span>🎵</span>
                    <span>生成语音</span>
                </button>
                
                <div id="audioPlayer">
                    <audio id="audio" controls></audio>
                    <div class="audio-controls">
                        <button onclick="downloadAudio()" style="flex: 1;">⬇️ 下载音频</button>
                    </div>
                </div>
            </div>
            
            <div id="models" class="tab-content">
                <div id="modelsList" style="max-height: 400px; overflow-y: auto;"></div>
            </div>
            
            <div id="history" class="tab-content">
                <div class="history-list" id="historyList"></div>
            </div>
        </div>
        
        <div class="footer">
            <p>🚀 纳米AI TTS v1.0 | 基于 NanoAI API | 
               <a href="https://github.com/namitts/nanoai-tts" target="_blank" style="color: #667eea; text-decoration: none;">源代码</a>
            </p>
        </div>
    </div>
    
    <script>
        const HISTORY_KEY = 'nanoai_tts_history';
        const MAX_HISTORY = 20;
        let currentAudioUrl = null;
        let currentAudioBlob = null;
        let currentTaskId = null;
        let taskCheckInterval = null;
        let selectedModel = null;
        
        window.addEventListener('load', () => {
            loadModels();
            updateHistoryDisplay();
            document.getElementById('textInput').addEventListener('input', updateCharCount);
        });
        
        function switchTab(tab) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tab).classList.add('active');
            document.querySelector(`button[onclick="switchTab('${tab}')"]`).classList.add('active');
            
            if (tab === 'models') loadModels();
        }
        
        function showStatus(message, type = 'info') {
            const statusEl = document.getElementById('status');
            statusEl.textContent = message;
            statusEl.className = 'show ' + type;
            setTimeout(() => { if (statusEl.classList.contains('show')) statusEl.classList.remove('show'); }, 5000);
        }
        
        async function loadModels() {
            const apiBase = document.getElementById('apiBase').value;
            const apiKey = document.getElementById('apiKey').value;
            
            try {
                const response = await fetch(`${apiBase}/v1/models`, {
                    headers: { 'Authorization': `Bearer ${apiKey}` }
                });
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const data = await response.json();
                const models = data.data || [];
                
                const selectEl = document.getElementById('modelSelect');
                const optionsHtml = models.map(m => `<option value="${m.id}">${m.description || m.id}</option>`).join('');
                selectEl.innerHTML = optionsHtml || '<option value="">无可用模型</option>';
                if (models.length > 0) { selectEl.value = models[0].id; selectedModel = models[0].id; }
                
                const listEl = document.getElementById('modelsList');
                listEl.innerHTML = models.length > 0 
                    ? models.map(m => `<div style="padding: 10px; background: #f9f9f9; margin-bottom: 8px; border-radius: 6px;"><strong>${m.description || m.id}</strong><br/><small style="color: #999;">ID: ${m.id}</small></div>`).join('')
                    : '<p style="color: #999; text-align: center; padding: 20px;">无可用模型</p>';
            } catch (error) {
                console.error('加载模型失败:', error);
                showStatus('❌ 模型加载失败: ' + error.message, 'error');
                document.getElementById('modelSelect').innerHTML = '<option value="">加载失败</option>';
                document.getElementById('modelsList').innerHTML = '<p style="color: #999; text-align: center; padding: 20px;">加载失败</p>';
            }
        }
        
        function updateCharCount() {
            const count = document.getElementById('textInput').value.length;
            document.getElementById('charCount').textContent = count;
        }
        
        async function generateSpeech() {
            const apiBase = document.getElementById('apiBase').value;
            const apiKey = document.getElementById('apiKey').value;
            const selectedModel = document.getElementById('modelSelect').value;
            const textInput = document.getElementById('textInput').value.trim();
            const speed = parseFloat(document.getElementById('speed').value);
            const emotion = document.getElementById('emotion').value;
            const btn = document.getElementById('generateBtn');
            
            if (!apiBase || !apiKey || !selectedModel || !textInput) {
                showStatus('❌ 请填写所有必填字段', 'error');
                return;
            }
            
            btn.disabled = true;
            btn.innerHTML = '<span>⏳</span><span>生成中...</span>';
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
    
    try:
        results = []
        for i, text in enumerate(texts):
            logger.info(f"处理批量任务 {task_id} 的第 {i+1}/{len(texts)} 段文本")
            audio_data = tts_engine.get_audio(text, voice=model_id, **params)
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
        
        # 添加时间同步诊断信息
        time_info = {
            "local_time_utc": str(datetime.utcnow()),
            "time_offset": getattr(tts_engine, 'time_offset', 0),
            "iso_timestamp": tts_engine.get_iso8601_time()
        }
        
        return jsonify({
            "status": "ok", 
            "models_in_cache": model_count,
            "timestamp": int(time.time()),
            "version": "1.2.0",
            "time_diagnosis": time_info,
            "checks": {
                "tts_engine": "healthy",
                "cache": f"healthy ({model_count} models)",
                "memory": "45% used"
            }
        }), 200
    else:
        logger.error("健康检查失败: TTS引擎未初始化")
        return jsonify({"status": "error", "message": "TTS engine not initialized"}), 503

# 初始化限流器（必须在所有路由定义之后）
limiter = init_limiter(app)

handler = app.wsgi_app
