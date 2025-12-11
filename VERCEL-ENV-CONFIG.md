# Vercel 环境变量配置指南

## 问题修复说明

### 修复前的错误
Vercel 构建失败，错误信息：
```
The `vercel.json` schema validation failed with the following message: 
should NOT have additional property `envs`
```

### 根本原因
`vercel.json` 文件中使用了无效的 `envs` 属性。Vercel 官方 schema 不支持此属性。

### 修复方案
从 `vercel.json` 中删除了无效的 `envs` 属性块。

---

## 如何正确配置环境变量

### 方法 1: 在 vercel.json 中配置（适合非敏感数据）

可以在 `env` 属性中设置所有环境中都需要的环境变量：

```json
{
  "version": 2,
  "name": "nanoai-tts",
  "env": {
    "PYTHONUNBUFFERED": "1",
    "ENVIRONMENT": "vercel",
    "CACHE_DURATION": "7200",
    "LOG_LEVEL": "INFO"
  }
}
```

### 方法 2: 在 Vercel 仪表板配置（推荐，适合敏感数据）

**强烈推荐此方法**，特别是对于 API 密钥等敏感信息。

#### 步骤：

1. **登录 Vercel 仪表板**: https://vercel.com/dashboard
2. **选择项目**: 选择 "nanoai-tts" 项目
3. **进入设置**: 点击 "Settings" 标签
4. **环境变量**: 在左侧菜单选择 "Environment Variables"
5. **添加变量**:
   - **Name**: `TTS_API_KEY`
   - **Value**: 你的实际 API 密钥
   - **Environments**: 选择环境（Production, Preview, Development）
   - **点击 "Save"**

#### 需要配置的环境变量：

| 变量名 | 说明 | 示例值 | 必填 |
|--------|------|--------|------|
| `TTS_API_KEY` | TTS 服务 API 密钥 | `sk-nanoai-xxx` | ✅ |
| `CACHE_DURATION` | 模型缓存时长（秒） | `7200` | ❌ |
| `LOG_LEVEL` | 日志级别 | `INFO` | ❌ |
| `DEBUG` | 调试模式 | `False` | ❌ |

### 方法 3: 使用 .env 文件（仅用于本地开发）

创建 `.env` 文件在项目根目录（参考 `.env.example`），但**不要提交**到版本控制系统。

```bash
# 复制示例文件
cp .env.example .env

# 编辑 .env，填入实际的值
nano .env
```

---

## 当前 vercel.json 配置

```json
{
  "version": 2,
  "name": "nanoai-tts",
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python@3.0.0",
      "config": {
        "maxLambdaSize": "50mb",
        "runtime": "python3.11"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ],
  "env": {
    "PYTHONUNBUFFERED": "1",
    "ENVIRONMENT": "vercel"
  }
}
```

### 配置说明：

- **version**: Vercel 配置版本（必须为 2）
- **name**: 项目名称
- **builds**: 构建配置
  - **src**: 入口文件
  - **use**: 使用的 Python 构建器
  - **config.maxLambdaSize**: Lambda 函数最大大小（50MB 充足）
  - **config.runtime**: Python 运行时版本（3.11）
- **routes**: 路由配置，将所有请求转发到 app.py
- **env**: 全局环境变量
  - `PYTHONUNBUFFERED=1`: 启用无缓冲的 Python 输出（更快的日志）
  - `ENVIRONMENT=vercel`: 标记部署环境

---

## 环境变量优先级

应用会按以下顺序查找环境变量：

1. **系统环境变量** （如果存在）
2. **.env 文件** （仅本地开发，Vercel 部署时不使用）
3. **vercel.json 的 env** （仅在 Vercel 上）
4. **Vercel 仪表板配置** （仅在 Vercel 上，优先级最高）
5. **默认值** （如果以上都不存在）

---

## 部署检查清单

- [x] 从 vercel.json 删除无效的 `envs` 属性
- [x] 验证 vercel.json 符合官方 schema
- [ ] 在 Vercel 仪表板中配置 `TTS_API_KEY`
- [ ] 测试 Vercel 部署
- [ ] 验证 `/health` 端点返回 200
- [ ] 验证 `/v1/models` 端点正常工作

---

## Vercel 官方 Schema 参考

更多信息参见：https://vercel.com/docs/projects/project-configuration

有效的顶级属性（仅列出常用的）：
- `version` ✅
- `name` ✅
- `builds` ✅
- `routes` ✅
- `env` ✅ （使用此属性）
- `envs` ❌ （无效，已删除）
- `regions` ✅
- `functions` ✅
- `outputDirectory` ✅

---

## 故障排查

### 构建仍然失败
1. 清除 Vercel 缓存：
   ```bash
   vercel deploy --prod --force
   ```
2. 检查构建日志中是否有其他错误

### 应用启动时缺少环境变量
1. 确认已在 Vercel 仪表板中配置所有需要的变量
2. 重新部署应用
3. 检查应用日志

### 仍有疑问
参考 VERCEL-FIX.md 中的更多技术细节。
