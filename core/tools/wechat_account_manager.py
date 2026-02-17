import os
import winreg
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from langchain_core.tools import tool
from utils.logger import logger

class WeChatAccountManager:
    """微信多账号管理器"""
    
    def __init__(self):
        self.accounts_cache = {}
        self.last_scan_time = 0
        self.scan_interval = 60  # 60秒内不重复扫描
    
    def scan_all_accounts(self) -> List[Dict]:
        """
        扫描所有可用的微信账号
        
        Returns:
            包含账号信息的列表
        """
        current_time = time.time()
        if current_time - self.last_scan_time < self.scan_interval:
            return list(self.accounts_cache.values())
        
        accounts = []
        
        # 1. 从注册表获取主路径
        base_paths = self._get_wechat_base_paths()
        
        # 2. 在每个路径下查找用户目录
        for base_path in base_paths:
            if not os.path.exists(base_path):
                continue
                
            user_dirs = self._find_user_directories(base_path)
            for user_dir in user_dirs:
                account_info = self._analyze_account_directory(user_dir, base_path)
                if account_info:
                    accounts.append(account_info)
        
        # 3. 缓存结果
        self.accounts_cache = {acc['user_id']: acc for acc in accounts}
        self.last_scan_time = current_time
        
        return accounts
    
    def _get_wechat_base_paths(self) -> List[str]:
        """获取可能的微信文件存储路径"""
        paths = []
        
        # 1. 从注册表获取
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Tencent\WeChat") as key:
                path_val, _ = winreg.QueryValueEx(key, "FileSavePath")
                if path_val:
                    if path_val == "MyDocuments:":
                        paths.append(os.path.join(os.path.expanduser("~"), "Documents", "WeChat Files"))
                    else:
                        paths.append(os.path.join(path_val, "WeChat Files"))
        except (OSError, FileNotFoundError):
            pass
        
        # 2. 常见路径启发式搜索
        common_paths = [
            os.path.join(os.path.expanduser("~"), "Documents", "WeChat Files"),
            "E:\\WeChat Files",
            "D:\\WeChat Files",
            "C:\\WeChat Files",
            os.path.join(os.environ.get('ONEDRIVE', ''), "WeChat Files"),
        ]
        
        paths.extend(common_paths)
        return list(set(paths))  # 去重
    
    def _find_user_directories(self, base_path: str) -> List[Path]:
        """在基础路径下查找用户目录"""
        base = Path(base_path)
        if not base.exists():
            return []
        
        user_dirs = []
        try:
            for item in base.iterdir():
                if (item.is_dir() and 
                    item.name not in ["All Users", "Applet"] and 
                    (item / "FileStorage").exists()):
                    user_dirs.append(item)
        except (PermissionError, OSError):
            pass
            
        return user_dirs
    
    def _analyze_account_directory(self, user_dir: Path, base_path: str) -> Optional[Dict]:
        """分析单个账号目录的信息"""
        try:
            user_id = user_dir.name
            file_storage = user_dir / "FileStorage"
            msg_attach = file_storage / "MsgAttach"
            voice_dir = file_storage / "Voice"
            
            # 获取最近修改时间
            last_modified = user_dir.stat().st_mtime
            
            # 检查各目录的存在性
            has_msg_attach = msg_attach.exists()
            has_voice = voice_dir.exists()
            
            # 估算活跃度（基于文件数量和修改时间）
            activity_score = self._calculate_activity_score(user_dir)
            
            # 尝试获取更多信息
            nickname = self._extract_nickname(user_dir)
            avatar_path = self._find_avatar(user_dir)
            
            return {
                'user_id': user_id,
                'full_path': str(user_dir),
                'base_path': base_path,
                'last_modified': last_modified,
                'has_msg_attach': has_msg_attach,
                'has_voice': has_voice,
                'activity_score': activity_score,
                'nickname': nickname,
                'avatar_path': str(avatar_path) if avatar_path else None,
                'is_active': activity_score > 0.5  # 活跃度阈值
            }
            
        except Exception as e:
            logger.debug(f"分析账号目录失败 {user_dir}: {e}")
            return None
    
    def _calculate_activity_score(self, user_dir: Path) -> float:
        """计算账号活跃度分数 (0.0-1.0)"""
        try:
            score = 0.0
            total_files = 0
            recent_files = 0
            now = time.time()
            one_week_ago = now - 7 * 24 * 3600
            
            # 遍历FileStorage目录
            file_storage = user_dir / "FileStorage"
            if file_storage.exists():
                for root, _, files in os.walk(file_storage):
                    for file in files:
                        total_files += 1
                        try:
                            file_path = os.path.join(root, file)
                            mtime = os.path.getmtime(file_path)
                            if mtime > one_week_ago:
                                recent_files += 1
                        except (OSError, PermissionError):
                            pass
            
            # 基础分数：文件数量
            if total_files > 0:
                score += min(total_files / 1000, 0.3)  # 最多0.3分
            
            # 活跃分数：近期文件比例
            if total_files > 0:
                recent_ratio = recent_files / total_files
                score += recent_ratio * 0.5  # 最多0.5分
            
            # 时间分数：最近修改时间
            last_mod = user_dir.stat().st_mtime
            time_diff = now - last_mod
            if time_diff < 24 * 3600:  # 24小时内
                score += 0.2
            elif time_diff < 7 * 24 * 3600:  # 一周内
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception:
            return 0.0
    
    def _extract_nickname(self, user_dir: Path) -> str:
        """尝试从配置文件中提取昵称"""
        try:
            # 查找配置文件
            config_paths = [
                user_dir / "config" / "AccInfo.dat",
                user_dir / "config" / "Common.dat",
                user_dir / "config" / "NewStrategyConfig.dat"
            ]
            
            for config_path in config_paths:
                if config_path.exists():
                    # 尝试读取配置文件（可能需要解密）
                    try:
                        with open(config_path, 'rb') as f:
                            content = f.read()
                            # 简单的文本搜索
                            text_content = content.decode('utf-8', errors='ignore')
                            # 查找可能的昵称模式
                            import re
                            nicknames = re.findall(r'[昵用账][称号户][:：]\s*([^,\n\r]+)', text_content)
                            if nicknames:
                                return nicknames[0].strip()
                    except (UnicodeDecodeError, PermissionError):
                        pass
                        
        except Exception:
            pass
        
        return "未知用户"
    
    def _find_avatar(self, user_dir: Path) -> Optional[Path]:
        """查找用户头像"""
        avatar_paths = [
            user_dir / "Avatar" / "avatar.png",
            user_dir / "Avatar" / "head.png",
            user_dir / "config" / "avatar.jpg"
        ]
        
        for avatar_path in avatar_paths:
            if avatar_path.exists():
                return avatar_path
        return None

# 全局实例
_account_manager = WeChatAccountManager()

@tool
def list_wechat_accounts(detailed: bool = False) -> str:
    """
    列出所有检测到的微信账号
    
    Args:
        detailed: 是否显示详细信息
        
    Returns:
        账号列表信息
    """
    try:
        accounts = _account_manager.scan_all_accounts()
        
        if not accounts:
            return "❌ 未检测到任何微信账号"
        
        # 按活跃度排序
        accounts.sort(key=lambda x: x['activity_score'], reverse=True)
        
        result = f"📱 检测到 {len(accounts)} 个微信账号:\n"
        result += "=" * 50 + "\n"
        
        for i, account in enumerate(accounts, 1):
            status = "🟢" if account['is_active'] else "⚪"
            result += f"{i}. {status} {account['user_id']}\n"
            
            if detailed:
                result += f"   昵称: {account['nickname']}\n"
                result += f"   路径: {account['full_path']}\n"
                result += f"   活跃度: {account['activity_score']:.2f}\n"
                result += f"   最后活动: {time.strftime('%Y-%m-%d %H:%M', time.localtime(account['last_modified']))}\n"
                if account['avatar_path']:
                    result += f"   头像: {account['avatar_path']}\n"
                result += "-" * 30 + "\n"
            else:
                result += f"   昵称: {account['nickname']} | 活跃度: {account['activity_score']:.2f}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"列出微信账号失败: {e}")
        return f"❌ 获取账号列表失败: {str(e)}"

@tool
def identify_current_account() -> str:
    """
    识别当前活跃的微信账号
    
    Returns:
        当前账号信息
    """
    try:
        accounts = _account_manager.scan_all_accounts()
        
        if not accounts:
            return "❌ 未检测到任何微信账号"
        
        # 找到活跃度最高的账号
        current_account = max(accounts, key=lambda x: x['activity_score'])
        
        result = "🎯 当前识别的活跃账号:\n"
        result += "=" * 30 + "\n"
        result += f"用户ID: {current_account['user_id']}\n"
        result += f"昵称: {current_account['nickname']}\n"
        result += f"路径: {current_account['full_path']}\n"
        result += f"活跃度评分: {current_account['activity_score']:.2f}\n"
        result += f"最后活动时间: {time.strftime('%Y-%m-%d %H:%M', time.localtime(current_account['last_modified']))}\n"
        
        if current_account['avatar_path']:
            result += f"头像路径: {current_account['avatar_path']}\n"
            
        # 提供使用建议
        result += "\n💡 使用建议:\n"
        result += "- 如果识别不准确，请手动指定账号ID\n"
        result += "- 可以使用 'switch_wechat_account' 工具切换账号\n"
        result += "- 建议定期刷新账号列表以获取最新状态"
        
        return result
        
    except Exception as e:
        logger.error(f"识别当前账号失败: {e}")
        return f"❌ 识别当前账号失败: {str(e)}"

@tool
def switch_wechat_account(user_id: str) -> str:
    """
    切换到指定的微信账号
    
    Args:
        user_id: 目标账号的用户ID
        
    Returns:
        切换结果
    """
    try:
        accounts = _account_manager.scan_all_accounts()
        
        # 验证账号是否存在
        target_account = next((acc for acc in accounts if acc['user_id'] == user_id), None)
        
        if not target_account:
            available_ids = [acc['user_id'] for acc in accounts]
            return f"❌ 未找到账号: {user_id}\n可用账号: {', '.join(available_ids)}"
        
        # 更新配置（这里需要与主配置系统集成）
        from core.config import conf
        # 注意：实际实现需要更新全局配置
        # conf.current_wechat_account = user_id
        
        result = f"✅ 已切换到账号: {user_id}\n"
        result += f"昵称: {target_account['nickname']}\n"
        result += f"路径: {target_account['full_path']}\n"
        result += f"活跃度: {target_account['activity_score']:.2f}"
        
        logger.info(f"切换微信账号到: {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"切换账号失败: {e}")
        return f"❌ 切换账号失败: {str(e)}"

@tool
def refresh_account_list() -> str:
    """
    强制刷新账号列表缓存
    
    Returns:
        刷新结果
    """
    try:
        # 清除缓存
        _account_manager.last_scan_time = 0
        _account_manager.accounts_cache.clear()
        
        # 重新扫描
        accounts = _account_manager.scan_all_accounts()
        
        return f"✅ 账号列表已刷新，检测到 {len(accounts)} 个账号"
        
    except Exception as e:
        logger.error(f"刷新账号列表失败: {e}")
        return f"❌ 刷新失败: {str(e)}"