"""
自定义导航组件 - 抽屉式树形菜单
"""

import streamlit as st
from typing import Dict, List, Callable


class NavigationItem:
    """导航项"""

    def __init__(self, key: str, label: str, icon: str = "", children: List = None, page_func: str = None):
        self.key = key
        self.label = label
        self.icon = icon
        self.children = children or []
        self.page_func = page_func  # 对应的页面函数名


def render_tree_navigation(menu_structure: List[NavigationItem], current_menu: str):
    """
    渲染树形导航菜单

    Args:
        menu_structure: 菜单结构
        current_menu: 当前选中的菜单 key
    """

    # 添加自定义 CSS
    st.markdown("""
    <style>
    /* 抽屉式导航样式 */
    .nav-item {
        padding: 8px 12px;
        margin: 2px 0;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s;
    }

    .nav-item:hover {
        background: rgba(255, 255, 255, 0.1);
    }

    .nav-item.active {
        background: rgba(0, 120, 212, 0.2);
        border-left: 3px solid #0078D4;
    }

    .nav-parent {
        font-weight: 600;
        padding: 10px 12px;
        margin: 5px 0;
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.05);
    }

    .nav-child {
        padding-left: 30px;
        font-size: 14px;
    }

    .nav-child.selected {
        background: rgba(0, 120, 212, 0.15);
        border-radius: 4px;
        color: #00d4ff;
    }

    /* Streamlit expander 样式覆盖 */
    .streamlit-expanderHeader {
        background: transparent !important;
        border: none !important;
    }

    .streamlit-expanderHeader:hover {
        background: rgba(255, 255, 255, 0.05) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    selected_key = None

    for item in menu_structure:
        # 一级菜单（无子菜单）
        if not item.children:
            col1, col2 = st.columns([1, 20])
            with col1:
                st.write(item.icon)
            with col2:
                if st.button(
                    f"{item.label}",
                    key=f"nav_{item.key}",
                    use_container_width=True,
                    type="primary" if current_menu == item.key else "secondary"
                ):
                    selected_key = item.key

        # 一级菜单（有子菜单）- 使用 expander
        else:
            with st.expander(f"{item.icon} {item.label}", expanded=True):
                # 子菜单
                for child in item.children:
                    col1, col2 = st.columns([1, 20])
                    with col1:
                        st.write(child.icon if child.icon else "•")
                    with col2:
                        is_selected = current_menu == child.key
                        if st.button(
                            f"{child.label}",
                            key=f"nav_{child.key}",
                            use_container_width=True,
                            type="primary" if is_selected else "secondary"
                        ):
                            selected_key = child.key

                        # 如果选中，显示标记
                        if is_selected:
                            st.markdown(f"""
                            <div style="background: #0078D4; padding: 2px 8px; border-radius: 4px; font-size: 12px;">
                                ✓ 当前
                            </div>
                            """, unsafe_allow_html=True)

    return selected_key


# 定义菜单结构
def get_menu_structure() -> List[NavigationItem]:
    """获取菜单结构"""

    return [
        # 一级
        NavigationItem("import", "📥 数据导入", "📥", page_func="show_import_page"),

        # 概览
        NavigationItem("overview", "📊 数据概览", "📊", page_func="show_overview_page"),

        # 浅层矩阵（带子菜单）
        NavigationItem("shallow", "📈 浅层矩阵", "📈", children=[
            NavigationItem("cross_analysis", "交叉分析", "🔄"),
            NavigationItem("environment", "环境漏出", "📈"),
            NavigationItem("severity", "严重程度", "⚠️"),
            NavigationItem("root_cause", "根因分析", "🔍"),
            NavigationItem("leak", "漏测分析", "💧"),
            NavigationItem("summary", "汇总分析", "📝"),
        ]),

        # 深层分析
        NavigationItem("deep", "🔍 深层分析", "🔍", children=[
            NavigationItem("deep_dev", "开发视角", "💻"),
            NavigationItem("deep_test", "测试视角", "🧪"),
            NavigationItem("deep_biz", "业务视角", "📊"),
        ]),

        # 聚合分析
        NavigationItem("aggregated", "🔑 聚合分析", "🔑", page_func="show_qmatrix_enhanced_page"),

        # 改进建议
        NavigationItem("actions", "📝 改进建议", "📝", page_func="show_action_items_page"),

        # 其他
        NavigationItem("data_list", "📋 数据列表", "📋", page_func="show_data_list_page"),
        NavigationItem("persistence", "💾 数据持久化", "💾", page_func="show_persistence_page"),

        # 成果导出
        NavigationItem("export", "📤 成果导出", "📤", page_func="show_export_page"),
    ]


# 菜单 key 到页面函数的映射
MENU_PAGE_MAP = {
    "import": "show_import_page",
    "overview": "show_overview_page",
    "cross_analysis": "show_cross_analysis_page",
    "environment": "show_environment_page",
    "severity": "show_severity_page",
    "root_cause": "show_root_cause_page",
    "leak": "show_leak_analysis_page",
    "summary": "show_summary_analysis_page",
    "deep_dev": "show_deep_dev_page",
    "deep_test": "show_deep_test_page",
    "deep_biz": "show_deep_biz_page",
    "aggregated": "show_qmatrix_enhanced_page",
    "actions": "show_action_items_page",
    "data_list": "show_data_list_page",
    "persistence": "show_persistence_page",
    "export": "show_export_page",
}
