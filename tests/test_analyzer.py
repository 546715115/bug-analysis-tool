"""
分析引擎模块测试
"""
import pytest
import pandas as pd
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_loader import get_config_loader
from analyzer import AnalysisEngine


class TestAnalyzer:
    """分析引擎测试类"""

    @pytest.fixture
    def analyzer(self):
        """创建分析引擎实例"""
        config_loader = get_config_loader()
        return AnalysisEngine(config_loader)

    @pytest.fixture
    def sample_data(self):
        """创建测试数据"""
        return pd.DataFrame({
            '问题编号': ['BUG001', 'BUG002', 'BUG003'],
            '问题标题': ['登录失败', '页面卡顿', '数据错误'],
            '严重程度': ['高', '中', '低'],
            '环境': ['测试环境', '生产环境', '测试环境'],
            '状态': ['已关闭', '处理中', '已关闭']
        })

    def test_analyzer_init(self, analyzer):
        """测试分析引擎初始化"""
        assert analyzer is not None
        assert analyzer.config_loader is not None

    def test_get_dimension_summary(self, analyzer, sample_data):
        """测试维度汇总"""
        result = analyzer.get_dimension_summary(sample_data, '严重程度')
        assert result is not None

    def test_cross_analysis(self, analyzer, sample_data):
        """测试交叉分析"""
        # 使用实际的列名
        result = analyzer.cross_analysis(sample_data, '环境', '严重程度')
        assert result is not None

    def test_dimension_summary(self, analyzer, sample_data):
        """测试维度汇总"""
        result = analyzer.get_dimension_summary(sample_data, '严重程度')
        assert result is not None

    def test_hot_values(self, analyzer, sample_data):
        """测试热门值获取"""
        result = analyzer.get_hot_values(sample_data, '严重程度', top_n=3)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
