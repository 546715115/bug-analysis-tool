"""
数据导入模块 - 支持Excel和API导入
"""
import pandas as pd
import requests
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import streamlit as st
from urllib.parse import urlparse


# SSRF防护：禁止的IP地址前缀
BLOCKED_IP_PREFIXES = ('10.', '172.16.', '172.17.', '172.18.', '172.19.',
                       '172.20.', '172.21.', '172.22.', '172.23.', '172.24.',
                       '172.25.', '172.26.', '172.27.', '172.28.', '172.29.',
                       '172.30.', '172.31.', '192.168.', '127.', '169.254.')
BLOCKED_HOSTS = ('localhost', 'localhost.localdomain', 'metadata.google.internal')


def validate_endpoint(url: str) -> Tuple[bool, str]:
    """
    验证API endpoint是否安全（防止SSRF攻击）

    Args:
        url: 要验证的URL

    Returns:
        (是否有效, 错误信息)
    """
    if not url:
        return False, "URL不能为空"

    try:
        parsed = urlparse(url)

        # 只允许http和https
        if parsed.scheme not in ('http', 'https'):
            return False, "只允许http或https协议"

        # 检查主机名
        host = parsed.hostname
        if not host:
            return False, "无效的URL主机名"

        # 禁止内部IP和特殊主机
        if host.lower() in BLOCKED_HOSTS:
            return False, f"禁止访问内部地址: {host}"

        # 禁止私有IP范围
        if host.startswith(BLOCKED_IP_PREFIXES):
            return False, f"禁止访问内部网络: {host}"

        # 禁止云元数据端点
        if host in ('169.254.169.254', 'metadata.google.internal'):
            return False, f"禁止访问云元数据端点: {host}"

        # 检查是否为数字IP（避免通过DNS绕过）
        import ipaddress
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback:
                return False, f"禁止访问私有或环回地址: {host}"
        except ValueError:
            # 不是有效IP地址，可能是域名，继续验证
            pass

        return True, ""

    except Exception as e:
        return False, f"URL解析错误: {str(e)}"


class DataImporter:
    """数据导入器"""

    def __init__(self, config_loader):
        self.config_loader = config_loader
        self.field_mapping = config_loader.get_field_mapping()

    def import_from_excel(self, file_path: str, field_mapping: Optional[Dict[str, str]] = None) -> pd.DataFrame:
        """
        从Excel文件导入数据

        Args:
            file_path: Excel文件路径
            field_mapping: 自定义字段映射，优先级高于配置文件

        Returns:
            DataFrame
        """
        # 读取Excel
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding='utf-8')
        else:
            df = pd.read_excel(file_path)

        # 列名标准化
        df = self._normalize_columns(df, field_mapping)

        return df

    # 文件大小限制：50MB
    MAX_FILE_SIZE = 50 * 1024 * 1024

    # 允许的MIME类型
    ALLOWED_MIME_TYPES = {
        'csv': 'text/csv',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'xls': 'application/vnd.ms-excel'
    }

    def import_from_excel_upload(self, uploaded_file, field_mapping: Optional[Dict[str, str]] = None) -> pd.DataFrame:
        """
        从上传的Excel文件导入数据

        Args:
            uploaded_file: Streamlit上传的文件对象
            field_mapping: 自定义字段映射

        Returns:
            DataFrame
        """
        # 文件大小验证
        uploaded_file.seek(0, 2)  # 跳到文件末尾
        file_size = uploaded_file.tell()
        uploaded_file.seek(0)  # 回到文件开头

        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(f"文件过大，最大允许50MB，当前文件 {file_size / 1024 / 1024:.1f}MB")

        # 文件名安全处理
        import re
        safe_name = re.sub(r'[^\w\s.-]', '', uploaded_file.name)
        safe_name = safe_name[:100]  # 限制长度

        # 根据文件类型读取
        if safe_name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        else:
            df = pd.read_excel(uploaded_file)

        # 列名标准化
        df = self._normalize_columns(df, field_mapping)

        return df

    def _normalize_columns(self, df: pd.DataFrame, custom_mapping: Optional[Dict[str, str]] = None) -> pd.DataFrame:
        """
        标准化列名，将原始列名映射到系统维度

        Args:
            df: 原始DataFrame
            custom_mapping: 自定义映射

        Returns:
            标准化后的DataFrame
        """
        df = df.copy()

        # 使用自定义映射或配置文件中的映射
        mapping = custom_mapping or {}

        # 如果没有提供自定义映射，使用配置文件中的智能映射
        if not mapping:
            mapping = self._build_auto_mapping(df.columns.tolist())

        # 重命名列
        rename_dict = {}
        for original_col in df.columns:
            for system_key, possible_names in mapping.items():
                if original_col.lower() in [n.lower() for n in possible_names]:
                    rename_dict[original_col] = system_key
                    break

        df = df.rename(columns=rename_dict)

        return df

    def _build_auto_mapping(self, columns: List[str]) -> Dict[str, List[str]]:
        """根据实际列名自动构建映射"""
        mapping = {}
        system_fields = ['business_type', 'bug_type', 'environment', 'severity', 'bug_id', 'title', 'create_time', 'status']

        for col in columns:
            col_lower = col.lower().strip()

            # 尝试匹配每个系统字段
            for system_field in system_fields:
                config_names = self.field_mapping.get(system_field, [])
                if col_lower in [n.lower() for n in config_names]:
                    mapping[system_field] = config_names
                    break

        return mapping

    def import_from_api(self, api_config: dict, max_pages: int = 10) -> pd.DataFrame:
        """
        从API接口导入数据

        Args:
            api_config: API配置字典
            max_pages: 最大页数限制

        Returns:
            DataFrame
        """
        # SSRF防护：验证endpoint
        endpoint = api_config.get('endpoint', '')
        is_valid, error_msg = validate_endpoint(endpoint)
        if not is_valid:
            raise ValueError(f"API地址验证失败: {error_msg}")

        all_data = []
        page = 1

        # 构建请求头
        headers = api_config.get('headers', {})
        auth = api_config.get('auth', {})

        if auth.get('type') == 'bearer':
            headers['Authorization'] = f"Bearer {auth.get('token', '')}"
        elif auth.get('type') == 'basic':
            import base64
            auth_str = f"{auth.get('username', '')}:{auth.get('password', '')}"
            headers['Authorization'] = f"Basic {base64.b64encode(auth_str.encode()).decode()}"

        # 分页获取数据
        while page <= max_pages:
            # 构建请求参数
            params = api_config.get('params', {}).copy()
            if api_config.get('pagination', {}).get('enabled'):
                params[api_config['pagination']['page_param']] = page
                params[api_config['pagination']['size_param']] = api_config.get('params', {}).get('page_size', 100)

            try:
                response = requests.request(
                    method=api_config.get('method', 'GET'),
                    url=api_config.get('endpoint'),
                    headers=headers,
                    params=params,
                    timeout=30,
                    verify=True  # 强制SSL证书验证
                )
                response.raise_for_status()
                data = response.json()

                # 提取数据
                data_path = api_config.get('response_mapping', {}).get('data_path', 'data')
                items = self._extract_by_path(data, data_path)

                if not items:
                    break

                all_data.extend(items)

                # 检查是否还有更多数据
                if api_config.get('pagination', {}).get('enabled'):
                    total_path = api_config['pagination'].get('total_param')
                    if total_path:
                        total = self._extract_by_path(data, total_path)
                        if total and len(all_data) >= total:
                            break

                    # 检查是否到达最后一页
                    if len(items) < params.get(api_config['pagination']['size_param'], 100):
                        break

                page += 1

            except Exception as e:
                st.error(f"API请求失败: {str(e)}")
                break

        # 转换为DataFrame
        if all_data:
            df = pd.DataFrame(all_data)

            # 字段映射
            field_mapping = api_config.get('response_mapping', {}).get('fields', {})
            df = self._map_api_fields(df, field_mapping)

            return df
        else:
            return pd.DataFrame()

    def _extract_by_path(self, data: dict, path: str) -> any:
        """根据路径从字典中提取数据"""
        keys = path.split('.')
        result = data
        for key in keys:
            if isinstance(result, dict):
                result = result.get(key, [])
            else:
                return []
        return result if isinstance(result, list) else [result]

    def _map_api_fields(self, df: pd.DataFrame, field_mapping: Dict[str, str]) -> pd.DataFrame:
        """映射API返回字段到系统维度"""
        if not field_mapping:
            return df

        # 反转映射
        reverse_mapping = {v: k for k, v in field_mapping.items()}

        # 重命名列
        rename_dict = {}
        for col in df.columns:
            if col in reverse_mapping:
                rename_dict[col] = reverse_mapping[col]

        df = df.rename(columns=rename_dict)
        return df

    def get_preview(self, df: pd.DataFrame, max_rows: int = 5) -> pd.DataFrame:
        """获取数据预览"""
        return df.head(max_rows)

    def validate_data(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        验证数据是否包含必要的维度字段

        Returns:
            (是否有效, 错误信息列表)
        """
        # 必要字段（必须有）
        required_fields = ['business_type', 'bug_type', 'environment', 'severity']
        errors = []

        for field in required_fields:
            if field not in df.columns:
                errors.append(f"缺少必要字段: {field}")

        # 建议字段（用于增强分析）
        recommended_fields = ['root_cause', 'leak_analysis', 'leak_analysis_type', 'is_regression']
        warnings = []

        for field in recommended_fields:
            if field not in df.columns:
                warnings.append(f"建议添加字段: {field}（用于根因和漏测分析）")

        # 合并错误和警告
        all_messages = errors + warnings

        # 检查数据是否为空
        if len(df) == 0:
            errors.append("数据为空")

        return len(errors) == 0, all_messages
