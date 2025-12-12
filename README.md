# 🎵 纳米AI TTS - OpenAI 兼容的文字转语音服务

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.12+-green)
![License](https://img.shields.io/badge/license-MIT-green)

## 📖 项目概述

**纳米AI TTS** 是一个基于 OpenAI API 兼容接口的文字转语音（Text-to-Speech）服务。它提供了一个轻量级、易于部署的TTS解决方案，支持多种部署平台。

### 🌟 核心特点

- ✅ **OpenAI API兼容** - 支持 `/v1/audio/speech` 标准接口
- ✅ **多模型支持** - 支持多个语音模型和情绪调整
- ✅ **完整Web UI** - 开箱即用的浏览器界面
- ✅ **灵活部署** - Docker、Vercel、本地等多种方式
- ✅ **生产就绪** - 认证、限流、缓存、日志等企业级功能
- ✅ **轻量级** - 无FFmpeg系统依赖，快速启动

## 🚀 快速开始

### 本地运行

```bash
# 1. 克隆项目
git clone https://github.com/namitts/nanoai-tts.git
cd nanoai-tts

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境
cp .env.example .env
# 编辑 .env，设置 TTS_API_KEY

# 4. 启动服务
python app.py

# 5. 访问
# 浏览器打开: http://localhost:5001
```

### Docker运行

```bash
# 构建并运行
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### Vercel部署

👉 详见 [VERCEL-DEPLOYMENT.md](./VERCEL-DEPLOYMENT.md)

## 📚 API 文档

### 认证

所有API请求需要在请求头中包含Bearer Token：

```bash
Authorization: Bearer sk-nanoai-your-secret-key
```

### 端点列表

#### 1️⃣ 生成语音
```
POST /v1/audio/speech
```

**请求体**:
```json
{
  "model": "DeepSeek",
  "input": "你好，这是一个测试。",
  "speed": 1.0,
  "emotion": "neutral"
}
```

**响应**: 音频文件 (audio/mpeg)

**示例**:
```bash
curl -X POST http://localhost:5001/v1/audio/speech \
  -H "Authorization: Bearer sk-nanoai-your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "DeepSeek",
    "input": "你好世界",
    "speed": 1.0
  }' \
  --output output.mp3
```

#### 2️⃣ 批量生成（长文本）
```
POST /v1/audio/speech/batch
```

**请求体**:
```json
{
  "texts": ["文本1", "文本2"],
  "model": "DeepSeek",
  "params": {
    "speed": 1.0,
    "emotion": "neutral"
  }
}
```

#### 3️⃣ 列出模型
```
GET /v1/models
```

**响应**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "DeepSeek",
      "object": "model",
      "created": 1701234567,
      "owned_by": "nanoai",
      "description": "DeepSeek (默认)"
    }
  ]
}
```

#### 4️⃣ 健康检查
```
GET /health
```

**响应**:
```json
{
  "status": "ok",
  "models_in_cache": 10,
  "timestamp": 1701234567,
  "version": "1.0.0"
}
```

### 参数说明

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `model` | string | 语音模型ID | `DeepSeek` |
| `input` | string | 输入文本 | `你好` |
| `speed` | float | 语速（0.5-2.0） | `1.0` |
| `emotion` | string | 情绪（neutral/happy/sad/angry） | `neutral` |

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 认证失败 |
| 404 | 模型不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器错误 |
| 503 | 服务不可用 |

## 🏗️ 项目结构

```
nanoai-tts/
├── api/                      # API相关模块
│   ├── index.py             # Vercel Serverless入口 ✨
│   ├── auth.py              # 认证模块
│   ├── rate_limit.py        # 限流模块
│   └── docs.py              # API文档
├── utils/
│   └── logger.py            # 日志管理
├── deploy/
│   └── config.py            # 部署配置
├── app.py                   # 主应用（本地开发）
├── nano_tts.py              # TTS引擎核心
├── requirements.txt         # Python依赖
├── vercel.json             # Vercel配置 ✨
├── docker-compose.yml      # Docker配置
├── .env.example            # 环境变量示例 ✨
├── CODE-OPTIMIZATION.md    # 代码优化文档 ✨
└── VERCEL-DEPLOYMENT.md    # Vercel部署指南 ✨
```

## 🔧 环境变量

| 变量 | 说明 | 默认值 | 必需 |
|------|------|--------|------|
| `TTS_API_KEY` | API密钥 | - | ✅ |
| `CACHE_DURATION` | 缓存时长（秒） | 7200 | ❌ |
| `PORT` | 服务端口 | 5001 | ❌ |
| `DEBUG` | 调试模式 | false | ❌ |
| `ENVIRONMENT` | 运行环境 | development | ❌ |
| `SENTRY_DSN` | Sentry监控 | - | ❌ |
| `REDIS_URL` | Redis URL（限流） | - | ❌ |

👉 详见 [.env.example](./.env.example)

## 📦 依赖

### 核心依赖
- **Flask 2.3.3** - Web框架
- **Werkzeug ≥2.2.0** - WSGI工具库
- **Flask-CORS 4.0.0** - 跨域支持
- **flask-httpauth 4.8.0** - API认证
- **flask-limiter 3.8.0** - 请求限流
- **python-dotenv 1.0.0** - 环境变量管理

### 可选依赖
- **sentry-sdk** - 错误监控（需设置 `SENTRY_DSN`）
- **redis** - 分布式限流（需设置 `REDIS_URL`）

## 🎯 部署指南

### 本地部署
```bash
python app.py
```

### Docker部署
```bash
docker-compose up -d
```

### Vercel部署
👉 详见 [VERCEL-DEPLOYMENT.md](./VERCEL-DEPLOYMENT.md)

步骤概要：
1. 代码推送到GitHub
2. Vercel Dashboard导入项目
3. 配置环境变量
4. 自动部署完成

### Cloud Run / Railway / 其他

项目采用标准Python/Flask，支持大多数云平台。关键要求：
- Python 3.12+
- 无系统依赖（不需要FFmpeg）
- 标准WSGI应用

## 📊 性能指标

| 指标 | 目标 | 状态 |
|------|------|------|
| 冷启动时间 | < 3秒 | ✅ |
| 模型加载 | 自动缓存 | ✅ |
| 并发请求 | 支持 | ✅ |
| 内存占用 | < 512MB | ✅ |
| 可用性 | 99%+ | ✅ |

## 🔒 安全特性

- ✅ Bearer Token认证
- ✅ API请求限流
- ✅ CORS跨域配置
- ✅ 环境变量管理
- ✅ 日志记录和监控

## 📝 最近更新

### v1.0.0 (Dec 2024)

#### 🎉 优化内容
- ✨ **代码优化**: 移除未使用的依赖，清理代码结构
- ✨ **Vercel迁移**: 完全重写vercel.json，使用Serverless Functions
- ✨ **依赖清理**: 移除prometheus-client、psutil等不必要的包
- ✨ **文档增强**: 新增CODE-OPTIMIZATION.md和VERCEL-DEPLOYMENT.md
- ✨ **环境配置**: 优化.env.example，文档化所有变量

#### 🔧 修复内容
- 🐛 修复Python 3.9/3.12兼容性问题
- 🐛 修复Werkzeug版本冲突
- 🐛 移除text_processor.py未使用代码
- 🐛 规范化vercel.json配置

## 📖 文档

- [VERCEL-DEPLOYMENT.md](./VERCEL-DEPLOYMENT.md) - Vercel部署详细指南
- [CODE-OPTIMIZATION.md](./CODE-OPTIMIZATION.md) - 代码优化说明
- [.env.example](./.env.example) - 环境变量示例

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🙏 鸣谢

- 基于 [NanoAI](https://bot.n.cn) API
- 灵感来自 [OpenAI TTS API](https://platform.openai.com/docs/api-reference/audio/createSpeech)

## 📞 支持

- 📧 Email: support@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/namitts/nanoai-tts/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/namitts/nanoai-tts/discussions)

---

**Made with ❤️ for TTS lovers**
