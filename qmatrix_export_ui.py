"""
Q-Matrix 成果导出 UI
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

from qmatrix_exporter import QMatrixExporter


def render_export_section(df: pd.DataFrame,
                         summary: Dict,
                         hotspots,
                         root_causes,
                         suggestions):
    """渲染导出功能区域"""

    st.header("📤 成果导出")

    # 初始化导出器
    exporter = QMatrixExporter()

    # 选项卡
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 原始数据",
        "🧹 清洗数据",
        "📝 分析报告",
        "📦 一键导出"
    ])

    with tab1:
        st.subheader("原始数据导出")

        col1, col2 = st.columns(2)

        with col1:
            format_choice = st.radio("导出格式", ["Excel", "CSV"], horizontal=True)

        with col2:
            st.info(f"当前数据: {len(df)} 行 × {len(df.columns)} 列")

        if st.button("📥 导出原始数据", type="primary"):
            with st.spinner("正在导出..."):
                fmt = format_choice.lower()
                filepath = exporter.export_raw_data(df, fmt)
                filename = Path(filepath).name

                # 读取文件用于下载
                with open(filepath, 'rb') as f:
                    data = f.read()

                st.success(f"✅ 导出成功: {filename}")

                st.download_button(
                    label="⬇️ 点击下载",
                    data=data,
                    file_name=filename,
                    mime="application/octet-stream"
                )

    with tab2:
        st.subheader("结构化清洗数据导出")

        st.info("""
        清洗后的数据包含：
        - 标准化字段列
        - 导出时间戳
        - 记录序号
        - 字段映射说明
        """)

        if st.button("📥 导出清洗数据", type="primary"):
            with st.spinner("正在导出..."):
                filepath = exporter.export_cleaned_data(df)
                filename = Path(filepath).name

                with open(filepath, 'rb') as f:
                    data = f.read()

                st.success(f"✅ 导出成功: {filename}")

                st.download_button(
                    label="⬇️ 点击下载",
                    data=data,
                    file_name=filename,
                    mime="application/octet-stream"
                )

    with tab3:
        st.subheader("综合测试分析报告")

        col1, col2 = st.columns(2)

        with col1:
            report_format = st.radio("报告格式", ["文本报告", "JSON数据"], horizontal=True)

        with col2:
            st.info("报告包含：数据概览、热点分析、根因分析、改进建议")

        # 报告预览
        with st.expander("📋 报告预览"):
            preview_text = exporter._generate_text_report(
                df, summary, hotspots, root_causes, suggestions
            )
            st.text(preview_text[:2000] + "..." if len(preview_text) > 2000 else preview_text)

        if st.button("📥 导出分析报告", type="primary"):
            with st.spinner("正在生成报告..."):
                fmt = 'json' if report_format == 'JSON数据' else 'text'
                filepath = exporter.export_analysis_report(
                    df, summary, hotspots, root_causes, suggestions, fmt
                )
                filename = Path(filepath).name

                with open(filepath, 'rb') as f:
                    data = f.read()

                st.success(f"✅ 导出成功: {filename}")

                st.download_button(
                    label="⬇️ 点击下载",
                    data=data,
                    file_name=filename,
                    mime="application/octet-stream"
                )

    with tab4:
        st.subheader("📦 一键导出所有成果")

        st.markdown("""
        **导出内容包含：**
        - 📊 原始数据 (Excel)
        - 📄 原始数据 (CSV)
        - 🧹 结构化清洗数据 (Excel)
        - 📝 综合分析报告 (文本)
        - 📋 分析报告数据 (JSON)
        """)

        if st.button("🚀 一键导出全部", type="primary", use_container_width=True):
            with st.spinner("正在导出全部成果..."):
                exports = exporter.export_all(
                    df, summary, hotspots, root_causes, suggestions
                )

                st.success("✅ 全部导出完成！")

                # 显示所有文件
                for key, filepath in exports.items():
                    filename = Path(filepath).name
                    file_size = Path(filepath).stat().st_size / 1024  # KB

                    with open(filepath, 'rb') as f:
                        data = f.read()

                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.write(f"📄 {filename}")
                    with col2:
                        st.caption(f"{file_size:.1f} KB")
                    with col3:
                        st.download_button(
                            label="⬇️",
                            data=data,
                            file_name=filename,
                            mime="application/octet-stream",
                            key=f"download_{key}"
                        )


def show_export_page():
    """显示导出页面"""
    st.header("📤 成果导出")

    if st.session_state.data is None:
        st.warning("⚠️ 请先导入数据")
        return

    df = st.session_state.data

    # 说明
    st.info("""
    **Q-Matrix 成果导出** 提供多种格式的导出选项：

    - 📊 **原始数据**: 保持导入时的原始格式
    - 🧹 **清洗数据**: 标准化字段，带元数据
    - 📝 **分析报告**: 包含完整深度分析的综合报告
    - 📦 **一键导出**: 一次性导出所有成果
    """)

    # 数据概览
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("数据总量", f"{len(df)} 条")
    with col2:
        st.metric("字段数量", f"{len(df.columns)} 个")
    with col3:
        business_count = df['业务模块'].nunique() if '业务模块' in df.columns else 'N/A'
        st.metric("业务模块", str(business_count))
    with col4:
        severity_count = len(df[df['影响程度'].isin(['P0', 'P1', '致命', '严重'])]) if '影响程度' in df.columns else 'N/A'
        st.metric("严重问题", str(severity_count))

    st.markdown("---")

    # 需要先生成分析
    from qmatrix_engine import QMatrixEngine

    engine = QMatrixEngine(df)

    # 生成分析数据
    summary = engine.generate_summary()
    hotspots = engine.identify_hotspots()
    root_causes = engine.analyze_root_causes(hotspots.top_cells[:5])
    suggestions = engine.generate_improvements(hotspots, root_causes)

    # 渲染导出区域
    render_export_section(df, summary, hotspots, root_causes, suggestions)
