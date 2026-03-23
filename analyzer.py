"""
分析引擎模块 - 负责多维交叉分析
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import plotly.express as px
import plotly.graph_objects as go


class AnalysisEngine:
    """分析引擎"""

    # 常量定义，消除魔法字符串
    SEVERE_PATTERNS = ['P0', 'P1', '致命', '严重']
    PROD_PATTERNS = ['prod', '现网', '生产', '正式']
    TEST_PATTERNS = ['test', '测试', 'uat', 'UAT']

    def __init__(self, config_loader):
        self.config_loader = config_loader

    def _is_severe_issue(self, severity: str) -> bool:
        """判断是否为严重问题（P0/P1）"""
        if pd.isna(severity):
            return False
        severity_str = str(severity)
        return any(pattern in severity_str for pattern in self.SEVERE_PATTERNS)

    def _is_production_environment(self, env: str) -> bool:
        """判断是否为生产环境"""
        if pd.isna(env):
            return False
        env_str = str(env)
        return any(pattern in env_str.lower() for pattern in self.PROD_PATTERNS)

    def _is_test_environment(self, env: str) -> bool:
        """判断是否为测试环境"""
        if pd.isna(env):
            return False
        env_str = str(env)
        return any(pattern in env_str.lower() for pattern in self.TEST_PATTERNS)

    def _get_severe_issues(self, df: pd.DataFrame, severity_col: str = 'severity') -> pd.DataFrame:
        """获取严重问题子集"""
        return df[df[severity_col].apply(self._is_severe_issue)]

    def _get_prod_issues(self, df: pd.DataFrame, env_col: str = 'environment') -> pd.DataFrame:
        """获取生产环境问题子集"""
        return df[df[env_col].apply(self._is_production_environment)]

    def _get_test_issues(self, df: pd.DataFrame, env_col: str = 'environment') -> pd.DataFrame:
        """获取测试环境问题子集"""
        return df[df[env_col].apply(self._is_test_environment)]

    def cross_analysis(self, df: pd.DataFrame, row_dim: str, col_dim: str,
                       filters: Optional[Dict[str, List]] = None) -> pd.DataFrame:
        """
        交叉分析 - 两个维度的交叉统计

        Args:
            df: 数据DataFrame
            row_dim: 竖轴维度（行维度）
            col_dim: 横轴维度（列维度）
            filters: 筛选条件 {维度: [可选值]}

        Returns:
            交叉分析表
        """
        # 验证维度列存在
        if row_dim not in df.columns or col_dim not in df.columns:
            return pd.DataFrame()

        # 应用筛选
        df_filtered = self._apply_filters(df, filters)

        # 创建交叉表
        cross_tab = pd.crosstab(
            df_filtered[row_dim],
            df_filtered[col_dim],
            margins=True,
            margins_name='合计'
        )

        return cross_tab

    def multi_dim_analysis(self, df: pd.DataFrame, dimensions: List[str],
                          values: str = None, aggfunc: str = 'count') -> pd.DataFrame:
        """
        多维分析 - 支持任意维度组合

        Args:
            df: 数据DataFrame
            dimensions: 维度列表
            values: 值字段（用于聚合）
            aggfunc: 聚合函数

        Returns:
            分析结果表
        """
        # 过滤掉没有数据的维度
        valid_dims = [d for d in dimensions if d in df.columns]

        if not valid_dims:
            return pd.DataFrame()

        if values and values in df.columns:
            # 分组聚合
            result = df.groupby(valid_dims)[values].agg(aggfunc).reset_index()
        else:
            # 仅计数
            result = df.groupby(valid_dims).size().reset_index(name='数量')

        return result

    def get_dimension_summary(self, df: pd.DataFrame, dimension: str) -> Dict:
        """
        获取某个维度的统计摘要

        Args:
            df: 数据DataFrame
            dimension: 维度字段

        Returns:
            统计摘要字典
        """
        if dimension not in df.columns:
            return {}

        counts = df[dimension].value_counts()
        total = len(df)

        return {
            'total': total,
            'unique_count': len(counts),
            'distribution': counts.to_dict(),
            'top_values': counts.head(10).to_dict()
        }

    def environment_leak_analysis(self, df: pd.DataFrame, business_dim: str = 'business_type',
                                   env_dim: str = 'environment') -> pd.DataFrame:
        """
        环境漏出分析 - 计算各环境问题占比

        Args:
            df: 数据DataFrame
            business_dim: 业务维度
            env_dim: 环境维度

        Returns:
            漏出分析表
        """
        if business_dim not in df.columns or env_dim not in df.columns:
            return pd.DataFrame()

        # 各业务在各环境的问题数
        cross = pd.crosstab(df[business_dim], df[env_dim])

        # 计算各环境的占比
        cross_pct = cross.div(cross.sum(axis=1), axis=0) * 100

        # 计算测试环境问题占比（测试质量指标）
        # 匹配 "测试"、"test"、"Test" 等
        test_cols = [c for c in cross.columns if 'test' in c.lower() or '测试' in c]

        if test_cols:
            test_leak = cross[test_cols].sum(axis=1)
            total = cross.sum(axis=1)
            # 避免除零错误
            leak_rate = ((total - test_leak) / total.replace(0, pd.NA) * 100).round(2)

            # 添加漏出率
            result = cross.copy()
            result['测试环境问题数'] = test_leak
            result['总问题数'] = total
            result['现网漏出率(%)'] = leak_rate

            return result

        return cross

    def severity_distribution(self, df: pd.DataFrame, row_dim: str = 'business_type',
                             severity_dim: str = 'severity') -> pd.DataFrame:
        """
        严重程度分布分析

        Args:
            df: 数据DataFrame
            row_dim: 维度（业务类型等）
            severity_dim: 严重程度维度

        Returns:
            严重程度分布表
        """
        if row_dim not in df.columns or severity_dim not in df.columns:
            return pd.DataFrame()

        cross = pd.crosstab(df[row_dim], df[severity_dim], margins=True)

        # 计算严重问题占比（P0+P1）
        severity_cols = [c for c in cross.columns if c != 'All']
        severe_cols = [c for c in severity_cols if 'P0' in str(c) or 'P1' in str(c) or '致命' in str(c) or '严重' in str(c)]

        if severe_cols and 'All' in cross.columns:
            severe_count = cross[severe_cols].sum(axis=1)
            total = cross['All']
            # 避免除零错误
            severe_rate = ((severe_count / total.replace(0, pd.NA)) * 100).round(2)

            result = cross.copy()
            result['严重问题数'] = severe_count
            result['严重问题占比(%)'] = severe_rate
            return result

        return cross

    def trend_analysis(self, df: pd.DataFrame, time_dim: str = 'create_time',
                       group_dim: str = 'bug_type') -> pd.DataFrame:
        """
        趋势分析 - 按时间分组统计

        Args:
            df: 数据DataFrame
            time_dim: 时间维度
            group_dim: 分组维度

        Returns:
            趋势数据表
        """
        if time_dim not in df.columns:
            return pd.DataFrame()

        # 转换时间列
        df_copy = df.copy()
        df_copy[time_dim] = pd.to_datetime(df_copy[time_dim], errors='coerce')
        df_copy = df_copy.dropna(subset=[time_dim])

        if group_dim not in df_copy.columns:
            group_dim = None

        # 按月统计
        df_copy['month'] = df_copy[time_dim].dt.to_period('M').astype(str)

        if group_dim:
            result = df_copy.groupby(['month', group_dim]).size().reset_index(name='数量')
            result = result.pivot(index='month', columns=group_dim, values='数量').fillna(0)
        else:
            result = df_copy.groupby('month').size().reset_index(name='数量')
            result = result.set_index('month')

        return result

    def get_hot_values(self, df: pd.DataFrame, dimension: str, top_n: int = 5) -> List[Tuple]:
        """
        获取某个维度的高频值

        Args:
            df: 数据DataFrame
            dimension: 维度字段
            top_n: 返回前N个

        Returns:
            [(值, 数量), ...] 列表
        """
        if dimension not in df.columns:
            return []

        counts = df[dimension].value_counts().head(top_n)
        return list(zip(counts.index, counts.values))

    def _apply_filters(self, df: pd.DataFrame, filters: Optional[Dict[str, List]]) -> pd.DataFrame:
        """应用筛选条件"""
        if not filters:
            return df

        df_filtered = df.copy()

        for dim, values in filters.items():
            if dim in df_filtered.columns and values:
                df_filtered = df_filtered[df_filtered[dim].isin(values)]

        return df_filtered

    def get_filter_options(self, df: pd.DataFrame, dimension: str) -> List:
        """获取某个维度的所有可选值"""
        if dimension not in df.columns:
            return []

        return sorted(df[dimension].dropna().unique().tolist())

    def root_cause_analysis(self, df: pd.DataFrame, row_dim: str = 'business_type',
                           root_cause_dim: str = 'root_cause') -> pd.DataFrame:
        """
        根因分析 - 分析各业务/模块的问题根因分布

        Args:
            df: 数据DataFrame
            row_dim: 行维度（如业务模块）
            root_cause_dim: 根因维度

        Returns:
            根因分析表
        """
        if row_dim not in df.columns or root_cause_dim not in df.columns:
            return pd.DataFrame()

        # 创建交叉表
        cross = pd.crosstab(df[row_dim], df[root_cause_dim], margins=True)

        # 计算各类根因占比
        root_cause_cols = [c for c in cross.columns if c != 'All' and c != '合计']
        if root_cause_cols and 'All' in cross.columns:
            for col in root_cause_cols:
                cross[f'{col}_占比(%)'] = (cross[col] / cross['All'] * 100).round(2)

        return cross

    def leak_analysis(self, df: pd.DataFrame, business_dim: str = 'business_type',
                     leak_dim: str = 'leak_analysis',
                     leak_type_dim: str = 'leak_analysis_type') -> Dict:
        """
        漏测分析 - 分析漏测的原因和问题类型

        Args:
            df: 数据DataFrame
            business_dim: 业务维度
            leak_dim: 漏测分析维度
            leak_type_dim: 漏测问题类型维度

        Returns:
            漏测分析结果字典
        """
        result = {}

        # 漏测原因分布
        if leak_dim in df.columns:
            leak_dist = df[leak_dim].value_counts()
            result['漏测原因分布'] = leak_dist

        # 漏测问题类型分布
        if leak_type_dim in df.columns:
            leak_type_dist = df[leak_type_dim].value_counts()
            result['漏测问题类型分布'] = leak_type_dist

        # 漏测 × 业务 交叉分析
        if leak_dim in df.columns and business_dim in df.columns:
            cross = pd.crosstab(df[business_dim], df[leak_dim], margins=True)
            result['漏测业务交叉'] = cross

        # 漏测 × 漏测问题类型 交叉分析
        if leak_dim in df.columns and leak_type_dim in df.columns:
            cross2 = pd.crosstab(df[leak_dim], df[leak_type_dim], margins=True)
            result['漏测类型交叉'] = cross2

        # 计算漏测率（现网问题 / 总问题）
        if 'environment' in df.columns:
            prod_issues = df[df['environment'].astype(str).str.contains('prod|现网', case=False, na=False)]
            total_issues = len(df)
            prod_count = len(prod_issues)

            if total_issues > 0:
                result['漏测率'] = round(prod_count / total_issues * 100, 2)
            else:
                result['漏测率'] = 0

            result['现网问题数'] = prod_count
            result['总问题数'] = total_issues

        return result

    def generate_summary(self, df: pd.DataFrame) -> str:
        """
        自动生成汇总分析报告

        Args:
            df: 数据DataFrame

        Returns:
            汇总分析报告文本
        """
        summary_parts = []

        # 1. 基本统计
        total_count = len(df)
        summary_parts.append(f"## 一、基本统计\n")
        summary_parts.append(f"- 本期共发现 **{total_count}** 个问题")

        # 2. 严重程度分布
        if 'severity' in df.columns:
            severe_issues = df[df['severity'].astype(str).str.contains('P0|P1|致命|严重', case=False, na=False)]
            severe_count = len(severe_issues)
            severe_rate = round(severe_count / total_count * 100, 2) if total_count > 0 else 0
            summary_parts.append(f"\n## 二、严重程度\n")
            summary_parts.append(f"- 严重问题（P0+P1）：**{severe_count}** 个（{severe_rate}%）")

            # 按严重程度分组统计
            severity_dist = df['severity'].value_counts()
            summary_parts.append(f"\n严重程度分布：")
            for sev, count in severity_dist.items():
                rate = round(count / total_count * 100, 2)
                summary_parts.append(f"  - {sev}: {count} 个（{rate}%）")

        # 3. 根因分析
        if 'root_cause' in df.columns:
            summary_parts.append(f"\n## 三、根因分析\n")
            root_cause_dist = df['root_cause'].value_counts()
            top_root_cause = root_cause_dist.head(3)

            summary_parts.append(f"主要根因分布（Top3）：")
            for cause, count in top_root_cause.items():
                rate = round(count / total_count * 100, 2)
                summary_parts.append(f"  - {cause}: {count} 个（{rate}%）")

            # 根因 × 业务模块分析
            if 'business_type' in df.columns:
                root_business = pd.crosstab(df['root_cause'], df['business_type'])
                max_cause = root_cause_dist.idxmax()
                if max_cause in root_business.index:
                    max_business = root_business.loc[max_cause].idxmax()
                    summary_parts.append(f"\n根因最严重的业务模块：**{max_business}**（{max_cause}类问题最多）")

        # 4. 漏测分析
        if 'environment' in df.columns:
            summary_parts.append(f"\n## 四、漏测分析\n")
            prod_issues = df[df['environment'].astype(str).str.contains('prod|现网', case=False, na=False)]
            prod_count = len(prod_issues)
            leak_rate = round(prod_count / total_count * 100, 2) if total_count > 0 else 0

            summary_parts.append(f"- 现网暴露问题：**{prod_count}** 个")
            summary_parts.append(f"- 漏测率：**{leak_rate}%**")

            # 漏测原因分析
            if 'leak_analysis' in df.columns:
                leak_prod = prod_issues['leak_analysis'].value_counts()
                top_leak = leak_prod.head(3)
                summary_parts.append(f"\n漏测主要原因（Top3）：")
                for leak_cause, count in top_leak.items():
                    rate = round(count / prod_count * 100, 2) if prod_count > 0 else 0
                    summary_parts.append(f"  - {leak_cause}: {count} 个（{rate}%）")

        # 5. 回归问题
        if 'is_regression' in df.columns:
            regression_issues = df[df['is_regression'].astype(str).str.contains('yes|是', case=False, na=False)]
            regression_count = len(regression_issues)
            if regression_count > 0:
                regression_rate = round(regression_count / total_count * 100, 2)
                summary_parts.append(f"\n## 五、回归问题\n")
                summary_parts.append(f"- 回归问题：**{regression_count}** 个（{regression_rate}%）")
                summary_parts.append(f"- 建议：加强回归测试覆盖")

        # 6. 改进建议
        summary_parts.append(f"\n## 六、改进建议\n")

        # 根据分析自动生成建议
        if 'root_cause' in df.columns:
            root_cause_dist = df['root_cause'].value_counts()
            if not root_cause_dist.empty:
                main_cause = root_cause_dist.idxmax()
                if main_cause == 'development':
                    summary_parts.append(f"1. **开发层面**：加强代码评审，重点关注逻辑边界和异常处理")
                elif main_cause == 'requirement':
                    summary_parts.append(f"1. **需求层面**：完善需求评审机制，确保需求描述清晰完整")
                elif main_cause == 'design':
                    summary_parts.append(f"1. **设计层面**：加强架构设计评审，充分考虑边界场景")
                elif main_cause == 'test':
                    summary_parts.append(f"1. **测试层面**：增加测试用例覆盖，特别是边界条件")

        if 'leak_analysis' in df.columns and 'environment' in df.columns:
            prod_issues = df[df['environment'].astype(str).str.contains('prod|现网', case=False, na=False)]
            if len(prod_issues) > 0:
                summary_parts.append(f"2. **漏测改进**：针对现网暴露的 {len(prod_issues)} 个问题，分析漏测原因，补充相关测试用例")

        if 'is_regression' in df.columns:
            regression_count = len(df[df['is_regression'].astype(str).str.contains('yes|是', case=False, na=False)])
            if regression_count > 0:
                summary_parts.append(f"3. **回归测试**：建立完善的回归测试机制，避免相同问题重复出现")

        summary_parts.append(f"4. **长效机制**：建立问题根因追踪机制，定期回顾分析，持续改进质量")

        return '\n'.join(summary_parts)

    def regression_analysis(self, df: pd.DataFrame, dimension: str = 'business_type') -> pd.DataFrame:
        """
        回归问题分析

        Args:
            df: 数据DataFrame
            dimension: 分析维度

        Returns:
            回归问题分析表
        """
        if 'is_regression' not in df.columns or dimension not in df.columns:
            return pd.DataFrame()

        # 筛选回归问题
        regression_df = df[df['is_regression'].astype(str).str.contains('yes|是', case=False, na=False)]

        if regression_df.empty:
            return pd.DataFrame()

        # 按维度统计回归问题
        result = pd.crosstab(regression_df[dimension], regression_df['is_regression'], margins=True)
        result.columns = ['回归问题数', '合计']

        # 添加占比
        total_by_dim = df.groupby(dimension).size()
        regression_by_dim = regression_df.groupby(dimension).size()
        result['总问题数'] = total_by_dim
        result['回归占比(%)'] = (regression_by_dim / total_by_dim * 100).round(2)

        return result
