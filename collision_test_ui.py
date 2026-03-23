"""
Q-Matrix 对撞测试 UI
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any

from collision_test import (
    run_collision_test,
    ProductManagerSkill,
    DeveloperSkill,
    TestAnalysisEngineerSkill
)


def render_skill_avatar(skill_name: str) -> str:
    """获取 Skill 头像"""
    avatars = {
        "Product Manager": "📦",
        "Developer": "💻",
        "Test Analysis Engineer": "🧪"
    }
    return avatars.get(skill_name, "👤")


def render_test_result_card(result):
    """渲染单个测试结果卡片"""
    with st.container():
        # 标题行
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**{result['test_type']}**")
        with col2:
            if result['passed']:
                st.success("✅ 通过")
            else:
                st.error("❌ 失败")

        # 得分
        score_color = "green" if result['score'] >= 70 else "orange" if result['score'] >= 50 else "red"
        st.markdown(f"得分: <span style='color:{score_color}'>{result['score']}</span>/100", unsafe_allow_html=True)

        # 发现列表
        if result['findings']:
            with st.expander("详细发现"):
                for finding in result['findings']:
                    st.write(finding)


def render_skill_section(skill_name: str, results: List[Dict]):
    """渲染单个 Skill 测试区域"""
    avatar = render_skill_avatar(skill_name)

    # 计算平均分
    scores = [r['score'] for r in results]
    avg_score = sum(scores) / len(scores) if scores else 0
    passed_count = sum(1 for r in results if r['passed'])

    # Skill 标题
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%);
                padding: 15px; border-radius: 10px; margin: 10px 0;">
        <h3 style="color: #00d4ff; margin: 0;">
            {avatar} {skill_name}
        </h3>
        <p style="color: #a0a0a0; margin: 5px 0 0 0;">
            测试项: {len(results)} | 通过: {passed_count} | 平均分: {avg_score:.1f}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 测试结果
    for result in results:
        render_test_result_card(result)

    st.markdown("---")


def render_collision_test_report(report: Dict):
    """渲染完整测试报告"""
    st.header("🔬 多视角对撞测试报告")

    # 总体概览
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("总测试项", report['total_tests'])

    with col2:
        st.metric("通过", report['passed'], delta=report['passed'])

    with col3:
        st.metric("失败", report['failed'], delta=-report['failed'], delta_color="inverse")

    with col4:
        score_color = "green" if report['average_score'] >= 70 else "orange" if report['average_score'] >= 50 else "red"
        st.markdown(f"""
        <div style="text-align: center; padding: 10px; background: #f0f0f0; border-radius: 5px;">
            <div style="font-size: 24px; color: {score_color}; font-weight: bold;">
                {report['average_score']:.1f}
            </div>
            <div style="font-size: 12px; color: #666;">平均得分</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 按 Skill 分组显示
    results_by_skill = report.get('results_by_skill', {})

    for skill_name in ["Product Manager", "Developer", "Test Analysis Engineer"]:
        if skill_name in results_by_skill:
            render_skill_section(skill_name, results_by_skill[skill_name])


def run_and_render_collision_test(df: pd.DataFrame, engine):
    """运行并渲染对撞测试"""
    from qmatrix_engine import QMatrixEngine

    # 读取引擎代码用于静态分析
    import inspect
    engine_code = inspect.getsource(QMatrixEngine)

    with st.spinner("正在执行多视角对撞测试..."):
        # 运行测试
        report = run_collision_test(df, engine, engine_code)

    # 渲染报告
    render_collision_test_report(report)

    return report


def show_collision_test_page():
    """显示对撞测试页面"""
    st.header("🔬 Q-Matrix 对撞测试")

    if st.session_state.data is None:
        st.warning("⚠️ 请先导入数据")
        return

    df = st.session_state.data

    # 说明
    st.info("""
    **多视角对撞测试** 模拟三种角色对 Q-Matrix 分析引擎进行验证：

    - 📦 **Product Manager**: 审视需求契合度，验证业务痛点提取
    - 💻 **Developer**: 检查代码质量、性能、数据处理正确性
    - 🧪 **Test Analysis Engineer**: 边界测试、并发测试、建议专业性验证
    """)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.metric("当前数据量", f"{len(df)} 条")

    with col2:
        st.metric("数据列数", f"{len(df.columns)} 列")

    st.markdown("---")

    # 导入引擎
    from qmatrix_engine import QMatrixEngine
    engine = QMatrixEngine(df)

    # 运行测试
    if st.button("🚀 开始对撞测试", type="primary"):
        report = run_and_render_collision_test(df, engine)

        # 总结建议
        st.markdown("---")
        st.subheader("📋 测试总结")

        if report['average_score'] >= 70:
            st.success("✅ 测试通过 - Q-Matrix 分析引擎运行良好")
        elif report['average_score'] >= 50:
            st.warning("⚠️ 测试部分通过 - 存在一些需要优化的问题")
        else:
            st.error("❌ 测试未通过 - 需要修复关键问题")

    else:
        st.info("点击上方按钮开始测试")
