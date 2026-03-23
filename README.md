# 测试问题单分析工具

一个本地运行的测试问题单多维分析工具，支持通过灵活的维度配置和排列组合分析问题内容。

## 功能特点

- 📥 **数据导入**: 支持Excel(.xlsx/.xls/.csv)和API接口导入
- 📊 **多维分析**: 支持业务类型、问题类型、发现环境、影响程度等维度
- 🔄 **交叉分析**: 任意两维度交叉分析，热力图可视化
- 📈 **环境漏出**: 分析各环境的测试质量问题漏出率
- ⚠️ **严重程度**: 分析各业务/类型的严重问题分布
- 📋 **数据管理**: 数据筛选、导出功能

## 快速开始

### 1. 安装依赖

```bash
cd bug_analysis
pip install -r requirements.txt
```

### 2. 运行应用

```bash
streamlit run app.py
```

### 3. 使用流程

1. **导入数据**: 在"数据导入"页面，上传Excel文件或配置API接口
2. **数据概览**: 查看数据的基本统计和各维度分布
3. **交叉分析**: 选择竖轴和横轴维度，生成交叉分析表格或热力图
4. **环境漏出**: 分析各业务模块在不同环境的分布和漏出率
5. **严重程度**: 分析各模块的严重问题占比

## 数据格式

### Excel/CSV格式

导入的Excel或CSV文件应包含以下字段（字段名不区分大小写）：

| 系统字段 | 可用列名 | 说明 |
|---------|---------|------|
| business_type | 业务模块、业务类型、模块 | 业务类型 |
| bug_type | 问题类型、类型 | 问题类型 |
| environment | 发现环境、环境 | 发现环境 |
| severity | 影响程度、严重程度、级别 | 影响程度 |
| bug_id | 问题单号、BUG编号、ID | 问题单号 |
| title | 问题标题、标题 | 问题标题 |
| create_time | 创建时间、发现时间 | 创建时间 |
| status | 状态 | 问题状态 |

示例数据文件: `sample_data.csv`

## 维度配置

维度配置位于 `config/dimensions_config.yaml`，可自定义修改：

```yaml
dimensions:
  business_type:
    name: "业务类型"
    options:
      - value: "order"
        label: "订单模块"
      # ... 其他选项
```

## API配置

API配置位于 `config/api_config.yaml`：

```yaml
apis:
  - name: "问题单接口"
    endpoint: "http://your-server/api/bugs"
    method: "GET"
    auth:
      type: "bearer"
      token: "your-token"
    response_mapping:
      data_path: "data.list"
      fields:
        business_type: "module"
        bug_type: "bug_type"
```

## 目录结构

```
bug_analysis/
├── app.py                    # 主应用
├── requirements.txt          # 依赖
├── config/
│   ├── dimensions_config.yaml    # 维度配置
│   └── api_config.yaml           # API配置
├── config_loader.py          # 配置加载器
├── data_importer.py          # 数据导入
├── analyzer.py               # 分析引擎
├── visualizer.py             # 可视化
├── sample_data.csv           # 示例数据
└── README.md                # 说明文档
```

## 技术栈

- **Streamlit**: Web框架
- **Pandas**: 数据处理
- **Plotly**: 可视化图表

## 注意事项

1. 首次使用建议先导入 `sample_data.csv` 测试
2. 数据导入后会自动识别字段，也可手动映射
3. 分析结果可导出为CSV文件
4. 所有数据本地处理，不会上传
