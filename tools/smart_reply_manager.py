import json
from typing import Dict, Optional
from langchain_core.tools import tool
from core.smart_responder import smart_responder
from utils.logger import logger

@tool
def configure_smart_reply(similarity_threshold: Optional[float] = None, 
                         history_size: Optional[int] = None,
                         time_window: Optional[int] = None) -> str:
    """
    配置智能回复参数
    
    Args:
        similarity_threshold: 相似度阈值 (0.0-1.0)，默认0.8
        history_size: 历史记录大小，默认50
        time_window: 时间窗口(秒)，默认300
        
    Returns:
        配置结果信息
    """
    try:
        changes = []
        
        if similarity_threshold is not None:
            if 0.0 <= similarity_threshold <= 1.0:
                smart_responder.similarity_threshold = similarity_threshold
                changes.append(f"相似度阈值设为 {similarity_threshold}")
            else:
                return "❌ 相似度阈值必须在 0.0-1.0 之间"
                
        if history_size is not None:
            if history_size > 0:
                # 重新初始化历史记录
                for receiver in smart_responder.reply_history:
                    smart_responder.reply_history[receiver] = smart_responder.reply_history[receiver].__class__(maxlen=history_size)
                changes.append(f"历史记录大小设为 {history_size}")
            else:
                return "❌ 历史记录大小必须大于0"
                
        if time_window is not None:
            if time_window > 0:
                smart_responder.time_window = time_window
                changes.append(f"时间窗口设为 {time_window}秒")
            else:
                return "❌ 时间窗口必须大于0"
        
        if changes:
            config_info = smart_responder.get_current_config()
            return f"✅ 智能回复配置已更新:\n" + "\n".join(changes) + f"\n\n当前配置:\n{config_info}"
        else:
            config_info = smart_responder.get_current_config()
            return f"ℹ️ 当前智能回复配置:\n{config_info}"
            
    except Exception as e:
        logger.error(f"配置智能回复失败: {e}")
        return f"❌ 配置失败: {str(e)}"

@tool
def get_reply_statistics(receiver: Optional[str] = None) -> str:
    """
    获取回复统计信息
    
    Args:
        receiver: 指定接收者，如果为None则显示所有
        
    Returns:
        统计信息
    """
    try:
        if receiver:
            stats = smart_responder.get_reply_statistics(receiver)
            return f"📊 {receiver} 的回复统计:\n{json.dumps(stats, indent=2, ensure_ascii=False)}"
        else:
            # 显示所有接收者的统计
            all_stats = {}
            for recv in smart_responder.reply_history.keys():
                all_stats[recv] = smart_responder.get_reply_statistics(recv)
            return f"📊 所有接收者的回复统计:\n{json.dumps(all_stats, indent=2, ensure_ascii=False)}"
            
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return f"❌ 获取统计失败: {str(e)}"

@tool
def clear_reply_history(receiver: Optional[str] = None) -> str:
    """
    清空回复历史
    
    Args:
        receiver: 指定接收者，如果为None则清空所有
        
    Returns:
        操作结果
    """
    try:
        smart_responder.clear_history(receiver)
        if receiver:
            return f"✅ 已清空 {receiver} 的回复历史"
        else:
            return "✅ 已清空所有回复历史"
            
    except Exception as e:
        logger.error(f"清空历史失败: {e}")
        return f"❌ 清空失败: {str(e)}"

@tool
def test_reply_uniqueness(receiver: str, content: str, context: Optional[str] = None) -> str:
    """
    测试回复是否会因为重复而被拦截
    
    Args:
        receiver: 接收者
        content: 测试内容
        context: 上下文
        
    Returns:
        测试结果
    """
    try:
        should_send, reason = smart_responder.should_send_reply(receiver, content, context)
        
        if should_send:
            return f"✅ 回复可以通过检查: {reason}\n内容: {content[:50]}..."
        else:
            return f"🚫 回复会被拦截: {reason}\n内容: {content[:50]}..."
            
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return f"❌ 测试失败: {str(e)}"