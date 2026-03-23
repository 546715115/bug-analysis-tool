"""
Q-Matrix 成果导出模块
支持原始数据、清洗数据、综合分析报告导出
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import base64


class QMatrixExporter:
    """Q-Matrix 成果导出器"""

    def __init__(self, output_dir: str = None):
        if output_dir is None:
            output_dir = Path(__file__).parent / "exports"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def export_raw_data(self, df: pd.DataFrame, format: str = 'excel') -> str:
        """
        导出原始数据

        Args:
            df: 原始数据
            format: 格式 'excel' 或 'csv'

        Returns:
            文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"raw_data_{timestamp}.{format}"
        filepath = self.output_dir / filename

        if format == 'excel':
            df.to_excel(filepath, index=False, engine='openpyxl')
        else:
            df.to_csv(filepath, index=False, encoding='utf-8-sig')

        return str(filepath)

    def export_cleaned_data(self, df: pd.DataFrame, mappings: Dict = None) -> str:
        """
        导出清洗后的结构化数据

        Args:
            df: 原始数据
            mappings: 字段映射关系

        Returns:
            文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cleaned_data_{timestamp}.xlsx"
        filepath = self.output_dir / filename

        # 创建清洗后的数据
        cleaned_df = df.copy()

        # 添加标准化列
        if mappings:
            for std_col, orig_col in mappings.items():
                if orig_col in df.columns and std_col not in df.columns:
                    cleaned_df[std_col] = df[orig_col]

        # 添加导出元数据
        cleaned_df['_export_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cleaned_df['_record_id'] = range(1, len(cleaned_df) + 1)

        cleaned_df.to_excel(filepath, index=False, engine='openpyxl')

        # 同时导出字段映射说明
        mapping_file = filepath.with_name(filepath.stem + "_mappings.txt")
        with open(mapping_file, 'w', encoding='utf-8') as f:
            f.write("字段映射说明\n")
            f.write("="*50 + "\n\n")
            if mappings:
                for std, orig in mappings.items():
                    f.write(f"{std} -> {orig}\n")
            else:
                f.write("无额外映射\n")

        return str(filepath)

    def export_analysis_report(self,
                              df: pd.DataFrame,
                              summary: Dict,
                              hotspots: Any,
                              root_causes: List,
                              suggestions: List,
                              format: str = 'text') -> str:
        """
        导出综合分析报告

        Args:
            df: 原始数据
            summary: 数据摘要
            hotspots: 热点区域
            root_causes: 根因分析
            suggestions: 改进建议
            format: 格式 'text' 或 'json'

        Returns:
            文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == 'json':
            filename = f"analysis_report_{timestamp}.json"
            filepath = self.output_dir / filename

            report_data = {
                "report_info": {
                    "generated_at": datetime.now().isoformat(),
                    "total_issues": len(df),
                    "data_columns": list(df.columns)
                },
                "summary": summary,
                "hotspots": {
                    "risk_level": hotspots.risk_level if hotspots else "unknown",
                    "total_issues": hotspots.total_issues if hotspots else 0,
                    "top_cells": [
                        {
                            "row": c.row_key,
                            "col": c.col_key,
                            "count": c.count,
                            "percentage": c.percentage
                        } for c in (hotspots.top_cells if hotspots else [])
                    ]
                },
                "root_causes": [
                    {
                        "category": rc.category,
                        "description": rc.description,
                        "frequency": rc.frequency,
                        "confidence": rc.confidence
                    } for rc in root_causes
                ],
                "suggestions": [
                    {
                        "category": s.category,
                        "priority": s.priority,
                        "title": s.title,
                        "description": s.description,
                        "actionable_steps": s.actionable_steps
                    } for s in suggestions
                ]
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)

            return str(filepath)

        else:
            # 生成文本报告
            filename = f"analysis_report_{timestamp}.txt"
            filepath = self.output_dir / filename

            report_content = self._generate_text_report(
                df, summary, hotspots, root_causes, suggestions
            )

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)

            return str(filepath)

    def _generate_text_report(self,
                             df: pd.DataFrame,
                             summary: Dict,
                             hotspots: Any,
                             root_causes: List,
                             suggestions: List) -> str:
        """生成文本格式的综合报告"""

        lines = []

        # 标题
        lines.append("="*70)
        lines.append("                    Q-Matrix 综合测试分析报告")
        lines.append("="*70)
        lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"数据总量: {len(df)} 条问题单")
        lines.append(f"数据维度: {len(df.columns)} 个字段")

        # 第一部分：数据概览
        lines.append("\n" + "="*70)
        lines.append("第一部分：数据概览")
        lines.append("="*70)

        if 'severity_distribution' in summary:
            lines.append("\n【严重程度分布】")
            for sev, count in summary['severity_distribution'].items():
                lines.append(f"  {sev}: {count} 条")

        if 'business_distribution' in summary:
            lines.append("\n【业务模块分布】")
            for biz, count in summary['business_distribution'].items():
                lines.append(f"  {biz}: {count} 条")

        if 'environment_distribution' in summary:
            lines.append("\n【发现环境分布】")
            for env, count in summary['environment_distribution'].items():
                lines.append(f"  {env}: {count} 条")

        # 第二部分：热点分析
        lines.append("\n" + "="*70)
        lines.append("第二部分：热点问题区域")
        lines.append("="*70)

        if hotspots:
            lines.append(f"\n风险等级: {hotspots.risk_level.upper()}")
            lines.append(f"问题总数: {hotspots.total_issues}")
            lines.append(f"热点单元格: {len(hotspots.top_cells)} 个")

            lines.append("\n【Top 10 热点问题】")
            for idx, cell in enumerate(hotspots.top_cells[:10], 1):
                lines.append(f"\n  {idx}. {cell.row_key} × {cell.col_key}")
                lines.append(f"     问题数量: {cell.count} ({cell.percentage:.1f}%)")
                if cell.severity_distribution:
                    lines.append(f"     严重程度: {cell.severity_distribution}")

        # 第三部分：根因分析
        lines.append("\n" + "="*70)
        lines.append("第三部分：深层归因分析")
        lines.append("="*70)

        if root_causes:
            for idx, rc in enumerate(root_causes, 1):
                lines.append(f"\n【{idx}. {rc.description}】")
                lines.append(f"    出现频次: {rc.frequency} 次")
                lines.append(f"    置信度: {rc.confidence*100:.0f}%")
                lines.append(f"    涉及模块: {', '.join(rc.related_modules[:5])}")
                if rc.code_patterns:
                    lines.append(f"    代码模式: {', '.join(rc.code_patterns)}")
        else:
            lines.append("\n暂无根因分析数据")

        # 第四部分：改进建议
        lines.append("\n" + "="*70)
        lines.append("第四部分：改进建议")
        lines.append("="*70)

        if suggestions:
            # 按优先级排序
            priority_order = {'high': 0, 'medium': 1, 'low': 2}
            sorted_suggestions = sorted(suggestions, key=lambda x: priority_order.get(x.priority, 3))

            for idx, sug in enumerate(sorted_suggestions, 1):
                priority_marker = "🔴" if sug.priority == 'high' else "🟡" if sug.priority == 'medium' else "🟢"
                lines.append(f"\n{idx}. {priority_marker} {sug.title} [{sug.priority.upper()}]")
                lines.append(f"   类别: {sug.category}")
                lines.append(f"   描述: {sug.description}")
                lines.append(f"   预计工作量: {sug.estimated_effort}")

                if sug.actionable_steps:
                    lines.append("   执行步骤:")
                    for step in sug.actionable_steps:
                        lines.append(f"     {step}")

                if sug.affected_modules:
                    lines.append(f"   影响模块: {', '.join(sug.affected_modules[:5])}")
        else:
            lines.append("\n暂无改进建议")

        # 第五部分：数据清单
        lines.append("\n" + "="*70)
        lines.append("第五部分：问题数据清单")
        lines.append("="*70)
        lines.append(f"\n（共 {len(df)} 条问题单，详见附件原始数据）")

        # 附录
        lines.append("\n" + "="*70)
        lines.append("附录：字段说明")
        lines.append("="*70)
        lines.append("\n核心分析字段：")
        lines.append("  - business_type: 业务场景分类")
        lines.append("  - issue_type: 问题类型")
        lines.append("  - discovery_stage: 发现阶段")
        lines.append("  - severity: 影响程度")
        lines.append("  - dev_root_cause: 开发根因分析")
        lines.append("  - test_review: 测试分析与复盘")
        lines.append("  - leak_analysis: 漏测分析")

        # 结束
        lines.append("\n" + "="*70)
        lines.append("                         报告结束")
        lines.append("="*70)

        return "\n".join(lines)

    def export_all(self,
                   df: pd.DataFrame,
                   summary: Dict,
                   hotspots: Any,
                   root_causes: List,
                   suggestions: List) -> Dict[str, str]:
        """
        导出所有成果

        Returns:
            导出文件路径字典
        """
        exports = {}

        # 1. 原始数据
        exports['raw_excel'] = self.export_raw_data(df, 'excel')
        exports['raw_csv'] = self.export_raw_data(df, 'csv')

        # 2. 清洗数据
        exports['cleaned'] = self.export_cleaned_data(df)

        # 3. 综合报告
        exports['report_text'] = self.export_analysis_report(
            df, summary, hotspots, root_causes, suggestions, 'text'
        )
        exports['report_json'] = self.export_analysis_report(
            df, summary, hotspots, root_causes, suggestions, 'json'
        )

        return exports


def get_download_link(filepath: str, text: str = "下载") -> str:
    """生成下载链接 HTML"""
    filename = Path(filepath).name

    with open(filepath, 'rb') as f:
        data = base64.b64encode(f.read()).decode()

    href = f'<a href="data:application/octet-stream;base64,{data}" download="{filename}">{text}</a>'
    return href
