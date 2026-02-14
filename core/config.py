import os
import winreg
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

class Config:
    """
    IronSentinel 全兼容配置加载器 (v10.9.2)
    1. 支持自动探测微信存储路径（注册表 + 跨盘搜寻）。
    2. 支持基于 .env 的多层配置覆盖。
    3. 自动注入代理配置。
    4. 具备属性访问冲突防御。
    """
    _instance = None
    PROJECT_ROOT = Path(__file__).resolve().parent.parent

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        # 1. 加载环境变量
        load_dotenv(dotenv_path=self.PROJECT_ROOT / ".env", override=True)
        
        # 2. 从模板加载默认值
        try:
            from core.config_template import ConfigTemplate
            for key, value in ConfigTemplate.__dict__.items():
                if not key.startswith("_"):
                    setattr(self, key.lower(), value)
        except ImportError:
            # 如果模板缺失，设置一些基础默认值
            self.log_level = "INFO"
            self.whitelist = ["文件传输助手"]

        # 3. 环境变量优先级更高，执行覆盖
        for key in list(self.__dict__.keys()):
            env_val = os.getenv(key.upper())
            if env_val:
                orig_val = getattr(self, key)
                if isinstance(orig_val, bool):
                    setattr(self, key, env_val.lower() in ("true", "1", "yes"))
                elif isinstance(orig_val, int):
                    setattr(self, key, int(env_val))
                elif isinstance(orig_val, list):
                    setattr(self, key, [i.strip() for i in env_val.split(",") if i.strip()])
                else:
                    setattr(self, key, env_val)

        # 4. 特殊字段处理与路径探测
        self._post_init()

    def _post_init(self):
        # 路径校准 (PROJECT_ROOT 由 property 维护)
        self.db_full_path = self.PROJECT_ROOT / getattr(self, 'db_path', 'data/work.db')
        self.log_full_dir = self.PROJECT_ROOT / 'logs'
        
        # [v10.9] 核心进化配置
        self.memory_window_size = int(getattr(self, 'memory_window_size', 10) or 10)
        self.xor_enabled = getattr(self, 'xor_enabled', True)
        
        # 微信文件路径自动探测
        self.wechat_files_root = self._detect_wechat_path()
        
        # 代理自动校准 (适配 gRPC)
        self._setup_proxies()

    def _detect_wechat_path(self) -> str:
        """自动从注册表探测微信存储路径"""
        env_root = os.getenv("WECHAT_FILES_ROOT")
        if env_root and os.path.exists(env_root):
            return env_root

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Tencent\WeChat", 0, winreg.KEY_READ)
            path_val, _ = winreg.QueryValueEx(key, "FileSavePath")
            winreg.CloseKey(key)
            if path_val:
                if path_val == "MyDocuments:":
                    res = os.path.join(os.path.expanduser("~"), "Documents", "WeChat Files")
                else:
                    res = os.path.join(path_val, "WeChat Files")
                if os.path.exists(res): return res
        except: pass

        # 启发式搜寻 (D/E/F/C)
        for drive in ["D:", "E:", "F:", "C:"]:
            p = f"{drive}\\WeChat Files"
            if os.path.exists(p): return p
            
        return os.path.join(os.path.expanduser("~"), "Documents", "WeChat Files")

    def _setup_proxies(self):
        """处理 HTTPS_PROXY/HTTP_PROXY 转换并注入环境"""
        def fix_url(url: Optional[str]) -> Optional[str]:
            if not url: return None
            return url.replace("socks5h://", "http://").replace("socks5://", "http://")

        final_https = fix_url(getattr(self, 'https_proxy', None))
        final_http = fix_url(getattr(self, 'http_proxy', None))

        if final_https:
            os.environ["HTTPS_PROXY"] = final_https
            os.environ["https_proxy"] = final_https
            os.environ["GRPC_PROXY_EXP"] = final_https
        if final_http:
            os.environ["HTTP_PROXY"] = final_http
            os.environ["http_proxy"] = final_http

    @property
    def project_root(self) -> Path:
        return self.PROJECT_ROOT

    def __getattr__(self, name: str):
        # 智能查找：如果访问大写属性，自动重定向到小写
        lower_name = name.lower()
        if lower_name in self.__dict__:
            return self.__dict__[lower_name]
        return None

# 实例化全局单例
conf = Config()

# 导出常用全局常量以增强代码可读性
PROJECT_ROOT = conf.project_root
DATA_DIR = PROJECT_ROOT / "data"
VOICE_MESSAGES_DIR = DATA_DIR / "voice_messages"