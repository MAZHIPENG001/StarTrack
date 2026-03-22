import json
import os

class ConfigManager:
    def __init__(self, filepath='./cfg/sys_config.json'):
        """初始化配置管家，默认将配置文件放在根目录"""
        self.filepath = filepath
        self.config = self._load_config()

    def _load_config(self):
        """内部方法：读取 JSON 文件，如果文件不存在或损坏，返回空字典"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 配置文件读取失败，将使用默认值: {e}")
                return {}
        return {}

    def get(self, key, default_value=None):
        """获取参数，如果找不到这个键，就返回你给的默认值"""
        return self.config.get(key, default_value)

    def set(self, key, value):
        """设置参数，并立即保存到硬盘"""
        self.config[key] = value
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                # indent=4 会让生成的 JSON 文件排版很漂亮，方便人类阅读
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"❌ 配置文件保存失败: {e}")

global_config = ConfigManager()