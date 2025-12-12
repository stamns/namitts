# utils/logger.py - 统一日志管理
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# 初始化日志器
logger = logging.getLogger('nanoai_tts')
logger.setLevel(logging.INFO)

# 日志格式
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
formatter = logging.Formatter(log_format)

# 控制台日志（总是添加，输出到 stdout）
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# 文件日志（仅在本地开发环境中启用）
# 在 Vercel/云环境中不创建日志目录，只使用 stdout
environment = os.getenv('ENVIRONMENT', 'development').lower()
is_readonly_env = environment in ('vercel', 'production', 'serverless', 'railway', 'render')

if not is_readonly_env:
    try:
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
        logger.info("文件日志已启用")
    except (OSError, IOError) as e:
        # 如果无法创建 logs 目录（例如只读文件系统），只使用 stdout
        logger.warning(f"无法创建日志目录: {e}，只使用控制台日志输出")

# Sentry错误监控（可选）
if os.getenv('SENTRY_DSN'):
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=os.getenv('SENTRY_DSN'),
            traces_sample_rate=1.0,
            environment=os.getenv('ENVIRONMENT', 'development')
        )
        logger.info("Sentry错误监控已启用")
    except Exception as e:
        logger.warning(f"Sentry 初始化失败: {e}")

# 导出日志器
def get_logger():
    return logger
