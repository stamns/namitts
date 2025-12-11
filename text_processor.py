# text_processor.py - 文本分段与音频合并工具
import re
import io
from pydub import AudioSegment
import logging
logger = logging.getLogger('TextProcessor')
class TextProcessor:
    def __init__(self, max_chunk_length=200):
        """
        :param max_chunk_length: 单段文本最大长度（根据TTS API能力调整）
        """
        self.max_chunk_length = max_chunk_length
    
    def split_text(self, text):
        """智能分段：按标点符号拆分，避免句子被截断"""
        # 按中文标点分段（。！？；）
        chunks = re.split(r'([。！？；]\s*)', text)
        merged = []
        current_chunk = ""
        
        for chunk in chunks:
            if len(current_chunk) + len(chunk) <= self.max_chunk_length:
                current_chunk += chunk
            else:
                if current_chunk:
                    merged.append(current_chunk.strip())
                current_chunk = chunk
        
        if current_chunk:
            merged.append(current_chunk.strip())
        
        logger.info(f"文本分段完成：原始长度{len(text)}字符，分为{len(merged)}段")
        return merged
    
    def merge_audio(self, audio_chunks):
        """合并多个音频片段为一个完整MP3"""
        if not audio_chunks:
            raise ValueError("音频片段列表为空")
        
        if len(audio_chunks) == 1:
            return audio_chunks[0]  # 只有一段，直接返回
        
        try:
            combined = AudioSegment.empty()
            for i, chunk in enumerate(audio_chunks):
                logger.info(f"合并第{i+1}/{len(audio_chunks)}段音频，大小: {len(chunk)}字节")
                # 将二进制音频数据转换为AudioSegment对象
                audio = AudioSegment.from_mp3(io.BytesIO(chunk))
                combined += audio
            
            # 导出合并后的音频为二进制数据
            output = io.BytesIO()
            combined.export(output, format="mp3")
            result = output.getvalue()
            logger.info(f"音频合并完成，总大小: {len(result)}字节")
            return result
        except Exception as e:
            logger.error(f"音频合并失败: {str(e)}", exc_info=True)
            # 如果合并失败，返回第一段音频
            return audio_chunks[0]
