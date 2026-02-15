import hashlib
from collections import deque
# from utils.logger import logger # 注释掉以支持独立测试

class MessageDeDuplicator:
    """
    [v12.2] 消息去重器
    采用 MD5 指纹校验和滑动窗口机制，确保消息幂等性。
    """
    def __init__(self, cache_size=200):
        # 使用 deque 维持固定大小的顺序，set 用于 O(1) 查询
        self.hash_queue = deque(maxlen=cache_size)
        self.seen_hashes = set()

    def is_duplicate(self, sender: str, content: str, msg_type: str = "Text") -> bool:
        """
        生成指纹并校验是否重复
        """
        # 1. 构造特征字符串
        raw_sig = f"{sender}|{content}|{msg_type}"
        
        # 2. 生成 MD5 哈希
        msg_hash = hashlib.md5(raw_sig.encode('utf-8')).hexdigest()

        # 3. 校验
        if msg_hash in self.seen_hashes:
            return True
        
        # 4. 记录并维护滑动窗口
        # 如果队列已满，且即将加入新元素导致 deque 弹出最旧元素，必须同步更新 set
        if len(self.hash_queue) == self.hash_queue.maxlen:
            oldest_hash = self.hash_queue[0]
            if oldest_hash in self.seen_hashes:
                self.seen_hashes.remove(oldest_hash)

        self.seen_hashes.add(msg_hash)
        self.hash_queue.append(msg_hash)
        
        return False

    def clear(self):
        """手动清空去重缓存"""
        self.seen_hashes.clear()
        self.hash_queue.clear()
        # logger.info("♻️ 消息去重器缓存已重置")

# 全局实体单例
deduplicator = MessageDeDuplicator()
