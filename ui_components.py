"""
UI组件模块 - 提取共享的UI组件和工具函数
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from typing import List, Dict, Any


def render_stat_card(title: str, value: Any, icon: str = "📊", help_text: str = None):
    """
    渲染统计卡片

    Args:
        title: 卡片标题
        value: 数值
        icon: 图标
        help_text: 提示文字
    """
    col = st.container()
    with col:
        st.metric(label=f"{icon} {title}", value=value, help=help_text)


def render_stats_row(stats: Dict[str, Any]):
    """
    渲染一行统计卡片

    Args:
        stats: 字典，key为标题，value为数值
    """
    cols = st.columns(len(stats))
    for idx, (title, value) in enumerate(stats.items()):
        with cols[idx]:
            render_stat_card(title, value)


def render_dimension_filter(df: pd.DataFrame, dimension_key: str, dimension_label: str):
    """
    渲染维度筛选器

    Returns:
        筛选后的数据
    """
    if dimension_key not in df.columns:
        return df

    options = df[dimension_key].unique().tolist()
    selected = st.multiselect(
        f"筛选 {dimension_label}",
        options=options,
        key=f"filter_{dimension_key}"
    )

    if selected:
        return df[df[dimension_key].isin(selected)]
    return df


def render_bar_chart(data: pd.DataFrame, x_col: str, y_col: str = None, title: str = None, **kwargs):
    """
    渲染柱状图

    Args:
        data: 数据
        x_col: X轴列名
        y_col: Y轴列名（可选，默认计数）
        title: 图表标题
    """
    if y_col:
        fig = px.bar(data, x=x_col, y=y_col, title=title, **kwargs)
    else:
        fig = px.bar(data, x=x_col, title=title, **kwargs)

    fig.update_layout(
        template="plotly_white",
        font=dict(family="Microsoft YaHei, sans-serif"),
        title_font_size=16
    )

    st.plotly_chart(fig, use_container_width=True)


def render_pie_chart(data: pd.DataFrame, names_col: str, values_col: str = None, title: str = None, **kwargs):
    """
    渲染饼图

    Args:
        data: 数据
        names_col: 名称列
        values_col: 数值列（可选，默认计数）
        title: 图表标题
    """
    if values_col:
        fig = px.pie(data, names=names_col, values=values_col, title=title, **kwargs)
    else:
        fig = px.pie(data, names=names_col, title=title, **kwargs)

    fig.update_layout(
        template="plotly_white",
        font=dict(family="Microsoft YaHei, sans-serif"),
        title_font_size=16
    )

    st.plotly_chart(fig, use_container_width=True)


def render_table(data: pd.DataFrame, page_size: int = 10):
    """
    渲染数据表格（带分页）

    Args:
        data: 数据
        page_size: 每页行数
    """
    total_rows = len(data)
    total_pages = (total_rows // page_size) + (1 if total_rows % page_size > 0 else 0)

    if total_pages > 1:
        page = st.number_input(
            "页码",
            min_value=1,
            max_value=total_pages,
            value=1,
            key="table_page"
        )
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_rows)
        display_data = data.iloc[start_idx:end_idx]
    else:
        display_data = data

    st.dataframe(display_data, use_container_width=True)

    if total_pages > 1:
        st.caption(f"显示 {start_idx+1}-{end_idx} 行，共 {total_rows} 行")


def render_download_button(data: pd.DataFrame, filename: str, label: str = "下载数据"):
    """
    渲染下载按钮

    Args:
        data: 数据
        filename: 下载文件名
        label: 按钮标签
    """
    csv = data.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label=label,
        data=csv,
        file_name=filename,
        mime="text/csv"
    )


def render_data_preview(df: pd.DataFrame, max_rows: int = 5, expanded: bool = True):
    """
    渲染数据预览

    Args:
        df: 数据
        max_rows: 预览行数
        expanded: 是否展开
    """
    with st.expander(f"数据预览（前{max_rows}行）", expanded=expanded):
        st.dataframe(df.head(max_rows), use_container_width=True)
        st.caption(f"共 {len(df)} 行，{len(df.columns)} 列")


def render_empty_data_message(message: str = "请先导入数据"):
    """
    渲染空数据提示

    Args:
        message: 提示信息
    """
    st.warning(f"⚠️ {message}")
    return None


def render_error_message(error: str):
    """
    渲染错误消息

    Args:
        error: 错误信息
    """
    st.error(f"❌ 错误: {error}")


def render_success_message(message: str):
    """
    渲染成功消息

    Args:
        message: 成功信息
    """
    st.success(f"✅ {message}")
