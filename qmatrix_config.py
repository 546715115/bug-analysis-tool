"""
Q-Matrix 数据分析引擎 - 核心数据模型
定义系统核心字段结构和配置
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import yaml
from pathlib import Path


class IssueType(Enum):
    """问题类型枚举"""
    FUNCTION = "function"          # 功能缺陷
    PERFORMANCE = "performance"    # 性能问题
    RELIABILITY = "reliability"   # 可靠性问题
    COMPATIBILITY = "compatibility"  # 兼容性问题
    SECURITY = "security"          # 安全问题
    UI = "ui"                     # 界面问题
    DATA = "data"                 # 数据问题
    FLOW = "flow"                 # 流程问题
    REQUIREMENT = "requirement"   # 需求遗漏
    OTHER = "other"               # 其他


class DiscoveryStage(Enum):
    """发现阶段枚举"""
    TEST = "test"           # 测试环境
    GRAY = "gray"          # 灰度环境
    PROD = "prod"          # 现网环境
    HCSO = "hcso"          # HCSO
    PARTNER = "partner"    # 合营云
    PRIVATE = "private"     # 私有化部署
    PREPUB = "prepub"      # 预发布环境
    UAT = "uat"            # UAT环境


class Severity(Enum):
    """影响程度枚举 (爆炸半径)"""
    P0 = "P0"      # 致命
    P1 = "P1"      # 严重
    P2 = "P2"      # 一般
    P3 = "P3"      # 提示
    P4 = "P4"      # P4事件单
    P4A = "P4A"    # P4A事件单


@dataclass
class QMatrixField:
    """Q-Matrix 字段定义"""
    key: str                      # 字段唯一标识
    name: str                      # 显示名称
    field_type: str                # 字段类型: select/multi_select/text/number/date
    options: List[Dict] = field(default_factory=list)  # 选项列表
    required: bool = False         # 是否必填
    customizable: bool = True     # 是否可自定义
    description: str = ""         # 字段描述
    analysis_enabled: bool = True # 是否参与分析


@dataclass
class QMatrixSchema:
    """Q-Matrix 数据模式定义"""

    # === 基础标记层 ===
    business_type: QMatrixField = field(default_factory=lambda: QMatrixField(
        key="business_type",
        name="业务场景分类",
        field_type="select",
        description="问题所属的业务模块",
        analysis_enabled=True
    ))

    issue_type: QMatrixField = field(default_factory=lambda: QMatrixField(
        key="issue_type",
        name="问题类型",
        field_type="multi_select",
        description="功能类/性能类/可靠性类等",
        analysis_enabled=True
    ))

    # === 发现节点层 ===
    discovery_stage: QMatrixField = field(default_factory=lambda: QMatrixField(
        key="discovery_stage",
        name="发现阶段",
        field_type="select",
        description="测试环境/灰度环境/HSO/恒云环境等",
        analysis_enabled=True
    ))

    # === 爆炸半径层 (影响面) ===
    severity: QMatrixField = field(default_factory=lambda: QMatrixField(
        key="severity",
        name="影响程度",
        field_type="select",
        description="提示/一般/重要/严重/致命/P1/P4/P4A",
        analysis_enabled=True
    ))

    # === 深度下钻层 (核心分析源) ===
    dev_root_cause: QMatrixField = field(default_factory=lambda: QMatrixField(
        key="dev_root_cause",
        name="开发根因分析",
        field_type="text",
        description="开发人员从代码层面总结的底层原因",
        analysis_enabled=True
    ))

    test_review: QMatrixField = field(default_factory=lambda: QMatrixField(
        key="test_review",
        name="测试分析与复盘",
        field_type="text",
        description="测试人员基于客户场景复盘的漏测原因及场景缺失分析",
        analysis_enabled=True
    ))

    leak_analysis: QMatrixField = field(default_factory=lambda: QMatrixField(
        key="leak_analysis",
        name="漏测分析",
        field_type="select",
        description="为何在测试阶段未发现",
        analysis_enabled=True
    ))

    # === 基础信息层 ===
    bug_id: QMatrixField = field(default_factory=lambda: QMatrixField(
        key="bug_id",
        name="问题编号",
        field_type="text",
        required=True,
        analysis_enabled=False
    ))

    title: QMatrixField = field(default_factory=lambda: QMatrixField(
        key="title",
        name="问题标题",
        field_type="text",
        required=True,
        analysis_enabled=False
    ))

    create_time: QMatrixField = field(default_factory=lambda: QMatrixField(
        key="create_time",
        name="创建时间",
        field_type="date",
        analysis_enabled=True
    ))

    status: QMatrixField = field(default_factory=lambda: QMatrixField(
        key="status",
        name="状态",
        field_type="select",
        analysis_enabled=True
    ))

    @classmethod
    def from_config(cls, config: Dict) -> 'QMatrixSchema':
        """从配置文件加载模式"""
        # 简化实现，实际可从 YAML 加载完整配置
        return cls()

    def get_analysis_fields(self) -> List[QMatrixField]:
        """获取所有参与分析的字段"""
        fields = []
        for field_name in dir(self):
            if not field_name.startswith('_'):
                field = getattr(self, field_name)
                if isinstance(field, QMatrixField) and field.analysis_enabled:
                    fields.append(field)
        return fields

    def get_required_fields(self) -> List[QMatrixField]:
        """获取必填字段"""
        fields = []
        for field_name in dir(self):
            if not field_name.startswith('_'):
                field = getattr(self, field_name)
                if isinstance(field, QMatrixField) and field.required:
                    fields.append(field)
        return fields


class QMatrixConfig:
    """Q-Matrix 配置管理器"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent / "config" / "dimensions_config.yaml"
        self.config_path = Path(config_path)
        self._config = self._load_config()

    def _load_config(self) -> Dict:
        """加载配置文件"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def get_dimensions(self) -> Dict:
        """获取维度配置"""
        return self._config.get('dimensions', {})

    def get_field_mapping(self) -> Dict:
        """获取字段映射配置"""
        return self._config.get('field_mapping', {})

    def get_all_fields(self) -> List[QMatrixField]:
        """获取所有字段定义"""
        fields = []
        dimensions = self.get_dimensions()

        for key, config in dimensions.items():
            field = QMatrixField(
                key=key,
                name=config.get('name', key),
                field_type=config.get('type', 'text'),
                options=config.get('options', []),
                customizable=config.get('customizable', True),
                description=config.get('description', ''),
                analysis_enabled=config.get('analysis_enabled', True)
            )
            fields.append(field)

        return fields


# 全局配置实例
_qmatrix_config = None

def get_qmatrix_config() -> QMatrixConfig:
    """获取 Q-Matrix 配置单例"""
    global _qmatrix_config
    if _qmatrix_config is None:
        _qmatrix_config = QMatrixConfig()
    return _qmatrix_config
