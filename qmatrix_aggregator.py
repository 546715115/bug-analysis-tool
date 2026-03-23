"""
Q-Matrix 聚合分析引擎
综合开发/测试/业务三视角，给出行之有效的结论
"""

import pandas as pd
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from collections import Counter


@dataclass
class AggregatedInsight:
    """聚合洞察"""
    title: str
    severity: str  # critical/high/medium/low
    category: str  # 开发/测试/业务
    description: str
    evidence: List[str]  # 支撑证据
    affected_modules: List[str]
    related_bugs: List[str]


@dataclass
class ActionItem:
    """行动项"""
    id: str
    title: str
    description: str
    category: str  # code_fix/test_coverage/process_improvement
    priority: str  # high/medium/low
    status: str  # pending/in_progress/completed
    assignee: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""


class QMatrixAggregator:
    """Q-Matrix 聚合分析器"""

    def __init__(self, df: pd.DataFrame, engine):
        self.df = df
        self.engine = engine
        self._prepare_data()

    def _prepare_data(self):
        """准备数据映射"""
        # 列名映射
        self.col_map = {}

        cols = ['业务模块', '问题类型', '发现环境', '影响程度', '问题单号',
                '根因详细', '漏测分析', '根因分类', '整改措施']

        for col in cols:
            if col in self.df.columns:
                self.col_map[col] = col

    def _get_col(self, name: str) -> str:
        """获取列名"""
        return self.col_map.get(name, name)

    # ==================== 开发视角分析 ====================

    def analyze_developer_perspective(self) -> Dict[str, Any]:
        """
        开发视角：从根因详细分析代码级问题
        """
        root_cause_col = self._get_col('根因详细')
        bug_id_col = self._get_col('问题单号')
        biz_col = self._get_col('业务模块')

        if root_cause_col not in self.df.columns:
            return {"status": "no_data", "insights": []}

        # 关键词模式
        patterns = {
            "空指针/空值": ["空指针", "null", "未判空", "空对象", "None"],
            "数据库问题": ["数据库", "SQL", "查询", "索引", "事务", "锁表"],
            "并发问题": ["并发", "线程", "锁", "竞态", "死锁", "同步"],
            "内存问题": ["内存", "OOM", "溢出", "泄漏"],
            "性能问题": ["性能", "慢", "超时", "响应时间", "卡顿"],
            "逻辑错误": ["逻辑", "判断", "条件", "边界", "遗漏"],
            "接口问题": ["接口", "API", "参数", "调用", "超时"],
            "配置问题": ["配置", "参数", "开关", "环境"],
        }

        insights = []
        bug_patterns = []

        for _, row in self.df.iterrows():
            root_cause = str(row.get(root_cause_col, ""))
            bug_id = str(row.get(bug_id_col, ""))
            biz = str(row.get(biz_col, "")) if biz_col in self.df.columns else "未知"

            if not root_cause or root_cause == "nan":
                continue

            for pattern_name, keywords in patterns.items():
                if any(kw in root_cause for kw in keywords):
                    bug_patterns.append({
                        "pattern": pattern_name,
                        "bug_id": bug_id,
                        "module": biz,
                        "root_cause": root_cause[:100]
                    })
                    break

        # 统计频次
        pattern_counts = Counter([b["pattern"] for b in bug_patterns])

        # 生成洞察
        for pattern, count in pattern_counts.most_common(5):
            affected = list(set([b["module"] for b in bug_patterns if b["pattern"] == pattern]))
            bug_ids = [b["bug_id"] for b in bug_patterns if b["pattern"] == pattern][:5]

            severity = "critical" if count >= 5 else "high" if count >= 3 else "medium"

            insights.append(AggregatedInsight(
                title=f"代码级问题: {pattern}",
                severity=severity,
                category="开发",
                description=f"发现 {count} 个{pattern}相关问题，主要影响: {', '.join(affected[:3])}",
                evidence=[f"涉及 {count} 个问题单"],
                affected_modules=affected,
                related_bugs=bug_ids
            ))

        return {
            "status": "success",
            "insights": insights,
            "total_issues": len(bug_patterns),
            "pattern_distribution": dict(pattern_counts)
        }

    # ==================== 测试视角分析 ====================

    def analyze_tester_perspective(self) -> Dict[str, Any]:
        """
        测试视角：从漏测分析分析测试覆盖缺失
        """
        leak_col = self._get_col('漏测分析')
        bug_id_col = self._get_col('问题单号')
        biz_col = self._get_col('业务模块')

        if leak_col not in self.df.columns:
            return {"status": "no_data", "insights": []}

        # 漏测类型模式
        patterns = {
            "测试覆盖不足": ["覆盖不足", "未覆盖", "测试用例", "边界条件", "异常场景"],
            "需求理解偏差": ["需求理解", "理解偏差", "需求遗漏", "理解错误"],
            "设计缺陷": ["设计缺陷", "设计问题", "未考虑", "遗漏"],
            "开发疏漏": ["开发疏漏", "开发遗漏", "实现缺陷"],
            "第三方因素": ["第三方", "外部", "依赖"],
            "环境差异": ["环境差异", "环境问题", "生产问题"],
        }

        insights = []
        leak_records = []

        for _, row in self.df.iterrows():
            leak = str(row.get(leak_col, ""))
            bug_id = str(row.get(bug_id_col, ""))
            biz = str(row.get(biz_col, "")) if biz_col in self.df.columns else "未知"

            if not leak or leak == "nan":
                continue

            for pattern_name, keywords in patterns.items():
                if any(kw in leak for kw in keywords):
                    leak_records.append({
                        "pattern": pattern_name,
                        "bug_id": bug_id,
                        "module": biz,
                        "leak_detail": leak[:100]
                    })
                    break

        # 统计
        pattern_counts = Counter([r["pattern"] for r in leak_records])

        for pattern, count in pattern_counts.most_common(5):
            affected = list(set([r["module"] for r in leak_records if r["pattern"] == pattern]))
            bug_ids = [r["bug_id"] for r in leak_records if r["pattern"] == pattern][:5]

            severity = "critical" if count >= 5 else "high" if count >= 3 else "medium"

            insights.append(AggregatedInsight(
                title=f"测试覆盖问题: {pattern}",
                severity=severity,
                category="测试",
                description=f"发现 {count} 个{pattern}问题，主要影响: {', '.join(affected[:3])}",
                evidence=[f"涉及 {count} 个问题单"],
                affected_modules=affected,
                related_bugs=bug_ids
            ))

        return {
            "status": "success",
            "insights": insights,
            "total_issues": len(leak_records),
            "pattern_distribution": dict(pattern_counts)
        }

    # ==================== 业务视角分析 ====================

    def analyze_business_perspective(self) -> Dict[str, Any]:
        """
        业务视角：从影响程度分析爆炸半径
        """
        severity_col = self._get_col('影响程度')
        biz_col = self._get_col('业务模块')
        bug_id_col = self._get_col('问题单号')

        if severity_col not in self.df.columns:
            return {"status": "no_data", "insights": []}

        # 严重程度映射
        severity_map = {
            "P0": ("critical", 10),
            "致命": ("critical", 10),
            "P1": ("high", 7),
            "严重": ("high", 7),
            "P2": ("medium", 4),
            "一般": ("medium", 4),
            "P3": ("low", 1),
            "提示": ("low", 1),
        }

        insights = []
        biz_risk = {}

        # 按业务模块计算风险分
        for _, row in self.df.iterrows():
            biz = str(row.get(biz_col, "未知"))
            severity = str(row.get(severity_col, "P3"))
            bug_id = str(row.get(bug_id_col, ""))

            if biz not in biz_risk:
                biz_risk[biz] = {"score": 0, "critical": [], "high": [], "medium": [], "low": []}

            sev_info = severity_map.get(severity, ("low", 1))
            biz_risk[biz]["score"] += sev_info[1]

            if sev_info[0] == "critical":
                biz_risk[biz]["critical"].append(bug_id)
            elif sev_info[0] == "high":
                biz_risk[biz]["high"].append(bug_id)
            elif sev_info[0] == "medium":
                biz_risk[biz]["medium"].append(bug_id)
            else:
                biz_risk[biz]["low"].append(bug_id)

        # 生成洞察
        sorted_biz = sorted(biz_risk.items(), key=lambda x: x[1]["score"], reverse=True)

        for biz, data in sorted_biz[:5]:
            total = len(data["critical"]) + len(data["high"]) + len(data["medium"]) + len(data["low"])
            severity = "critical" if len(data["critical"]) >= 2 else "high" if len(data["critical"]) >= 1 or len(data["high"]) >= 3 else "medium"

            all_bugs = data["critical"] + data["high"] + data["medium"][:3]

            insights.append(AggregatedInsight(
                title=f"业务风险: {biz}",
                severity=severity,
                category="业务",
                description=f"风险评分 {data['score']}分，严重问题 {len(data['critical'])}个，高风险 {len(data['high'])}个",
                evidence=[
                    f"严重(P0): {len(data['critical'])}个",
                    f"高(P1): {len(data['high'])}个",
                    f"中(P2): {len(data['medium'])}个"
                ],
                affected_modules=[biz],
                related_bugs=all_bugs[:5]
            ))

        return {
            "status": "success",
            "insights": insights,
            "risk_ranking": [(b, d["score"]) for b, d in sorted_biz]
        }

    # ==================== 聚合分析 ====================

    def generate_aggregated_analysis(self) -> Dict[str, Any]:
        """
        核心：生成聚合分析结论
        综合三视角，给出行之有效的结论
        """

        # 执行三视角分析
        dev_result = self.analyze_developer_perspective()
        test_result = self.analyze_tester_perspective()
        biz_result = self.analyze_business_perspective()

        # 聚合洞察
        all_insights = []

        if dev_result["status"] == "success":
            all_insights.extend(dev_result["insights"])
        if test_result["status"] == "success":
            all_insights.extend(test_result["insights"])
        if biz_result["status"] == "success":
            all_insights.extend(biz_result["insights"])

        # 按严重程度排序
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_insights.sort(key=lambda x: severity_order.get(x.severity, 3))

        # 生成核心结论
        conclusions = []

        # 1. 最高优先级问题
        critical_insights = [i for i in all_insights if i.severity == "critical"]
        if critical_insights:
            conclusions.append({
                "priority": "critical",
                "title": "🔴 最高优先级: 立即处理",
                "content": f"发现 {len(critical_insights)} 个严重问题，需要立即处理：",
                "items": [f"- {i.title}: {i.description}" for i in critical_insights[:3]]
            })

        # 2. 开发侧重点
        dev_insights = [i for i in all_insights if i.category == "开发"]
        if dev_insights:
            top_dev = dev_insights[0]
            conclusions.append({
                "priority": "high",
                "title": "💻 开发重点: 代码质量改进",
                "content": f"代码层面主要问题：{top_dev.title}，影响模块: {', '.join(top_dev.affected_modules[:3])}",
                "items": []
            })

        # 3. 测试侧重点
        test_insights = [i for i in all_insights if i.category == "测试"]
        if test_insights:
            top_test = test_insights[0]
            conclusions.append({
                "priority": "high",
                "title": "🧪 测试重点: 提升覆盖能力",
                "content": f"测试层面主要问题：{top_test.title}，建议补充相关测试用例",
                "items": []
            })

        # 4. 业务风险
        biz_insights = [i for i in all_insights if i.category == "业务"]
        if biz_insights:
            top_biz = biz_insights[0]
            conclusions.append({
                "priority": "high",
                "title": "📊 业务风险: 重点关注模块",
                "content": f"业务风险最高的模块：{top_biz.title}，{top_biz.description}",
                "items": top_biz.evidence
            })

        return {
            "summary": {
                "total_insights": len(all_insights),
                "critical_count": len(critical_insights),
                "high_count": len([i for i in all_insights if i.severity == "high"]),
                "medium_count": len([i for i in all_insights if i.severity == "medium"]),
            },
            "developer_perspective": dev_result,
            "tester_perspective": test_result,
            "business_perspective": biz_result,
            "all_insights": all_insights,
            "conclusions": conclusions
        }


class ActionItemManager:
    """行动项管理器 - 改进建议的保存和自定义"""

    def __init__(self, storage_path: str = None):
        if storage_path is None:
            from pathlib import Path
            storage_path = Path(__file__).parent / "data" / "action_items.json"
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(exist_ok=True)
        self._items = self._load()

    def _load(self) -> List[Dict]:
        """加载保存的行动项"""
        import json
        if self.storage_path.exists():
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save(self):
        """保存行动项"""
        import json
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self._items, f, ensure_ascii=False, indent=2)

    def add_item(self, title: str, description: str, category: str, priority: str = "medium") -> ActionItem:
        """添加行动项"""
        from datetime import datetime
        import uuid

        item = ActionItem(
            id=str(uuid.uuid4())[:8],
            title=title,
            description=description,
            category=category,
            priority=priority,
            status="pending",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

        self._items.append({
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "category": item.category,
            "priority": item.priority,
            "status": item.status,
            "notes": item.notes,
            "created_at": item.created_at,
            "updated_at": item.updated_at
        })

        self._save()
        return item

    def update_item(self, item_id: str, **kwargs) -> bool:
        """更新行动项"""
        from datetime import datetime

        for item in self._items:
            if item["id"] == item_id:
                item.update(kwargs)
                item["updated_at"] = datetime.now().isoformat()
                self._save()
                return True
        return False

    def delete_item(self, item_id: str) -> bool:
        """删除行动项"""
        self._items = [i for i in self._items if i["id"] != item_id]
        self._save()
        return True

    def get_items(self, status: str = None, priority: str = None) -> List[Dict]:
        """获取行动项列表"""
        items = self._items
        if status:
            items = [i for i in items if i["status"] == status]
        if priority:
            items = [i for i in items if i["priority"] == priority]
        return items

    def add_auto_suggestions(self, suggestions: List) -> List[ActionItem]:
        """从分析引擎添加自动生成的建议"""
        added = []
        for sug in suggestions:
            item = self.add_item(
                title=sug.title,
                description=sug.description,
                category=sug.category,
                priority=sug.priority
            )
            added.append(item)
        return added
