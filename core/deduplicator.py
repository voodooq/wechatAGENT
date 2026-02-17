import hashlib
from collections import deque
from typing import Optional
from utils.logger import logger

class MessageDeDuplicator:
    """
    [v12.2] 消息去重器
    采用 MD5 指纹校验和滑动窗口机制，确保消息幂等性。
    """
    def __init__(self, cache_size: int = 200):
        # 使用 deque 维持固定大小的顺序，set 用于 O(1) 查询
        self.hash_queue = deque(maxlen=cache_size)
        self.seen_hashes = set()
        self.cache_size = cache_size
        logger.debug(f"消息去重器初始化完成，缓存大小: {cache_size}")

    def is_duplicate(self, sender: str, content: str, msg_type: str = "Text") -> bool:
        """
        生成指纹并校验是否重复
        
        Args:
            sender: 消息发送者
            content: 消息内容
            msg_type: 消息类型，默认为"Text"
            
        Returns:
            bool: True表示重复，False表示新消息
        """
        try:
            # 1. 构造特征字符串
            raw_sig = f"{sender}|{content}|{msg_type}"
            
            # 2. 生成 MD5 哈希
            msg_hash = hashlib.md5(raw_sig.encode('utf-8')).hexdigest()

            # 3. 校验
            if msg_hash in self.seen_hashes:
                logger.debug(f"检测到重复消息: {sender} - {content[:50]}...")
                return True
            
            # 4. 记录并维护滑动窗口
            # 如果队列已满，且即将加入新元素导致 deque 弹出最旧元素，必须同步更新 set
            if len(self.hash_queue) == self.hash_queue.maxlen:
                oldest_hash = self.hash_queue[0]
                if oldest_hash in self.seen_hashes:
                    self.seen_hashes.remove(oldest_hash)
                    logger.debug(f"移除最旧哈希以维持缓存大小: {oldest_hash[:8]}...")

            self.seen_hashes.add(msg_hash)
            self.hash_queue.append(msg_hash)
            logger.debug(f"新消息已记录: {sender} - {content[:50]}...")
            
            return False
            
        except Exception as e:
            logger.error(f"消息去重处理异常: {e}")
            return False

    def clear(self):
        """手动清空去重缓存"""
        old_size = len(self.seen_hashes)
        self.seen_hashes.clear()
        self.hash_queue.clear()
        logger.info(f"♻️ 消息去重器缓存已重置 (原大小: {old_size})")

    def get_cache_info(self) -> dict:
        """
        获取缓存状态信息
        
        Returns:
            dict: 包含缓存大小、容量等信息
        """
        return {
            "current_size": len(self.seen_hashes),
            "max_size": self.cache_size,
            "queue_length": len(self.hash_queue)
        }

# 全局实体单例
deduplicator = MessageDeDuplicator()