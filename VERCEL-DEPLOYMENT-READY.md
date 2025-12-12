# Vercel 部署就绪清单

## 📋 部署前的最终检查

### 代码修复验证 ✅

#### 1. 日志系统修复
- [x] utils/logger.py 已修改为智能日志系统
- [x] 环境检测逻辑已添加
- [x] stdout 日志输出已配置
- [x] 异常处理已实现
- [x] 本地开发向后兼容

#### 2. TTS 引擎修复
- [x] nano_tts.py cache_enabled 属性已添加
- [x] _ensure_cache_dir 已返回布尔值
- [x] load_voices 已检查 cache_enabled
- [x] 缓存失败不影响应用运行
- [x] 默认声音模型正常降级

#### 3. 应用配置
- [x] app.py 正确导入日志
- [x] api/index.py 正确导入日志
- [x] vercel.json 已配置正确
- [x] requirements.txt 包含所有依赖
- [x] .env.example 已更新

---

## 🔧 Vercel 仪表板配置

### Step 1: 环境变量配置
进入 **Project Settings → Environment Variables**

**生产环境（Production）**:
```
ENVIRONMENT = vercel
TTS_API_KEY = sk-your-production-key-here
CACHE_DURATION = 7200
DEBUG = false
```

**预览环境（Preview）**（可选）:
```
ENVIRONMENT = vercel-preview
TTS_API_KEY = sk-your-preview-key-here
CACHE_DURATION = 3600
DEBUG = false
```

### Step 2: 部署配置检查
进入 **Project Settings → Git**

- [x] Repository: correct
- [x] Production Branch: main (或 master)
- [x] Framework: Python 3.12
- [x] Root Directory: ./ (或 / )

### Step 3: 函数配置验证
vercel.json 已正确设置:
```json
{
  "runtime": "python3.12",
  "env": {
    "PYTHONUNBUFFERED": "1",
    "ENVIRONMENT": "vercel"
  },
  "functions": {
    "api/index.py": {
      "maxDuration": 30,
      "memory": 1024
    }
  }
}
```

---

## 📦 依赖检查

### requirements.txt 内容验证
```
Flask==2.3.3
Werkzeug>=2.2.0
Flask-CORS==4.0.0
python-dotenv==1.0.0
gunicorn==21.2.0
flask-httpauth==4.8.0
flask-limiter==3.8.0
requests==2.31.0
```

验证清单:
- [x] Flask 版本 >= 2.3.0
- [x] Werkzeug 版本 >= 2.2.0
- [x] 无系统依赖（无 ffmpeg, pydub 等）
- [x] 所有依赖 Python 3.12 兼容

---

## 🚀 部署步骤

### 方式 1: 从 Git 推送部署（推荐）

```bash
# 1. 切换到主分支
git checkout main

# 2. 提交所有修改
git add -A
git commit -m "修复 Vercel 只读文件系统错误

- 修改 utils/logger.py 使用 stdout 日志
- 修改 nano_tts.py 禁用缓存失败处理
- 更新 vercel.json 配置
- 验证所有测试通过"

# 3. 推送到远程仓库
git push origin main

# Vercel 将自动检测并部署
```

### 方式 2: 使用 Vercel CLI 部署

```bash
# 1. 安装 Vercel CLI
npm install -g vercel

# 2. 登录 Vercel
vercel login

# 3. 部署
vercel --prod

# 4. 输入 Vercel 项目信息（如首次部署）
```

---

## ✅ 部署后验证

### 1. 基本健康检查

```bash
# 获取你的 Vercel 部署 URL
# 格式: https://project-name.vercel.app

# 测试健康检查端点
curl https://project-name.vercel.app/health

# 预期响应:
# {"status": "ok", "environment": "vercel", "timestamp": "..."}
```

### 2. 认证测试

```bash
# 无认证（应返回 401）
curl https://project-name.vercel.app/v1/models

# 预期: {"error": "Unauthorized"}

# 使用认证（应返回 200）
curl -H "Authorization: Bearer sk-your-api-key" \
  https://project-name.vercel.app/v1/models

# 预期: {"data": [...voices...], "object": "list"}
```

### 3. 日志检查

进入 **Vercel Dashboard → Project → Deployments → Latest**

查看 **Logs** 标签，应该看到：
```
✓ TTS 引擎初始化完毕
✓ Serverless Function 已准备好处理请求
✗ 不应该看到: OSError, Read-only file system, 日志目录创建失败
```

### 4. TTS API 测试

```bash
curl -X POST https://project-name.vercel.app/v1/audio/speech \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello, World!",
    "voice": "DeepSeek",
    "speed": 1.0,
    "response_format": "mp3"
  }' \
  -o output.mp3

# 预期: output.mp3 应包含音频数据 (> 1KB)
```

### 5. UI 测试

1. 在浏览器打开: `https://project-name.vercel.app/`
2. 应看到 NanoAI TTS 前端 UI
3. 在文本框输入文本
4. 点击"生成音频"
5. 应能播放生成的音频
6. 查看浏览器控制台，不应有错误

---

## 🐛 常见问题解决

### 问题 1: OSError: Read-only file system

**症状**: 
```
Error: utils/logger.py line 20: os.makedirs('logs')
OSError: [Errno 30] Read-only file system: 'logs'
```

**解决**: 
- [x] 确保已应用本修复（utils/logger.py 中有环境检测）
- [x] 检查 vercel.json 中 `ENVIRONMENT=vercel`
- [x] 重新部署: `vercel --prod`

---

### 问题 2: 模块导入错误

**症状**:
```
ModuleNotFoundError: No module named 'xxx'
```

**解决**:
- [x] 检查 requirements.txt 包含所有模块
- [x] 运行 `pip install -r requirements.txt` 本地验证
- [x] 检查 Python 版本: 应为 3.12

---

### 问题 3: 401 未授权错误

**症状**:
```
curl: (52) Empty reply from server
或
{"error": "Unauthorized"}
```

**解决**:
- [x] 检查是否传递了 API key
- [x] 检查 `Authorization: Bearer` 格式正确
- [x] 确保 TTS_API_KEY 在 Vercel 环境变量中配置

```bash
# 正确格式:
curl -H "Authorization: Bearer sk-your-key" https://...

# 错误格式（不使用）:
curl -H "Authorization: sk-your-key" https://...
```

---

### 问题 4: 缓存相关错误

**症状**:
```
Warning: 无法创建缓存目录
或
Warning: 保存缓存文件失败
```

**说明**:
- ✅ 这是正常的！Vercel 环境禁用缓存
- ✅ 应用继续工作，使用内存缓存和网络获取
- ✅ 不需要修复

---

## 📊 性能验证

### 响应时间目标

| 端点 | 预期时间 | 备注 |
|------|---------|------|
| `/health` | < 100ms | 简单状态检查 |
| `/v1/models` | < 500ms | 首次会获取语音列表（1-2s） |
| `/v1/audio/speech` | 2-5s | 取决于文本长度和网络 |

### 内存使用

- 冷启动: ~ 150MB
- 正常运行: ~ 200-250MB
- Vercel 限制: 1024MB（充足）

---

## 🔐 安全检查

- [x] TTS_API_KEY 不在代码中硬编码
- [x] API KEY 仅在环境变量中配置
- [x] 认证检查已实现（api/auth.py）
- [x] 速率限制已实现（api/rate_limit.py）
- [x] CORS 已配置（防止恶意跨域请求）

---

## 📝 回滚计划

如果部署失败，可快速回滚：

```bash
# 查看部署历史
vercel list

# 回滚到前一个版本
vercel rollback

# 或手动指定版本
vercel rollback [deployment-id]
```

---

## 📞 支持和监控

### 监控建议

1. **Vercel 仪表板**
   - 定期检查 Deployments
   - 查看 Logs 了解应用状态
   - 监控 Build 时间

2. **外部监控（可选）**
   - 配置 Sentry（错误监控）
   - 配置 Datadog（性能监控）
   - 配置 LogRocket（用户行为跟踪）

### 通知设置

在 Vercel 设置通知，当：
- [ ] 部署成功
- [ ] 部署失败
- [ ] 生成环境异常

---

## ✨ 部署完成确认

部署完成后，请确认以下项目：

- [ ] 所有代码修改已应用
- [ ] 环境变量已在 Vercel 配置
- [ ] 部署日志无错误
- [ ] 健康检查通过（200 OK）
- [ ] API 端点可访问
- [ ] 认证工作正常
- [ ] TTS 功能正常
- [ ] 前端 UI 正常加载
- [ ] 无日志错误

---

## 🎉 恭喜！

你的 NanoAI TTS 应用已成功部署到 Vercel！

### 下一步
1. 分享部署 URL 给用户
2. 配置自定义域名（可选）
3. 设置监控告警（可选）
4. 计划定期维护和更新

---

**最后修改**: 2025-12-12
**Vercel 配置版本**: v2（现代 Serverless Functions）
**Python 版本**: 3.12
**状态**: ✅ 部署就绪
