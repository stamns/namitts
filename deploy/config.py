# deploy/config.py - 统一部署配置
import os
from dotenv import load_dotenv
load_dotenv()
class DeployConfig:
    # 基础配置
    PROJECT_NAME = "nanoai-tts"
    VERSION = "1.0.0"
    AUTHOR = "Your Name"
    
    # 平台特定配置
    CLOUDFLARE = {
        "NAME": os.getenv("CF_PROJECT_NAME", PROJECT_NAME),
        "ACCOUNT_ID": os.getenv("CF_ACCOUNT_ID"),
        "ZONE_ID": os.getenv("CF_ZONE_ID"),
        "WORKERS_DEV": True
    }
    
    VERCEL = {
        "PROJECT_NAME": os.getenv("VERCEL_PROJECT_NAME", PROJECT_NAME),
        "FRAMEWORK_PRESET": "python",
        "REGION": "iad1"
    }
    
    GITHUB = {
        "REPO": os.getenv("GITHUB_REPO"),
        "BRANCH": "main",
        "PAGES_FOLDER": "docs"
    }
