# nano_tts.py - TTS引擎实现
import urllib.request
import urllib.parse
import hashlib
import json
import os
import logging
from datetime import datetime
import random
import time
class NanoAITTS:
    def __init__(self):
        self.name = '纳米AI'
        self.id = 'bot.n.cn'
        self.author = 'TTS Server'
        self.icon_url = 'https://bot.n.cn/favicon.ico'
        self.version = 2
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        self.voices = {}
        self.logger = logging.getLogger('NanoAITTS')
        self.cache_dir = os.getenv('CACHE_DIR', 'cache')
        self.cache_enabled = self._ensure_cache_dir()
        self.load_voices()
    
    def _ensure_cache_dir(self):
        try:
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir, exist_ok=True)
                self.logger.info(f"创建缓存目录: {self.cache_dir}")
            return True
        except (OSError, IOError) as e:
            self.logger.warning(f"无法创建缓存目录: {str(e)}，缓存功能已禁用")
            return False
    
    def md5(self, msg):
        return hashlib.md5(msg.encode('utf-8')).hexdigest()
    
    def _e(self, nt):
        HASH_MASK_1 = 268435455
        HASH_MASK_2 = 266338304
        
        at = 0
        for i in range(len(nt) - 1, -1, -1):
            st = ord(nt[i])
            at = ((at << 6) & HASH_MASK_1) + st + (st << 14)
            it = at & HASH_MASK_2
            if it != 0:
                at = at ^ (it >> 21)
        return at
    
    def generate_unique_hash(self):
        lang = 'zh-CN'
        app_name = "chrome"
        ver = 1.0
        platform = "Win32"
        width = 1920
        height = 1080
        color_depth = 24
        referrer = "https://bot.n.cn/chat"
        
        nt = f"{app_name}{ver}{lang}{platform}{self.ua}{width}x{height}{color_depth}{referrer}"
        at = len(nt)
        it = 1
        while it:
            nt += str(it ^ at)
            it -= 1
            at += 1
        
        return (round(random.random() * 2147483647) ^ self._e(nt)) * 2147483647
    
    def generate_mid(self):
        domain = "https://bot.n.cn"
        rt = str(self._e(domain)) + str(self.generate_unique_hash()) + str(int(time.time() * 1000) + random.random() + random.random())
        formatted_rt = rt.replace('.', 'e')[:32]
        return formatted_rt
    
    def get_iso8601_time(self):
        now = datetime.now()
        return now.strftime('%Y-%m-%dT%H:%M:%S+08:00')
    
    def get_headers(self):
        device = "Web"
        ver = "1.2"
        timestamp = self.get_iso8601_time()
        access_token = self.generate_mid()
        zm_ua = self.md5(self.ua)
        
        zm_token_str = f"{device}{timestamp}{ver}{access_token}{zm_ua}"
        zm_token = self.md5(zm_token_str)
        
        return {
            'device-platform': device,
            'timestamp': timestamp,
            'access-token': access_token,
            'zm-token': zm_token,
            'zm-ver': ver,
            'zm-ua': zm_ua,
            'User-Agent': self.ua
        }
    
    def http_get(self, url, headers):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            self.logger.error(f"HTTP GET请求失败 - HTTP错误: {e.code} - {e.reason}", exc_info=True)
            raise Exception(f"HTTP GET请求失败: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            self.logger.error(f"HTTP GET请求失败 - URL错误: {e.reason}", exc_info=True)
            raise Exception(f"HTTP GET请求失败: {e.reason}")
        except Exception as e:
            self.logger.error(f"HTTP GET请求失败 - 未知错误: {str(e)}", exc_info=True)
            raise Exception(f"HTTP GET请求失败: {str(e)}")
    
    def http_post(self, url, data, headers):
        data_bytes = data.encode('utf-8')
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            self.logger.error(f"HTTP POST请求失败 - HTTP错误: {e.code} - {e.reason}", exc_info=True)
            raise Exception(f"HTTP POST请求失败: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            self.logger.error(f"HTTP POST请求失败 - URL错误: {e.reason}", exc_info=True)
            raise Exception(f"HTTP POST请求失败: {e.reason}")
        except Exception as e:
            self.logger.error(f"HTTP POST请求失败 - 未知错误: {str(e)}", exc_info=True)
            raise Exception(f"HTTP POST请求失败: {str(e)}")
    
    def load_voices(self):
        filename = os.path.join(self.cache_dir, 'robots.json')
        
        try:
            # 尝试从缓存文件加载（仅在缓存可用时）
            if self.cache_enabled and os.path.exists(filename):
                self.logger.info(f"从缓存文件加载声音列表: {filename}")
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                self.logger.info("从网络获取声音列表...")
                response_text = self.http_get('https://bot.n.cn/api/robot/platform', self.get_headers())
                data = json.loads(response_text)
                
                # 尝试保存到缓存（仅在缓存可用时）
                if self.cache_enabled:
                    try:
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        self.logger.info(f"声音列表已缓存到: {filename}")
                    except Exception as e:
                        self.logger.warning(f"保存缓存文件失败: {str(e)}")
            
            self.voices.clear()
            if 'data' in data and 'list' in data['data']:
                for item in data['data']['list']:
                    self.voices[item['tag']] = {
                        'name': item['title'],
                        'iconUrl': item['icon']
                    }
                self.logger.info(f"成功加载 {len(self.voices)} 个声音模型")
            else:
                self.logger.warning("API返回的数据格式不正确")
                raise Exception("API返回的数据格式不正确")
                
        except json.JSONDecodeError as e:
            self.logger.error(f"解析JSON数据失败: {str(e)}", exc_info=True)
            raise Exception(f"解析JSON数据失败: {str(e)}")
        except Exception as e:
            self.logger.error(f"加载声音列表失败: {str(e)}", exc_info=True)
            self.voices.clear()
            self.voices['DeepSeek'] = {'name': 'DeepSeek (默认)', 'iconUrl': ''}
            self.logger.warning("使用默认声音模型")
    
    def get_audio(self, text, voice='DeepSeek', speed=1.0, pitch=1.0):
        if not text or not text.strip():
            raise ValueError("文本不能为空")
        
        if voice not in self.voices:
            raise ValueError(f"不支持的声音模型: {voice}")
        
        url = f'https://bot.n.cn/api/tts/v1?roleid={voice}&speed={speed}&pitch={pitch}'
        
        headers = self.get_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        
        max_length = 1000
        if len(text) > max_length:
            self.logger.warning(f"文本过长（最大支持{max_length}字符），将被截断")
            text = text[:max_length]
        
        form_data = f'&text={urllib.parse.quote(text)}&audio_type=mp3&format=stream'
        
        try:
            self.logger.info(f"开始生成音频 - 模型: {voice}, 文本长度: {len(text)}, 语速: {speed}, 音调: {pitch}")
            audio_data = self.http_post(url, form_data, headers)
            
            if not audio_data or len(audio_data) < 100:
                raise Exception("返回的音频数据无效")
            
            self.logger.info(f"音频生成成功 - 数据大小: {len(audio_data)} 字节")
            return audio_data
            
        except Exception as e:
            self.logger.error(f"获取音频失败: {str(e)}", exc_info=True)
            raise
