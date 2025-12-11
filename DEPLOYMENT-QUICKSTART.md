# NanoAI TTS 部署快速开始指南

> 🚀 5-10 分钟快速部署 NanoAI TTS 服务

---

## 📋 前置要求

### 本地开发
- Python 3.8+
- FFmpeg
- Git

### Docker 部署
- Docker 20.10+
- Docker Compose 1.29+

### 云平台部署
- 云服务商账号（Google Cloud / Railway / DigitalOcean 等）
- 信用卡（部分平台需要）

---

## ⚡ 最快部署方式

### 选项 1: Railway（推荐，最简单）

```bash
# 1. Fork 项目到你的 GitHub
# 2. 访问 https://railway.app/
# 3. 点击 "New Project" → "Deploy from GitHub repo"
# 4. 选择你的 namitts 仓库
# 5. 添加环境变量：
#    - TTS_API_KEY=your_key_here
# 6. 点击 Deploy
# ✅ 完成！Railway 会自动部署并提供一个 URL
```

**预计时间：** 5 分钟  
**成本：** $5/月起

---

### 选项 2: Docker Compose（本地/VPS）

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/namitts.git
cd namitts

# 2. 配置环境变量
cp .env.example .env
nano .env  # 编辑 TTS_API_KEY

# 3. 启动服务
docker-compose up -d

# 4. 检查状态
curl http://localhost:5001/health

# ✅ 完成！访问 http://localhost:5001
```

**预计时间：** 10 分钟  
**成本：** VPS $5-20/月

---

### 选项 3: Google Cloud Run

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/namitts.git
cd namitts

# 2. 登录 GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 3. 构建并部署
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/nanoai-tts
gcloud run deploy nanoai-tts \
  --image gcr.io/YOUR_PROJECT_ID/nanoai-tts \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars TTS_API_KEY=your_key

# ✅ 完成！GCP 会返回服务 URL
```

**预计时间：** 15 分钟  
**成本：** 按需付费，前 200 万请求免费

---

## 🔧 详细配置

### 必填环境变量

```bash
TTS_API_KEY=sk-nanoai-your-secret-key-here  # 必须
```

### 可选环境变量

```bash
PORT=5001                    # 服务端口
DEBUG=False                  # 调试模式
CACHE_DURATION=7200          # 缓存时长（秒）
REDIS_URL=redis://...        # Redis 地址（可选）
SENTRY_DSN=https://...       # Sentry 监控（可选）
```

---

## ✅ 验证部署

```bash
# 1. 健康检查
curl http://your-domain.com/health

# 预期输出：
# {"status":"ok","models_in_cache":XX,"timestamp":...}

# 2. 获取模型列表
curl http://your-domain.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"

# 3. 测试语音合成
curl -X POST http://your-domain.com/v1/audio/speech \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "DeepSeek", "input": "你好世界"}' \
  --output test.mp3

# 4. 播放测试
ffplay test.mp3  # 或使用其他播放器
```

---

## 🚨 常见问题

### Q1: Docker 构建失败
```bash
# 清理缓存重新构建
docker-compose down
docker system prune -a
docker-compose build --no-cache
docker-compose up -d
```

### Q2: Redis 连接失败
```bash
# 检查 Redis 是否运行
docker-compose ps

# 查看日志
docker-compose logs redis

# 临时禁用 Redis（使用内存存储）
# 在 .env 中注释掉 REDIS_URL
```

### Q3: API 返回 401 Unauthorized
```bash
# 检查 API 密钥是否正确设置
echo $TTS_API_KEY

# 确保请求头格式正确
# Authorization: Bearer sk-xxx
```

### Q4: FFmpeg not found
```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Docker: 已包含在镜像中
```

---

## 📊 性能优化

### 推荐配置

| 并发请求 | CPU | 内存 | Workers |
|---------|-----|------|---------|
| < 10    | 1   | 512MB | 2 |
| 10-50   | 2   | 1GB   | 4 |
| 50-100  | 4   | 2GB   | 8 |
| > 100   | 8+  | 4GB+  | 16+ |

### Gunicorn 调优

```bash
# .env 或 docker-compose.yml
GUNICORN_WORKERS=4        # CPU 核心数 * 2 + 1
GUNICORN_THREADS=8        # 每个 worker 的线程数
GUNICORN_TIMEOUT=120      # 请求超时（秒）
```

---

## 🔒 安全建议

1. **更改默认 API 密钥**
   ```bash
   # 生成强密钥
   openssl rand -base64 32
   ```

2. **启用 HTTPS**
   - 使用 Cloudflare、nginx 或平台自带 SSL

3. **限制速率**
   - 已内置 Flask-Limiter
   - 建议配置 Redis 用于分布式限流

4. **设置防火墙**
   ```bash
   # 仅允许 HTTP/HTTPS
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw enable
   ```

---

## 📈 监控和日志

### 查看日志

```bash
# Docker Compose
docker-compose logs -f nanoai-tts

# Kubernetes
kubectl logs -f deployment/nanoai-tts

# 本地文件
tail -f logs/nanoai_tts.log
```

### 健康检查

```bash
# 设置监控脚本（cron）
*/5 * * * * curl -f http://localhost:5001/health || systemctl restart nanoai-tts
```

### Sentry 集成（可选）

```bash
# 在 .env 中添加
SENTRY_DSN=https://xxx@sentry.io/xxx
```

---

## 🔄 更新部署

### Docker Compose

```bash
# 拉取最新代码
git pull origin main

# 重新构建并重启
docker-compose down
docker-compose build
docker-compose up -d
```

### Cloud Run

```bash
# 重新部署
gcloud builds submit --tag gcr.io/PROJECT/nanoai-tts
gcloud run deploy nanoai-tts --image gcr.io/PROJECT/nanoai-tts
```

### Railway

```bash
# 推送到 GitHub，Railway 自动部署
git push origin main
```

---

## 📞 获取帮助

- **完整文档**: [DEPLOYMENT-ANALYSIS.md](./DEPLOYMENT-ANALYSIS.md)
- **API 文档**: [README.md](./README.md)
- **问题反馈**: GitHub Issues

---

**🎉 恭喜！你的 NanoAI TTS 服务已成功部署！**
