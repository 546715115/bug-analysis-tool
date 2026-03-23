"""
配置加载模块测试
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_loader import get_config_loader


class TestConfigLoader:
    """配置加载器测试类"""

    def test_get_config_loader(self):
        """测试获取配置加载器"""
        loader = get_config_loader()
        assert loader is not None

    def test_load_dimensions_config(self):
        """测试加载维度配置"""
        loader = get_config_loader()
        dimensions = loader.get_dimensions()
        assert dimensions is not None
        assert isinstance(dimensions, dict)

    def test_load_api_config(self):
        """测试加载API配置"""
        loader = get_config_loader()
        # 实际属性名是 api_config
        api_config = loader.api_config
        assert api_config is None or isinstance(api_config, dict)

    def test_get_dimension_options(self):
        """测试获取维度选项"""
        loader = get_config_loader()
        # 测试已知维度
        options = loader.get_dimension_options("severity")
        assert options is not None
        assert isinstance(options, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
