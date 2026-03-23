"""
可视化模块 - 负责生成各种图表
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional


class Visualizer:
    """可视化器"""

    def __init__(self, config_loader):
        self.config_loader = config_loader

    def create_heatmap(self, cross_tab: pd.DataFrame, title: str = "热力图") -> go.Figure:
        """
        创建热力图

        Args:
            cross_tab: 交叉分析表
            title: 图表标题

        Returns:
            Plotly图形对象
        """
        # 移除"合计"行和列用于热力图
        data = cross_tab.copy()
        if '合计' in data.index:
            data = data.drop('合计')
        if '合计' in data.columns:
            data = data.drop('合计', axis=1)

        if data.empty:
            fig = go.Figure()
            fig.add_annotation(text="无数据", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig

        fig = px.imshow(
            data,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdYlGn_r",
            title=title
        )

        fig.update_layout(
            height=500,
            xaxis_title="",
            yaxis_title=""
        )

        return fig

    def create_stacked_bar(self, df: pd.DataFrame, x_dim: str, y_dim: str = None,
                          color_dim: str = None, title: str = "堆叠柱状图") -> go.Figure:
        """
        创建堆叠柱状图

        Args:
            df: 数据DataFrame
            x_dim: X轴维度
            y_dim: Y轴维度（计数）
            color_dim: 颜色分组维度
            title: 图表标题

        Returns:
            Plotly图形对象
        """
        if color_dim and color_dim in df.columns:
            # 使用plotly自动聚合
            fig = px.bar(
                df,
                x=x_dim,
                color=color_dim,
                title=title,
                barmode='stack'
            )
        else:
            # 手动计算聚合
            grouped = df.groupby(x_dim).size().reset_index(name='数量')
            fig = px.bar(grouped, x=x_dim, y='数量', title=title)

        fig.update_layout(
            height=500,
            xaxis_title=x_dim,
            yaxis_title="数量",
            xaxis_tickangle=-45
        )

        return fig

    def create_pie_chart(self, df: pd.DataFrame, dimension: str, title: str = None) -> go.Figure:
        """
        创建饼图

        Args:
            df: 数据DataFrame
            dimension: 分析维度
            title: 图表标题

        Returns:
            Plotly图形对象
        """
        if dimension not in df.columns:
            fig = go.Figure()
            return fig

        counts = df[dimension].value_counts().reset_index()
        counts.columns = [dimension, '数量']

        title = title or f"{dimension}分布"

        fig = px.pie(
            counts,
            values='数量',
            names=dimension,
            title=title,
            hole=0.4
        )

        fig.update_traces(textposition='inside', textinfo='percent+label')

        return fig

    def create_trend_line(self, trend_data: pd.DataFrame, title: str = "趋势图") -> go.Figure:
        """
        创建趋势折线图

        Args:
            trend_data: 趋势数据（index为时间）
            title: 图表标题

        Returns:
            Plotly图形对象
        """
        if trend_data.empty:
            fig = go.Figure()
            fig.add_annotation(text="无数据", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            return fig

        fig = px.line(
            trend_data,
            x=trend_data.index,
            y=trend_data.columns,
            title=title,
            markers=True
        )

        fig.update_layout(
            height=400,
            xaxis_title="时间",
            yaxis_title="数量",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        return fig

    def create_summary_cards(self, df: pd.DataFrame, dimension: str) -> List[Dict]:
        """
        创建数据摘要卡片

        Args:
            df: 数据DataFrame
            dimension: 维度

        Returns:
            卡片数据列表
        """
        if dimension not in df.columns:
            return []

        total = len(df)
        unique_count = df[dimension].nunique()
        top_values = df[dimension].value_counts().head(5)

        return [
            {
                "title": f"总问题数",
                "value": f"{total}",
                "icon": "📊"
            },
            {
                "title": f"{dimension}类别数",
                "value": f"{unique_count}",
                "icon": "📁"
            },
            {
                "title": f"TOP1 {dimension}",
                "value": f"{top_values.index[0] if len(top_values) > 0 else 'N/A'}",
                "sub_value": f"({top_values.iloc[0] if len(top_values) > 0 else 0}个)",
                "icon": "🏆"
            }
        ]

    def create_severity_gauge(self, rate: float, title: str = "严重问题占比") -> go.Figure:
        """
        创建严重程度仪表盘

        Args:
            rate: 严重问题占比
            title: 标题

        Returns:
            Plotly图形对象
        """
        # 确定颜色
        if rate >= 30:
            color = "red"
        elif rate >= 15:
            color = "orange"
        else:
            color = "green"

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=rate,
            title={'text': title},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 15], 'color': "lightgreen"},
                    {'range': [15, 30], 'color': "lightyellow"},
                    {'range': [30, 100], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 2},
                    'thickness': 0.75,
                    'value': rate
                }
            }
        ))

        fig.update_layout(height=300)

        return fig

    def create_data_table(self, df: pd.DataFrame, title: str = "数据表") -> go.Figure:
        """
        创建数据表格

        Args:
            df: 数据DataFrame
            title: 标题

        Returns:
            Plotly图形对象
        """
        # 格式化数据用于显示
        df_display = df.copy()

        fig = go.Figure(data=[go.Table(
            header=dict(
                values=list(df_display.columns),
                fill_color='#4472C4',
                font=dict(color='white', size=12),
                align='center',
                height=30
            ),
            cells=dict(
                values=[df_display[col] for col in df_display.columns],
                fill_color=[['white', '#f0f0f0'] * len(df_display)],
                align='center',
                height=25,
                font=dict(size=11)
            )
        )])

        fig.update_layout(title=title, height=400)

        return fig
