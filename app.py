"""
测试问题单分析工具 - 主应用
运行方式: streamlit run app.py
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import yaml
import plotly.express as px
from functools import lru_cache

# 导入自定义模块
from config_loader import get_config_loader
from data_importer import DataImporter
from analyzer import AnalysisEngine
from visualizer import Visualizer
from auth import init_session_state, is_authenticated, show_login_page, logout
from data_persistence import show_persistence_ui
from data_manager import show_data_manager_page
from qmatrix_enhanced_ui import show_qmatrix_enhanced_page
from qmatrix_export_ui import show_export_page
from navigation import get_menu_structure, MENU_PAGE_MAP

# 页面配置
st.set_page_config(
    page_title="Q-Matrix Bug分析引擎",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化配置
config_loader = get_config_loader()
data_importer = DataImporter(config_loader)
analyzer = AnalysisEngine(config_loader)
visualizer = Visualizer(config_loader)

# 会话状态初始化
if 'data' not in st.session_state:
    st.session_state.data = None
if 'data_source' not in st.session_state:
    st.session_state.data_source = None
if 'menu' not in st.session_state:
    st.session_state.menu = "📥 数据导入"


def main():
    """主函数"""
    # 初始化认证状态
    init_session_state()

    # 检查登录状态
    if not is_authenticated():
        show_login_page()
        return

    # 侧边栏 - 抽屉式导航
    with st.sidebar:
        st.title("🔷 Q-Matrix 分析引擎")

        # 初始化菜单状态
        if 'menu' not in st.session_state:
            st.session_state.menu = "import"

        # 使用 expander 实现抽屉式导航
        # 1. 数据管理（可展开）
        with st.expander("📥 数据管理", expanded=True):
            if st.button("📥 导入数据", use_container_width=True,
                         type="primary" if st.session_state.menu == "import" else "secondary"):
                st.session_state.menu = "import"
            if st.button("📂 已保存数据", use_container_width=True,
                         type="primary" if st.session_state.menu == "saved_data" else "secondary"):
                st.session_state.menu = "saved_data"

        # 2. 数据概览
        if st.button("📊 数据概览", use_container_width=True,
                     type="primary" if st.session_state.menu == "overview" else "secondary"):
            st.session_state.menu = "overview"

        # 3. 浅层矩阵（可展开）
        with st.expander("📈 浅层矩阵", expanded=True):
            if st.button("🔄 交叉分析", use_container_width=True,
                         type="primary" if st.session_state.menu == "cross_analysis" else "secondary"):
                st.session_state.menu = "cross_analysis"
            if st.button("📈 环境漏出", use_container_width=True,
                         type="primary" if st.session_state.menu == "environment" else "secondary"):
                st.session_state.menu = "environment"
            if st.button("⚠️ 严重程度", use_container_width=True,
                         type="primary" if st.session_state.menu == "severity" else "secondary"):
                st.session_state.menu = "severity"
            if st.button("🔍 根因分析", use_container_width=True,
                         type="primary" if st.session_state.menu == "root_cause" else "secondary"):
                st.session_state.menu = "root_cause"
            if st.button("💧 漏测分析", use_container_width=True,
                         type="primary" if st.session_state.menu == "leak" else "secondary"):
                st.session_state.menu = "leak"
            if st.button("📝 汇总分析", use_container_width=True,
                         type="primary" if st.session_state.menu == "summary" else "secondary"):
                st.session_state.menu = "summary"

        # 4. 深层分析
        with st.expander("🔍 深层分析", expanded=True):
            if st.button("💻 开发视角", use_container_width=True,
                         type="primary" if st.session_state.menu == "deep_dev" else "secondary"):
                st.session_state.menu = "deep_dev"
            if st.button("🧪 测试视角", use_container_width=True,
                         type="primary" if st.session_state.menu == "deep_test" else "secondary"):
                st.session_state.menu = "deep_test"
            if st.button("📊 业务视角", use_container_width=True,
                         type="primary" if st.session_state.menu == "deep_biz" else "secondary"):
                st.session_state.menu = "deep_biz"

        # 5. 聚合分析
        if st.button("🔑 聚合分析", use_container_width=True,
                     type="primary" if st.session_state.menu == "aggregated" else "secondary"):
            st.session_state.menu = "aggregated"

        # 6. 改进建议
        if st.button("📝 改进建议", use_container_width=True,
                     type="primary" if st.session_state.menu == "actions" else "secondary"):
            st.session_state.menu = "actions"

        # 7. 数据列表
        if st.button("📋 数据列表", use_container_width=True,
                     type="primary" if st.session_state.menu == "data_list" else "secondary"):
            st.session_state.menu = "data_list"

        # 8. 数据持久化
        if st.button("💾 数据持久化", use_container_width=True,
                     type="primary" if st.session_state.menu == "persistence" else "secondary"):
            st.session_state.menu = "persistence"

        # 9. 成果导出
        if st.button("📤 成果导出", use_container_width=True,
                     type="primary" if st.session_state.menu == "export" else "secondary"):
            st.session_state.menu = "export"

        st.markdown("---")

        # 显示数据状态
        if st.session_state.data is not None:
            st.success(f"✅ 已加载数据: {len(st.session_state.data)} 条")
        else:
            st.warning("⚠️ 请先导入数据")

        st.markdown("---")

        # 显示当前用户和登出按钮
        user = st.session_state.get("user")
        if user:
            st.caption(f"👤 登录用户: {user.get('name', user.get('username', 'Unknown'))}")
            if st.button("🚪 退出登录", use_container_width=True):
                logout()

    # 主内容区
    menu = st.session_state.menu

    # 页面路由映射
    if menu == "import":
        show_import_page()
    elif menu == "saved_data":
        show_data_manager_page()
    elif menu == "overview":
        show_overview_page()
    elif menu == "cross_analysis":
        show_cross_analysis_page()
    elif menu == "environment":
        show_environment_page()
    elif menu == "severity":
        show_severity_page()
    elif menu == "root_cause":
        show_root_cause_page()
    elif menu == "leak":
        show_leak_analysis_page()
    elif menu == "summary":
        show_summary_analysis_page()
    # 深层分析
    elif menu == "deep_dev":
        show_deep_analysis_page("dev")
    elif menu == "deep_test":
        show_deep_analysis_page("test")
    elif menu == "deep_biz":
        show_deep_analysis_page("biz")
    # 聚合分析
    elif menu == "aggregated":
        show_aggregated_analysis_page()
    # 改进建议
    elif menu == "actions":
        show_actions_page()
    # 其他
    elif menu == "data_list":
        show_data_list_page()
    elif menu == "persistence":
        show_persistence_page()
    elif menu == "export":
        show_export_page()


def show_import_page():
    """数据导入页面"""
    st.header("📥 数据导入")

    tab1, tab2 = st.tabs(["📁 Excel导入", "🌐 API导入"])

    with tab1:
        st.subheader("Excel文件导入")

        # 文件上传
        uploaded_file = st.file_uploader(
            "选择Excel或CSV文件",
            type=['xlsx', 'xls', 'csv'],
            help="支持.xlsx, .xls, .csv格式"
        )

        if uploaded_file is not None:
            try:
                # 读取并显示预览（不自动标准化，保留原始列名用于手动映射）
                df = data_importer.import_from_excel_upload(uploaded_file, skip_normalization=True)

                st.success(f"✅ 成功读取 {len(df)} 条数据")

                # 显示预览
                with st.expander("数据预览（前5行）", expanded=True):
                    st.dataframe(df.head())

                # 字段确认
                st.subheader("字段映射确认")

                dimensions = config_loader.get_dimensions()
                dimension_labels = config_loader.get_all_dimension_labels()
                field_mapping = config_loader.get_field_mapping()

                # 清除所有映射选择状态，确保每次重新计算
                for dim_key in dimension_labels.keys():
                    if f"map_{dim_key}" in st.session_state:
                        del st.session_state[f"map_{dim_key}"]

                cols = st.columns(4)
                col_idx = 0

                for dim_key, dim_label in dimension_labels.items():
                    available_cols = [''] + list(df.columns)

                    # 自动匹配：检查 field_mapping 中的所有可能列名
                    default_index = 0  # 默认选择空
                    mapping_options = field_mapping.get(dim_key, [])

                    for i, col in enumerate(available_cols):
                        if col:  # 跳过空字符串
                            col_lower = col.lower().strip()
                            # 检查是否在映射配置中
                            for mapped_name in mapping_options:
                                if col_lower == mapped_name.lower().strip():
                                    default_index = i
                                    break
                            if default_index > 0:
                                break

                    with cols[col_idx % 4]:
                        selected = st.selectbox(
                            f"{dim_label} ({dim_key})",
                            available_cols,
                            index=default_index,
                            key=f"map_{dim_key}"
                        )
                    col_idx += 1

                # 确认导入
                if st.button("确认导入数据", type="primary"):
                    # 构建字段映射
                    field_map = {}
                    for dim_key in dimension_labels.keys():
                        selected = st.session_state.get(f"map_{dim_key}")
                        if selected:
                            field_map[dim_key] = selected

                    # 重置文件指针位置
                    uploaded_file.seek(0)

                    # 应用映射到已读取的数据
                    if field_map:
                        df = df.rename(columns=field_map)

                    # 验证
                    valid, errors, warnings = data_importer.validate_data(df)

                    if valid:
                        st.session_state.data = df
                        st.session_state.data_source = f"Excel: {uploaded_file.name}"
                        st.success("✅ 数据导入成功！")

                        # 显示建议字段警告（不影响导入）
                        if warnings:
                            for warn in warnings:
                                st.info(f"💡 {warn}")
                        st.toast("数据已就绪，可以开始分析", icon="📊")
                        st.rerun()
                    else:
                        for err in errors:
                            st.error(f"❌ {err}")

            except Exception as e:
                st.error(f"❌ 读取失败: {str(e)}")

    with tab2:
        st.subheader("API接口导入")

        # API配置输入
        st.info("请在配置文件中设置API接口: config/api_config.yaml")

        # 显示配置模板
        with st.expander("查看API配置示例"):
            st.code("""
# config/api_config.yaml 示例
apis:
  - name: "问题单接口"
    enabled: true
    endpoint: "http://your-server/api/bugs"
    method: "GET"
    auth:
      type: "bearer"
      token: "your-token"
    response_mapping:
      data_path: "data.list"
      fields:
        bug_id: "id"
        business_type: "module"
        bug_type: "bug_type"
        environment: "env"
        severity: "level"
    pagination:
      enabled: true
      page_param: "page"
      size_param: "page_size"
            """, language="yaml")

        # 手动输入API配置
        st.subheader("快速API配置")

        api_endpoint = st.text_input("API地址", placeholder="http://example.com/api/bugs")
        api_token = st.text_input("Bearer Token", type="password")

        if st.button("从API导入数据", type="primary"):
            if api_endpoint:
                api_config = {
                    'endpoint': api_endpoint,
                    'method': 'GET',
                    'auth': {'type': 'bearer', 'token': api_token},
                    'response_mapping': {
                        'data_path': 'data',
                        'fields': {}
                    },
                    'pagination': {'enabled': False}
                }

                with st.spinner("正在从API获取数据..."):
                    try:
                        df = data_importer.import_from_api(api_config)

                        if not df.empty:
                            st.session_state.data = df
                            st.session_state.data_source = f"API: {api_endpoint}"
                            st.success(f"✅ 成功从API获取 {len(df)} 条数据")
                            st.rerun()
                        else:
                            st.warning("⚠️ API返回空数据")
                    except Exception as e:
                        st.error(f"❌ API请求失败: {str(e)}")
            else:
                st.error("❌ 请输入API地址")


def show_overview_page():
    """数据概览页面"""
    st.header("📊 数据概览")

    if st.session_state.data is None:
        st.warning("⚠️ 请先导入数据")
        return

    df = st.session_state.data

    # 数据统计卡片
    st.subheader("数据统计")

    cols = st.columns(4)
    with cols[0]:
        st.metric("总问题数", len(df))
    with cols[1]:
        st.metric("业务模块数", df['business_type'].nunique() if 'business_type' in df.columns else 0)
    with cols[2]:
        st.metric("问题类型数", df['bug_type'].nunique() if 'bug_type' in df.columns else 0)
    with cols[3]:
        st.metric("环境数", df['environment'].nunique() if 'environment' in df.columns else 0)

    # 维度分布
    st.subheader("维度分布")

    dimensions = config_loader.get_dimensions()
    dimension_labels = config_loader.get_all_dimension_labels()

    cols = st.columns(2)

    for idx, (dim_key, dim_label) in enumerate(dimension_labels.items()):
        if dim_key in df.columns:
            with cols[idx % 2]:
                fig = visualizer.create_pie_chart(df, dim_key, f"{dim_label}分布")
                st.plotly_chart(fig, use_container_width=True)


def show_cross_analysis_page():
    """交叉分析页面"""
    st.header("🔄 交叉分析")

    if st.session_state.data is None:
        st.warning("⚠️ 请先导入数据")
        return

    df = st.session_state.data
    dimension_labels = config_loader.get_all_dimension_labels()

    # 分析配置
    with st.container():
        st.subheader("分析配置")

        cols = st.columns(3)

        with cols[0]:
            row_dim = st.selectbox(
                "选择竖轴维度（行）",
                options=list(dimension_labels.keys()),
                index=0,
                format_func=lambda x: dimension_labels.get(x, x)
            )

        with cols[1]:
            col_dim = st.selectbox(
                "选择横轴维度（列）",
                options=list(dimension_labels.keys()),
                index=1 if len(dimension_labels) > 1 else 0,
                format_func=lambda x: dimension_labels.get(x, x)
            )

        with cols[2]:
            analysis_type = st.selectbox(
                "分析类型",
                ["表格分析", "热力图", "堆叠柱状图"]
            )

    # 筛选条件 - 放在按钮外面以便持久化
    with st.expander("筛选条件（可选）"):
        filter_cols = st.columns(4)
        filters = {}
        for idx, (dim_key, dim_label) in enumerate(dimension_labels.items()):
            if dim_key in df.columns:
                options = analyzer.get_filter_options(df, dim_key)
                with filter_cols[idx % 4]:
                    # 使用session_state保存筛选状态
                    filter_key = f"cross_filter_{dim_key}"
                    if filter_key not in st.session_state:
                        st.session_state[filter_key] = []
                    selected = st.multiselect(
                        f"筛选 {dim_label}",
                        options=options,
                        default=st.session_state[filter_key],
                        key=filter_key
                    )
                    if selected:
                        filters[dim_key] = selected

    # 执行分析
    if st.button("🔍 开始分析", type="primary"):
        with st.spinner("正在分析中..."):
            # 执行交叉分析
            cross_tab = analyzer.cross_analysis(df, row_dim, col_dim, filters)

        # 显示结果
        st.subheader(f"📊 {dimension_labels[row_dim]} × {dimension_labels[col_dim]} 交叉分析")

        if analysis_type == "表格分析":
            # 表格展示
            st.dataframe(cross_tab, use_container_width=True)

            # 导出功能
            csv = cross_tab.to_csv().encode('utf-8')
            st.download_button(
                label="📥 导出为CSV",
                data=csv,
                file_name=f"交叉分析_{row_dim}_{col_dim}.csv",
                mime="text/csv"
            )

        elif analysis_type == "热力图":
            fig = visualizer.create_heatmap(cross_tab, f"{dimension_labels[row_dim]} × {dimension_labels[col_dim]} 热力图")
            st.plotly_chart(fig, use_container_width=True)

        elif analysis_type == "堆叠柱状图":
            # 转换为长格式用于堆叠图
            cross_long = cross_tab.reset_index().melt(
                id_vars=[row_dim],
                var_name=col_dim,
                value_name='数量'
            )
            # 过滤掉合计行和合计列
            if row_dim in cross_long.columns:
                cross_long = cross_long[cross_long[row_dim] != '合计']
            if col_dim in cross_long.columns:
                cross_long = cross_long[cross_long[col_dim] != 'All']
            fig = visualizer.create_stacked_bar(cross_long, row_dim, '数量', col_dim)
            st.plotly_chart(fig, use_container_width=True)


def show_environment_page():
    """环境漏出分析页面"""
    st.header("📈 环境漏出分析")

    if st.session_state.data is None:
        st.warning("⚠️ 请先导入数据")
        return

    df = st.session_state.data
    dimension_labels = config_loader.get_all_dimension_labels()

    # 验证必要的列存在
    if 'environment' not in df.columns:
        st.error("数据中缺少环境(environment)字段，无法进行分析")
        return

    # 选择业务维度 - 只显示存在于数据中的列
    available_dims = [k for k in dimension_labels.keys() if k in df.columns and k != 'environment']

    if not available_dims:
        st.warning("数据中没有可用的业务维度")
        return

    business_dim = st.selectbox(
        "选择业务维度",
        options=available_dims,
        index=0,
        format_func=lambda x: dimension_labels.get(x, x)
    )

    # 执行分析
    if st.button("🔍 分析环境漏出", type="primary"):
        with st.spinner("正在分析环境漏出..."):
            result = analyzer.environment_leak_analysis(df, business_dim, 'environment')

        if not result.empty:
            st.subheader("📊 各环境问题分布")

            # 显示表格
            st.dataframe(result, use_container_width=True)

            # 堆叠柱状图
            st.subheader("📈 环境问题分布图")

            # 准备数据
            env_cols = [c for c in result.columns if c not in ['测试环境问题数', '总问题数', '现网漏出率(%)']]
            plot_data = result[env_cols].reset_index()
            # 过滤掉合计行 - 需要检查原始索引名或'index'
            idx_col = business_dim if business_dim in plot_data.columns else 'index'
            if idx_col in plot_data.columns:
                plot_data = plot_data[plot_data[idx_col] != '合计']

            if not plot_data.empty:
                fig = visualizer.create_stacked_bar(plot_data, business_dim)
                st.plotly_chart(fig, use_container_width=True)

            # 现网漏出率
            if '现网漏出率(%)' in result.columns:
                st.subheader("⚠️ 现网漏出率")

                leak_data = result[['总问题数', '现网漏出率(%)']].dropna().sort_values('现网漏出率(%)', ascending=False)
                # 移除合计行
                leak_data = leak_data[leak_data.index != '合计']

                if not leak_data.empty:
                    # 重置索引以便x轴显示业务名称
                    leak_data_reset = leak_data.reset_index()
                    # 确保 'index' 列存在
                    x_col = 'index' if 'index' in leak_data_reset.columns else leak_data_reset.columns[0]
                    fig = px.bar(
                        leak_data_reset,
                        x=x_col,
                        y='现网漏出率(%)',
                        title="各业务现网漏出率(%)",
                        color='现网漏出率(%)',
                        color_continuous_scale='RdYlGn_r'
                    )
                    fig.update_layout(xaxis_title=business_dim)
                    st.plotly_chart(fig, use_container_width=True)

            # 导出
            csv = result.to_csv().encode('utf-8')
            st.download_button(
                label="📥 导出分析结果",
                data=csv,
                file_name="环境漏出分析.csv",
                mime="text/csv"
            )


def show_severity_page():
    """严重程度分析页面"""
    st.header("⚠️ 严重程度分析")

    if st.session_state.data is None:
        st.warning("⚠️ 请先导入数据")
        return

    df = st.session_state.data
    dimension_labels = config_loader.get_all_dimension_labels()

    # 选择维度 - 只显示存在于数据中的列
    available_dims = [k for k in dimension_labels.keys() if k in df.columns and k != 'severity']

    if not available_dims:
        st.warning("数据中没有可用的分析维度")
        return

    cols = st.columns(2)

    with cols[0]:
        row_dim = st.selectbox(
            "选择分析维度",
            options=available_dims,
            index=0,
            format_func=lambda x: dimension_labels.get(x, x)
        )

    # 执行分析
    if 'severity' not in df.columns:
        st.error("数据中缺少严重程度(severity)字段，无法进行分析")
        return

    if st.button("🔍 分析严重程度", type="primary"):
        with st.spinner("正在分析严重程度..."):
            result = analyzer.severity_distribution(df, row_dim, 'severity')

        if not result.empty:
            st.subheader(f"📊 {dimension_labels[row_dim]} 严重程度分布")

            # 显示表格
            st.dataframe(result, use_container_width=True)

            # 严重问题占比
            if '严重问题占比(%)' in result.columns:
                st.subheader("⚠️ 严重问题占比")

                severe_data = result[['严重问题数', '严重问题占比(%)']].dropna()
                severe_data = severe_data.sort_values('严重问题占比(%)', ascending=False)

                # 过滤掉合计行
                if 'All' in severe_data.index:
                    severe_data = severe_data[severe_data.index != 'All']

                if not severe_data.empty:
                    # 重置索引以便x轴显示业务名称
                    severe_data_reset = severe_data.reset_index()
                    # 确保 'index' 列存在
                    x_col = 'index' if 'index' in severe_data_reset.columns else severe_data_reset.columns[0]
                    fig = px.bar(
                        severe_data_reset,
                        x=x_col,
                        y='严重问题占比(%)',
                        title="严重问题占比(%)",
                        color='严重问题占比(%)',
                        color_continuous_scale='RdYlGn_r'
                    )
                    fig.update_layout(xaxis_title=row_dim)
                    st.plotly_chart(fig, use_container_width=True)

            # 导出
            csv = result.to_csv().encode('utf-8')
            st.download_button(
                label="📥 导出分析结果",
                data=csv,
                file_name="严重程度分析.csv",
                mime="text/csv"
            )


def show_data_list_page():
    """数据列表页面"""
    st.header("📋 数据列表")

    if st.session_state.data is None:
        st.warning("⚠️ 请先导入数据")
        return

    df = st.session_state.data
    dimension_labels = config_loader.get_all_dimension_labels()

    # 筛选
    with st.expander("筛选条件", expanded=True):
        cols = st.columns(4)

        for idx, (dim_key, dim_label) in enumerate(dimension_labels.items()):
            if dim_key in df.columns:
                options = analyzer.get_filter_options(df, dim_key)
                with cols[idx % 4]:
                    selected = st.multiselect(
                        f"筛选 {dim_label}",
                        options=options,
                        key=f"list_filter_{dim_key}"
                    )
                    if selected:
                        df = df[df[dim_key].isin(selected)]

    # 显示数据
    st.write(f"共 {len(df)} 条数据")

    # 显示表格
    st.dataframe(
        df,
        use_container_width=True,
        height=500
    )

    # 导出
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 导出全部数据",
        data=csv,
        file_name="问题单数据.csv",
        mime="text/csv"
    )


def show_root_cause_page():
    """根因分析页面"""
    st.header("🔍 根因分析")

    if st.session_state.data is None:
        st.warning("⚠️ 请先导入数据")
        return

    df = st.session_state.data
    dimension_labels = config_loader.get_all_dimension_labels()

    # 检查根因字段是否存在（支持中英文列名）
    root_cause_cols = [col for col in df.columns if 'root_cause' in col.lower() or '根因' in col]
    if not root_cause_cols:
        st.warning("⚠️ 数据中缺少根因分类字段，无法进行根因分析")
        st.info("请在数据中添加 '根因分类' 或 'root_cause' 字段")
        return

    root_cause_col = root_cause_cols[0]

    # 分析配置
    cols = st.columns(2)

    with cols[0]:
        row_dim = st.selectbox(
            "选择分析维度",
            options=[k for k in dimension_labels.keys() if k in df.columns and k != 'root_cause'],
            index=0,
            format_func=lambda x: dimension_labels.get(x, x)
        )

    # 执行分析
    if st.button("🔍 分析根因", type="primary"):
        with st.spinner("正在分析根因..."):
            result = analyzer.root_cause_analysis(df, row_dim, root_cause_col)

        if not result.empty:
            st.subheader(f"📊 {dimension_labels[row_dim]} × 根因分类 交叉分析")

            # 显示表格
            st.dataframe(result, use_container_width=True)

            # 根因分布饼图
            st.subheader("📈 根因分布")

            root_cause_counts = df[root_cause_col].value_counts().reset_index()
            root_cause_counts.columns = ['根因分类', '数量']

            fig = px.pie(
                root_cause_counts,
                values='数量',
                names='根因分类',
                title="根因分类分布",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)

            # 根因 × 维度 热力图
            st.subheader("🔥 根因热力图")

            numeric_cols = [c for c in result.columns if '占比' not in c and c != 'All' and c != '合计']
            heatmap_data = result[numeric_cols] if numeric_cols else result

            if '合计' in heatmap_data.index:
                heatmap_data = heatmap_data.drop('合计')

            if not heatmap_data.empty:
                fig = px.imshow(
                    heatmap_data,
                    text_auto=True,
                    aspect="auto",
                    color_continuous_scale="RdYlGn_r",
                    title="根因分布热力图"
                )
                st.plotly_chart(fig, use_container_width=True)

            # 导出
            csv = result.to_csv().encode('utf-8')
            st.download_button(
                label="📥 导出分析结果",
                data=csv,
                file_name="根因分析.csv",
                mime="text/csv"
            )

    # 整改措施追踪
    st.markdown("---")
    st.subheader("📋 整改措施追踪")

    if 'fix_measure' in df.columns:
        has_fix = df[df['fix_measure'].notna() & (df['fix_measure'] != '')]
        no_fix = df[df['fix_measure'].isna() | (df['fix_measure'] == '')]

        cols = st.columns(3)
        with cols[0]:
            st.metric("总问题数", len(df))
        with cols[1]:
            st.metric("已填写整改措施", len(has_fix))
        with cols[2]:
            st.metric("未填写整改措施", len(no_fix))

        # 未填写整改措施的问题列表
        if not no_fix.empty:
            with st.expander(f"⚠️ 未填写整改措施的问题 ({len(no_fix)}个)"):
                st.dataframe(no_fix[['bug_id', 'title', 'root_cause', 'business_type']].head(20))
    else:
        st.info("数据中无整改措施字段")


def show_leak_analysis_page():
    """漏测分析页面"""
    st.header("💧 漏测分析")

    if st.session_state.data is None:
        st.warning("⚠️ 请先导入数据")
        return

    df = st.session_state.data

    # 检查漏测分析字段是否存在（支持中英文列名）
    leak_cols = [col for col in df.columns if 'leak' in col.lower() or '漏测' in col]
    if not leak_cols:
        st.warning("⚠️ 数据中缺少漏测分析字段，无法进行漏测分析")
        st.info("请在数据中添加 '漏测分析' 或 'leak_analysis' 字段")
        return

    leak_analysis_col = leak_cols[0]
    # 尝试找到漏测问题类型列
    leak_type_cols = [col for col in df.columns if 'leak' in col.lower() and 'type' in col.lower() or '漏测' in col and '类型' in col]
    leak_type_col = leak_type_cols[0] if leak_type_cols else None

    # 执行漏测分析
    result = analyzer.leak_analysis(df, 'business_type', leak_analysis_col, leak_type_col if leak_type_col else 'leak_analysis_type')

    # 漏测概览
    st.subheader("📊 漏测概览")

    cols = st.columns(4)
    with cols[0]:
        st.metric("总问题数", result.get('总问题数', len(df)))
    with cols[1]:
        st.metric("现网问题数", result.get('现网问题数', 0))
    with cols[2]:
        st.metric("漏测率", f"{result.get('漏测率', 0)}%")
    with cols[3]:
        if 'leak_analysis_type' in df.columns:
            st.metric("漏测问题类型数", len(df['leak_analysis_type'].dropna().unique()))

    # 漏测原因分布
    if '漏测原因分布' in result:
        st.subheader("📈 漏测原因分布")

        leak_dist = result['漏测原因分布'].reset_index()
        leak_dist.columns = ['漏测原因', '数量']

        fig = px.pie(
            leak_dist,
            values='数量',
            names='漏测原因',
            title="漏测原因分布",
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)

    # 漏测问题类型分布
    if '漏测问题类型分布' in result:
        st.subheader("📊 漏测问题类型分布")

        leak_type_dist = result['漏测问题类型分布'].reset_index()
        leak_type_dist.columns = ['漏测问题类型', '数量']

        fig = px.bar(
            leak_type_dist,
            x='漏测问题类型',
            y='数量',
            title="漏测问题类型分布",
            color='数量',
            color_continuous_scale='RdYlGn_r'
        )
        st.plotly_chart(fig, use_container_width=True)

    # 漏测 × 业务交叉分析
    if '漏测业务交叉' in result:
        st.subheader("🔥 漏测 × 业务模块 交叉分析")

        cross_data = result['漏测业务交叉']
        if '合计' in cross_data.index:
            cross_data = cross_data.drop('合计')

        if not cross_data.empty:
            fig = px.imshow(
                cross_data,
                text_auto=True,
                aspect="auto",
                color_continuous_scale="RdYlGn_r",
                title="漏测业务交叉分析"
            )
            st.plotly_chart(fig, use_container_width=True)

    # 漏测 × 漏测类型交叉
    if '漏测类型交叉' in result:
        st.subheader("🔥 漏测原因 × 漏测问题类型 交叉分析")

        cross_data = result['漏测类型交叉']
        if '合计' in cross_data.index:
            cross_data = cross_data.drop('合计')

        if not cross_data.empty:
            fig = px.imshow(
                cross_data,
                text_auto=True,
                aspect="auto",
                color_continuous_scale="Blues",
                title="漏测原因与问题类型交叉"
            )
            st.plotly_chart(fig, use_container_width=True)

    # 漏测详情列表
    st.markdown("---")
    st.subheader("📋 漏测问题详情")

    if 'environment' in df.columns:
        # 筛选现网问题
        prod_issues = df[df['environment'].astype(str).str.contains('prod|现网', case=False, na=False)]

        if not prod_issues.empty:
            st.write(f"现网暴露问题列表（共 {len(prod_issues)} 个）：")

            # 显示关键列 - 动态获取列名
            display_cols = ['bug_id', 'title', 'business_type']
            # 添加根因相关列
            root_cause_cols = [c for c in prod_issues.columns if 'root_cause' in c.lower() or '根因' in c]
            display_cols.extend(root_cause_cols)
            # 添加漏测相关列
            leak_cols = [c for c in prod_issues.columns if 'leak' in c.lower() or '漏测' in c]
            display_cols.extend(leak_cols)

            available_cols = [c for c in display_cols if c in prod_issues.columns]
            if available_cols:
                st.dataframe(prod_issues[available_cols], use_container_width=True)

            # 导出
            csv = prod_issues.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 导出漏测问题",
                data=csv,
                file_name="漏测问题列表.csv",
                mime="text/csv"
            )


def show_persistence_page():
    """数据持久化页面"""
    st.header("💾 数据持久化")

    from data_persistence import (
        show_persistence_ui,
        list_saved_sessions,
        load_analysis_session,
        delete_session,
        export_to_excel,
        export_to_csv
    )

    # 使用持久化UI
    show_persistence_ui()


def show_qmatrix_page():
    """Q-Matrix 分析引擎页面"""
    if st.session_state.data is None:
        st.warning("⚠️ 请先导入数据")
        return

    # 渲染 Q-Matrix 分析
    render_full_analysis(st.session_state.data)


def show_summary_analysis_page():
    """汇总分析页面"""
    st.header("📝 汇总分析")

    if st.session_state.data is None:
        st.warning("⚠️ 请先导入数据")
        return

    df = st.session_state.data

    # 自动生成汇总分析
    st.subheader("🤖 自动生成的汇总分析")

    # 页面加载时自动生成汇总（如果还没有）
    if 'summary_analysis' not in st.session_state or not st.session_state.summary_analysis:
        with st.spinner("正在生成汇总分析..."):
            summary = analyzer.generate_summary(df)
            st.session_state.summary_analysis = summary

    # 重新生成按钮
    if st.button("🔄 重新生成汇总分析", type="secondary"):
        with st.spinner("正在生成汇总分析..."):
            summary = analyzer.generate_summary(df)
            st.session_state.summary_analysis = summary
            st.rerun()

    # 显示已有的汇总分析或编辑
    current_summary = st.session_state.summary_analysis if 'summary_analysis' in st.session_state else ""

    # 允许人工编辑
    edited_summary = st.text_area(
        "汇总总结（可人工改写）",
        value=current_summary,
        height=400,
        key="summary_edit"
    )

    # 保存编辑后的内容
    if edited_summary != current_summary:
        st.session_state.summary_analysis = edited_summary

    # 复制按钮
    if edited_summary:
        st.code(edited_summary, language="markdown")

    # 一页总览 Dashboard
    st.markdown("---")
    st.subheader("📊 一页总览 (Dashboard)")

    # 关键指标
    cols = st.columns(4)
    with cols[0]:
        st.metric("总问题数", len(df))

    # 严重问题
    if 'severity' in df.columns:
        severe = df[df['severity'].astype(str).str.contains('P0|P1', case=False, na=False)]
        with cols[1]:
            st.metric("严重问题(P0+P1)", len(severe), delta=f"{round(len(severe)/len(df)*100, 1)}%")

    # 漏测问题
    if 'environment' in df.columns:
        prod = df[df['environment'].astype(str).str.contains('prod|现网', case=False, na=False)]
        with cols[2]:
            st.metric("现网问题", len(prod), delta=f"{round(len(prod)/len(df)*100, 1)}%")

    # 回归问题
    if 'is_regression' in df.columns:
        regression = df[df['is_regression'].astype(str).str.contains('yes|是', case=False, na=False)]
        with cols[3]:
            st.metric("回归问题", len(regression), delta=f"{round(len(regression)/len(df)*100, 1)}%")

    # 趋势图（如果有时间字段）
    if 'create_time' in df.columns:
        st.subheader("📈 问题趋势")

        try:
            df_copy = df.copy()
            df_copy['create_time'] = pd.to_datetime(df_copy['create_time'], errors='coerce')
            df_copy = df_copy.dropna(subset=['create_time'])

            if not df_copy.empty:
                df_copy['month'] = df_copy['create_time'].dt.to_period('M').astype(str)
                trend = df_copy.groupby('month').size().reset_index(name='问题数')

                fig = px.line(
                    trend,
                    x='month',
                    y='问题数',
                    title="问题数量趋势",
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"无法生成趋势图: {str(e)}")

    # 根因分布（如果有）
    if 'root_cause' in df.columns:
        st.subheader("🔍 根因分布")

        root_dist = df['root_cause'].value_counts().reset_index()
        root_dist.columns = ['根因', '数量']

        fig = px.bar(
            root_dist.head(10),
            x='根因',
            y='数量',
            title="根因分布 (Top10)",
            color='数量',
            color_continuous_scale='RdYlGn_r'
        )
        st.plotly_chart(fig, use_container_width=True)

    # 漏测分布（如果有）
    leak_dist_cols = [col for col in df.columns if 'leak' in col.lower() or '漏测' in col]
    if leak_dist_cols:
        st.subheader("💧 漏测分布")

        leak_col = leak_dist_cols[0]
        leak_dist = df[leak_col].value_counts().reset_index()
        leak_dist.columns = ['漏测原因', '数量']

        fig = px.bar(
            leak_dist,
            x='漏测原因',
            y='数量',
            title="漏测原因分布",
            color='数量',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)


def show_deep_analysis_page(perspective: str = "dev"):
    """深层分析页面"""
    from qmatrix_engine import QMatrixEngine
    from qmatrix_aggregator import QMatrixAggregator

    st.header("🔍 深层分析")

    if st.session_state.data is None:
        st.warning("⚠️ 请先导入数据")
        return

    df = st.session_state.data
    engine = QMatrixEngine(df)
    aggregator = QMatrixAggregator(df, engine)

    # 子导航
    tabs = {
        "dev": ("💻 开发视角", "开发"),
        "test": ("🧪 测试视角", "测试"),
        "biz": ("📊 业务视角", "业务")
    }

    tab_names = list(tabs.keys())
    tab_labels = [t[0] for t in tabs.values()]

    if perspective == "dev":
        active_tab = 0
    elif perspective == "test":
        active_tab = 1
    else:
        active_tab = 2

    selected = st.segmented_control("选择视角", tab_labels, default=tab_labels[active_tab], key="perspective_selector")

    if selected == "💻 开发视角":
        st.subheader("💻 开发视角 - 根因分析")
        dev_result = aggregator.analyze_developer_perspective()

        if dev_result["status"] == "success" and dev_result["insights"]:
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
            st.info("📋 开发视角数据不可用，请导入包含「根因详细」字段的数据")

    elif selected == "🧪 测试视角":
        st.subheader("🧪 测试视角 - 漏测分析")
        test_result = aggregator.analyze_tester_perspective()

        if test_result["status"] == "success" and test_result["insights"]:
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
            st.info("📋 测试视角数据不可用，请导入包含「漏测分析」字段的数据")

    elif selected == "📊 业务视角":
        st.subheader("📊 业务视角 - 风险分析")
        biz_result = aggregator.analyze_business_perspective()

        if biz_result["status"] == "success" and biz_result["insights"]:
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
        else:
            st.info("📋 业务视角数据不可用，请导入包含「影响程度」字段的数据")


def show_aggregated_analysis_page():
    """聚合分析页面"""
    from qmatrix_engine import QMatrixEngine
    from qmatrix_aggregator import QMatrixAggregator

    st.header("🔑 聚合分析")

    if st.session_state.data is None:
        st.warning("⚠️ 请先导入数据")
        return

    df = st.session_state.data
    engine = QMatrixEngine(df)
    aggregator = QMatrixAggregator(df, engine)

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

    if summary["total_insights"] == 0:
        st.info("📋 聚合分析数据不可用，请导入包含「根因详细」「漏测分析」等字段的完整数据")
        st.markdown("""
        **需要的字段：**
        - 根因详细 - 用于开发视角分析
        - 漏测分析 - 用于测试视角分析
        - 影响程度 - 用于业务视角分析
        """)
        return

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


def show_actions_page():
    """改进建议页面"""
    from qmatrix_aggregator import ActionItemManager

    st.header("📝 改进建议")

    action_manager = ActionItemManager()

    # 标签页
    tab1, tab2, tab3 = st.tabs(["📋 建议列表", "➕ 添加建议", "🔧 管理"])

    with tab1:
        st.subheader("建议列表")

        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox("状态", ["全部", "pending", "in_progress", "completed"], key="action_status")
        with col2:
            priority_filter = st.selectbox("优先级", ["全部", "high", "medium", "low"], key="action_priority")

        status = None if status_filter == "全部" else status_filter
        priority = None if priority_filter == "全部" else priority_filter

        items = action_manager.get_items(status=status, priority=priority)

        if not items:
            st.info("暂无改进建议，请点击「添加建议」创建")
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


if __name__ == "__main__":
    main()
