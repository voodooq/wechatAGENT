import hashlib
import json
from collections import deque, defaultdict
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
import time

from utils.logger import logger
from core.config import conf

class SmartResponder:
    """
    智能回复管理器
    防止重复和过于相似的回复，提高回复质量
    """
    
    def __init__(self, history_size: int = 50, similarity_threshold: float = 0.8):
        # 回复历史缓存
        self.reply_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=history_size))
        # 相似度阈值 (0.0-1.0)
        self.similarity_threshold = similarity_threshold
        # 时间窗口 (秒)
        self.time_window = 300  # 5分钟内避免重复
        
    def should_send_reply(self, receiver: str, reply_content: str, context: Optional[str] = None) -> Tuple[bool, str]:
        """
        智能判断是否应该发送回复
        
        Args:
            receiver: 接收者
            reply_content: 回复内容
            context: 上下文信息（可选）
            
        Returns:
            Tuple[是否应该发送, 原因说明]
        """
        try:
            # 0. [v11.1] 系统消息白名单 (优先放行)
            # 包含特定关键词的消息 (如超时、错误、AI生成标识) 直接放行，不进行去重/相似度检查
            system_keywords = [
                "响应超时", "[Timeout]", "[Error]", "Access Denied", 
                "无法连接", "请稍后再试", "AI 生成", "[OpenClaw Error]"
            ]
            if any(k in reply_content for k in system_keywords):
                return True, "系统消息白名单放行"

            # 1. 基础去重检查
            basic_check = self._basic_duplicate_check(receiver, reply_content)
            if not basic_check[0]:
                return basic_check
                
            # 2. 相似度检查
            similarity_check = self._similarity_check(receiver, reply_content)
            if not similarity_check[0]:
                return similarity_check
                
            # 3. 上下文相关性检查
            if context:
                context_check = self._context_relevance_check(receiver, reply_content, context)
                if not context_check[0]:
                    return context_check
            
            # 4. 记录本次回复
            self._record_reply(receiver, reply_content)
            
            return True, "回复内容通过所有检查"
            
        except Exception as e:
            logger.error(f"智能回复检查异常: {e}")
            # 出错时保守地允许发送
            return True, "检查异常，允许发送"
    
    def _basic_duplicate_check(self, receiver: str, content: str) -> Tuple[bool, str]:
        """基础去重检查"""
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        # 检查最近的回复
        recent_replies = list(self.reply_history[receiver])
        
        for record in recent_replies[-10:]:  # 检查最近10条
            if record['hash'] == content_hash:
                time_diff = time.time() - record['timestamp']
                if time_diff < self.time_window:
                    return False, f"检测到重复回复 (时间差: {int(time_diff)}秒)"
        
        return True, "基础检查通过"
    
    def _similarity_check(self, receiver: str, content: str) -> Tuple[bool, str]:
        """相似度检查"""
        if len(content) < 10:  # 太短的内容不检查相似度
            return True, "内容过短，跳过相似度检查"
            
        recent_replies = list(self.reply_history[receiver])
        
        for record in recent_replies[-5:]:  # 检查最近5条
            similarity = self._calculate_similarity(content, record['content'])
            if similarity > self.similarity_threshold:
                time_diff = time.time() - record['timestamp']
                if time_diff < self.time_window:
                    return False, f"检测到相似回复 (相似度: {similarity:.2f})"
        
        return True, "相似度检查通过"
    
    def _context_relevance_check(self, receiver: str, content: str, context: str) -> Tuple[bool, str]:
        """上下文相关性检查"""
        # 检查回复是否与上下文相关
        context_similarity = self._calculate_similarity(content, context)
        
        # 如果回复与上下文完全无关，可能是机械回复
        # 降低阈值以避免误拦截（从0.1降低到0.05）
        if context_similarity < 0.05:
            return False, "回复与上下文关联度过低"
            
        return True, "上下文检查通过"
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的相似度"""
        # 使用SequenceMatcher计算相似度
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def _record_reply(self, receiver: str, content: str):
        """记录回复历史"""
        record = {
            'content': content,
            'hash': hashlib.md5(content.encode('utf-8')).hexdigest(),
            'timestamp': time.time(),
            'length': len(content)
        }
        self.reply_history[receiver].append(record)
        logger.debug(f"记录回复历史: {receiver} - {content[:30]}...")
    
    def get_reply_statistics(self, receiver: str) -> Dict:
        """获取指定接收者的回复统计信息"""
        history = list(self.reply_history[receiver])
        if not history:
            return {"total_replies": 0}
            
        return {
            "total_replies": len(history),
            "unique_replies": len(set(r['hash'] for r in history)),
            "avg_length": sum(r['length'] for r in history) / len(history),
            "recent_reply_times": [time.time() - r['timestamp'] for r in history[-5:]]
        }
    
    def get_current_config(self) -> str:
        """获取当前配置信息"""
        return (f"相似度阈值: {self.similarity_threshold}\n"
                f"历史记录大小: {next(iter(self.reply_history.values())).maxlen if self.reply_history else 'N/A'}\n"
                f"时间窗口: {self.time_window}秒\n"
                f"跟踪的接收者数量: {len(self.reply_history)}")
    
    def clear_history(self, receiver: Optional[str] = None):
        """清空回复历史"""
        if receiver:
            if receiver in self.reply_history:
                count = len(self.reply_history[receiver])
                self.reply_history[receiver].clear()
                logger.info(f"已清空 {receiver} 的回复历史 ({count} 条)")
        else:
            total_count = sum(len(history) for history in self.reply_history.values())
            self.reply_history.clear()
            logger.info(f"已清空所有回复历史 ({total_count} 条)")

# 全局智能回复管理器
smart_responder = SmartResponder()