import os
from pathlib import Path
from typing import Optional

class Config:
    """
    IronSentinel 全兼容配置加载器 (v10.0)
    1. 支持 Template -> Private -> Env 三层覆盖
    2. 支持大小写不敏感访问 (conf.google_api_key 或 conf.GOOGLE_API_KEY)
    3. 完整继承 settings.py 的路径推算与代理注入逻辑
    """
    _instance = None
    PROJECT_ROOT = Path(__file__).resolve().parent.parent

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        # 1. 加载公开模板
        try:
            from core.config_template import ConfigTemplate
            for key, value in ConfigTemplate.__dict__.items():
                if not key.startswith("_"):
                    setattr(self, key.lower(), value)
        except ImportError:
            pass

        # 2. 加载私有配置
        try:
            from core.config_private import PrivateConfig
            for key, value in PrivateConfig.__dict__.items():
                if not key.startswith("_"):
                    setattr(self, key.lower(), value)
        except ImportError:
            pass

        # 3. 环境变量覆盖
        for key in list(self.__dict__.keys()):
            env_val = os.getenv(key.upper())
            if env_val:
                # 尝试进行类型转换
                orig_val = getattr(self, key)
                if isinstance(orig_val, int):
                    setattr(self, key, int(env_val))
                elif isinstance(orig_val, float):
                    setattr(self, key, float(env_val))
                elif isinstance(orig_val, list) and "," in env_val:
                    setattr(self, key, [i.strip() for i in env_val.split(",")])
                else:
                    setattr(self, key, env_val)

        # 4. 执行后处理 (代理注入与路径校准)
        self._post_init()

    def _post_init(self):
        # 路径校准
        self.db_full_path = self.PROJECT_ROOT / getattr(self, 'db_path', 'data/work.db')
        self.log_full_dir = self.PROJECT_ROOT / 'logs'
        
        # 代理自动注入 (适配 gRPC)
        def fix_proxy(url: Optional[str]) -> Optional[str]:
            if not url: return None
            if url.startswith("socks5"):
                return url.replace("socks5h://", "http://").replace("socks5://", "http://")
            return url

        final_https = fix_proxy(getattr(self, 'https_proxy', None))
        final_http = fix_proxy(getattr(self, 'http_proxy', None))

        if final_https:
            os.environ["HTTPS_PROXY"] = final_https
            os.environ["https_proxy"] = final_https
            os.environ["GRPC_PROXY_EXP"] = final_https
        if final_http:
            os.environ["HTTP_PROXY"] = final_http
            os.environ["http_proxy"] = final_http

    def __getattr__(self, name: str):
        # 智能重定向：如果访问大写属性，自动查找小写副本
        lower_name = name.lower()
        if lower_name in self.__dict__:
            return self.__dict__[lower_name]
        raise AttributeError(f"'Config' object has no attribute '{name}'")

    @property
    def project_root(self) -> Path:
        return self.PROJECT_ROOT

conf = Config()
