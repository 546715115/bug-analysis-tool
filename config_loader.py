"""
配置加载器 - 负责加载维度配置和API配置
"""
import os
import yaml
from pathlib import Path


class ConfigLoader:
    """配置加载器"""

    def __init__(self):
        self.config_dir = Path(__file__).parent / "config"
        self.dimensions_config = None
        self.api_config = None
        self._load_configs()

    def _load_configs(self):
        """加载所有配置文件"""
        # 加载维度配置
        dimensions_path = self.config_dir / "dimensions_config.yaml"
        if dimensions_path.exists():
            with open(dimensions_path, 'r', encoding='utf-8') as f:
                self.dimensions_config = yaml.safe_load(f)

        # 加载API配置
        api_path = self.config_dir / "api_config.yaml"
        if api_path.exists():
            with open(api_path, 'r', encoding='utf-8') as f:
                self.api_config = yaml.safe_load(f)

    def get_dimensions(self):
        """获取维度配置"""
        return self.dimensions_config.get('dimensions', {}) if self.dimensions_config else {}

    def get_dimension_options(self, dimension_key):
        """获取某个维度的选项列表"""
        dimensions = self.get_dimensions()
        dim = dimensions.get(dimension_key, {})
        options = dim.get('options', [])
        return {opt['value']: opt['label'] for opt in options}

    def get_dimension_label(self, dimension_key):
        """获取维度的显示名称"""
        dimensions = self.get_dimensions()
        dim = dimensions.get(dimension_key, {})
        return dim.get('name', dimension_key)

    def get_all_dimension_labels(self):
        """获取所有维度的标签（用于表格显示）"""
        dimensions = self.get_dimensions()
        return {key: val.get('name', key) for key, val in dimensions.items()}

    def get_field_mapping(self):
        """获取字段映射配置"""
        return self.dimensions_config.get('field_mapping', {}) if self.dimensions_config else {}

    def get_api_configs(self):
        """获取API配置列表"""
        return self.api_config.get('apis', []) if self.api_config else []

    def save_dimension_config(self, dimensions):
        """保存维度配置"""
        if self.dimensions_config:
            self.dimensions_config['dimensions'] = dimensions
            dimensions_path = self.config_dir / "dimensions_config.yaml"
            with open(dimensions_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.dimensions_config, f, allow_unicode=True, default_flow_style=False)


# 全局配置加载器实例
_config_loader = None


def get_config_loader():
    """获取配置加载器单例"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader
