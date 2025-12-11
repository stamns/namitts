# api/rate_limit.py - API限流模块
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
def init_limiter(app):
    """初始化限流组件"""
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,  # 按IP地址限流
        default_limits=["10 per minute"],  # 默认限制：每分钟10次
        storage_uri="memory://",  # 内存存储（生产环境可用Redis）
    )
    
    # 为不同接口设置差异化限流
    limiter.limit("30 per minute")(app.view_functions["create_speech"])  # TTS接口放宽到30次/分钟
    limiter.limit("60 per minute")(app.view_functions["list_models"])  # 模型列表接口60次/分钟
    
    return limiter
