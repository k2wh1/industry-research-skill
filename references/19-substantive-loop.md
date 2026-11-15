# 19｜定量结论与财务时间序列反查、外部阻断前替代研究（v2.9）

## 目的
修复云计算 M9 中 AWS 营业利润率2023—2025年呈先升后降、文字却宣称连续改善的错误；防止把单项公司内部 ROIC 缺失当作云存储、Serverless、MaaS、SaaS 研究全部停止的理由。

## A｜数值→文字双向验证
- 对所有核心结论里“连续改善/下降、加速、反转、领先”等比较性表述建立逐条原文位置、时间区间、指标与数据来源的核验清单。重要结论不能只检查公式而不检查文字。
- 用 assets/series-template.csv 与 assets/quantitative-claims-template.csv 建立数值和比较谓词；单调、首尾变化、非单调等关系运行 scripts/substantive_stop_gate.py。
- 加速、同比、份额领先等尚不支持的谓词必须人工逐项核算并记录，不得声称程序覆盖所有表达。报告中的未登记句子不算经过验证。
- 不同公司或报告期发生定义变化时先做可比口径桥接，数据不能被空值自动填补。
- 原始数据的来源必须确实被打开核验，且保留定位；脚本对用户输入数字只执行数学检查，不证明来源真实。

## B｜外部阻断前验证替代方案
- 任意 EXTERNAL_BLOCKED 必须严格限定在具体问题，并拥有原始数据取得尝试的定位。
- 至少实际评估两个不同替代研究方案，比如官方产品定价与标准负载TCO、历史同公司财务、客户使用行为敏感性、可比服务商披露。不能虚构“尝试过”。
- 只要发现任何 FEASIBLE 的方案，必须立即研究并复核，不得借其他内部数据不可得来结束任务。INFEASIBLE 要写明无法回答何种具体结论。
- 行业覆盖高优先级问题不能用“局部 ROIC 不公开”全局阻断。若当前执行资源真正耗尽，使用 STOP_LIMIT，交付具体未完成工作及实际限制，不自称研究验收完成。

## C｜任务闭环
每轮 Reflection 查找未解决的研究问题→产生新的 Execute 实质任务→追加证据/模型→回看修订后的完整报告。不得为了评分或版本号强行宣布完成。研究内容充分而因数据不可得无法独立终审时保留 STAGED，但必须解释不可执行部分，并证实其他任务已被执行。

运行：
```bash
python scripts/substantive_stop_gate.py --series outputs/series.csv --claims outputs/quantitative_claims.csv --blockers outputs/blocker_alternatives.csv --out outputs/substantive_gate_result.json
```

此检查器只验证登记的时间序列、比较谓词和替代研究记录，不能核验外部来源真实性或未登记的文字，更不能自动发布正式报告。
