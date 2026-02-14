"""
IronSentinel - 安全网关 & RBAC 鉴权

实现基于微信备注名的角色访问控制 (RBAC)，
管理权限等级、白名单和 Sudo 模式。
"""
import sqlite3
import random
from enum import IntEnum
from dataclasses import dataclass
from typing import Optional

from core.config import conf
from utils.logger import logger


class RoleLevel(IntEnum):
    """权限等级定义"""
    STRANGER = 0    # 陌生人：直接忽略
    GUEST = 1      # 客群：仅基础对话
    ADMIN = 2      # 管理：查询业务数据
    ROOT = 3       # 主人：全局控制 (CMD/RPA)


@dataclass
class AuthInfo:
    """授权信息对象"""
    remark_name: str
    role_level: RoleLevel
    is_master: bool = False
    wxid: Optional[str] = None


class SecurityGate:
    """
    铁壁安全网关

    负责所有进入消息的身份鉴定和权限查验。
    """

    def __init__(self):
        self._db_path = conf.db_full_path
        self._master_remark = conf.master_remark
        self._master_wxid = conf.master_wxid
        self._sudo_tokens: dict[str, str] = {}  # 存储待确认的 sudo 令牌 {remark_name: token}

    def _get_db_conn(self):
        return sqlite3.connect(self._db_path)

    def authenticate(self, sender: str, room: Optional[str] = None, wxid: Optional[str] = None) -> AuthInfo:
        """
        鉴定身份并返回权限等级

        @param sender 发送者备注名
        @param room 群名称 (可选)
        @param wxid 发送者唯一微信号 (可选)
        @returns 授权信息对象
        """
        # 1. 绝对主人校验 (最高安全性：WxID > 备注名)
        if self._master_wxid:
            # 如果配置了 WxID，则以此为准
            if wxid and wxid == self._master_wxid:
                return AuthInfo(sender, RoleLevel.ROOT, True, wxid)
            
            # 如果备注名匹配但 WxID 不匹配（可能是冒充），直接拒绝 Root 权限
            if sender == self._master_remark and wxid and wxid != self._master_wxid:
                logger.warning(f"检测到疑似冒充行为: 备注名 [{sender}] 匹配但 WxID [{wxid}] 不匹配")
                return AuthInfo(sender, RoleLevel.STRANGER, False, wxid)
        
        # 兼容模式：如果没配 WxID 或 WxID 获取不到，降级到备注名匹配
        if sender == self._master_remark:
            return AuthInfo(sender, RoleLevel.ROOT, True, wxid)

        # 2. 数据库查询权限
        try:
            with self._get_db_conn() as conn:
                cursor = conn.cursor()
                
                # 查询用户权限
                cursor.execute(
                    "SELECT role_level FROM user_permissions WHERE remark_name = ?",
                    (sender,)
                )
                res = cursor.fetchone()
                if res:
                    return AuthInfo(sender, RoleLevel(res[0]))

                # 3. 如果是群聊，检查群白名单
                if room:
                    cursor.execute(
                        "SELECT allow_guest_chat FROM group_whitelist WHERE group_name = ?",
                        (room,)
                    )
                    group_res = cursor.fetchone()
                    if group_res and group_res[0]:
                        return AuthInfo(sender, RoleLevel.GUEST)

        except Exception as e:
            logger.error(f"鉴权过程异常: {e}")

        # 4. 默认拒绝
        return AuthInfo(sender, RoleLevel.STRANGER)

    def generate_sudo_token(self, remark_name: str) -> str:
        """为敏感操作生成 4 位动态验证码"""
        token = str(random.randint(1000, 9999))
        self._sudo_tokens[remark_name] = token
        return token

    def verify_sudo_token(self, remark_name: str, input_token: str) -> bool:
        """验证验证码"""
        stored = self._sudo_tokens.get(remark_name)
        if stored and stored == input_token:
            del self._sudo_tokens[remark_name]
            return True
        return False

    def update_permission(self, target: str, level: int, admin: str) -> bool:
        """[ROOT 专用] 更新用户权限"""
        try:
            with self._get_db_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO user_permissions (remark_name, role_level, added_by) VALUES (?, ?, ?)",
                    (target, level, admin)
                )
                conn.commit()
                logger.info(f"权限更新: {target} -> {level} (由 {admin} 执行)")
                return True
        except Exception as e:
            logger.error(f"更新权限失败: {e}")
            return False


# 全局安全网关单例
security_gate = SecurityGate()
