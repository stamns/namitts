# Vercel部署指南 (Vercel Deployment Guide)

## 目录
1. [前置条件](#前置条件)
2. [部署步骤](#部署步骤)
3. [环境变量配置](#环境变量配置)
4. [验证部署](#验证部署)
5. [常见问题](#常见问题)
6. [监控和维护](#监控和维护)

## 前置条件

### 必需
- [ ] GitHub账户（用于连接到Vercel）
- [ ] Vercel账户（可在https://vercel.com免费注册）
- [ ] 项目代码已推送到GitHub
- [ ] 有效的TTS_API_KEY

### 可选
- [ ] Sentry账户（用于错误监控）
- [ ] Redis实例（用于分布式限流）

## 部署步骤

### Step 1: 准备代码
```bash
# 确保在正确的分支上
git branch
git status

# 更新依赖
pip install -r requirements.txt

# 本地验证
python app.py
# 访问 http://localhost:5001

# 提交更改
git add .
git commit -m "Optimize code and fix Vercel deployment"
git push origin main
```

### Step 2: 在Vercel中导入项目

1. 访问 https://vercel.com/dashboard
2. 点击 "New Project" / "新建项目"
3. 选择 "Import Git Repository" / "导入Git仓库"
4. 搜索并选择你的GitHub仓库
5. 点击 "Import" / "导入"

### Step 3: 配置项目设置

在Vercel导入界面中：

#### 项目名称
- 设置为: `nanoai-tts`
- 或自定义名称

#### 框架检测
- 应该自动检测为 Python
- 如果未检测，手动选择 "Python"

#### 构建命令和输出目录
- **构建命令**: 留空（Vercel自动检测）
- **输出目录**: 留空
- **安装命令**: 留空（Vercel自动运行）

#### 根目录
- 选择 `.` （项目根目录）

### Step 4: 添加环境变量

在Vercel导项目设置中，进入 "Environment Variables" / "环境变量"：

#### 必需环境变量

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `TTS_API_KEY` | `sk-nanoai-your-secret-key` | TTS API密钥（Bearer Token） |
| `ENVIRONMENT` | `production` | 运行环境标识 |
| `CACHE_DURATION` | `7200` | 缓存时长（秒） |
| `DEBUG` | `false` | 禁用调试模式 |
| `PYTHONUNBUFFERED` | `1` | Python非缓冲输出 |

#### 可选环境变量

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `SENTRY_DSN` | `https://...@sentry.io/...` | Sentry错误监控DSN |
| `REDIS_URL` | `redis://...` | Redis连接URL（分布式限流） |
| `CACHE_DIR` | `cache` | 缓存目录 |

### Step 5: 部署

1. 确保所有环境变量已设置
2. 点击 "Deploy" / "部署"
3. 等待部署完成（通常1-2分钟）

## 部署后验证

### 查看部署日志

1. 在Vercel Dashboard中点击项目
2. 进入 "Deployments" / "部署历史"
3. 点击最新的部署
4. 查看 "Logs" / "日志" 标签

### 测试API端点

#### 1. 健康检查
```bash
curl https://your-project.vercel.app/health
```

应该返回:
```json
{
  "status": "ok",
  "models_in_cache": 10,
  "timestamp": 1701234567,
  "version": "1.0.0",
  "checks": {
    "tts_engine": "healthy",
    "cache": "healthy (10 models)",
    "memory": "45% used"
  }
}
```

#### 2. 列出模型
```bash
curl -H "Authorization: Bearer sk-nanoai-your-secret-key" \
     https://your-project.vercel.app/v1/models
```

应该返回模型列表:
```json
{
  "object": "list",
  "data": [
    {
      "id": "model_1",
      "object": "model",
      "created": 1701234567,
      "owned_by": "nanoai",
      "description": "Model Name"
    }
  ]
}
```

#### 3. 生成语音
```bash
curl -X POST https://your-project.vercel.app/v1/audio/speech \
     -H "Authorization: Bearer sk-nanoai-your-secret-key" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "model_id",
       "input": "你好，这是一个测试。",
       "speed": 1.0,
       "emotion": "neutral"
     }' \
     --output output.mp3
```

### 访问Web UI

在浏览器中打开: `https://your-project.vercel.app`

应该看到一个完整的Web界面，可以：
- 选择模型
- 输入文本
- 生成语音
- 下载音频
- 查看历史记录

## 常见问题

### Q1: 部署失败，提示 "Function invocation failed"
**原因**: 通常是由于未指定的系统依赖或配置错误

**解决方案**:
1. 检查 `requirements.txt` 是否缺少依赖
2. 查看Vercel日志了解具体错误
3. 确保 `vercel.json` 配置正确
4. 检查Python版本兼容性

### Q2: 环境变量未生效
**原因**: 环境变量未正确设置或需要重新部署

**解决方案**:
1. 在Vercel Dashboard中确认变量已设置
2. 重新部署项目: 
   ```bash
   git commit --allow-empty -m "Trigger redeploy"
   git push origin main
   ```
3. 检查日志中的环境变量值

### Q3: 模型列表为空
**原因**: bot.n.cn API可能无响应或被限制

**解决方案**:
1. 检查网络连接
2. 查看日志了解具体错误
3. 尝试重新启动应用
4. 验证robots.json缓存文件

### Q4: API返回 "Unauthorized"
**原因**: 未正确提供或验证了API密钥

**解决方案**:
1. 确保在请求头中包含: `Authorization: Bearer YOUR_API_KEY`
2. 验证 `TTS_API_KEY` 环境变量已正确设置
3. 检查密钥是否与配置匹配

### Q5: 内存或超时错误
**原因**: 函数超时或内存不足

**解决方案**:
1. 在 `vercel.json` 中增加 `maxDuration` (最大30秒)
2. 缩短超时前的文本长度
3. 使用batch API处理长文本
4. 检查bot.n.cn API响应时间

### Q6: 部署很慢或经常超时
**原因**: 可能是网络连接问题或Vercel负载过高

**解决方案**:
1. 重新部署
2. 考虑使用Vercel地区选项（在项目设置中）
3. 检查bot.n.cn服务器状态
4. 优化代码以减少初始化时间

## 监控和维护

### 查看实时日志
```bash
# 使用Vercel CLI查看实时日志
vercel logs https://your-project.vercel.app
```

### 设置告警（可选）

1. 进入项目设置
2. 找到 "Analytics" / "分析"
3. 配置错误率或延迟告警

### 监控部署

**重要指标**:
- ✅ 部署成功率
- ✅ 函数响应时间
- ✅ 错误率
- ✅ 并发请求数

### 定期更新依赖
```bash
# 检查过时的包
pip list --outdated

# 更新依赖
pip install --upgrade -r requirements.txt

# 更新requirements.txt
pip freeze > requirements.txt.new
# 手动审核后替换
mv requirements.txt.new requirements.txt

# 提交更改
git add requirements.txt
git commit -m "Update dependencies"
git push origin main
```

## 性能优化建议

### 1. 使用缓存
- 模型列表自动缓存2小时
- 考虑缓存频繁使用的文本

### 2. 优化文本长度
- 单个请求< 500字符时速度最快
- 长文本使用 `/v1/audio/speech/batch` 端点

### 3. 并发控制
- API限速: 10请求/分钟（全局）
- TTS端点: 30请求/分钟
- 模型列表: 60请求/分钟
- 可在 `api/rate_limit.py` 中调整

### 4. 错误处理
- 实现重试逻辑
- 使用指数退避
- 记录错误用于调试

## Vercel CLI命令参考

```bash
# 安装Vercel CLI
npm install -g vercel

# 登录
vercel login

# 本地开发
vercel dev

# 预览部署
vercel --prod --prebuilt

# 查看项目信息
vercel projects list

# 查看部署列表
vercel deployments list

# 查看实时日志
vercel logs <deployment-url>
```

## 清单 - 部署前检查

- [ ] 代码已提交到GitHub main分支
- [ ] `vercel.json` 已正确配置
- [ ] `requirements.txt` 包含所有依赖
- [ ] `.env.example` 已更新
- [ ] 所有环境变量已在Vercel Dashboard中设置
- [ ] 本地测试通过
- [ ] 部署日志无错误
- [ ] API端点能正常响应
- [ ] Web UI能正常加载
- [ ] 健康检查返回200状态码

## 滚回部署

如果新部署出现问题：

1. 进入Vercel Dashboard
2. 点击项目的 "Deployments" / "部署"
3. 找到之前的稳定部署
4. 点击 "Promote to Production" / "提升到生产环境"

## 支持和反馈

如遇到问题：
1. 查看Vercel官方文档: https://vercel.com/docs
2. 检查本项目的GitHub Issues
3. 查看应用日志获取更多信息
