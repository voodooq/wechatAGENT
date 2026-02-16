import os
import winreg
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

class Config:
    """
    IronSentinel 全兼容配置加载器 (v11.9)
    1. 支持自动探测微信存储路径（注册表 + 跨盘搜寻）。
    2. 支持基于 .env 的多层配置覆盖。
    3. 自动注入代理配置。
    4. 具备属性访问冲突防御。
    5. 新增精确微信用户路径探测。
    """
    _instance = None
    PROJECT_ROOT = Path(__file__).resolve().parent.parent

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        # 0. 初始化基础路径
        self.project_root = self.PROJECT_ROOT

        # 1. 加载环境变量
        load_dotenv(dotenv_path=self.project_root / ".env", override=True)

        
        # 2. 从模板加载默认值
        try:
            from core.config_template import ConfigTemplate
            for key, value in ConfigTemplate.__dict__.items():
                if not key.startswith("_"):
                    setattr(self, key, value)
        except ImportError:
            pass
        
        # 3. 环境变量覆盖
        for key in dir(self):
            if not key.startswith("_"):
                env_val = os.getenv(key.upper())
                if env_val is not None:
                    setattr(self, key, env_val)
        
        # 4. 特殊路径处理
        self.db_full_path = self.PROJECT_ROOT / getattr(self, 'db_path', 'data/work.db')
        
        # 5. 微信路径探测
        self.wechat_files_root = self._detect_wechat_path()
        self.wechat_user_path = self._detect_wechat_user_path()
        
        # 6. 代理配置
        self._inject_proxy_config()

    def _detect_wechat_path(self) -> str:
        """[Omni-Path] 自动解析注册表与占位符，锁定微信存储物理路径"""
        # 1. 环境变量优先
        env_root = os.getenv("WECHAT_FILES_ROOT")
        if env_root and os.path.exists(env_root):
            return env_root
        
        # 2. 注册表探测
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Tencent\WeChat", 0, winreg.KEY_READ)
            path_val, _ = winreg.QueryValueEx(key, "FileSavePath")
            winreg.CloseKey(key)
            
            # 处理 MyDocuments: 占位符
            if path_val.startswith("MyDocuments:"):
                docs_path = os.path.join(os.environ.get("USERPROFILE", ""), "Documents")
                relative = path_val.replace("MyDocuments:", "").lstrip("\\")
                full_path = os.path.join(docs_path, relative)
                if os.path.exists(full_path):
                    return full_path
            elif os.path.exists(path_val):
                return path_val
        except Exception:
            pass
        
        # 3. 默认路径
        default_path = os.path.join(os.environ.get("USERPROFILE", ""), "Documents", "WeChat Files")
        return default_path

    def _detect_wechat_user_path(self) -> str:
        """[精确探测] 自动查找当前活跃用户的微信文件存储路径"""
        wechat_root = self.wechat_files_root
        
        # 1. 检查是否存在用户目录
        if not os.path.exists(wechat_root):
            return wechat_root
        
        # 2. 查找可能的用户目录
        user_dirs = []
        try:
            for item in os.listdir(wechat_root):
                item_path = os.path.join(wechat_root, item)
                if os.path.isdir(item_path):
                    # 微信用户目录通常包含 wxid_ 或微信号
                    if item.startswith("wxid_") or "@" in item:
                        user_dirs.append(item_path)
        except Exception:
            pass
        
        # 3. 如果有多个用户目录，尝试找到最新的
        if user_dirs:
            # 按修改时间排序，取最新的
            user_dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            latest_user_dir = user_dirs[0]
            
            # 4. 检查 FileStorage/MsgAttach 结构
            file_storage = os.path.join(latest_user_dir, "FileStorage")
            if os.path.exists(file_storage):
                msg_attach = os.path.join(file_storage, "MsgAttach")
                if os.path.exists(msg_attach):
                    return msg_attach
                return file_storage
            return latest_user_dir
        
        return wechat_root

    def _inject_proxy_config(self):
        """注入代理配置"""
        proxy_url = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
        if proxy_url:
            os.environ["HTTP_PROXY"] = proxy_url
            os.environ["HTTPS_PROXY"] = proxy_url

    @property
    def wechat_attachments_path(self) -> str:
        """获取微信附件路径（最精确的路径）"""
        return self.wechat_user_path

    def __getattr__(self, name):
        """防御性属性访问"""
        if name.startswith("_"):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        return None

# 创建全局配置实例
conf = Config()
