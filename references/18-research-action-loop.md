# 18｜Reflection 直接触发研究行动（v2.8）

## 为什么需要这道关卡
过去云计算报告出现“来源占位、章节拼接、纯假设模型、HIGH=pass但实证不足、八个评分维度写同一个下一步”等问题，而工作流仍在阶段性提交后停止。这是**研究调度失败**，不能靠增加评分轮次解决。

## 执行状态机（严格先研究，后交付）
PLAN → EXECUTE → SOURCE AUDIT → REFLECT WHOLE REPORT → GENERATE ACTION QUEUE → **AUTO EXECUTE ACTION** → VERIFY SOURCES/FORMULAS → REWRITE/INTEGRATE → REFLECT AGAIN。

### 每轮 Reflection 必须做的事
- 将发现转换为具体可执行任务：事实核对、结构重构、经营机制深化、财务模型校准、反证研究、图表排版六类。**不能只告诉用户“建议继续”。**
- 一个任务必须具有：原文位置、问题为何影响决策、最小可执行修复动作、修改后文档位置、复验记录。使用 assets/reflection-actions-template.csv。
- P0/P1 可行动事项为 OPEN 时，**当前任务直接启动它**，不得停在“阶段性报告”，不得让用户再次输入“继续”。
- EXTERNAL_BLOCKED 仅适用于该项核心事实确实不可获取，记录尝试的公开来源和已完成的替代工作。不影响其他任务。STOP_LIMIT 仅适用于本次真实工具/执行资源边界，保留未完成清单、不能宣称终审。
- 将**实质研究与编辑返工分开**：来源不可靠、核心模型无现实输入、公司经济性比较不足时，不得用修复字体或多生成图片替代研究。
- 模型必须显示：变量单位、数据出处、参数区间来源、模型内生与外部校准的区别、反事实/敏感性结论的适用范围。假设性项目模型不能当作真实云厂商盈利预测。
- 文稿修订前先审阅结构：主报告跨行业问题只讲一次，细分专题解释独特经营机制。新增研究段落要融合到相应章节，不能每次在文末新添一章。

### 源证据验证
- 新增 source_review.csv（模板 assets/source-review-template.csv），对每个正文 E### 引用记录 VERIFIED / UNVERIFIED / CONFLICT；VERIFIED 必须有**确实打开的原始资料及准确定位**。只存在一个 URL 或引用编号，不算核验。
- 原始网页无法访问时记 UNVERIFIED，不能填 VERIFIED。研究机构市场数据不能冒充审计财务数据；投资评论和公司指引分开列示。
- 任何“原始资料X”“2026-xx”等占位内容不允许出现在标记为正式稿的正文及附录。
- 研究覆盖 HIGH 不得只因有文字和引用就通过。对重要环节以 3/3（可检验、有核心财务机制和反证）作为主要目标；2/3 只能是有明确缺口的阶段性研究。
- 对已完成评分表的每个维度，分别提出对应的研究动作：证据问题→来源复核；模型问题→模型校准；结构问题→正文重构。若 8 项动作几乎一致，重做 Reflection。

### 运行方式
必须配合已有 coverage_stop_gate.py、autonomous_loop_gate.py、score_report.py、revision_gate.py、run_qa.py 使用。新增：
    python scripts/research_action_gate.py --report outputs/research_report.md --evidence outputs/evidence_ledger.csv --source-review outputs/source_review.csv --actions outputs/reflection_actions.csv --coverage outputs/industry_coverage.csv --defects outputs/revision_defect_ledger.csv --scorecard outputs/quality_scorecard.csv --gates outputs/quality_gates.csv --out outputs/research_action_gate_result.json

此工具只做输入记录一致性检查，不能验证外部来源真伪或证明 AI 真的完成研究；不得用 PASS 冒充正式终审。在 SOURCE REVIEW 未完全核实、质量硬门槛 UNKNOWN 或 3/3 分析不足时，最多 STAGED；如果仍有可执行 OPEN 项，则不得正常终止（真实限制按 STOP_LIMIT 留痕）。

## 终止逻辑
- **正常验收**：P0/P1 实质问题全部有修复+复验，HIGH 均有可检验证据，引用不存在未核验的核心事实，图表财务模型可复算，去重整合完成，所有硬门槛 PASS，完成全稿复查；进入“等待独立复核”，不是 RELEASED。
- **真正阻断**：逐项说明实际公开资料尝试/无法取得之处、模型可以替代的部分、未阻断的研究全部已继续。阶段性文件允许交付但不得称完成研究。
- **执行资源限制**：明确 STOP_LIMIT、保留具体未完成问题及可复现产物。这是执行限制，不代表研究质量合格。

需要多轮，但**不能为了做三轮而做三轮**；每轮都应体现新增核验、经营判断或修正结论。
