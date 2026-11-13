# Changelog

## v2.4.0 — Quality Scoring Loop (2026-11-13)

- Added eight-dimension weighted review (100 points), human scoring evidence, six non-negotiable quality gates and round-by-round history.
- Introduced `references/16-quality-loop.md`, CSV templates and `scripts/score_report.py` for deterministic arithmetic, priority queue and score deltas.
- Integrated scorecards and gates into full-industry `run_qa.py`; a good score does not override failed/unknown audits or imply factual certification.
- Added unit tests for weighted scoring, incomplete records, blocked status and revision deltas.


## v2.3.0 — Research Quality Upgrade (2026-11-09)

- Added four reference protocols: `12-data-audit.md`, `13-independent-modeling.md`, `14-analytical-depth.md`, `15-visualization.md`.
- Added numeric/unit/period audit (`scripts/data_audit.py`) with explicit CSV rules and deterministic failed example (1185 vs 1165); no claims of live fact verification.
- Added circular-validation safeguards (`scripts/model_check.py`) and model declaration template.
- Added figure manifest integrity check (`scripts/figure_check.py`) plus research visualization methodology.
- Added `scripts/run_qa.py` integrated check. Missing required full-industry artifacts or errors result in BLOCKED. Manual evidence audit is still mandatory.
- Enhanced editorial rule: meaningful graphs and differentiated deep dives, not repetitive two-paragraph product cards.
- Expanded unit tests from 17 to 27, including data arithmetic, unit equivalence, source timing, input overlap, chart file and release gate checks.
- Preserved all v2.2 sector/depth/coverage content; no alteration to user's previously generated research reports.


## v2.2.0 — 2026-11-09

- 将 `industry_full` 定义为默认的全行业深度层级（用户要求完整/系统/深度时）；不再将速览稿标记为已完成全行业研究。
- 新增 `references/11-depth-completeness.md`：细分行业逐项覆盖、市场模型、公司地图、历史对照、正文建议篇幅和完整性阶段门槛。
- 重写 `assets/industry-report-template.md`，涵盖全景、市场供需、竞争公司、结构变化、投资含义和附录等研究内容。
- 新增 `assets/industry-coverage-template.csv`、`assets/revision-coverage-template.md`；编辑旧稿实施内容保留协议，不以“去 AI 味”为名删掉实质内容。
- 新增 `scripts/completeness_check.py`：结构化评估覆盖登记表，高优先级缺口与状态可追踪；新增4项测试。
- 在行业适配器中增加半导体设备专属研究卡要求，避免只分析市场总量与海外龙头利润率。
- 增强完整性检查：任何未完成项都会阻止标记“已完成完整版”；缺少证据、承诺的量化产出或不适用理由也会阻断；防止单条研究记录通过整行业检查。
- 新增半导体设备36项研究覆盖示例、原稿-7页稿的主题对照、Codex深度研究任务。
- 自动化单元测试增加至17项。

## v2.1.0 — 2026-11-09

- 新增 `references/10-writing-editorial.md`：面向研报的连续叙述、克制语言、宽表拆分、Word 排版、同口径财务对比等写作标准。
- 将写作与排版审校变为 `SKILL.md` 的强制步骤，并要求事实口径审核先于文字润色。
- 改写 `assets/industry-report-template.md`，研究摘要以段落为主，五力、反证、风险台账放入附录。
- `scripts/quality_check.py` 加入启发式格式检查：超过4列表格、密集粗体、箭头链、过程性标题。
- 新增两项测试（共10项通过），不声称脚本具备 AI 文本识别或事实真伪验证能力。
