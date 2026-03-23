"""
Q-Matrix 增强版 UI
集成浅层矩阵、深层分析、聚合分析、改进建议
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from qmatrix_engine import QMatrixEngine
from qmatrix_aggregator import QMatrixAggregator, ActionItemManager


def render_header():
    """渲染标题"""
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h1 style="color: #00d4ff; margin: 0; font-size: 28px;">🔷 Q-Matrix Bug分析引擎</h1>
        <p style="color: #a0a0a0; margin: 10px 0 0 0;">浅层矩阵 → 深层归因 → 聚合分析 → 改进建议</p>
    </div>
    """, unsafe_allow_html=True)


def render_data_overview(df: pd.DataFrame, engine: QMatrixEngine):
    """数据概览"""
    st.subheader("📊 数据概览")

    summary = engine.generate_summary()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总问题数", summary.get("total_issues", len(df)))
    with col2:
        biz_dist = summary.get("business_distribution", {})
        st.metric("业务模块", len(biz_dist))
    with col3:
        severity_dist = summary.get("severity_distribution", {})
        critical = severity_dist.get("P0", 0) + severity_dist.get("P1", 0)
        st.metric("严重问题", critical)
    with col4:
        env_dist = summary.get("environment_distribution", {})
        st.metric("涉及环境", len(env_dist))

    # 严重程度分布图
    if severity_dist:
        fig = px.bar(
            x=list(severity_dist.keys()),
            y=list(severity_dist.values()),
            labels={'x': '严重程度', 'y': '数量'},
            color=list(severity_dist.values()),
            color_continuous_scale="Reds"
        )
        fig.update_layout(template="plotly_white", height=300)
        st.plotly_chart(fig, use_container_width=True)


def render_shallow_matrix(df: pd.DataFrame, engine: QMatrixEngine):
    """浅层矩阵 - 整合原有分析功能"""
    st.header("📈 浅层矩阵分析")

    # 选择矩阵维度
    available_dims = {
        'business_type': '业务模块',
        'issue_type': '问题类型',
        'environment': '发现环境',
        'severity': '影响程度'
    }

    col1, col2 = st.columns(2)

    with col1:
        row_dim = st.selectbox(
            "行维度",
            options=list(available_dims.keys()),
            format_func=lambda x: available_dims.get(x, x),
            index=0,
            key="matrix_row"
        )

    with col2:
        col_dim = st.selectbox(
            "列维度",
            options=list(available_dims.keys()),
            format_func=lambda x: available_dims.get(x, x),
            index=1,
            key="matrix_col"
        )

    # 构建矩阵
    matrix = engine.build_matrix(row_dim, col_dim)

    # 热力图
    if not matrix.empty:
        display_matrix = matrix.copy()
        if '合计' in display_matrix.index:
            display_matrix = display_matrix.drop('合计')
        if '合计' in display_matrix.columns:
            display_matrix = display_matrix.drop('合计', axis=1)

        if not display_matrix.empty:
            fig = px.imshow(
                display_matrix,
                text_auto=True,
                aspect="auto",
                color_continuous_scale="Blues",
                title=f"{available_dims[row_dim]} × {available_dims[col_dim]}"
            )
            fig.update_layout(template="plotly_white", height=400)
            st.plotly_chart(fig, use_container_width=True)

    # 热点识别
    hotspots = engine.identify_hotspots(row_dim, col_dim)

    st.subheader("🔴 热点问题区域")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("风险等级", hotspots.risk_level.upper())
    with col2:
        st.metric("问题总数", hotspots.total_issues)
    with col3:
        st.metric("热点区域", len(hotspots.top_cells))

    # Top 热点列表
    for idx, cell in enumerate(hotspots.top_cells[:5], 1):
        with st.expander(f"#{idx} {cell.row_key} × {cell.col_key} ({cell.count}个)"):
            st.write(f"占比: {cell.percentage:.1f}%")
            if cell.severity_distribution:
                st.write("严重程度:", cell.severity_distribution)


def render_deep_analysis(df: pd.DataFrame, aggregator: QMatrixAggregator):
    """深层分析 - 三视角"""
    st.header("🔍 深层分析")

    # 标签页：开发/测试/业务
    tab1, tab2, tab3 = st.tabs(["💻 开发视角", "🧪 测试视角", "📊 业务视角"])

    with tab1:
        st.subheader("💻 开发视角 - 根因分析")
        dev_result = aggregator.analyze_developer_perspective()

        if dev_result["status"] == "success":
            # 统计图
            if dev_result["pattern_distribution"]:
                patterns = dev_result["pattern_distribution"]
                fig = px.bar(
                    x=list(patterns.keys()),
                    y=list(patterns.values()),
                    labels={'x': '问题类型', 'y': '数量'},
                    color=list(patterns.values()),
                    color_continuous_scale="Oranges"
                )
                fig.update_layout(template="plotly_white", height=300)
                st.plotly_chart(fig, use_container_width=True)

            # 洞察列表
            for insight in dev_result["insights"]:
                severity_color = {"critical": "🔴", "high": "🟠", "medium": "🟡"}.get(insight.severity, "⚪")
                with st.container():
                    st.markdown(f"""
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #ff6b6b;">
                        <h4 style="margin: 0;">{severity_color} {insight.title}</h4>
                        <p style="margin: 5px 0; color: #666;">{insight.description}</p>
                        <p style="margin: 5px 0; font-size: 12px;">影响模块: {', '.join(insight.affected_modules[:3])}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("未找到根因详细数据")

    with tab2:
        st.subheader("🧪 测试视角 - 漏测分析")
        test_result = aggregator.analyze_tester_perspective()

        if test_result["status"] == "success":
            if test_result["pattern_distribution"]:
                patterns = test_result["pattern_distribution"]
                fig = px.bar(
                    x=list(patterns.keys()),
                    y=list(patterns.values()),
                    labels={'x': '漏测类型', 'y': '数量'},
                    color=list(patterns.values()),
                    color_continuous_scale="Greens"
                )
                fig.update_layout(template="plotly_white", height=300)
                st.plotly_chart(fig, use_container_width=True)

            for insight in test_result["insights"]:
                severity_color = {"critical": "🔴", "high": "🟠", "medium": "🟡"}.get(insight.severity, "⚪")
                with st.container():
                    st.markdown(f"""
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #2ed573;">
                        <h4 style="margin: 0;">{severity_color} {insight.title}</h4>
                        <p style="margin: 5px 0; color: #666;">{insight.description}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("未找到漏测分析数据")

    with tab3:
        st.subheader("📊 业务视角 - 风险分析")
        biz_result = aggregator.analyze_business_perspective()

        if biz_result["status"] == "success":
            if biz_result["risk_ranking"]:
                risks = biz_result["risk_ranking"][:8]
                fig = px.bar(
                    x=[r[0] for r in risks],
                    y=[r[1] for r in risks],
                    labels={'x': '业务模块', 'y': '风险评分'},
                    color=[r[1] for r in risks],
                    color_continuous_scale="Reds"
                )
                fig.update_layout(template="plotly_white", height=300)
                st.plotly_chart(fig, use_container_width=True)

            for insight in biz_result["insights"]:
                severity_color = {"critical": "🔴", "high": "🟠", "medium": "🟡"}.get(insight.severity, "⚪")
                with st.container():
                    st.markdown(f"""
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #00d4ff;">
                        <h4 style="margin: 0;">{severity_color} {insight.title}</h4>
                        <p style="margin: 5px 0; color: #666;">{insight.description}</p>
                        <p style="margin: 5px 0; font-size: 12px;">{' | '.join(insight.evidence)}</p>
                    </div>
                    """, unsafe_allow_html=True)


def render_aggregated_analysis(df: pd.DataFrame, aggregator: QMatrixAggregator):
    """聚合分析 - 核心引擎"""
    st.header("🔑 聚合分析")

    with st.spinner("正在生成聚合分析..."):
        result = aggregator.generate_aggregated_analysis()

    # 总体摘要
    summary = result["summary"]
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总洞察", summary["total_insights"])
    with col2:
        st.metric("🔴 严重", summary["critical_count"])
    with col3:
        st.metric("🟠 高风险", summary["high_count"])
    with col4:
        st.metric("🟡 中风险", summary["medium_count"])

    st.markdown("---")

    # 核心结论
    st.subheader("💡 核心结论")

    for conclusion in result["conclusions"]:
        priority_colors = {
            "critical": "#ff4757",
            "high": "#ffa502",
            "medium": "#2ed573"
        }
        color = priority_colors.get(conclusion["priority"], "#999")

        with st.container():
            st.markdown(f"""
            <div style="background: #ffffff; padding: 20px; border-radius: 10px; margin: 15px 0; border: 1px solid #e0e0e0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h3 style="margin: 0 0 10px 0; color: {color};">{conclusion['title']}</h3>
                <p style="margin: 10px 0; color: #333;">{conclusion['content']}</p>
                {''.join([f'<li>{item}</li>' for item in conclusion['items']]) if conclusion['items'] else ''}
            </div>
            """, unsafe_allow_html=True)


def render_action_items():
    """改进建议 - 自定义编写和保存"""
    st.header("📝 改进建议")

    # 初始化管理器
    action_manager = ActionItemManager()

    # 标签页
    tab1, tab2, tab3 = st.tabs(["📋 建议列表", "➕ 添加建议", "🔧 管理"])

    with tab1:
        st.subheader("建议列表")

        # 筛选
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox("状态", ["全部", "pending", "in_progress", "completed"], key="action_status")
        with col2:
            priority_filter = st.selectbox("优先级", ["全部", "high", "medium", "low"], key="action_priority")

        status = None if status_filter == "全部" else status_filter
        priority = None if priority_filter == "全部" else priority_filter

        items = action_manager.get_items(status=status, priority=priority)

        if not items:
            st.info("暂无改进建议")
        else:
            for item in items:
                priority_colors = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                status_icons = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}

                with st.container():
                    st.markdown(f"""
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;">
                        <div style="display: flex; justify-content: space-between;">
                            <h4 style="margin: 0;">{priority_colors.get(item['priority'], '⚪')} {item['title']}</h4>
                            <span>{status_icons.get(item['status'], '⚪')}</span>
                        </div>
                        <p style="margin: 5px 0; color: #666;">{item['description']}</p>
                        <p style="margin: 5px 0; font-size: 12px; color: #999;">{item['created_at'][:10]} | {item['category']}</p>
                    </div>
                    """, unsafe_allow_html=True)

    with tab2:
        st.subheader("添加建议")

        with st.form("add_action_form"):
            title = st.text_input("标题")
            description = st.text_area("描述")
            col1, col2 = st.columns(2)
            with col1:
                category = st.selectbox("类别", ["code_fix", "test_coverage", "process_improvement", "other"])
            with col2:
                priority = st.selectbox("优先级", ["high", "medium", "low"])

            submit = st.form_submit_button("保存", type="primary")

            if submit and title:
                action_manager.add_item(title, description, category, priority)
                st.success("建议已保存!")
                st.rerun()

    with tab3:
        st.subheader("管理建议")

        items = action_manager.get_items()
        for item in items:
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.write(f"**{item['title']}**")

            with col2:
                new_status = st.selectbox(
                    "状态",
                    ["pending", "in_progress", "completed"],
                    index=["pending", "in_progress", "completed"].index(item["status"]),
                    key=f"status_{item['id']}"
                )
                if new_status != item["status"]:
                    action_manager.update_item(item["id"], status=new_status)
                    st.rerun()

            with col3:
                if st.button("删除", key=f"del_{item['id']}"):
                    action_manager.delete_item(item["id"])
                    st.rerun()


def render_full_qmatrix_analysis(df: pd.DataFrame):
    """完整的 Q-Matrix 分析流程"""
    render_header()

    if df is None or len(df) == 0:
        st.warning("请先导入数据")
        return

    # 创建引擎
    engine = QMatrixEngine(df)
    aggregator = QMatrixAggregator(df, engine)

    # 侧边栏导航
    with st.sidebar:
        st.header("导航")

        section = st.radio(
            "选择分析模块",
            ["数据概览", "浅层矩阵", "深层分析", "聚合分析", "改进建议"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # 快速统计
        st.caption("快速统计")
        severity_col = '影响程度' if '影响程度' in df.columns else None
        if severity_col:
            critical = len(df[df[severity_col].isin(['P0', 'P1', '致命', '严重'])])
            st.metric("严重问题", critical)

    # 渲染选择的部分
    if section == "数据概览":
        render_data_overview(df, engine)

    elif section == "浅层矩阵":
        render_shallow_matrix(df, engine)

    elif section == "深层分析":
        render_deep_analysis(df, aggregator)

    elif section == "聚合分析":
        render_aggregated_analysis(df, aggregator)

    elif section == "改进建议":
        render_action_items()


# 导出函数供 app.py 调用
def show_qmatrix_enhanced_page():
    """显示增强版 Q-Matrix 页面"""
    if st.session_state.data is None:
        st.warning("⚠️ 请先导入数据")
        return

    render_full_qmatrix_analysis(st.session_state.data)
