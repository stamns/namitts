# api/auth.py - API认证模块
from flask_httpauth import HTTPTokenAuth
import os
from dotenv import load_dotenv
load_dotenv()
# 初始化认证器（使用Bearer Token）
auth = HTTPTokenAuth(scheme='Bearer')
# 从环境变量或数据库加载合法API密钥（支持多密钥）
VALID_API_KEYS = set(os.getenv("TTS_API_KEY", "sk-nanoai-default-key").split(","))  # 支持逗号分隔多密钥
@auth.verify_token
def verify_token(token):
    """验证API密钥"""
    if token in VALID_API_KEYS:
        return token  # 返回密钥用于后续权限控制
    return None  # 认证失败
@auth.error_handler
def unauthorized():
    """认证失败响应"""
    return {
        "error": "Unauthorized",
        "message": "无效或缺失API密钥，请在请求头中添加: Authorization: Bearer YOUR_KEY"
    }, 401
