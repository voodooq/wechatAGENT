import os
import time
from pathlib import Path
from typing import Dict, Optional
from langchain_core.tools import tool
from utils.logger import logger
from core.tools.wechat_account_manager import _account_manager

@tool
def enhanced_wechat_locator(include_account_info: bool = True) -> str:
    """
    [增强版] 微信路径探测器，包含账号识别信息
    
    Args:
        include_account_info: 是否包含详细的账号信息
        
    Returns:
        包含路径和账号信息的结果
    """
    try:
        # 获取基础路径定位结果
        from core.tools.wechat_locator import ultra_wechat_locator
        base_result = ultra_wechat_locator.invoke({})
        
        if "❌" in base_result:
            return base_result
            
        # 获取账号信息
        accounts = _account_manager.scan_all_accounts()
        
        if not accounts:
            return f"✅ 路径定位成功: {base_result}\n⚠️ 未检测到账号信息"
        
        # 识别当前最可能的账号
        current_account = max(accounts, key=lambda x: x['activity_score'])
        
        # 构建详细结果
        result = f"✅ 微信路径定位成功\n"
        result += "=" * 40 + "\n"
        result += f"基础路径: {base_result}\n"
        result += f"当前活跃账号: {current_account['user_id']}\n"
        result += f"账号昵称: {current_account['nickname']}\n"
        result += f"活跃度评分: {current_account['activity_score']:.2f}\n"
        result += f"最后活动: {time.strftime('%Y-%m-%d %H:%M', time.localtime(current_account['last_modified']))}\n"
        
        if include_account_info:
            result += "\n📋 所有检测到的账号:\n"
            result += "-" * 30 + "\n"
            for i, account in enumerate(accounts, 1):
                status = "🟢" if account['is_active'] else "⚪"
                result += f"{i}. {status} {account['user_id']} ({account['nickname']})\n"
                result += f"   活跃度: {account['activity_score']:.2f} | "
                result += f"路径: {account['full_path']}\n"
        
        result += "\n💡 使用建议:\n"
        result += "- 如需切换账号，请使用 'switch_wechat_account' 工具\n"
        result += "- 可使用 'list_wechat_accounts detailed=True' 查看详细信息\n"
        result += "- 定期使用 'refresh_account_list' 更新账号状态"
        
        return result
        
    except Exception as e:
        logger.error(f"增强版微信定位失败: {e}")
        return f"❌ 增强定位失败: {str(e)}"

@tool
def get_current_wechat_context() -> str:
    """
    获取当前微信使用上下文信息
    
    Returns:
        包含当前账号、路径、使用状态的详细信息
    """
    try:
        # 获取所有账号信息
        accounts = _account_manager.scan_all_accounts()
        
        if not accounts:
            return "❌ 未检测到任何微信账号"
        
        # 按活跃度排序
        accounts.sort(key=lambda x: x['activity_score'], reverse=True)
        current_account = accounts[0]
        
        # 获取语音文件信息
        voice_path = None
        if current_account['has_voice']:
            voice_dir = Path(current_account['full_path']) / "FileStorage" / "Voice"
            if voice_dir.exists():
                # 查找最新的语音文件
                latest_voice = None
                latest_time = 0
                try:
                    for root, _, files in os.walk(voice_dir):
                        for file in files:
                            if file.lower().endswith(('.silk', '.aud', '.mp3', '.wav')):
                                file_path = os.path.join(root, file)
                                mtime = os.path.getmtime(file_path)
                                if mtime > latest_time:
                                    latest_time = mtime
                                    latest_voice = file_path
                except (PermissionError, OSError):
                    pass
                
                voice_path = latest_voice
        
        # 构建上下文信息
        result = "📱 当前微信使用上下文\n"
        result += "=" * 35 + "\n"
        result += f"👤 当前账号: {current_account['user_id']}\n"
        result += f"📝 昵称: {current_account['nickname']}\n"
        result += f"📍 账号路径: {current_account['full_path']}\n"
        result += f"📊 活跃度: {current_account['activity_score']:.2f}/1.00\n"
        result += f"⏰ 最后活动: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_account['last_modified']))}\n"
        
        if voice_path:
            result += f"🔊 语音功能: 可用 (最近语音: {time.strftime('%H:%M:%S', time.localtime(latest_time))})\n"
        else:
            result += f"🔊 语音功能: {'可用' if current_account['has_voice'] else '不可用'}\n"
            
        result += f"📁 消息附件: {'可用' if current_account['has_msg_attach'] else '不可用'}\n"
        
        if len(accounts) > 1:
            result += f"\n👥 其他 {len(accounts)-1} 个账号:\n"
            for account in accounts[1:4]:  # 显示前3个其他账号
                result += f"   • {account['user_id']} ({account['nickname']}) - 活跃度: {account['activity_score']:.2f}\n"
        
        result += f"\n🔧 系统状态:\n"
        result += f"   账号总数: {len(accounts)}\n"
        result += f"   活跃账号: {sum(1 for acc in accounts if acc['is_active'])}\n"
        result += f"   语音支持: {sum(1 for acc in accounts if acc['has_voice'])}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"获取微信上下文失败: {e}")
        return f"❌ 获取上下文失败: {str(e)}"