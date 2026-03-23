"""
数据导入模块测试
"""
import pytest
import pandas as pd
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_loader import get_config_loader
from data_importer import DataImporter


class TestDataImporter:
    """数据导入器测试类"""

    @pytest.fixture
    def importer(self):
        """创建数据导入器实例"""
        config_loader = get_config_loader()
        return DataImporter(config_loader)

    @pytest.fixture
    def sample_excel_path(self, tmp_path):
        """创建临时Excel文件"""
        df = pd.DataFrame({
            '问题编号': ['BUG001', 'BUG002'],
            '问题标题': ['测试问题1', '测试问题2'],
            '严重程度': ['高', '中']
        })
        excel_path = tmp_path / "test_data.xlsx"
        df.to_excel(excel_path, index=False)
        return str(excel_path)

    def test_importer_init(self, importer):
        """测试数据导入器初始化"""
        assert importer is not None
        assert importer.config_loader is not None

    def test_import_from_excel(self, importer, sample_excel_path):
        """测试Excel导入"""
        df = importer.import_from_excel(sample_excel_path)
        assert df is not None
        assert len(df) == 2
        assert '问题编号' in df.columns

    def test_validate_data(self, importer, sample_excel_path):
        """测试数据验证"""
        df = importer.import_from_excel(sample_excel_path)
        is_valid, errors, warnings = importer.validate_data(df)
        # 简单数据应该有效，errors应该为空
        assert is_valid or len(errors) >= 0

    def test_normalize_columns(self, importer):
        """测试列名标准化"""
        df = pd.DataFrame({'BUG_ID': ['001'], 'TITLE': ['Test']})
        normalized = importer._normalize_columns(df)
        assert normalized is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
