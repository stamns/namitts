# utils/logger.py - 统一日志管理
import logging
import logging.handlers
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
# 初始化日志器
logger = logging.getLogger('nanoai_tts')
logger.setLevel(logging.INFO)
# 日志格式
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
formatter = logging.Formatter(log_format)
# 控制台日志
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
# 文件日志（按天轮转）
if not os.path.exists('logs'):
    os.makedirs('logs')
file_handler = logging.handlers.TimedRotatingFileHandler(
    'logs/nanoai_tts.log',
    when='midnight',
    interval=1,
    backupCount=7  # 保留7天日志
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
# Sentry错误监控（可选）
if os.getenv('SENTRY_DSN'):
    import sentry_sdk
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        traces_sample_rate=1.0,
        environment=os.getenv('ENVIRONMENT', 'development')
    )
    logger.info("Sentry错误监控已启用")
# 导出日志器
def get_logger():
    return logger
