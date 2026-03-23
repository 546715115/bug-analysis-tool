"""
数据持久化模块 - 支持保存和加载分析数据
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import json
from datetime import datetime
import os


def get_data_dir():
    """获取数据存储目录"""
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def save_analysis_session(data: pd.DataFrame, metadata: dict = None) -> str:
    """
    保存分析会话数据

    Args:
        data: 要保存的DataFrame
        metadata: 可选的元数据

    Returns:
        保存的文件路径
    """
    data_dir = get_data_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analysis_{timestamp}.parquet"
    filepath = data_dir / filename

    # 保存数据为Parquet格式（高效压缩）
    data.to_parquet(filepath, index=False)

    # 保存元数据
    if metadata is None:
        metadata = {}
    metadata.update({
        "saved_at": datetime.now().isoformat(),
        "rows": len(data),
        "columns": list(data.columns)
    })

    meta_file = filepath.with_suffix('.json')
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return str(filepath)


def load_analysis_session(filepath: str) -> tuple:
    """
    加载分析会话数据

    Returns:
        (data, metadata) 元组
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"文件不存在: {filepath}")

    # 加载数据
    data = pd.read_parquet(filepath)

    # 加载元数据
    meta_file = filepath.with_suffix('.json')
    metadata = {}
    if meta_file.exists():
        with open(meta_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

    return data, metadata


def list_saved_sessions() -> list:
    """列出所有已保存的会话"""
    data_dir = get_data_dir()
    sessions = []

    for parquet_file in data_dir.glob("analysis_*.parquet"):
        meta_file = parquet_file.with_suffix('.json')
        if meta_file.exists():
            with open(meta_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {}

        sessions.append({
            "path": str(parquet_file),
            "filename": parquet_file.name,
            "saved_at": metadata.get("saved_at", ""),
            "rows": metadata.get("rows", 0)
        })

    # 按时间排序（最新的在前）
    sessions.sort(key=lambda x: x["saved_at"], reverse=True)
    return sessions


def delete_session(filepath: str) -> bool:
    """删除已保存的会话"""
    filepath = Path(filepath)
    if filepath.exists():
        filepath.unlink()

        # 同时删除元数据文件
        meta_file = filepath.with_suffix('.json')
        if meta_file.exists():
            meta_file.unlink()
        return True
    return False


def export_to_excel(data: pd.DataFrame, filename: str = None) -> str:
    """
    导出数据到Excel

    Returns:
        保存的文件路径
    """
    data_dir = get_data_dir()

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{timestamp}.xlsx"

    filepath = data_dir / filename
    data.to_excel(filepath, index=False)
    return str(filepath)


def export_to_csv(data: pd.DataFrame, filename: str = None) -> str:
    """
    导出数据到CSV

    Returns:
        保存的文件路径
    """
    data_dir = get_data_dir()

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{timestamp}.csv"

    filepath = data_dir / filename
    data.to_csv(filepath, index=False, encoding='utf-8-sig')
    return str(filepath)


def show_persistence_ui():
    """显示数据持久化UI"""
    st.subheader("💾 数据持久化")

    tab1, tab2 = st.tabs(["💾 保存当前数据", "📂 加载已保存数据"])

    with tab1:
        if st.session_state.data is not None:
            col1, col2 = st.columns(2)

            with col1:
                if st.button("保存当前数据", use_container_width=True):
                    try:
                        filepath = save_analysis_session(
                            st.session_state.data,
                            {"source": st.session_state.get("data_source", "unknown")}
                        )
                        st.success(f"✅ 数据已保存到: {Path(filepath).name}")
                    except Exception as e:
                        st.error(f"保存失败: {e}")

            with col2:
                if st.button("导出为Excel", use_container_width=True):
                    try:
                        filepath = export_to_excel(st.session_state.data)
                        st.success(f"✅ 已导出到: {Path(filepath).name}")
                    except Exception as e:
                        st.error(f"导出失败: {e}")

            st.info(f"当前数据: {len(st.session_state.data)} 行")
        else:
            st.warning("请先导入数据")

    with tab2:
        sessions = list_saved_sessions()

        if sessions:
            st.write("已保存的数据会话:")

            for session in sessions:
                col1, col2, col3 = st.columns([3, 2, 1])

                with col1:
                    st.write(f"**{session['filename']}**")
                with col2:
                    st.caption(f"{session['rows']} 行 | {session['saved_at'][:19] if session['saved_at'] else '未知时间'}")
                with col3:
                    if st.button("加载", key=f"load_{session['path']}"):
                        try:
                            data, metadata = load_analysis_session(session['path'])
                            st.session_state.data = data
                            st.session_state.data_source = metadata.get("source", "已保存会话")
                            st.success(f"✅ 已加载 {len(data)} 行数据")
                            st.rerun()
                        except Exception as e:
                            st.error(f"加载失败: {e}")

                st.markdown("---")
        else:
            st.info("暂无已保存的数据")
