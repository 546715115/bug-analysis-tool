"""
增强版数据管理器
支持多数据导入、合并、数据集管理
"""

import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime
import json
import uuid


class Dataset:
    """数据集"""

    def __init__(self, id: str, name: str, data: pd.DataFrame, source: str = "import"):
        self.id = id
        self.name = name
        self.data = data
        self.source = source
        self.created_at = datetime.now().isoformat()
        self.row_count = len(data)
        self.columns = list(data.columns)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "source": self.source,
            "created_at": self.created_at,
            "row_count": self.row_count,
            "columns": self.columns
        }


class DataManager:
    """数据管理器"""

    def __init__(self, storage_path: str = None):
        if storage_path is None:
            storage_path = Path(__file__).parent / "data" / "datasets"
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.meta_file = self.storage_path / "datasets_meta.json"
        self._load_meta()

    def _load_meta(self):
        """加载元数据"""
        if self.meta_file.exists():
            with open(self.meta_file, 'r', encoding='utf-8') as f:
                self.meta = json.load(f)
        else:
            self.meta = {"datasets": [], "current_id": None}

    def _save_meta(self):
        """保存元数据"""
        with open(self.meta_file, 'w', encoding='utf-8') as f:
            json.dump(self.meta, f, ensure_ascii=False, indent=2)

    def add_dataset(self, name: str, data: pd.DataFrame, source: str = "import") -> Dataset:
        """添加数据集"""
        dataset = Dataset(
            id=str(uuid.uuid4())[:8],
            name=name,
            data=data,
            source=source
        )

        # 保存数据文件
        data_file = self.storage_path / f"{dataset.id}.parquet"
        data.to_parquet(data_file, index=False)

        # 保存元数据
        self.meta["datasets"].append(dataset.to_dict())
        self._save_meta()

        return dataset

    def get_dataset(self, dataset_id: str) -> Dataset:
        """获取数据集"""
        # 查找元数据
        meta = None
        for d in self.meta.get("datasets", []):
            if d["id"] == dataset_id:
                meta = d
                break

        if not meta:
            return None

        # 加载数据
        data_file = self.storage_path / f"{dataset_id}.parquet"
        if data_file.exists():
            data = pd.read_parquet(data_file)
            return Dataset(
                id=meta["id"],
                name=meta["name"],
                data=data,
                source=meta["source"]
            )
        return None

    def list_datasets(self) -> list:
        """列出所有数据集"""
        return self.meta.get("datasets", [])

    def get_current_dataset(self) -> Dataset:
        """获取当前加载的数据集"""
        current_id = self.meta.get("current_id")
        if current_id:
            return self.get_dataset(current_id)
        return None

    def set_current_dataset(self, dataset_id: str):
        """设置当前数据集"""
        self.meta["current_id"] = dataset_id
        self._save_meta()

    def delete_dataset(self, dataset_id: str) -> bool:
        """删除数据集"""
        # 删除数据文件
        data_file = self.storage_path / f"{dataset_id}.parquet"
        if data_file.exists():
            data_file.unlink()

        # 如果是当前数据集，清除
        if self.meta.get("current_id") == dataset_id:
            self.meta["current_id"] = None

        # 删除元数据
        self.meta["datasets"] = [
            d for d in self.meta.get("datasets", [])
            if d["id"] != dataset_id
        ]
        self._save_meta()
        return True

    def merge_datasets(self, dataset_ids: list, merged_name: str = None) -> Dataset:
        """合并多个数据集"""
        datasets = []
        for ds_id in dataset_ids:
            ds = self.get_dataset(ds_id)
            if ds:
                datasets.append(ds.data)

        if not datasets:
            return None

        # 合并数据（纵向拼接）
        merged_data = pd.concat(datasets, ignore_index=True)

        return self.add_dataset(
            name=merged_name or f"合并_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            data=merged_data,
            source="merged"
        )


def render_data_manager_ui():
    """渲染数据管理器UI"""
    # 初始化管理器
    dm = DataManager()

    # 检查是否有当前加载的数据
    current_ds = dm.get_current_dataset()

    # 顶部状态栏
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if current_ds:
            st.success(f"✅ 当前数据: {current_ds.name} ({current_ds.row_count}行)")
        else:
            st.warning("⚠️ 未加载数据")

    with col2:
        if st.button("🔄 刷新"):
            st.rerun()

    with col3:
        if current_ds:
            if st.button("🗑️ 卸载数据"):
                # 清除当前会话的数据
                st.session_state.data = None
                st.session_state.data_source = None
                dm.set_current_dataset(None)
                st.rerun()

    st.markdown("---")

    # 标签页
    tab1, tab2, tab3 = st.tabs(["📥 导入/加载", "📦 数据集管理", "🔗 数据合并"])

    # ========== 1. 导入/加载 ==========
    with tab1:
        st.subheader("📥 导入新数据")

        import_type = st.radio("导入方式", ["Excel文件", "CSV文件", "API接口"], horizontal=True)

        if import_type == "Excel文件":
            st.info("支持同时上传多个Excel文件")

            uploaded_files = st.file_uploader(
                "选择Excel文件",
                type=['xlsx', 'xls'],
                accept_multiple_files=True
            )

            if uploaded_files:
                st.write(f"已选择 {len(uploaded_files)} 个文件")

                for i, file in enumerate(uploaded_files):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"📄 **{file.name}**")
                    with col2:
                        try:
                            df = pd.read_excel(file)
                            st.caption(f"{len(df)} 行")
                        except:
                            st.caption("读取失败")
                    with col3:
                        if st.button(f"导入", key=f"import_excel_{i}"):
                            try:
                                df = pd.read_excel(file)
                                # 保存到数据集
                                dataset = dm.add_dataset(
                                    name=file.name,
                                    data=df,
                                    source="excel"
                                )
                                # 加载到当前会话
                                st.session_state.data = df
                                st.session_state.data_source = file.name
                                dm.set_current_dataset(dataset.id)
                                st.success(f"✅ 已导入并加载!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"失败: {e}")

        elif import_type == "CSV文件":
            st.info("支持同时上传多个CSV文件")

            uploaded_files = st.file_uploader(
                "选择CSV文件",
                type=['csv'],
                accept_multiple_files=True
            )

            if uploaded_files:
                for i, file in enumerate(uploaded_files):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"📄 **{file.name}**")
                    with col2:
                        try:
                            df = pd.read_csv(file)
                            st.caption(f"{len(df)} 行")
                        except:
                            st.caption("读取失败")
                    with col3:
                        if st.button(f"导入", key=f"import_csv_{i}"):
                            try:
                                df = pd.read_csv(file)
                                dataset = dm.add_dataset(
                                    name=file.name,
                                    data=df,
                                    source="csv"
                                )
                                st.session_state.data = df
                                st.session_state.data_source = file.name
                                dm.set_current_dataset(dataset.id)
                                st.success(f"✅ 已导入!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"失败: {e}")

        elif import_type == "API接口":
            col1, col2 = st.columns([3, 1])
            with col1:
                api_url = st.text_input("API URL")
            with col2:
                api_name = st.text_input("名称", value="API数据")

            if st.button("🌐 从API导入", type="primary"):
                if api_url:
                    with st.spinner("正在获取数据..."):
                        try:
                            import requests
                            resp = requests.get(api_url, timeout=30, verify=True)
                            resp.raise_for_status()
                            data = resp.json()

                            if isinstance(data, list):
                                df = pd.DataFrame(data)
                            elif isinstance(data, dict) and 'data' in data:
                                df = pd.DataFrame(data['data'])
                            else:
                                df = pd.DataFrame([data])

                            dataset = dm.add_dataset(name=api_name, data=df, source="api")
                            st.session_state.data = df
                            st.session_state.data_source = api_name
                            dm.set_current_dataset(dataset.id)
                            st.success(f"✅ 导入成功! ({len(df)}行)")
                            st.rerun()
                        except Exception as e:
                            st.error(f"失败: {e}")

        st.markdown("---")

        # 快速加载已保存的数据
        st.subheader("📂 加载已保存数据")
        datasets = dm.list_datasets()

        if not datasets:
            st.info("暂无已保存的数据集")
        else:
            st.write("**已保存的数据集:**")
            for ds in datasets:
                is_current = ds["id"] == dm.meta.get("current_id")

                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    if is_current:
                        st.write(f"✅ **{ds['name']}** (当前)")
                    else:
                        st.write(f"📄 **{ds['name']}**")
                with col2:
                    st.caption(f"{ds['row_count']}行")
                with col3:
                    if not is_current:
                        if st.button("📥 加载", key=f"load_{ds['id']}"):
                            ds_obj = dm.get_dataset(ds["id"])
                            if ds_obj:
                                st.session_state.data = ds_obj.data
                                st.session_state.data_source = ds_obj.name
                                dm.set_current_dataset(ds["id"])
                                st.rerun()
                with col4:
                    if st.button("🗑️", key=f"del_{ds['id']}"):
                        dm.delete_dataset(ds["id"])
                        st.rerun()

    # ========== 2. 数据集管理 ==========
    with tab2:
        st.subheader("📦 数据集管理")

        datasets = dm.list_datasets()

        if not datasets:
            st.info("暂无已保存的数据集")
        else:
            # 批量选择
            selected_ids = st.multiselect(
                "选择数据集",
                options=[d["id"] for d in datasets],
                format_func=lambda x: next((d["name"] for d in datasets if d["id"] == x), x)
            )

            if selected_ids:
                col1, col2 = st.columns(2)

                with col1:
                    if len(selected_ids) == 1:
                        ds = dm.get_dataset(selected_ids[0])
                        if ds:
                            # 预览
                            st.write(f"**{ds.name}** 预览:")
                            st.dataframe(ds.data.head(10), use_container_width=True)

                with col2:
                    st.write("批量操作:")
                    if st.button(f"🗑️ 删除选中的 {len(selected_ids)} 个", use_container_width=True):
                        for ds_id in selected_ids:
                            dm.delete_dataset(ds_id)
                        st.success("已删除")
                        st.rerun()

                    if len(selected_ids) >= 2:
                        merged_name = st.text_input("合并后名称")
                        if st.button(f"🔗 合并选中的 {len(selected_ids)} 个", use_container_width=True):
                            new_ds = dm.merge_datasets(selected_ids, merged_name)
                            if new_ds:
                                st.success(f"合并成功: {new_ds.name}")
                                st.rerun()

    # ========== 3. 数据合并 ==========
    with tab3:
        st.subheader("🔗 数据集合并")

        if len(datasets) < 2:
            st.warning("需要至少2个数据集才能合并，请先导入数据")
        else:
            merge_ids = st.multiselect(
                "选择要合并的数据集",
                options=[d["id"] for d in datasets],
                format_func=lambda x: next((d["name"] for d in datasets if d["id"] == x), x)
            )

            if len(merge_ids) >= 2:
                # 预览
                if st.checkbox("预览合并结果"):
                    dfs = []
                    for mid in merge_ids:
                        ds = dm.get_dataset(mid)
                        if ds:
                            dfs.append(ds.data)
                    if dfs:
                        merged = pd.concat(dfs, ignore_index=True)
                        st.dataframe(merged.head(10))
                        st.caption(f"合并后共 {len(merged)} 行")

                merged_name = st.text_input("合并后数据集名称", value=f"合并数据_{datetime.now().strftime('%m%d')}")

                if st.button("🔗 执行合并", type="primary"):
                    new_ds = dm.merge_datasets(merge_ids, merged_name)
                    if new_ds:
                        # 询问是否加载
                        if st.success(f"✅ 合并成功: {new_ds.name} ({new_ds.row_count}行)"):
                            st.session_state.data = new_ds.data
                            st.session_state.data_source = new_ds.name
                            dm.set_current_dataset(new_ds.id)
                            st.rerun()


def show_data_manager_page():
    """显示数据管理器页面"""
    render_data_manager_ui()
