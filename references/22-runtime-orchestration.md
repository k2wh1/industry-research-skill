# 22｜运行时研究任务编排：从规范走向真正执行（v3 preview）

## 这项改动解决什么
现有 v2.11 Skill 的大部分脚本是 **验证器**，并不真正召集研究工具、找财报、计算指标、编写整稿和修订。即使 76 项结构测试全部通过，也不证明能自主完成真实行业报告。

新增 `scripts/research_runtime.py` 是前台执行器，持久化 `state.json`，通过受信任的外部 worker 逐阶段 **实际执行**：
`plan → research → analyze → draft → review → (revise → review)* → render`。

不是又一张“阶段已完成”打勾表：每阶段完成后将打开实际文件、核对源快照 SHA256、原文摘录存在性、模型表达式和结果、主要专题正文引证、审查决定及渲染文件格式。错误时返回非零，保留状态，修复后可重试。

## 运行路径（用户环境，需要 Codex 已安装登录、具备研究与文件写入权限）
PowerShell 示例：

```powershell
cd "$HOME\Documents\industry-research"
python scripts/research_runtime.py init --brief assets/research-runtime-semi-example.json --workspace "$HOME\Documents\semi-research-run"
python scripts/research_runtime.py run --workspace "$HOME\Documents\semi-research-run" --max-revisions 3 --worker python "$PWD\scripts\codex_worker.py"
```

Linux/macOS：

```bash
python scripts/research_runtime.py init --brief assets/research-runtime-semi-example.json --workspace ./semi-research-run
python scripts/research_runtime.py run --workspace ./semi-research-run --max-revisions 3 --worker python "$(pwd)/scripts/codex_worker.py"
```

**不要从已经运行中的 Codex agent 内递归启动另一个 Codex**。如果 Skill 本身已在一个工具齐全的代理环境内运行，代理可以依照同样的文件契约直接执行研究，再使用验证器，或从外部终端启动该编排器。

## 文件契约
- `brief.json`：固定题目、研究基准日、HIGH 细分行业，不许为了通过 QA 擅自缩窄
- `plan.json`：核心问题和所有 HIGH 研究任务
- `sources.json`、`claims.json`：原始资料文本快照路径、哈希、URL、获取日期；逐项原文摘录、明确位置和分析主张
- `models.json`：带单位、期间、变量、表达式和来源 claim ID 的计算结果
- `report.md`：完整正文及可追溯的 `[C001]` 引证
- `audit_review.md`、`review.json`：研究缺陷、P0/P1/P2 分类、PASS 或 REVISE
- `report.docx`、`report.pdf`：实际渲染产物
- `state.json`：持久执行队列、轮次、阶段验收历史；中断后恢复、未解决问题不冒充完成

真实数据不可得、Codex 工具无法检索/打开原文或生产 Word/PDF 时，应明确失败并保留缺口，**不生成假证据、虚构计算或空白文件**。

## 能力边界（非常重要）
这是 **可运行的端到端编排底座**，**不是已经完成端到端真实行业研究的证明**。
- 真正的搜证、阅读与写作依赖 Codex worker 或其他有权限的实际研究 agent；编排器本身不提供登录/抓取服务、不调用付费数据库、不保证源文真实。
- SHA256 确保文件在登记后未被修改、原文摘录匹配已捕获文本；不证明官网真实性、断章取义问题、历史口径可比或推断因果成立。
- 数学检查只处理登记的纯算术表达式，不验证模型选型、期初投入资本、估值假设或未登记公式。
- 格式签名只能排除明显损坏的 PDF/DOCX；中文字体、图表质量、版式必须实际逐页查看。
- 程序的最高状态是 `INTERNAL_RESEARCH_CANDIDATE`，**不是 `FORMAL_RESEARCH_FINAL` 或独立终审批准**；正式定稿还需 v2.10 的五项实质验收与实际来源审阅。
- 当前版本仍以单个大阶段处理全部 HIGH 模块，尚缺真正的分模块动态检索/并发调度、外部财报下载与自动抽取、可靠的跨全文陈述核对和真实的 91 页半导体端到端验收。**这些是下一步工程任务，而非可直接宣称已经实现的能力。**

## 实际验收标准（区别于单测）
1. 冷启动，从 `brief.json` 得到包括九个半导体专题的完整研究计划。
2. 自动收集主来源原文、保留摘要和可复核摘录，不靠人工填写 VERIFIED。
3. 自动按真实财报数据生成计算模型并完成反向测试。
4. 自动输出报告及 Word/PDF，并逐页检查版式，发现 P0/P1 自动修订。
5. 完整日志与 QA 无 P0/P1 后才可提请正式研究定稿验收；必须让独立复核人能够重演每项关键指标。

**测试边界**：CI 使用的是完全虚构且明确标注的离线研究 worker，只验证执行器、持久恢复、返工和异常阻断，绝不能冒充真实半导体研究能力。
