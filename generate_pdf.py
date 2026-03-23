"""
Q-Matrix Bug分析引擎 - PDF文档生成
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from io import BytesIO
import os

# 创建PDF
output_path = r"e:\BUG_ANALYSIS4\docs\Q-Matrix_技术文档.pdf"

# 创建文档
doc = SimpleDocTemplate(
    output_path,
    pagesize=A4,
    rightMargin=2*cm,
    leftMargin=2*cm,
    topMargin=2*cm,
    bottomMargin=2*cm
)

# 故事（内容）
story = []

# 样式
styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=24,
    alignment=TA_CENTER,
    spaceAfter=30
)
heading_style = ParagraphStyle(
    'CustomHeading',
    parent=styles['Heading2'],
    fontSize=16,
    spaceBefore=20,
    spaceAfter=10
)
subheading_style = ParagraphStyle(
    'CustomSubHeading',
    parent=styles['Heading3'],
    fontSize=13,
    spaceBefore=15,
    spaceAfter=8
)
body_style = ParagraphStyle(
    'CustomBody',
    parent=styles['BodyText'],
    fontSize=10,
    spaceBefore=6,
    spaceAfter=6,
    leading=16
)
code_style = ParagraphStyle(
    'Code',
    parent=styles['Code'],
    fontSize=9,
    spaceBefore=4,
    spaceAfter=4,
    leftIndent=20
)

# 标题
story.append(Paragraph("Q-Matrix Bug分析引擎", title_style))
story.append(Paragraph("技术设计文档", styles['Heading3']))
story.append(Spacer(1, 20))
story.append(Paragraph("版本: 1.0 &nbsp;&nbsp;&nbsp; 日期: 2026-03-22", body_style))
story.append(Spacer(1, 30))

# 一、概述
story.append(Paragraph("一、概述", heading_style))
story.append(Paragraph("""
Q-Matrix 是一款面向测试团队的Bug数据分析引擎，旨在从浅层次到深层次、多视角地
对问题单进行深度分析，挖掘产品核心痛点，并输出可落地的改进措施。
""", body_style))

story.append(Paragraph("核心价值：", subheading_style))
story.append(Paragraph("""
• 不是简单的图表统计，而是作为"分析引擎"<br/>
• 深度挖掘500-1000个规模的Bug数据<br/>
• 找出产品核心痛点<br/>
• 输出可落地的测试改进措施
""", body_style))

# 二、整体架构
story.append(Paragraph("二、整体架构", heading_style))
story.append(Paragraph("""
Q-Matrix分析引擎包含以下核心模块：
""", body_style))

story.append(Paragraph("1. 数据输入层", subheading_style))
story.append(Paragraph("""
支持多种数据导入方式：Excel导入 (.xlsx, .xls)、CSV导入 (.csv)、API动态获取。
核心字段包括：基础标记（问题类型、业务场景分类）、发现节点（测试环境、灰度环境、HSO、恒云环境等）、
爆炸半径（P0、P1、P2、P3、P4、P4A）、深度下钻（开发根因分析、测试分析与复盘）。
""", body_style))

story.append(Paragraph("2. 浅层矩阵分析", subheading_style))
story.append(Paragraph("""
功能：交叉矩阵构建（业务×类型、环境×阶段等）、热力图可视化、热点问题区域自动识别。
输出：问题数量统计、占比分析、严重程度分布。
""", body_style))

story.append(Paragraph("3. 深层分析（三视角）", subheading_style))
story.append(Paragraph("""
【开发视角】- 从"根因详细"字段分析代码级问题<br/>
&nbsp;&nbsp;关键词模式：空指针/空值处理不当、数据库操作问题、并发/多线程问题、内存管理问题、性能问题、业务逻辑缺陷<br/><br/>

【测试视角】- 从"漏测分析"字段分析测试覆盖缺失<br/>
&nbsp;&nbsp;关键词模式：测试覆盖不足、需求理解偏差、设计缺陷、开发疏漏、第三方因素<br/><br/>

【业务视角】- 从"影响程度"分析爆炸半径<br/>
&nbsp;&nbsp;按业务模块计算风险评分：严重(P0) > 高(P1) > 中(P2) > 低(P3)
""", body_style))

story.append(Paragraph("4. 聚合分析（核心引擎）", subheading_style))
story.append(Paragraph("""
综合三视角，自动生成核心结论：
• 最高优先级问题（critical）- 立即处理的问题<br/>
• 开发重点 - 代码质量改进方向<br/>
• 测试重点 - 提升测试覆盖能力<br/>
• 业务风险 - 重点关注模块
""", body_style))

story.append(Paragraph("5. 改进建议", subheading_style))
story.append(Paragraph("""
• 自动生成改进建议<br/>
• 自定义编写建议<br/>
• 分类管理（code_fix / test_coverage / process_improvement）<br/>
• 优先级标记（high / medium / low）<br/>
• 状态跟踪（pending / in_progress / completed）<br/>
• 持久化存储
""", body_style))

# 三、核心模块说明
story.append(Paragraph("三、文件结构", heading_style))
story.append(Paragraph("""
BUG_ANALYSIS4/<br/>
├── app.py &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# 主应用入口<br/>
├── auth.py &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# 认证模块<br/>
├── data_persistence.py &nbsp;&nbsp;# 数据持久化<br/>
├── qmatrix_config.py &nbsp;&nbsp;&nbsp;# 数据模型定义<br/>
├── qmatrix_engine.py &nbsp;&nbsp;&nbsp;# 核心分析引擎<br/>
├── qmatrix_aggregator.py &nbsp;# 聚合分析引擎 ★<br/>
├── qmatrix_enhanced_ui.py # 增强版UI ★<br/>
├── qmatrix_exporter.py &nbsp;&nbsp;# 导出模块<br/>
├── qmatrix_export_ui.py &nbsp;# 导出UI<br/>
├── ui_components.py &nbsp;&nbsp;# 通用UI组件<br/>
├── tests/ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# 单元测试<br/>
└── config/ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# 配置文件
""", code_style))

# 四、使用说明
story.append(Paragraph("四、使用说明", heading_style))

story.append(Paragraph("4.1 启动应用", subheading_style))
story.append(Paragraph("""
cd BUG_ANALYSIS4<br/>
streamlit run app.py --server.port 8505<br/><br/>
访问: http://localhost:8505<br/>
登录: admin / admin123
""", body_style))

story.append(Paragraph("4.2 Q-Matrix分析流程", subheading_style))
story.append(Paragraph("""
1. 进入"Q-Matrix分析"<br/>
2. 【数据概览】- 查看总体统计、严重程度分布<br/>
3. 【浅层矩阵】- 选择行/列维度、查看交叉矩阵热力图、识别热点<br/>
4. 【深层分析】- 开发/测试/业务三视角分析<br/>
5. 【聚合分析】- 查看综合结论<br/>
6. 【改进建议】- 添加自定义建议、跟踪执行状态
""", body_style))

story.append(Paragraph("4.3 导出成果", subheading_style))
story.append(Paragraph("""
进入"成果导出"页面：<br/>
• 原始数据（Excel/CSV）<br/>
• 清洗数据<br/>
• 分析报告（文本/JSON）<br/>
• 一键导出全部
""", body_style))

# 五、技术栈
story.append(Paragraph("五、技术栈", heading_style))
story.append(Paragraph("""
• 后端: Python 3.10<br/>
• 前端: Streamlit<br/>
• 数据处理: Pandas<br/>
• 可视化: Plotly<br/>
• 配置: YAML<br/>
• 认证: SHA256 + Salt
""", body_style))

# 生成PDF
doc.build(story)

print(f"PDF文档已生成: {output_path}")
print(f"文件大小: {os.path.getsize(output_path) / 1024:.1f} KB")
