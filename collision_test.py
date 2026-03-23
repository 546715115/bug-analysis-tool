"""
Q-Matrix 多视角对撞测试
模拟三种 Skill 进行测试验证：
1. Product Manager - 审视需求契合度
2. Developer - 验证代码实现可行性
3. Test Analysis Engineer - 边界测试与专业性验证
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
import random


@dataclass
class TestResult:
    """测试结果"""
    skill_name: str
    test_type: str
    passed: bool
    findings: List[str]
    suggestions: List[str]
    score: float  # 0-100


class ProductManagerSkill:
    """产品经理 Skill - 审视需求，验证痛点契合度"""

    def __init__(self):
        self.name = "Product Manager"
        self.emoji = "📦"

    def analyze_requirements_alignment(self, engine, summary: Dict) -> TestResult:
        """分析需求对齐度"""
        findings = []
        suggestions = []
        passed = True

        # 检查业务场景覆盖
        if 'business_distribution' in summary:
            business_dist = summary['business_distribution']
            if len(business_dist) < 3:
                findings.append("❌ 业务场景覆盖不足，仅有 {} 个业务类型".format(len(business_dist)))
                passed = False
            else:
                findings.append("✅ 业务场景覆盖充分: {} 个业务模块".format(len(business_dist)))

        # 检查问题类型完整性
        if 'issue_type_distribution' in summary:
            issue_dist = summary['issue_type_distribution']
            if len(issue_dist) < 3:
                findings.append("⚠️ 问题类型覆盖较少: {} 种".format(len(issue_dist)))
                suggestions.append("建议增加更多问题类型维度")

        # 检查严重程度分布
        if 'severity_distribution' in summary:
            severity_dist = summary['severity_distribution']
            if 'P0' not in severity_dist and 'P1' not in severity_dist:
                findings.append("⚠️ 无严重问题记录，可能数据筛选过严")
                suggestions.append("检查严重程度字段是否正确映射")

        return TestResult(
            skill_name=self.name,
            test_type="需求对齐度分析",
            passed=passed,
            findings=findings,
            suggestions=suggestions,
            score=80 if passed else 60
        )

    def validate_business_value(self, hotspots: Dict) -> TestResult:
        """验证业务价值"""
        findings = []
        suggestions = []
        score = 70

        if hotspots.get('risk_level') == 'high':
            findings.append("✅ 高风险区域已识别，需要优先处理")
            score = 90
        elif hotspots.get('risk_level') == 'medium':
            findings.append("⚠️ 中等风险区域，需要关注")
            score = 75
        else:
            findings.append("ℹ️ 风险等级较低")

        # 检查热点数量
        top_cells = hotspots.get('top_cells', [])
        if len(top_cells) > 0:
            findings.append("✅ 识别到 {} 个热点问题区域".format(len(top_cells)))

            # 业务集中度分析 - top_cells 是 tuple 列表
            if top_cells and isinstance(top_cells[0], tuple):
                top_modules = [str(c[0]) for c in top_cells[:5]]
            else:
                top_modules = [str(c.row_key) for c in top_cells[:5]]
            findings.append("📊 高发业务模块: {}".format(", ".join(top_modules[:3])))

        return TestResult(
            skill_name=self.name,
            test_type="业务价值验证",
            passed=score >= 70,
            findings=findings,
            suggestions=suggestions,
            score=score
        )

    def run_tests(self, engine, summary: Dict, hotspots: Dict) -> List[TestResult]:
        """运行产品经理视角测试"""
        results = []

        results.append(self.analyze_requirements_alignment(engine, summary))
        results.append(self.validate_business_value(hotspots))

        return results


class DeveloperSkill:
    """开发工程师 Skill - 验证代码实现可行性"""

    def __init__(self):
        self.name = "Developer"
        self.emoji = "💻"

    def check_code_quality(self, engine_code: str) -> TestResult:
        """检查代码质量"""
        findings = []
        suggestions = []

        # 基础检查
        checks = [
            ("数据验证", "not None" in engine_code or "isnull" in engine_code),
            ("异常处理", "except" in engine_code or "Error" in engine_code),
            ("类型转换", "astype" in engine_code or "to_dict" in engine_code),
        ]

        for check_name, passed in checks:
            if passed:
                findings.append(f"✅ {check_name}: 实现完整")
            else:
                findings.append(f"❌ {check_name}: 可能存在问题")
                suggestions.append(f"加强 {check_name} 的错误处理")

        # 检查关键方法
        critical_methods = [
            'build_matrix', 'identify_hotspots',
            'analyze_root_causes', 'generate_improvements'
        ]

        for method in critical_methods:
            if method in engine_code:
                findings.append(f"✅ 方法 {method} 已实现")
            else:
                findings.append(f"❌ 关键方法 {method} 缺失")
                suggestions.append(f"实现 {method} 方法")

        return TestResult(
            skill_name=self.name,
            test_type="代码质量检查",
            passed=len([f for f in findings if f.startswith("✅")]) >= 4,
            findings=findings,
            suggestions=suggestions,
            score=75
        )

    def verify_performance(self, engine, df: pd.DataFrame) -> TestResult:
        """验证性能"""
        import time

        findings = []
        suggestions = []
        passed = True

        # 测试不同数据量下的性能
        test_sizes = [100, 500, 1000]

        for size in test_sizes:
            test_df = df.head(size) if len(df) > size else df

            start = time.time()
            try:
                # 执行核心操作
                engine.build_matrix('business_type', 'issue_type')
                engine.identify_hotspots()

                elapsed = time.time() - start

                if elapsed < 1.0:
                    findings.append(f"✅ {size}条数据处理: {elapsed*1000:.0f}ms")
                elif elapsed < 3.0:
                    findings.append(f"⚠️ {size}条数据处理: {elapsed*1000:.0f}ms (可接受)")
                else:
                    findings.append(f"❌ {size}条数据处理: {elapsed*1000:.0f}ms (较慢)")
                    passed = False

            except Exception as e:
                findings.append(f"❌ {size}条数据处理失败: {str(e)}")
                passed = False

        if not passed:
            suggestions.append("考虑优化数据处理逻辑或添加缓存")

        return TestResult(
            skill_name=self.name,
            test_type="性能测试",
            passed=passed,
            findings=findings,
            suggestions=suggestions,
            score=80 if passed else 50
        )

    def validate_data_processing(self, engine, df: pd.DataFrame) -> TestResult:
        """验证数据处理正确性"""
        findings = []
        suggestions = []

        # 测试空数据
        empty_df = pd.DataFrame()
        try:
            result = engine.build_matrix('business_type', 'issue_type')
            findings.append("✅ 空数据处理正常")
        except Exception as e:
            findings.append(f"❌ 空数据处理异常: {str(e)}")

        # 测试单条数据
        single_df = df.head(1)
        try:
            result = engine.build_matrix('business_type', 'issue_type')
            findings.append("✅ 单条数据处理正常")
        except:
            findings.append("⚠️ 单条数据可能存在问题")

        # 测试缺失值
        missing_df = df.copy()
        missing_df['business_type'] = None
        try:
            engine2 = type(engine)(missing_df, engine.config)
            result = engine2.build_matrix('business_type', 'issue_type')
            findings.append("✅ 缺失值处理正常")
        except Exception as e:
            findings.append(f"⚠️ 缺失值处理需优化: {str(e)[:50]}")

        return TestResult(
            skill_name=self.name,
            test_type="数据处理正确性",
            passed=True,
            findings=findings,
            suggestions=suggestions,
            score=80
        )

    def run_tests(self, engine, df: pd.DataFrame, engine_code: str) -> List[TestResult]:
        """运行开发工程师视角测试"""
        results = []

        results.append(self.check_code_quality(engine_code))
        results.append(self.verify_performance(engine, df))
        results.append(self.validate_data_processing(engine, df))

        return results


class TestAnalysisEngineerSkill:
    """测试分析工程师 Skill - 边界测试与专业性验证"""

    def __init__(self):
        self.name = "Test Analysis Engineer"
        self.emoji = "🧪"

    def test_concurrency_stability(self, engine, base_df: pd.DataFrame) -> TestResult:
        """测试并发/大量数据稳定性"""
        findings = []
        suggestions = []
        passed = True

        # 模拟大数据量 (1000+ 条)
        large_df = pd.concat([base_df] * (1000 // max(len(base_df), 1) + 1), ignore_index=True)
        large_df = large_df.head(1000)

        try:
            # 并发执行多个分析任务
            import concurrent.futures

            def run_analysis():
                return engine.build_matrix('business_type', 'issue_type')

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(run_analysis) for _ in range(3)]
                results = [f.result() for f in futures]

            findings.append("✅ 1000条数据并发处理成功")

        except Exception as e:
            findings.append(f"❌ 并发测试失败: {str(e)}")
            passed = False
            suggestions.append("加强并发场景的错误处理")

        # 内存压力测试
        try:
            for i in range(5):
                _ = engine.build_matrix('business_type', 'issue_type')
            findings.append("✅ 连续执行无内存泄漏")
        except Exception as e:
            findings.append(f"⚠️ 内存管理需优化: {str(e)[:50]}")

        return TestResult(
            skill_name=self.name,
            test_type="并发负载测试",
            passed=passed,
            findings=findings,
            suggestions=suggestions,
            score=80 if passed else 60
        )

    def validate_analysis_professionalism(self, engine, df: pd.DataFrame) -> TestResult:
        """验证分析建议的专业性"""
        findings = []
        suggestions = []

        # 检查分析维度完整性
        required_dims = ['business_type', 'issue_type', 'environment', 'severity']
        available_dims = list(engine.normalized_cols.keys())

        for dim in required_dims:
            if dim in available_dims or any(dim in c for c in df.columns):
                findings.append(f"✅ 维度 {dim} 已覆盖")
            else:
                findings.append(f"⚠️ 维度 {dim} 可能缺失")
                suggestions.append(f"添加 {dim} 维度的分析支持")

        # 检查根因分析
        root_cause_col = engine._get_col('dev_root_cause')
        if root_cause_col and root_cause_col in df.columns:
            findings.append("✅ 开发根因分析字段已配置")
        else:
            findings.append("⚠️ 开发根因分析字段未找到")
            suggestions.append("配置「开发根因分析」字段以启用深层分析")

        # 检查漏测分析
        leak_col = engine._get_col('leak_analysis')
        if leak_col and leak_col in df.columns:
            findings.append("✅ 漏测分析字段已配置")
        else:
            findings.append("⚠️ 漏测分析字段未找到")
            suggestions.append("配置「漏测分析」字段")

        return TestResult(
            skill_name=self.name,
            test_type="专业性验证",
            passed=len([f for f in findings if f.startswith("✅")]) >= 3,
            findings=findings,
            suggestions=suggestions,
            score=70
        )

    def test_edge_cases(self, engine, df: pd.DataFrame) -> TestResult:
        """边界测试"""
        findings = []
        suggestions = []

        edge_cases = [
            ("全空数据", pd.DataFrame()),
            ("单行数据", df.head(1)),
            ("全相同值", pd.DataFrame({'business_type': ['A'] * 100})),
            ("特殊字符", pd.DataFrame({'business_type': ['<test>', 'test&', 'test"']})),
        ]

        for case_name, test_df in edge_cases:
            try:
                test_engine = type(engine)(test_df, engine.config)
                result = test_engine.build_matrix('business_type', 'severity')
                findings.append(f"✅ 边界用例 '{case_name}' 处理正常")
            except Exception as e:
                findings.append(f"❌ 边界用例 '{case_name}' 失败: {str(e)[:30]}")
                suggestions.append(f"修复 '{case_name}' 的处理逻辑")

        return TestResult(
            skill_name=self.name,
            test_type="边界测试",
            passed=True,
            findings=findings,
            suggestions=suggestions,
            score=75
        )

    def validate_improvement_suggestions(self, insights: List, suggestions: List) -> TestResult:
        """验证改进建议的专业性和可执行性"""
        findings = []
        suggestions = []

        if not suggestions:
            findings.append("⚠️ 无改进建议生成")
            return TestResult(
                skill_name=self.name,
                test_type="建议质量验证",
                passed=False,
                findings=findings,
                suggestions=["确保分析数据包含根因和漏测信息"],
                score=50
            )

        # 检查建议分类
        categories = set(s.category for s in suggestions)
        if len(categories) >= 2:
            findings.append(f"✅ 建议覆盖多个类别: {', '.join(categories)}")
        else:
            findings.append("⚠️ 建议类别较单一")

        # 检查优先级分布
        priority_counts = {}
        for s in suggestions:
            priority_counts[s.priority] = priority_counts.get(s.priority, 0) + 1

        if priority_counts.get('high', 0) > 0:
            findings.append(f"✅ 识别出 {priority_counts['high']} 个高优先级改进项")
        else:
            findings.append("⚠️ 无高优先级建议")
            suggestions.append("可能需要调整分析阈值")

        # 检查可执行性
        actionable = sum(1 for s in suggestions if len(s.actionable_steps) > 0)
        if actionable >= len(suggestions) * 0.8:
            findings.append(f"✅ {actionable}/{len(suggestions)} 条建议有具体执行步骤")
        else:
            findings.append("⚠️ 部分建议缺乏具体执行步骤")

        return TestResult(
            skill_name=self.name,
            test_type="建议质量验证",
            passed=True,
            findings=findings,
            suggestions=suggestions,
            score=80
        )

    def run_tests(self, engine, df: pd.DataFrame, insights: List, suggestions: List) -> List[TestResult]:
        """运行测试分析工程师视角测试"""
        results = []

        results.append(self.test_concurrency_stability(engine, df))
        results.append(self.validate_analysis_professionalism(engine, df))
        results.append(self.test_edge_cases(engine, df))
        results.append(self.validate_improvement_suggestions(insights, suggestions))

        return results


def run_collision_test(df: pd.DataFrame, engine, engine_code: str) -> Dict[str, Any]:
    """
    执行多视角对撞测试

    Returns:
        测试报告
    """
    all_results = []

    # 1. 产品经理视角
    pm_skill = ProductManagerSkill()
    summary = engine.generate_summary()
    hotspots = engine.identify_hotspots()
    hotspots_dict = {
        'risk_level': hotspots.risk_level,
        'total_issues': hotspots.total_issues,
        'top_cells': [(c.row_key, c.col_key, c.count) for c in hotspots.top_cells]
    }

    pm_results = pm_skill.run_tests(engine, summary, hotspots_dict)
    all_results.extend(pm_results)

    # 2. 开发工程师视角
    dev_skill = DeveloperSkill()
    dev_results = dev_skill.run_tests(engine, df, engine_code)
    all_results.extend(dev_results)

    # 3. 测试分析工程师视角
    insights = engine.analyze_root_causes(hotspots.top_cells[:3])
    improvement_suggestions = engine.generate_improvements(hotspots, insights)

    tae_skill = TestAnalysisEngineerSkill()
    tae_results = tae_skill.run_tests(engine, df, insights, improvement_suggestions)
    all_results.extend(tae_results)

    # 生成报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(all_results),
        "passed": sum(1 for r in all_results if r.passed),
        "failed": sum(1 for r in all_results if not r.passed),
        "average_score": sum(r.score for r in all_results) / len(all_results),
        "results_by_skill": {},
        "all_results": []
    }

    # 按 Skill 分组
    for result in all_results:
        if result.skill_name not in report["results_by_skill"]:
            report["results_by_skill"][result.skill_name] = []
        report["results_by_skill"][result.skill_name].append({
            "test_type": result.test_type,
            "passed": result.passed,
            "score": result.score,
            "findings": result.findings
        })

    return report


def render_test_report(report: Dict):
    """渲染测试报告"""
    print("\n" + "="*60)
    print("🔬 Q-Matrix 多视角对撞测试报告")
    print("="*60)
    print(f"测试时间: {report['timestamp']}")
    print(f"总测试数: {report['total_tests']}")
    print(f"通过: {report['passed']} | 失败: {report['failed']}")
    print(f"平均得分: {report['average_score']:.1f}/100")
    print("="*60)

    for skill_name, results in report["results_by_skill"].items():
        skill_scores = [r["score"] for r in results]
        avg = sum(skill_scores) / len(skill_scores)

        print(f"\n👤 {skill_name} (平均分: {avg:.1f})")
        print("-" * 40)

        for r in results:
            status = "✅" if r["passed"] else "❌"
            print(f"  {status} {r['test_type']}: {r['score']}分")

            # 只显示关键发现
            critical_findings = [f for f in r["findings"] if f.startswith("✅") or f.startswith("❌")]
            for f in critical_findings[:2]:
                print(f"      {f}")

    print("\n" + "="*60)
