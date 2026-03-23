"""
Q-Matrix 分析引擎 - 核心分析逻辑
实现浅层矩阵 + 深层归因 + 改进建议生成
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import re
from collections import Counter


@dataclass
class MatrixCell:
    """矩阵单元格数据"""
    row_key: str
    col_key: str
    count: int
    percentage: float
    severity_distribution: Dict[str, int]
    sample_bug_ids: List[str]


@dataclass
class HotspotData:
    """热点区域数据"""
    dimension_pair: Tuple[str, str]
    top_cells: List[MatrixCell]
    total_issues: int
    severity_breakdown: Dict[str, int]
    risk_level: str  # high/medium/low


@dataclass
class RootCauseInsight:
    """根因洞察"""
    category: str
    description: str
    frequency: int
    related_modules: List[str]
    code_patterns: List[str]
    confidence: float  # 0-1


@dataclass
class ImprovementSuggestion:
    """改进建议"""
    category: str  # test_case/code_refactor/performance/investigation
    priority: str  # high/medium/low
    title: str
    description: str
    affected_modules: List[str]
    estimated_effort: str  # small/medium/large
    actionable_steps: List[str]


class QMatrixEngine:
    """Q-Matrix 分析引擎"""

    def __init__(self, df: pd.DataFrame, config: Dict = None):
        """
        初始化分析引擎

        Args:
            df: 问题单数据 DataFrame
            config: 配置字典
        """
        self.df = df
        self.config = config or {}
        self._prepare_data()

    def _prepare_data(self):
        """准备数据，标准化列名"""
        # 确保必要列存在
        self.normalized_cols = {}

        # 业务场景列
        for col in ['业务模块', '业务类型', 'business_type', '模块', 'module']:
            if col in self.df.columns:
                self.normalized_cols['business_type'] = col
                break

        # 问题类型列
        for col in ['问题类型', 'issue_type', 'type', 'bug_type']:
            if col in self.df.columns:
                self.normalized_cols['issue_type'] = col
                break

        # 发现环境列
        for col in ['发现环境', 'environment', 'env', '发现阶段']:
            if col in self.df.columns:
                self.normalized_cols['environment'] = col
                break

        # 严重程度列
        for col in ['影响程度', '严重程度', 'severity', 'level', 'priority']:
            if col in self.df.columns:
                self.normalized_cols['severity'] = col
                break

        # 根因分析列
        for col in ['根因详细', 'root_cause_detail', '开发根因分析', '根因描述']:
            if col in self.df.columns:
                self.normalized_cols['dev_root_cause'] = col
                break

        # 漏测分析列
        for col in ['漏测分析', 'leak_analysis', '测试分析与复盘', '测试复盘']:
            if col in self.df.columns:
                self.normalized_cols['leak_analysis'] = col
                break

        # 问题编号列
        for col in ['问题单号', 'BUG编号', 'bug_id', 'id']:
            if col in self.df.columns:
                self.normalized_cols['bug_id'] = col
                break

    def _get_col(self, field: str) -> Optional[str]:
        """获取标准化后的列名"""
        return self.normalized_cols.get(field)

    # ==================== 浅层矩阵分析 ====================

    def build_matrix(self, row_dim: str, col_dim: str) -> pd.DataFrame:
        """
        构建交叉矩阵

        Args:
            row_dim: 行维度（字段名）
            col_dim: 列维度（字段名）

        Returns:
            交叉统计矩阵
        """
        row_col = self._get_col(row_dim) or row_dim
        col_col = self._get_col(col_dim) or col_dim

        if row_col not in self.df.columns or col_col not in self.df.columns:
            return pd.DataFrame()

        # 构建交叉表
        matrix = pd.crosstab(
            self.df[row_col],
            self.df[col_col],
            margins=True,
            margins_name='合计'
        )

        return matrix

    def get_matrix_with_severity(self, row_dim: str, col_dim: str) -> List[MatrixCell]:
        """
        获取带严重程度分布的矩阵数据

        Returns:
            矩阵单元格列表
        """
        row_col = self._get_col(row_dim) or row_dim
        col_col = self._get_col(col_dim) or col_dim
        severity_col = self._get_col('severity')
        bug_id_col = self._get_col('bug_id')

        if row_col not in self.df.columns or col_col not in self.df.columns:
            return []

        cells = []

        for row_val in self.df[row_col].unique():
            for col_val in self.df[col_col].unique():
                subset = self.df[(self.df[row_col] == row_val) & (self.df[col_col] == col_val)]

                if len(subset) == 0:
                    continue

                # 严重程度分布
                severity_dist = {}
                if severity_col and severity_col in subset.columns:
                    severity_dist = subset[severity_col].value_counts().to_dict()

                # 样本 bug ID
                sample_ids = []
                if bug_id_col and bug_id_col in subset.columns:
                    sample_ids = subset[bug_id_col].head(3).tolist()

                cell = MatrixCell(
                    row_key=str(row_val),
                    col_key=str(col_val),
                    count=len(subset),
                    percentage=len(subset) / len(self.df) * 100,
                    severity_distribution=severity_dist,
                    sample_bug_ids=sample_ids
                )
                cells.append(cell)

        # 按数量排序
        cells.sort(key=lambda x: x.count, reverse=True)
        return cells

    # ==================== 热点区域识别 ====================

    def identify_hotspots(self, row_dim: str = 'business_type',
                          col_dim: str = 'issue_type',
                          top_n: int = 10) -> HotspotData:
        """
        识别热点区域

        Args:
            row_dim: 行维度
            col_dim: 列维度
            top_n: 返回前 N 个热点

        Returns:
            热点区域数据
        """
        cells = self.get_matrix_with_severity(row_dim, col_dim)
        severity_col = self._get_col('severity')

        # 统计严重程度
        severity_breakdown = {}
        if severity_col and severity_col in self.df.columns:
            severity_breakdown = self.df[severity_col].value_counts().to_dict()

        # 计算风险等级
        total_issues = len(self.df)
        high_risk_count = sum(1 for c in cells if any(
            s in ['P0', 'P1', '致命', '严重'] for s in c.severity_distribution.keys()
        ))

        if high_risk_count >= len(cells) * 0.3:
            risk_level = 'high'
        elif high_risk_count >= len(cells) * 0.1:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        return HotspotData(
            dimension_pair=(row_dim, col_dim),
            top_cells=cells[:top_n],
            total_issues=total_issues,
            severity_breakdown=severity_breakdown,
            risk_level=risk_level
        )

    # ==================== 深层归因分析 ====================

    def analyze_root_causes(self, hotspot_cells: List[MatrixCell]) -> List[RootCauseInsight]:
        """
        对热点区域进行深层归因分析

        Args:
            hotspot_cells: 热点单元格列表

        Returns:
            根因洞察列表
        """
        root_cause_col = self._get_col('dev_root_cause')
        leak_analysis_col = self._get_col('leak_analysis')
        bug_id_col = self._get_col('bug_id')

        if not root_cause_col or root_cause_col not in self.df.columns:
            return []

        insights = []

        # 收集所有根因文本
        all_root_causes = []
        bug_ids_by_cell = {}

        for cell in hotspot_cells:
            row_col = self._get_col('business_type')
            col_col = self._get_col('issue_type')

            if row_col and col_col:
                subset = self.df[
                    (self.df[row_col] == cell.row_key) &
                    (self.df[col_col] == cell.col_key)
                ]
                if root_cause_col in subset.columns:
                    texts = subset[root_cause_col].dropna().tolist()
                    all_root_causes.extend(texts)

                    # 记录 bug ID 关联
                    if bug_id_col in subset.columns:
                        bug_ids_by_cell[f"{cell.row_key}_{cell.col_key}"] = \
                            subset[bug_id_col].tolist()

        # 简单关键词提取和分析
        keyword_patterns = {
            'null_pointer': ['空指针', 'NullPointer', 'null', '未判空'],
            'database': ['数据库', 'SQL', '查询', '索引', '事务'],
            'concurrency': ['并发', '线程', '锁', '竞态', '死锁'],
            'memory': ['内存', 'OOM', '溢出', '泄漏'],
            'performance': ['性能', '慢', '超时', '响应时间'],
            'logic': ['逻辑', '判断', '条件', '边界'],
            'interface': ['接口', 'API', '调用', '参数'],
            'config': ['配置', '参数', '开关'],
        }

        keyword_counts = Counter()

        for text in all_root_causes:
            if not isinstance(text, str):
                continue
            for category, keywords in keyword_patterns.items():
                if any(kw in text for kw in keywords):
                    keyword_counts[category] += 1

        # 生成洞察
        for category, count in keyword_counts.most_common(5):
            insight = RootCauseInsight(
                category=category,
                description=self._get_category_description(category),
                frequency=count,
                related_modules=list(set(c.row_key for c in hotspot_cells[:5])),
                code_patterns=keyword_patterns[category],
                confidence=min(count / len(all_root_causes) * 10, 1.0) if all_root_causes else 0
            )
            insights.append(insight)

        return insights

    def _get_category_description(self, category: str) -> str:
        """获取分类描述"""
        descriptions = {
            'null_pointer': '空指针/空值处理不当',
            'database': '数据库操作问题（SQL、索引、事务）',
            'concurrency': '并发/多线程问题',
            'memory': '内存管理问题（溢出、泄漏）',
            'performance': '性能问题（响应时间、超时）',
            'logic': '业务逻辑缺陷',
            'interface': '接口/API调用问题',
            'config': '配置参数问题'
        }
        return descriptions.get(category, category)

    # ==================== 漏测分析 ====================

    def analyze_leak_causes(self) -> Dict[str, Any]:
        """
        分析漏测原因

        Returns:
            漏测分析结果
        """
        leak_col = self._get_col('leak_analysis')

        if not leak_col or leak_col not in self.df.columns:
            return {}

        leak_stats = self.df[leak_col].value_counts().to_dict()

        # 按严重程度交叉分析
        severity_col = self._get_col('severity')
        leak_by_severity = {}

        if severity_col and severity_col in self.df.columns:
            for severity in self.df[severity_col].unique():
                subset = self.df[self.df[severity_col] == severity]
                leak_by_severity[severity] = subset[leak_col].value_counts().to_dict()

        return {
            'overall_distribution': leak_stats,
            'by_severity': leak_by_severity,
            'total_leak_issues': len(self.df[leak_col].dropna())
        }

    # ==================== 改进建议生成 ====================

    def generate_improvements(self, hotspots: HotspotData,
                             root_causes: List[RootCauseInsight]) -> List[ImprovementSuggestion]:
        """
        基于分析结果生成改进建议

        Args:
            hotspots: 热点区域
            root_causes: 根因洞察

        Returns:
            改进建议列表
        """
        suggestions = []

        # 基于根因生成建议
        for insight in root_causes:
            if insight.category == 'null_pointer':
                suggestions.append(ImprovementSuggestion(
                    category='code_refactor',
                    priority='high',
                    title='加强空值校验',
                    description=f'发现 {insight.frequency} 处空指针相关问题，建议在核心模块增加防御性编程',
                    affected_modules=insight.related_modules,
                    estimated_effort='medium',
                    actionable_steps=[
                        '1. 在数据入口处增加非空校验',
                        '2. 使用 Optional 处理可能为空的返回值',
                        '3. 编写空值处理相关的单元测试'
                    ]
                ))

            elif insight.category == 'database':
                suggestions.append(ImprovementSuggestion(
                    category='code_refactor',
                    priority='high',
                    title='优化数据库操作',
                    description=f'发现 {insight.frequency} 处数据库相关问题',
                    affected_modules=insight.related_modules,
                    estimated_effort='large',
                    actionable_steps=[
                        '1. 检查并优化慢 SQL',
                        '2. 添加必要的数据库索引',
                        '3. 检查事务边界是否合理'
                    ]
                ))

            elif insight.category == 'concurrency':
                suggestions.append(ImprovementSuggestion(
                    category='test_case',
                    priority='high',
                    title='增加并发测试用例',
                    description=f'发现 {insight.frequency} 处并发相关问题',
                    affected_modules=insight.related_modules,
                    estimated_effort='medium',
                    actionable_steps=[
                        '1. 设计并发场景测试用例',
                        '2. 使用 JMeter/Locust 进行压力测试',
                        '3. 添加线程安全相关的代码审查检查点'
                    ]
                ))

            elif insight.category == 'performance':
                suggestions.append(ImprovementSuggestion(
                    category='investigation',
                    priority='high',
                    title='性能摸底测试',
                    description=f'发现 {insight.frequency} 处性能问题',
                    affected_modules=insight.related_modules,
                    estimated_effort='large',
                    actionable_steps=[
                        '1. 使用 Profiling 工具定位性能瓶颈',
                        '2. 进行全链路性能测试',
                        '3. 制定性能基线和告警阈值'
                    ]
                ))

        # 基于热点区域生成测试建议
        if hotspots.risk_level == 'high':
            suggestions.append(ImprovementSuggestion(
                category='test_case',
                priority='high',
                title='加强高风险模块测试覆盖',
                description=f'发现 {len(hotspots.top_cells)} 个高风险问题区域',
                affected_modules=[c.row_key for c in hotspots.top_cells[:5]],
                estimated_effort='large',
                actionable_steps=[
                    '1. 对高风险模块进行测试用例补充',
                    '2. 增加边界条件和异常场景测试',
                    '3. 建立回归测试集'
                ]
            ))

        # 基于漏测分析生成建议
        leak_analysis = self.analyze_leak_causes()
        if leak_analysis:
            suggestions.append(ImprovementSuggestion(
                category='test_case',
                priority='medium',
                title='完善测试用例设计',
                description='基于漏测分析结果优化测试策略',
                affected_modules=[],
                estimated_effort='medium',
                actionable_steps=[
                    '1. 分析漏测原因分类',
                    '2. 补充缺失的测试场景',
                    '3. 建立测试用例评审机制'
                ]
            ))

        return suggestions

    # ==================== 综合报告生成 ====================

    def generate_summary(self) -> Dict[str, Any]:
        """
        生成综合分析摘要

        Returns:
            分析摘要
        """
        severity_col = self._get_col('severity')
        env_col = self._get_col('environment')

        summary = {
            'total_issues': len(self.df),
            'severity_distribution': {},
            'environment_distribution': {},
            'business_distribution': {},
            'issue_type_distribution': {}
        }

        if severity_col and severity_col in self.df.columns:
            summary['severity_distribution'] = self.df[severity_col].value_counts().to_dict()

        if env_col and env_col in self.df.columns:
            summary['environment_distribution'] = self.df[env_col].value_counts().to_dict()

        business_col = self._get_col('business_type')
        if business_col and business_col in self.df.columns:
            summary['business_distribution'] = self.df[business_col].value_counts().to_dict()

        issue_col = self._get_col('issue_type')
        if issue_col and issue_col in self.df.columns:
            summary['issue_type_distribution'] = self.df[issue_col].value_counts().to_dict()

        return summary
