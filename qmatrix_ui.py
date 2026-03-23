"""
Q-Matrix 分析引擎 UI 组件
渐进式披露逻辑的可视化界面
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any

from qmatrix_engine import QMatrixEngine, HotspotData, RootCauseInsight, ImprovementSuggestion


def render_qmatrix_header():
    """渲染 Q-Matrix 标题"""
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h1 style="color: #00d4ff; margin: 0; font-size: 28px;">🔷 Q-Matrix 分析引擎</h1>
        <p style="color: #a0a0a0; margin: 10px 0 0 0;">深度挖掘Bug数据，精准定位产品痛点，输出可落地改进措施</p>
    </div>
    """, unsafe_allow_html=True)


def render_progress_indicator(current_step: int):
    """渲染进度指示器"""
    steps = [
        ("1️⃣", "数据导入"),
        ("2️⃣", "浅层矩阵"),
        ("3️⃣", "深层归因"),
        ("4️⃣", "改进建议")
    ]

    cols = st.columns(len(steps))
    for idx, (icon, label) in enumerate(steps):
        with cols[idx]:
            if idx < current_step:
                color = "#00d4ff"
            elif idx == current_step:
                color = "#ff6b6b"
            else:
                color = "#555555"

            st.markdown(f"""
            <div style="text-align: center; color: {color};">
                <div style="font-size: 24px;">{icon}</div>
                <div style="font-size: 12px;">{label}</div>
            </div>
            """, unsafe_allow_html=True)


def render_matrix_visualization(matrix: pd.DataFrame, title: str = "交叉矩阵"):
    """渲染热力图矩阵"""
    if matrix.empty:
        st.warning("暂无数据")
        return

    # 移除合计行和列
    display_matrix = matrix.copy()
    if '合计' in display_matrix.index:
        display_matrix = display_matrix.drop('合计')
    if '合计' in display_matrix.columns:
        display_matrix = display_matrix.drop('合计', axis=1)

    if display_matrix.empty:
        st.warning("数据不足，无法生成矩阵")
        return

    # 创建热力图
    fig = px.imshow(
        display_matrix,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Blues",
        title=title
    )

    fig.update_layout(
        template="plotly_white",
        font=dict(family="Microsoft YaHei, sans-serif"),
        xaxis_title="",
        yaxis_title="",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)


def render_hotspot_summary(hotspot: HotspotData):
    """渲染热点区域摘要"""
    risk_colors = {
        'high': '#ff4757',
        'medium': '#ffa502',
        'low': '#2ed573'
    }

    risk_color = risk_colors.get(hotspot.risk_level, '#999')

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("总问题数", hotspot.total_issues)

    with col2:
        st.metric("热点单元格", len(hotspot.top_cells))

    with col3:
        st.markdown(f"""
        <div style="background: {risk_color}; padding: 10px; border-radius: 5px; text-align: center; color: white; font-weight: bold;">
            风险等级: {hotspot.risk_level.upper()}
        </div>
        """, unsafe_allow_html=True)

    # 严重程度分布
    if hotspot.severity_breakdown:
        st.subheader("严重程度分布")
        fig = px.bar(
            x=list(hotspot.severity_breakdown.keys()),
            y=list(hotspot.severity_breakdown.values()),
            labels={'x': '严重程度', 'y': '数量'},
            color=list(hotspot.severity_breakdown.values()),
            color_continuous_scale="Reds"
        )
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)


def render_top_hotspots(cells: List, max_display: int = 10):
    """渲染热点单元格列表"""
    st.subheader(f"🔴 Top {max_display} 热点问题区域")

    for idx, cell in enumerate(cells[:max_display]):
        with st.expander(f"#{idx+1} {cell.row_key} × {cell.col_key} ({cell.count}个问题)"):
            col1, col2 = st.columns(2)

            with col1:
                st.metric("问题数量", cell.count)
                st.caption(f"占比: {cell.percentage:.1f}%")

            with col2:
                if cell.severity_distribution:
                    st.write("**严重程度分布:**")
                    for sev, cnt in cell.severity_distribution.items():
                        st.write(f"  - {sev}: {cnt}")

            if cell.sample_bug_ids:
                st.write("**样本问题编号:**")
                st.code(", ".join(cell.sample_bug_ids))


def render_root_causes(insights: List[RootCauseInsight]):
    """渲染根因分析结果"""
    st.subheader("🔍 深层归因分析")

    if not insights:
        st.info("暂无根因分析数据，请确保数据包含「开发根因分析」字段")
        return

    for idx, insight in enumerate(insights):
        confidence_pct = insight.confidence * 100

        # 置信度颜色
        if confidence_pct >= 70:
            conf_color = "#ff4757"
        elif confidence_pct >= 40:
            conf_color = "#ffa502"
        else:
            conf_color = "#2ed573"

        with st.container():
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid {conf_color};">
                <h4 style="margin: 0 0 10px 0;">{idx+1}. {insight.description}</h4>
                <p style="margin: 5px 0; color: #666;">出现频次: {insight.frequency} 次</p>
                <p style="margin: 5px 0; color: #666;">置信度: <span style="color: {conf_color}; font-weight: bold;">{confidence_pct:.0f}%</span></p>
                <p style="margin: 5px 0;">涉及模块: {', '.join(insight.related_modules[:5])}</p>
            </div>
            """, unsafe_allow_html=True)

            # 代码模式标签
            if insight.code_patterns:
                st.write("**相关代码模式:**")
                cols = st.columns(len(insight.code_patterns))
                for i, pattern in enumerate(insight.code_patterns):
                    with cols[i]:
                        st.caption(f"🔹 {pattern}")


def render_improvement_suggestions(suggestions: List[ImprovementSuggestion]):
    """渲染改进建议"""
    st.subheader("💡 改进建议")

    if not suggestions:
        st.info("暂无改进建议")
        return

    # 按优先级排序
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    suggestions.sort(key=lambda x: priority_order.get(x.priority, 3))

    for idx, sug in enumerate(suggestions):
        # 优先级颜色
        priority_colors = {
            'high': '#ff4757',
            'medium': '#ffa502',
            'low': '#2ed573'
        }
        priority_color = priority_colors.get(sug.priority, '#999')

        # 分类图标
        category_icons = {
            'test_case': '📝',
            'code_refactor': '🔧',
            'performance': '⚡',
            'investigation': '🔬'
        }
        icon = category_icons.get(sug.category, '📋')

        with st.container():
            st.markdown(f"""
            <div style="background: #ffffff; padding: 15px; border-radius: 8px; margin: 10px 0; border: 1px solid #e0e0e0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h4 style="margin: 0;">{icon} {sug.title}</h4>
                    <span style="background: {priority_color}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 12px;">{sug.priority.upper()}</span>
                </div>
                <p style="color: #666; margin: 10px 0;">{sug.description}</p>
                <p style="font-size: 12px; color: #888;">预计工作量: {sug.estimated_effort}</p>
            </div>
            """, unsafe_allow_html=True)

            # 可执行步骤
            with st.expander("📋 执行步骤"):
                for step in sug.actionable_steps:
                    st.write(step)

            if sug.affected_modules:
                st.caption(f"影响模块: {', '.join(sug.affected_modules[:5])}")

            st.markdown("---")


def render_phase1_import():
    """第一阶段：数据导入"""
    st.header("📥 第一阶段：数据导入")

    col1, col2 = st.columns(2)

    with col1:
        st.info("""
        **支持的数据格式：**
        - Excel (.xlsx, .xls)
        - CSV (.csv)
        - API 动态获取
        """)

    with col2:
        st.info("""
        **核心分析字段：**
        - 业务场景、问题类型
        - 发现阶段、环境
        - 影响程度（爆炸半径）
        - 开发根因分析、漏测分析
        """)


def render_phase2_matrix(df: pd.DataFrame, engine: QMatrixEngine):
    """第二阶段：浅层矩阵"""
    st.header("📊 第二阶段：浅层矩阵分析")

    # 选择矩阵维度
    col1, col2 = st.columns(2)

    available_dims = {
        'business_type': '业务场景',
        'issue_type': '问题类型',
        'environment': '发现环境',
        'severity': '影响程度'
    }

    with col1:
        row_dim = st.selectbox(
            "行维度",
            options=list(available_dims.keys()),
            format_func=lambda x: available_dims.get(x, x),
            index=0
        )

    with col2:
        col_dim = st.selectbox(
            "列维度",
            options=list(available_dims.keys()),
            format_func=lambda x: available_dims.get(x, x),
            index=1
        )

    # 构建矩阵
    matrix = engine.build_matrix(row_dim, col_dim)

    # 渲染矩阵热力图
    render_matrix_visualization(matrix, f"{available_dims[row_dim]} × {available_dims[col_dim]}")

    # 识别热点
    hotspot = engine.identify_hotspots(row_dim, col_dim)

    # 渲染热点摘要
    render_hotspot_summary(hotspot)

    # 渲染热点列表
    render_top_hotspots(hotspot.top_cells)

    return hotspot


def render_phase3_root_cause(df: pd.DataFrame, engine: QMatrixEngine, hotspot: HotspotData):
    """第三阶段：深层归因"""
    st.header("🔍 第三阶段：深层归因分析")

    if hotspot and hotspot.top_cells:
        # 进行根因分析
        insights = engine.analyze_root_causes(hotspot.top_cells[:5])

        # 渲染根因分析
        render_root_causes(insights)

        return insights

    st.warning("请先完成第二阶段分析")
    return []


def render_phase4_improvements(df: pd.DataFrame, engine: QMatrixEngine,
                               hotspot: HotspotData, insights: List[RootCauseInsight]):
    """第四阶段：改进建议"""
    st.header("💡 第四阶段：改进建议")

    if hotspot and insights:
        # 生成改进建议
        suggestions = engine.generate_improvements(hotspot, insights)

        # 渲染改进建议
        render_improvement_suggestions(suggestions)

        return suggestions

    st.warning("请先完成第二、三阶段分析")
    return []


def render_full_analysis(df: pd.DataFrame):
    """执行完整分析流程"""
    render_qmatrix_header()
    render_progress_indicator(0)

    if df is None or len(df) == 0:
        st.warning("请先导入数据")
        return

    # 创建分析引擎
    engine = QMatrixEngine(df)

    # 显示数据概览
    st.subheader("📈 数据概览")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总问题数", len(df))
    with col2:
        severity_col = engine._get_col('severity')
        if severity_col and severity_col in df.columns:
            st.metric("严重问题", len(df[df[severity_col].isin(['P0', 'P1', '致命', '严重'])]))
    with col3:
        business_col = engine._get_col('business_type')
        if business_col and business_col in df.columns:
            st.metric("业务模块数", df[business_col].nunique())
    with col4:
        env_col = engine._get_col('environment')
        if env_col and env_col in df.columns:
            st.metric("涉及环境数", df[env_col].nunique())

    st.markdown("---")

    # 阶段选择
    phase = st.radio(
        "分析阶段",
        ["浅层矩阵分析", "深层归因分析", "改进建议生成", "完整分析报告"],
        horizontal=True
    )

    hotspot = None
    insights = []

    if phase == "浅层矩阵分析" or phase == "完整分析报告":
        hotspot = render_phase2_matrix(df, engine)
        st.markdown("---")

    if phase == "深层归因分析" or phase == "完整分析报告":
        if hotspot is None:
            hotspot = engine.identify_hotspots()
        insights = render_phase3_root_cause(df, engine, hotspot)
        st.markdown("---")

    if phase == "改进建议生成" or phase == "完整分析报告":
        if hotspot is None:
            hotspot = engine.identify_hotspots()
        suggestions = render_phase4_improvements(df, engine, hotspot, insights)
        st.markdown("---")

    # 生成综合报告
    if phase == "完整分析报告" and hotspot and insights:
        st.header("📋 综合分析报告")

        summary = engine.generate_summary()

        st.json(summary)
