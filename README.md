# industry-research v2.3 — 行业研究、公司研究与投资研究 Skill

面向 Codex 及兼容 [Agent Skills](https://agentskills.io/specification) 的工具。以「核心争议 → 证据 → 产业/竞争 → 公司经营 → 财务预测 → 市场预期与估值 → 证伪与跟踪」为研究主线，而非把长报告目录填满。

## 安装

**推荐方式：项目级安装。** 将整个 `industry-research` 文件夹复制到项目中的 `.agents/skills/industry-research/`。比如存入你的投研项目：

```text
investment_research_copilot/
└── .agents/
    └── skills/
        └── industry-research/
            ├── SKILL.md
            ├── references/
            ├── assets/
            └── scripts/
```

**个人级安装**：`$HOME/.agents/skills/industry-research/`。Windows PowerShell 里 `$HOME` 指 Windows 用户主目录；在 WSL2 Ubuntu 里 `$HOME` 是 Linux 的用户主目录，二者不同。

无需 Python 包依赖（仅运行本包脚本需要 Python 3.10+）。Codex 可通过 `$industry-research` 明确调用；如果没有识别，重新启动 Codex 或确认工作目录位于对应项目树中。参见 [Codex Skill 官方文档](https://learn.chatgpt.com/docs/build-skills)。

## v2.3：研究质量优先，而不是继续堆篇幅

本版针对前一份《全球半导体设备行业深度》暴露的**加总错误、单位误差、同公司财务口径矛盾、校准模型循环验证、细分行业只写简介、图表缺失**升级。原来的九阶段研究工作流、深度覆盖和“去 AI 味不删实质内容”规则全部保留。

| 升级内容 | 具体变化 | 为什么重要 |
|---|---|---|
| 数据审计 | `references/12-data-audit.md`、`metrics.csv` 和 `audit_rules.csv`、`scripts/data_audit.py` | 复核加总/同比/占比、金额量纲、同口径跨章节冲突、来源时点；不能替代原文核对 |
| 独立建模 | `references/13-independent-modeling.md`、`model_manifest.json`、`scripts/model_check.py` | 区分机构预测、校准、自下而上测算、真正独立验证；发现显式循环验证 |
| 研究深度审查 | `references/14-analytical-depth.md`、`research_review.md` | 高优先级章节必须从“术语及厂商名单”深化到业务机制、证据、财务传导及反证 |
| 研究图表 | `references/15-visualization.md`、`figure_plan.md`、`figure_manifest.csv`、`scripts/figure_check.py` | 产出有用的历史趋势、需求驱动、竞争地图、财务和敏感性图；没有源数据不造图 |
| 一键检查 | `scripts/run_qa.py` | 全行业深度缺关键文件、数值有 ERROR、覆盖不完整时阻止通过结构性发布门槛 |

**重要界限：** 这些程序只检查已提供的输入。比如你没有把正文中的数字登记到 `metrics.csv`，它不会从长篇 Markdown 里自动核实全部数字。对原始披露、财报、政策文件和参数选择进行实质审查仍然是必要步骤。工具返回 PASS 不能写成“财务数据真实性已核实”。

### 推荐的 Codex 使用方法

1. 安装 Skill 后，将旧报告、证据账本及模型放进一个研究项目目录。
2. 使用 `examples/semiconductor-equipment-v23-research-prompt.md` 开展质量升级：先审计、再测算、后写作。
3. 先根据 `assets/metrics-template.csv`、`assets/audit-rules-template.csv`、`assets/model-manifest-template.json` 和 `assets/figure-manifest-template.csv`、`assets/figure-plan-template.md`、`assets/data-audit-log-template.md` 生成对应研究数据。
4. 在 Skill 根目录运行测试：

```bash
python -m unittest discover -s tests -v
python scripts/data_audit.py examples/numeric-audit-demo/metrics.csv --rules examples/numeric-audit-demo/audit_rules.csv --as-of 2026-11-09
```

第二条故意是**失败示例**：9 个分项求和为 1185，而待审表格写 1165，因此会报错并以退出码 1 结束。它演示了审计功能，不表示相关市场数字经过独立核实。

对完整行业研究执行：

```bash
python scripts/run_qa.py --mode industry_full \
  --report outputs/research_report.md \
  --ledger outputs/evidence_ledger.csv \
  --coverage outputs/industry_coverage.csv \
  --metrics outputs/metrics.csv --rules outputs/audit_rules.csv \
  --models outputs/model_manifest.json \
  --figures outputs/figure_manifest.csv \
  --review outputs/research_review.md --figure-plan outputs/figure_plan.md \
  --as-of 2026-11-09
```

**注意：** 该命令是结构、算术及材料齐备性的检查。还需要打开原始数据核实，并对图表/Word/PDF 实际预览。命令通过后只能写“通过当前已提供材料的自动化 QA，尚未代替人工事实审计”。

## v2.2：怎样生成真正完整的行业深度

- **默认深度**：当用户说“行业深度/完整/系统研究”时，不再把最终产物压缩为 7 页行业摘要。按研究对象建立 `industry_coverage.csv`，逐细分研究业务、量价供需、竞争、公司及资本效率，并维护缺口。
- **常用规划**：行业速览约 3–8 页、专题 10–20 页、全行业深度约 25–50 页（按复杂度和图表调整）。这是研究规模参考而非凑页数目标。
- **编写纪律**：先分批完成研究与证据核验，再自然叙述；“去 AI 味/改排版”任务必须保留已有实质内容，输出 `revision_coverage.md`；无法验证内容要标待审，不得偷偷删除。
- **验收**：`scripts/completeness_check.py` 检查覆盖表的结构性缺口、部分完成项、缺少证据、未交付的量化模型，以及没有理由的不适用项。默认需至少10个研究条目和4个研究部分作为基础结构门槛；这些门槛可以调整，但不意味着真实内容已经完成。脚本不检测事实真伪。

例如：

```text
$industry-research
请对全球半导体设备产业开展 industry_full 完整深度研究，不要生成行业速览。
先列出一级/二级产品树，建立 industry_coverage.csv，并分别研究光刻、刻蚀、沉积、清洗、CMP、量检测、离子注入、热处理、先进封装和测试。
对每个重要环节解释产品、工艺、客户、市场、供需、竞争者、壁垒与未来变化；建立至少一个可复算的行业需求/资本开支传导模型，并提供多年财务和公司映射。
研究完成后再撰写自然流畅的完整报告。不要因为“去 AI 味”压缩分析；没有证据的环节标明缺口，不得编造数字。附上证据账本、假设台账、覆盖登记表、研究缺口、质量检查。
```

## 四种调用方式

### 1. 行业深度研究

```text
$industry-research
研究全球存储半导体（DRAM / HBM / NAND）行业，截至研究日核实数据。重点讨论产品、客户与付费、供需平衡、位元需求/产能和价格传导、主要原厂竞争和利润池。先列出核心争议，建立证据台账及可复算模型，最后输出行业深度与证伪指标。不强制给目标价。
```

### 2. 公司首次覆盖

```text
$industry-research
做美光科技的公司首次覆盖研究：使用可核实的公开财报及公告，以业务驱动预测未来3年收入、利润、自由现金流；分析 ROIC、增量 Capex 与竞争格局，测算市场隐含预期；选择适用估值方法并给出悲观/基准/乐观情景、敏感性和反证清单。未验证数据不要造数，不足以估值时明确写缺口。
```

### 3. 专题研究

```text
$industry-research
研究 HBM 扩产对通用 DRAM 供给、价格和原厂利润的潜在影响。明确核心争议、产品转换瓶颈、数量测算、可能受益/受损环节与反向情景。只覆盖与这一争议有关的内容。
```

### 4. 定期跟踪

```text
$industry-research
更新上一版存储产业报告：阅读历史报告与假设账本，新增证据后区分哪些事实、假设、预测和估值发生变化。输出差异、原因、信号阈值与下一次更新需要的数据，保留历史版本。
```

## 文件说明

| 位置 | 用途 |
|---|---|
| `SKILL.md` | 触发条件、9 阶段工作流、质量控制、输出协议 |
| `references/` | 证据、行业、竞争、公司、预测、估值、风险、结论、跟踪、行业适配的详细研究说明 |
| `assets/*-template.md` | 行业、公司、专题、跟踪报告模板 |
| `assets/*-template.csv` | 证据账本、假设账本的表头示例 |
| `assets/dcf-input-example.json` | **完全虚构的教学情景**输入（百万货币单位），非任何公司的真实数据 |
| `scripts/dcf.py` | FCFF DCF 企业价值/股权价值、每股价值和敏感性，离线计算 |
| `scripts/quality_check.py` | 简单结构检查、证据编号与台账匹配检查、日期和口径提示 |
| `scripts/completeness_check.py` | 覆盖表结构检查；有未完成项、证据缺失或约定模型缺失时不允许“完整版已完成”状态 |
| `scripts/data_audit.py` | 已登记数据的单位、期间、重复口径与加总/同比/占比运算检查 |
| `scripts/model_check.py` | 模型清单、输入与验证/校准目标重叠检查 |
| `scripts/figure_check.py` | 图表元数据与报告引用完整性检查 |
| `scripts/run_qa.py` | 一键汇集结构和算术检查，缺少强制材料时阻断 |
| `references/12–15-*.md` | 数据、独立建模、深度审核和图表的专项研究纪律 |
| `assets/*manifest-template.*` | 数字台账、算术规则、模型与图表清单及深度评审模板 |
| `references/11-depth-completeness.md` | 全行业深度与旧稿内容保留约束 |
| `assets/industry-coverage-template.csv` | 行业逐项覆盖登记表，按行业增补细分行 |
| `assets/revision-coverage-template.md` | 改写旧报告时逐项追踪实质内容是否保留 |
| `examples/` | 半导体设备行业覆盖样例、原稿与7页稿的内容映射及Codex实战任务 |
| `tests/` | 脚本单元测试 |

## 半导体设备实战：从7页摘要过渡到完整深度

可直接查看：

- `examples/semiconductor-equipment-coverage-example.csv`：基于用户旧稿的**预评估**覆盖登记表（36条，暂记28项部分、8项缺失），未核验的证据编号不自动填入。
- `examples/semiconductor-equipment-revision-audit.md`：原稿与七页改写稿的主题对应，标明需要恢复与深化的部分。
- `examples/semiconductor-equipment-full-research-prompt.md`：Codex 完整研究任务，明确先补证据、分环节研究、再编写30–45页目标稿。

这些示例是研究规划，不是最新市场数据，也不代表已完成半导体设备报告。

## 脚本命令

在 `industry-research` 文件夹内：

```bash
python scripts/dcf.py assets/dcf-input-example.json --out valuation_output.json
python scripts/quality_check.py path/to/research_report.md --ledger path/to/evidence_ledger.csv
python scripts/completeness_check.py path/to/industry_coverage.csv --strict
python -m unittest discover -s tests -v
```

DCF 计算假设年末折现、FCFF 与 WACC 配套，净债务和股数单位需和 FCFF 一致；它不为你估计折现率、股价或盈利，也不替代业务、会计及事实核验。QA 仅能检查文本结构和部分引用关联，**无法验证网页真伪、财报口径或分析结论是否成立**。

## 正式报告写作规范

v2.1 起新增 `references/10-writing-editorial.md`（正式报告写作、去模板化、数据口径、Word 排版）。研究过程可使用五力、反证、证据等矩阵，但正文禁止机械粘贴研究矩阵。正文应有完整段落、克制标题、较少表格、统一财务口径；写作完成前必须执行事实审校与编辑审校。

## 输出协议与使用建议

正式报告通常生成：`research_report.md`、`evidence_ledger.csv`、`assumptions.csv`、`research_gaps.md`；需要估值则额外提供可复算模型和参数表。

建议先让 Skill 为研究对象列出 3–7 个关键争议和覆盖计划，再让它优先解决最影响预测和投资结论的问题；可逐章研究，但不能绕过证据和反方检验。Skill 可以给出条件化投资研究结论，不代表保证收益或适合个人账户的投资建议。

## 版本

`v2.3.0` — 增加数据与模型审计、深度分级、图表来源管理、集成 QA；严格区分自动检查与真实事实核验。

`v2.2.0` — 新增深度覆盖协议、逐环节行业报告模板、覆盖登记表、报告改写内容保留协议和更严格的完整性检查；提供半导体设备36项研究覆盖样例，防止将完整版误压缩成7页速览。


`v2.1.0` — 新增双重审校、自然段研究叙述和表格规范，修改行业报告模板。

`v2.0.0` — 九阶段研究工作流；新增独立预测、市场隐含预期、反方证伪与滚动修订；添加可复算 DCF 和结构自检脚本。
