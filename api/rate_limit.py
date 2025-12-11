# api/rate_limit.py - API限流模块
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def init_limiter(app):
    """初始化限流组件"""
    # 优先使用 Redis，如果不可用则回退到内存存储
    redis_url = os.getenv('REDIS_URL', 'memory://')
    
    # 检测运行环境
    environment = os.getenv('ENVIRONMENT', 'development')
    if redis_url != 'memory://':
        app.logger.info(f"使用 Redis 作为限流存储: {redis_url}")
    else:
        app.logger.warning("使用内存存储进行限流，重启后限流计数器将重置")
    
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,  # 按IP地址限流
        default_limits=["10 per minute"],  # 默认限制：每分钟10次
        storage_uri=redis_url,  # 动态选择存储后端
    )
    
    # 为不同接口设置差异化限流
    limiter.limit("30 per minute")(app.view_functions["create_speech"])  # TTS接口放宽到30次/分钟
    limiter.limit("60 per minute")(app.view_functions["list_models"])  # 模型列表接口60次/分钟
    
    return limiter
