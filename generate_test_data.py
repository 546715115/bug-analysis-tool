import pandas as pd
import random
from datetime import datetime, timedelta

# 设置随机种子以保证可重复性
random.seed(42)

# 数据池
business_modules = ['订单模块', '支付模块', '用户模块', '商品模块', '库存模块', '物流模块', '售后模块', '营销模块', '报表模块', '运营模块']
bug_types = ['功能缺陷', '性能问题', '兼容性问题', '安全问题', '界面问题', '数据问题', '流程问题', '需求遗漏']
environments = ['测试环境', '现网环境', '灰度环境', 'HCSO', '合营云', '私有化部署', '预发布环境', 'UAT环境']
severities = ['P0', 'P1', 'P2', 'P3']
root_causes = ['开发问题', '需求问题', '设计问题', '第三方问题', '其他']
leak_analyses = ['其他', '测试覆盖不足', '需求理解偏差', '设计缺陷', '开发疏漏', '第三方因素']
leak_types = ['功能缺陷', '性能问题', '兼容性问题', '安全问题', '界面问题', '数据问题', '流程问题']
is_regressions = ['是', '否']
statuses = ['已关闭', '处理中', '待处理', '已验证']

# 根因详细和整改措施池
root_cause_details = [
    '空指针未处理', 'SQL未优化', '需求描述不清', '浏览器兼容未考虑', '状态机设计缺陷',
    '缓存未使用', '并发锁未加', '边界条件未处理', 'N+1查询问题', '未做加密处理',
    '事务未正确提交', '接口设计不合理', '需求遗漏场景', '业务规则未校验', '计算逻辑错误',
    '测试环境差异', '架构设计不足', '短信服务异常', '数据未同步更新', '接口超时未处理',
    '异步回调未处理', '测试用例遗漏', '索引缺失', '样式未统一管理', '扣减逻辑复杂',
    '流程设计不完善', '静态资源未CDN', '唯一约束未加', '参数校验缺失', '物流接口不稳定',
    '分页未处理', '文件上传未限制', '导出Excel格式错误', '时间时区未处理', 'JSON解析异常',
    '金额计算精度问题', '订单号重复生成', 'session超时未验证', '权限校验遗漏', '日志记录不完整',
    '异常未捕获', '死循环风险', '内存泄漏', '数据库连接未释放', 'API限流未处理'
]

fix_measures = [
    '增加空值检查测试覆盖', '优化SQL添加索引', '完善需求文档', '增加兼容性测试', '优化状态机设计',
    '引入缓存机制', '添加分布式锁', '完善边界处理', '优化查询逻辑', '引入加密组件',
    '检查事务配置', '优化接口设计', '补充需求用例', '完善规则校验', '修正计算逻辑',
    '统一测试环境', '优化架构设计', '增加重试机制', '检查数据同步', '增加超时处理',
    '完善异步处理', '补充测试用例', '添加索引', '建立样式规范', '优化扣减逻辑',
    '优化流程设计', '引入CDN', '添加唯一约束', '完善参数校验', '增加容错处理',
    '添加分页处理', '限制文件大小', '修复Excel导出格式', '处理时区转换', '完善JSON解析',
    '使用Decimal类型', '使用UUID生成订单号', '验证session有效性', '补充权限校验', '完善日志记录',
    '添加异常捕获', '优化循环逻辑', '修复内存泄漏', '使用连接池', '添加限流机制'
]

# 问题标题模板
bug_titles = [
    '订单创建失败', '支付超时严重', '用户登录异常', '商品图片显示不全', '订单取消失败',
    '支付响应慢', '库存扣减异常', '物流信息展示错误', '订单列表加载慢', '用户密码明文传输',
    '商品下架失败', '支付方式选择异常', '售后流程无法流转', '优惠券发放失败', '报表数据不准确',
    '订单详情页错位', '大促期间支付崩溃', '验证码发送失败', '商品价格显示错误', '物流跟踪异常',
    '订单支付成功后未生成', '部分浏览器无法支付', '库存查询超时', '页面样式不统一', '商品库存扣减超时',
    '退货退款流程异常', '活动页面访问慢', '订单数据重复', '退款申请无法提交', '物流签收状态未更新',
    '用户注册失败', '商品搜索无结果', '购物车添加失败', '优惠券无法使用', '订单无法发货',
    '支付方式无法加载', '售后申请提交失败', '评价无法提交', '积分计算错误', '会员等级异常',
    '促销活动无法参与', '库存显示不准', '价格显示错误', '搜索结果排序错乱', '推荐商品不准确',
    '用户头像上传失败', '消息通知未发送', '数据导出失败', '批量操作无响应', '页面刷新白屏'
]

# 生成500+条数据
num_records = 550

data = {
    '问题单号': [f'BUG-{str(i+1).zfill(4)}' for i in range(num_records)],
    '业务模块': [random.choice(business_modules) for _ in range(num_records)],
    '问题类型': [random.choice(bug_types) for _ in range(num_records)],
    '发现环境': random.choices(environments, weights=[50, 15, 12, 5, 5, 3, 5, 5], k=num_records),
    '影响程度': random.choices(severities, weights=[5, 15, 50, 30], k=num_records),
    '问题标题': [random.choice(bug_titles) for _ in range(num_records)],
    '创建时间': [],
    '状态': random.choices(statuses, weights=[60, 20, 15, 5], k=num_records),
    '根因分类': [random.choice(root_causes) for _ in range(num_records)],
    '根因详细': [random.choice(root_cause_details) for _ in range(num_records)],
    '整改措施': [random.choice(fix_measures) for _ in range(num_records)],
    '漏测分析': [random.choice(leak_analyses) for _ in range(num_records)],
    '漏测问题类型': [random.choice(leak_types) for _ in range(num_records)],
    '是否回归': random.choices(is_regressions, weights=[15, 85], k=num_records),
    '汇总总结': [''] * num_records
}

# 生成日期（2024年1月-2025年3月）
start_date = datetime(2024, 1, 1)
for i in range(num_records):
    random_days = random.randint(0, 450)
    data['创建时间'].append((start_date + timedelta(days=random_days)).strftime('%Y-%m-%d'))

df = pd.DataFrame(data)

# 保存为Excel
df.to_excel('test_data_all_fields.xlsx', index=False, engine='openpyxl')
print(f"Excel文件已生成: test_data_all_fields.xlsx")
print(f"数据行数: {len(df)}")
print(f"列名: {list(df.columns)}")
print(f"\n数据统计:")
print(f"- 现网问题: {len(df[df['发现环境'].str.contains('现网')])} ({len(df[df['发现环境'].str.contains('现网')])/len(df)*100:.1f}%)")
print(f"- 严重问题(P0+P1): {len(df[df['影响程度'].isin(['P0', 'P1'])])} ({len(df[df['影响程度'].isin(['P0', 'P1'])])/len(df)*100:.1f}%)")
print(f"- 回归问题: {len(df[df['是否回归'] == '是'])} ({len(df[df['是否回归'] == '是'])/len(df)*100:.1f}%)")
