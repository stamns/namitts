1. 本地部署文档
# 本地部署指南
## 环境要求
- Python 3.8+
- pip 包管理器
- ffmpeg（音频处理）
## 快速开始
### 1. 克隆项目
```bash
git clone https://github.com/yourusername/nanoai-tts.git
cd nanoai-tts
2. 安装依赖
pip install -r requirements.txt
3. 配置环境变量
复制 .env.example 为 .env 并配置：
cp .env.example .env
# 编辑 .env 文件，设置 TTS_API_KEY


4. 启动服务
python app.py
5. 访问服务
打开浏览器访问：http://localhost:5001

系统依赖安装
Windows
下载 ffmpeg
添加到系统环境变量 PATH
macOS
brew install ffmpeg
Linux (Ubuntu/Debian)
sudo apt update
sudo apt install ffmpeg



常见问题
Q: 端口被占用
A: 修改 .env 文件中的 PORT 配置

Q: 依赖安装失败
A: 尝试升级 pip: pip install --upgrade pip

### 2. Cloudflare部署文档
```markdown
# Cloudflare Workers 部署指南
## 前置条件
- Cloudflare 账户
- Node.js 和 npm
- Wrangler CLI
## 安装 Wrangler
```bash
npm install -g wrangler
登录 Cloudflare
wrangler login
配置环境变量
在 .env 文件中添加：
CF_ACCOUNT_ID=your_account_id
CF_ZONE_ID=your_zone_id
CF_PROJECT_NAME=nanoai-tts-prod



部署
# 使用部署脚本
./deploy.sh cloudflare prod
# 或手动部署
wrangler deploy


验证部署
访问 Cloudflare 提供的 .workers.dev 域名

自定义域名
在 Cloudflare 控制台添加自定义域名
配置 DNS 记录
在 Workers 设置中绑定域名
### 3. Vercel部署文档
```markdown
# Vercel 部署指南
## 前置条件
- Vercel 账户
- Node.js 和 npm
- Vercel CLI
## 安装 Vercel CLI
```bash
npm install -g vercel
登录 Vercel
vercel login
配置环境变量
在 .env 文件中添加：

VERCEL_PROJECT_NAME=nanoai-tts
部署
# 使用部署脚本
./deploy.sh vercel prod
# 或手动部署
vercel --prod


环境变量配置
在 Vercel 控制台的项目设置中添加环境变量：

TTS_API_KEY
CACHE_DURATION
验证部署
访问 Vercel 提供的 .vercel.app 域名

### 4. Docker部署文档
```markdown
# Docker 部署指南
## 构建镜像
```bash
docker build -t nanoai-tts .
运行容器
# 使用部署脚本
./deploy.sh vercel prod
# 或手动部署
vercel --prod


环境变量
通过 -e 参数设置环境变量：
docker run -p 5001:5001 \
  -e TTS_API_KEY=your_key \
  -e DEBUG=False \
  nanoai-tts


数据持久化
# 挂载日志目录
docker run -p 5001:5001 \
  -v $(pwd)/logs:/app/logs \
  nanoai-tts



健康检查
curl http://localhost:5001/health
### 5. API使用文档
```markdown
# API 使用文档
## 认证
所有 API 请求都需要在请求头中包含 API 密钥：
Authorization: Bearer YOUR_API_KEY

## 接口列表
### 1. 生成语音
**POST** `/v1/audio/speech`
#### 请求参数
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| text | string | 是 | 待合成文本 |
| model | string | 是 | 声音模型ID |
| speed | float | 否 | 语速（0.5-2.0） |
| emotion | string | 否 | 情绪（neutral/happy/sad/angry） |
#### 示例
```bash
curl -X POST "https://your-domain.com/v1/audio/speech" \
  -H "Authorization: Bearer sk-xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好世界",
    "model": "DeepSeek",
    "speed": 1.2,
    "emotion": "happy"
  }' \
  --output hello.mp3
2. 批量生成
POST /v1/audio/speech/batch

请求参数
参数	类型	必需	说明
texts	array	是	文本数组（最多10条）
model	string	是	声音模型ID
params	object	否	音频参数
示例
curl -X POST "https://your-domain.com/v1/audio/speech/batch" \
  -H "Authorization: Bearer sk-xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["文本1", "文本2"],
    "model": "DeepSeek"
  }'



3. 获取模型列表
GET /v1/models

示例
curl -X GET "https://your-domain.com/v1/models" \
  -H "Authorization: Bearer sk-xxx"



4. 健康检查
GET /health

示例
curl https://your-domain.com/health
错误码
状态码	说明
200	成功
400	请求参数错误
401	认证失败
404	模型不存在
429	请求频率超限
500	服务器内部错误
503	服务不可用
## 🎯 项目特点总结
### ✅ 已实现功能
1. **无限制文本长度**：智能分段处理，支持任意长度文本
2. **音频参数控制**：语速、情绪等参数实时调整
3. **多平台部署**：支持Cloudflare、Vercel、Docker等
4. **完整API体系**：认证、限流、批量处理等企业级功能
5. **用户体验优化**：进度显示、历史记录、响应式界面
6. **生产就绪**：日志监控、健康检查、容器化部署
### 🚀 部署方式
- **本地部署**：适合开发和测试
- **Cloudflare Workers**：全球CDN，免费额度
- **Vercel**：自动扩缩，开发者友好
- **Docker**：生产环境，易于管理
### 📈 扩展性
- 模块化设计，易于添加新功能
- 支持多种TTS引擎插件
- 可集成到现有系统
