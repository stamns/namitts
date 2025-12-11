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
