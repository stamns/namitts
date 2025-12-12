# Vercel 环境变量配置指南

## ⚠️ 重要提示

在 Vercel 部署之前，**必须**在 Vercel 仪表板中配置环境变量。否则部署会失败。

---

## 必需的环境变量

### 1. TTS_API_KEY（必需）

**说明**: API 认证密钥，用于保护 API 端点  
**格式**: 字符串，多个密钥用逗号分隔（无空格）  
**示例**:
- 单个密钥: `sk-nanoai-production-key-12345`
- 多个密钥: `sk-key1,sk-key2,sk-key3`

**Vercel 配置步骤**:
1. 进入 Vercel 项目仪表板
2. 点击 "Settings" → "Environment Variables"
3. 添加变量:
   - **Key**: `TTS_API_KEY`
   - **Value**: `sk-your-secret-key-here`
   - **Environment**: 选择 "Production", "Preview", "Development"（根据需要）
4. 点击 "Save"

---

## 可选的环境变量

以下环境变量已在 `vercel.json` 中配置默认值，通常不需要在 Vercel 仪表板中额外配置。  
如果需要自定义，可以在 Vercel 仪表板中覆盖这些值。

### 2. PYTHONUNBUFFERED

**说明**: Python 输出缓冲控制  
**默认值**: `"1"`（已在 vercel.json 配置）  
**建议**: 保持默认值

### 3. ENVIRONMENT

**说明**: 部署环境标识  
**默认值**: `"vercel"`（已在 vercel.json 配置）  
**建议**: 保持默认值

### 4. CACHE_DURATION

**说明**: 模型缓存时长（秒）  
**默认值**: `"7200"`（2小时，已在 vercel.json 配置）  
**自定义**: 如果需要更长或更短的缓存时间，可以在 Vercel 仪表板中覆盖

### 5. DEBUG

**说明**: 调试模式开关  
**默认值**: `"false"`（已在 vercel.json 配置）  
**建议**: 生产环境保持 `false`，调试时可设置为 `true`

### 6. REDIS_URL（可选）

**说明**: Redis 连接 URL（用于分布式限流）  
**默认值**: `"memory://"`（使用内存存储）  
**格式**: `redis://username:password@host:port`  
**示例**: `redis://:password123@redis.example.com:6379`

**注意**: 如果不配置，系统会使用内存存储进行限流（每次重启会清空限流计数器）

### 7. SENTRY_DSN（可选）

**说明**: Sentry 错误监控 DSN  
**默认值**: 未设置  
**格式**: `https://xxxx@o123456.ingest.sentry.io/7890123`  
**用途**: 生产环境错误监控和追踪

---

## 完整配置示例

### 最小配置（仅必需项）

在 Vercel 仪表板配置：

```
TTS_API_KEY=sk-nanoai-production-key-abc123
```

### 推荐配置（生产环境）

在 Vercel 仪表板配置：

```
TTS_API_KEY=sk-nanoai-production-key-abc123
CACHE_DURATION=3600
DEBUG=false
REDIS_URL=redis://:password@your-redis.com:6379
SENTRY_DSN=https://xxxx@sentry.io/123456
```

### 开发/测试配置

在 Vercel 仪表板配置：

```
TTS_API_KEY=sk-nanoai-dev-key-test123
DEBUG=true
CACHE_DURATION=300
```

---

## 配置验证

部署完成后，访问以下端点验证配置：

### 1. 健康检查（无需认证）

```bash
curl https://your-app.vercel.app/health
```

**预期响应**:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "models_in_cache": 1,
  "timestamp": 1765550745,
  "checks": {
    "tts_engine": "healthy",
    "cache": "healthy (1 models)",
    "memory": "45% used"
  }
}
```

### 2. 模型列表（需要认证）

```bash
curl https://your-app.vercel.app/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**预期响应**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "DeepSeek",
      "object": "model",
      "created": 1765550745,
      "owned_by": "nanoai",
      "description": "DeepSeek (默认)"
    }
  ]
}
```

### 3. 测试错误的 API 密钥

```bash
curl https://your-app.vercel.app/v1/models \
  -H "Authorization: Bearer wrong-key"
```

**预期响应** (HTTP 401):
```json
{
  "error": "Unauthorized",
  "message": "无效或缺失API密钥，请在请求头中添加: Authorization: Bearer YOUR_KEY"
}
```

---

## 常见问题

### Q1: 部署后访问 API 返回 401 Unauthorized

**原因**: `TTS_API_KEY` 未在 Vercel 仪表板配置  
**解决**: 按照上述步骤在 Vercel 仪表板添加 `TTS_API_KEY` 环境变量，然后重新部署

### Q2: 部署失败，提示 "Module initialization failed"

**原因**: 环境变量配置错误或缺失  
**解决**: 
1. 检查 Vercel 部署日志
2. 确认 `TTS_API_KEY` 已正确配置
3. 查看错误信息，确认是否有其他配置问题

### Q3: 如何支持多个 API 密钥？

**答案**: 在 `TTS_API_KEY` 中使用逗号分隔（无空格）

```
TTS_API_KEY=sk-key1,sk-key2,sk-key3
```

每个密钥都可以独立使用进行认证。

### Q4: 可以在不同环境使用不同的密钥吗？

**答案**: 可以。在 Vercel 仪表板配置环境变量时，为 Production、Preview、Development 分别设置不同的值：

- **Production**: `sk-prod-key`
- **Preview**: `sk-preview-key`
- **Development**: `sk-dev-key`

### Q5: 限流计数器重启后会清空吗？

**答案**: 
- **默认配置**: 是的，使用内存存储（`memory://`），重启后清空
- **推荐配置**: 配置 `REDIS_URL` 使用 Redis 存储，重启后保留限流计数器

---

## 安全最佳实践

### ✅ 推荐做法

1. **生产环境使用强密钥**: 
   ```
   sk-prod-$(openssl rand -hex 16)
   ```

2. **定期轮换密钥**: 
   - 支持多密钥配置
   - 添加新密钥后再移除旧密钥
   - 确保无缝过渡

3. **不同环境使用不同密钥**:
   - Production: 强密钥，严格保密
   - Preview: 测试密钥
   - Development: 开发密钥

4. **启用错误监控**:
   - 配置 `SENTRY_DSN`
   - 及时发现异常访问

5. **配置 Redis 限流**:
   - 使用外部 Redis 服务
   - 防止恶意请求

### ❌ 避免做法

1. ❌ 将密钥硬编码在代码中
2. ❌ 使用简单密钥（如 `123456`, `password`）
3. ❌ 在公开仓库中提交 `.env` 文件
4. ❌ 所有环境共用同一密钥
5. ❌ 不设置限流保护

---

## 相关文档

- [Vercel 环境变量官方文档](https://vercel.com/docs/projects/environment-variables)
- [Vercel Serverless Functions 文档](https://vercel.com/docs/functions/serverless-functions)
- [项目 README](./README.md)
- [Vercel 部署指南](./VERCEL-DEPLOYMENT.md)
- [深度调试报告](./VERCEL-DEBUG-REPORT.md)

---

**更新日期**: 2024-12-12  
**版本**: 1.0  
**适用于**: NanoAI TTS v1.0 Vercel 部署
