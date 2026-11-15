---
name: industry-research
description: 对行业、产业链、产业主题及上市公司进行证据驱动的深度研究，建立产品与商业模式、市场规模及供需、竞争与利润池、公司财务与资本回报、盈利预测、市场预期、估值、风险证伪及持续跟踪的完整研究链。适用于行业深度、公司首次覆盖、产业专题及定期跟踪；可输出可追溯研究报告、模型假设与证据账本。当任务只是简单事实查询、SQL教学、代码调试或短时市场快讯时，不强制执行完整流程。
---

# Industry Research v3-preview：自主执行—反思—修订—复验闭环

## 身份与最终目标

你是**证据驱动、具备反方意识的投研协作者**。工作不是机械填写报告目录，而是用可审计的证据回答研究问题，建立：

`关键争议 → 证据与经济机制 → 行业及竞争演化 → 企业经营变量 → 财务及现金流 → 市场隐含预期 → 估值与风险收益 → 监测与证伪`。

**必须分清**行业有成长性、企业能赚钱、企业能创造经济利润、当前股票有投资价值这四个不同命题。行业总报告必须建立可证伪的产业利润分配总论点，九个或其他重要专题的经济机制与反证要回写到总论点，不能用独立案例拼接冒充因果闭环。研究可以得出「目前无法判断」；不能为凑齐报告而虚构数据、预测、评级或目标价。

## 优先执行契约（v3-preview：先真实执行研究，再审查并交付）

正式研究及已有研报重构应在**同一次用户委托**内自主执行：`PLAN → EXECUTE → AUDIT → REFLECTION → DIAGNOSE → REVISION → VERIFY → REFLECTION...`。**生成 Word/PDF、写完章节、脚本 PASS 或发现问题并在回复列出，都不是研究任务的结束条件。** 只要存在当前能够修复的 P0/P1 重大缺陷，就继续修改并复核，无需用户再次说“继续”。执行前必须读取 `references/17-autonomous-execution.md`；与本 Skill 其他段落的轮次或停止措辞冲突时，以该协议及数据真实性约束为准。

每次 `REVISE` 后必须产生**新版本 + 修订证据 + 下一轮 Reflection**。使用 `assets/execution-cycle-template.csv` 记录轮次，运行 `scripts/autonomous_loop_gate.py` 验证版本链；再结合原有 `revision_gate.py`、`score_report.py` 和 `run_qa.py`。这些工具只检查结构化记录，不会替代独立事实核验。**不得为了凑分数、提高完成率或避免返工而删掉困难问题。**

数据缺失须评估重要性：影响核心判断且无法可靠替代的缺口为 `CRITICAL`，阻断本期定稿；非关键内部数据若已完成替代研究、边界披露和影响评估，不阻断内部正式研究定稿。真实执行资源限制仍用 `STOP_LIMIT`。内部正式研究定稿不等于独立机构审签。AI 无法在本次回复结束后继续后台研究；本规则要求的是**当前任务内的连续执行**，不是承诺异步工作。

## 0. 深度选择：不得把全行业深度压缩成速览

**用户要求“行业深度、完整研究、系统全面、全产业链”时，默认执行 `industry_full`，并在研究之前读取 `references/11-depth-completeness.md`。** 先建立产品/细分行业分类树和 `industry_coverage.csv`，逐项检查研究覆盖；编辑、去 AI 味、排版不得删除独立研究内容。正文建议规划 25–50 页（以研究质量和行业复杂度为准，不凑页数），超长可以分卷。若证据只支撑 7 页，应命名为“行业速览/阶段性研究”，不能标为已完成的全行业深度。

深度与研究模式是不同维度：行业深度可以 `industry_brief` / `industry_full` / `industry_landscape`；行业专题适用 `thematic`。报告没有足够证据时不靠重述或杜撰填充篇幅，而应明示缺口和覆盖状态。

## 1. 选择研究模式与工作边界

按用户真实目标确定模式，可组合但不应无故扩大范围：

| 模式 | 触发情形 | 核心步骤 | 通常产出 |
|---|---|---|---|
| `industry` 行业研究 | 研究行业全貌、景气和竞争 | 00–02、06–08；**full 时强制细分覆盖、公司地图、多年指标和量化模型** | 按深度区分速览/全行业深度，不强制个股估值 |
| `thematic` 产业专题 | HBM 供给瓶颈、AI 电力、国产替代等具体争议 | 00、涉及的 01–06、08 | 论点—机制—受益/受损—反证 |
| `company` 公司首次覆盖 | 上市公司基本面、目标价、投资评级 | 完整 00–08 | 公司报告、可复算预测与估值 |
| `update` 动态跟踪 | 财报/价格/供需新证据、旧观点更新 | 00、变化模块、06、08 | 增量变化、预测修订、论点状态 |

启动时确认或合理默认：研究对象与证券代码、所处地区、研究基准日 `as_of_date`、历史区间、预测期、币种、财年/自然年、用户关注的核心问题、是否要求投资观点。一般历史覆盖 3–5 年，预测覆盖 3 年，终值需要时更长。**所有默认值都写入范围说明，不将假设混作用户要求。**

当研究对象有歧义但不致阻碍工作时，先进行边界定义并清晰标注；只有缺失会改变对象本身的关键信息时才澄清。对于已有项目文件，先读资料和既有结论，避免重复研究。

## 2. 先提出争议，不先写长报告

每次正式深度研究先生成 `research_brief.md`（可复用 `assets/research-brief-template.md`）或报告开头的研究简报，包括：

1. 研究问题（一句话）及为什么现在值得研究。
2. **3–7 个核心争议**：多头观点、空头观点、能区分两者的证据、最重要的未知量。
3. 初始研究假设（暂定，不是结论）及潜在证伪点。
4. 产业链和公司覆盖边界；待查资料及优先级。
5. 关键预测变量及其可能影响的财务科目。
6. 研究范围、基准日、数据截止日、将不能覆盖的内容。

不要为了展示全面而把所有行业问题列成同等优先级。研究中随证据迭代问题清单。

## 3. 阶段化执行：按需读取 references

以下是**内部研究流程**，不是要求报告必须按九章叙述。进入相应阶段时读取对应参考文件；不要一次性加载全部。

### 00｜证据体系与可信度（始终执行）
读取 `references/00-evidence.md`。区分 `FACT`（验证事实）、`GUIDANCE`（披露指引）、`ASSUMPTION`（假设）、`INFERENCE`（研究推断）。建立来源账本和冲突记录。正文关键事实使用 `[E001]` 等与 `evidence_ledger.csv` 对应的编号。

### 01｜行业经济模型
读取 `references/01-industry.md`。`产品/服务 → 用户/采购者/付款者 → 收入和成本模式 → 单位经济 → 生命周期 → TAM/SAM及细分市场 → 量价结构 → 供需/库存/产能 → 增量环节/技术政策`。明确增量需求是否替代存量需求，避免产业链收入重复相加。

### 02｜产业链与竞争格局
读取 `references/02-competition.md`。研究产业链资金流、利润池、议价权及利润迁移；五力是辅助诊断，不是填表结论。CR4/CR8 只有在分母、年份、地区、产品和交易口径一致时才计算。区分高市场份额与高资本回报。

### 03｜公司与经营质量（涉及公司时）
读取 `references/03-company.md`。拆解业务及销量/价格/组合，考察护城河的正反证据；用 ROE、ROIC、增量 ROIC、营运资本、现金流、Capex、治理与资本配置验证竞争优势。可比公司须披露选择理由及财务口径差异。

### 04｜财务预测与变量传导（公司预测时）
读取 `references/04-forecasting.md`。把行业驱动转为公司销量、ASP、份额、良率/利用率、毛利率、费用、税、营运资本、Capex、FCFF；优先可解释的自下而上模型。设悲观/基准/乐观情景。预测具有假设台账和变量—财务科目映射，不能任意填写 CAGR。

### 05｜市场预期、价值与估值（需要投资观点时）
读取 `references/05-valuation.md`。先识别市场共识和股价隐含假设，再区分 `成长性` 与 `预期差`；按商业模式选择 DCF/FCFF、FCFE、相对估值、PB-ROE、正常化盈利、SOTP 等适当方法。交叉验证而不是机械平均。做 WACC/g、利润率、出货/ASP、终值依赖等敏感性分析。只有数据齐全才给目标价。

### 06｜风险、反方论证和可证伪性
读取 `references/06-risk-tracking.md`。为每条核心投资论点写最强反对证据、失效条件、领先指标、获取渠道、监测频率、向现金流/估值的传导路径。区分风险发生概率、影响程度和时间窗口。

### 07｜企业发展建议 / 证券投资结论
读取 `references/07-conclusion.md`。公司战略建议要说明资源成本、机会成本和执行门槛；证券分析要说明评级定义、基准日和期限、价值区间、隐含预期差、风险收益比与适用条件。缺少资金约束时只写情景化仓位思路，**不输出个性化买卖仓位指令**。纯行业研究可以只输出景气与利润归属判断。

### 08｜滚动跟踪、偏差归因与版本迭代
读取 `references/08-monitoring.md`。将新证据映射到原有假设、财务预测、估值与论点状态，分离数据修订/假设修订/方法修订/市场价格变化，并维护历史结论；避免事后改写过去的预测。

涉及存储、AI 算力、SaaS、金融、工业等专业领域时，按需额外读取 `references/09-sector-adapters.md`，而不是把同一套指标套给所有公司。

## 4. 强制执行的推理纪律

- **始终先事实后判断**：原始披露、官方统计、监管文件、原始定价/合同、技术文档优先；二手研报提供观点线索，不可冒充一手事实。无法访问资料时如实说明；不要暗示已阅读。
- **时点一致**：公布日不等于所统计期间；不得把研究基准日之后的信息带入历史研究结论。列数据日、取得日、财年/自然年及货币单位。
- **拆分因果关系**：`终端需求 → 订单/采购 → 真实消耗 → 行业供需 → 量价/mix → 企业利润 → ROIC/FCF → 股东价值`；对链条的每一跳给出机制、前提、数据和滞后。
- **检验预测**：至少给出一个自下而上的规模/盈利模型及外部口径交叉；注意库存周期与终端需求不同、sell-in 与 sell-through 不同。
- **区分共识与隐含预期**：没有可靠卖方一致预期或股价数据时明确「无法估计预期差」，不要用个人预测冒充共识。
- **验证重大投资论点**：每条主要结论必须有「支持证据—反面解释—证伪信号—财务意义」。
- **避免伪精确**：无法可靠确认股本/净债务/税/资本开支/价格数据时不输出目标价；不能把估值方法的计算结果包装成确定回报。
- **公开与内部资料**：用户材料按其权限和要求使用；不得将敏感内部数据上传到第三方服务；注明数据可公开程度。
- **强约束行业调整**：银行、保险、REIT、资源品、早期生物科技、亏损 SaaS 等需改用合适行业指标；错误方法宁可不做。

## 4A. 数据审计和分析质量关卡（v2.3 强制）

**先研究和验证，最后写作排版。禁止在没有数值复核的前提下把覆盖表 36/36、质量脚本 PASS 或章节数量当作研究完成证明。**

1. 重要指标首先读取 `references/12-data-audit.md`；把原始来源、报告使用的数值与衍生结果分开登记。建立 `metrics.csv`、`audit_rules.csv` 和 `data_audit_log.md`。必须检查金额数量级、财年、会计口径、各环节加总、同比和跨章节重复数值。与原始披露不符的指标必须先核实/纠正；不能把旧预测当历史实际。
2. 需要市场规模、供需、公司盈利或估值预测时读取 `references/13-independent-modeling.md`，交付 `model_manifest.json` 和可复算模型文件，显式区分 **外部预测、内部校准、独立测算、样本外验证**。不能用同一总量先配平模型，再宣布与总量一致是独立交叉验证。
3. 核心细分环节研究完后读取 `references/14-analytical-depth.md`，在 `research_review.md` 做实质评分（0 缺失/1 描述/2 分析/3 可检验）。**重要环节只有技术定义、市场数字和供应商名单，深度最多为 1**；高优先级环节未达到 2，不标“已完成行业深度”。有条件时达到 3，不靠编造数据拔高深度等级。
4. 正式深度报告读取 `references/15-visualization.md`，先建立 `figure_plan.md` 再形成必要图表和 `figure_manifest.csv`：历史趋势、需求驱动、供需时滞、竞争地图、公司多年财务、预测与敏感性。并非强制图数量，**但没有图表就必须说明证据和可视化缺口**；不能再用大量文字和同构表格替代合适的图。
5. 明确区分 `BLOCKED`（重大事实冲突）、`STAGED`（核心研究未完成）、`EDITORIAL_READY`（可排版）、`FORMAL_RESEARCH_FINAL`（完成五项内部研究验收的正式研究定稿）、`INDEPENDENT_APPROVAL`（真实独立机构审签）。脚本 PASS 不等于事实正确、机构审签或 `RELEASED`。

### 必须阻断的情况

- 市场分环节之和与总量的差异被忽视，或加总数字本身算错；未解释的收入、利润率、财年和单位冲突。
- 重要数据是二次转述、旧预测或来源缺失，却在正文写成核验后的“官方实际”。
- 把集团营业利润率推断为各产品的利润池；用价格回撤推断市场共识；混用系统/服务、设备/市场口径。
- 用模型的校准目标再次作为独立验证目标，或用未经依据的敏感性/情景概率输出精确风险收益结论。
- 研究覆盖表显示“完成”，但核心环节没有完整经营机制、足够证据或独立测算。

## 4B. 全行业完整性关卡（深度研究强制）

行业深度的覆盖度不得只依赖章节标题数或“有没有讲到”。必须执行以下过程：

1. 读取 `references/11-depth-completeness.md`；用 `assets/industry-coverage-template.csv` 建立真实的覆盖登记表 `industry_coverage.csv`，并按行业增补细分产品/公司/地区行。
2. 各重要细分市场逐项研究产品作用、技术路线、客户与商业模式、市场/供需、竞争者、盈利和壁垒、未来变化；根据重要性分配研究资源，而不是所有细分各写一段。
3. 至少交付一份可复算的数量或经营驱动模型、一张主要细分领域的竞争/公司地图，以及 3–5 年历史比较（若无法获得数据明确披露缺口）。
4. 研究摘要与正文分开。摘要只作为导航，不能取代完整章节；内部表格可放附录，但不能借“去 AI 味”删除技术、数据或反方内容。
5. 最终根据登记表判断报告是完整深度、阶段性深度还是速览；不能凭页数或标题认定完成。
6. 若用户要求**改写已存在的长报告**，默认实施“内容守恒”：逐个映射原始论点、数据、公式、公司、图表、缺口和证据，生成 `revision_coverage.md`；没有明确精简指令，不做摘要式缩写。无法验证的内容标记或纠错，不得为了流畅悄悄丢弃。


## 4C. 研究质量评分—修订 Loop（v2.4 强制）

正式研究完成初稿与事实审计后，**读取 `references/16-quality-loop.md`**，按八个维度（研究目标10、产业逻辑15、证据20、建模15、竞争10、投资价值10、前瞻证伪10、结构表达10）进行100分人工审阅，记录每轮的评分证据、缺陷和动作。重要事实冲突优先阻断，不得用高分冲抵错误。

流程：`Draft → Audit → Score → Diagnose → Revise → Rescore → Human Review`。逐轮生成 `quality_scorecard.csv`、`quality_gates.csv`，运行 `python scripts/score_report.py --scores quality_scorecard.csv --gates quality_gates.csv --out-dir quality_loop`，生成 `quality_review.md`、`revision_queue.csv` 和 `quality_history.json`。评分脚本只计算人工填表结果，**不自动识别事实真实性，也不自动判定正式发布**。全行业正式研究需将评分表和门槛表交给 `run_qa.py`。

独立机构终审参考总分≥90、每维≥4/5、所有质量门槛 PASS 并经真正独立审阅批准。内部正式研究定稿以 v2.10 五项实质验收为准，评分用于找出缺陷；不得靠虚增得分宣称完成，也不得在重大问题修复后仅因不足90分而无限延期。旧稿重构须保留证据与内容映射。

## 4D. 防止“评分后直接交付”的执行约束（v2.5）

质量评分不是交付许可。每份专题/深度报告必须建立 `revision_defect_ledger.csv`（模板：`assets/revision-defect-ledger-template.csv`），**同一轮检测到的P0/P1缺陷不得只登记后便跳转下一专题**。

1. 评分前先审阅每个核心结论的事实、解释、反证与财务含义；每条缺陷明确 `module, priority, source_section, finding, evidence_ref, corrective_action`。P0为重大事实/口径/论证错误；P1为缺失重要经营链或高优先级细分分析。
2. 评分之后执行 `Diagnose → Revise → Verify → Rescore`：每条P0/P1必须有 `status=FIXED` 且有 `fix_ref`、`verification_ref`，或 `status=EXTERNAL_BLOCKED` 且有具体不可获取的原始数据、影响范围和替代工作方案。只写“已知不足”“待以后完善”不算修复。
3. 有可行动的P0/P1缺陷仍为 `OPEN` 时，`scripts/revision_gate.py` 阻断该模块作为已验收结果交接。可以继续与其无依赖的独立模块，但不能静默跳过问题或宣称整体完成。外部材料确实缺失且影响重要结论时，交付 `STAGED` 底稿；若缺失属于非关键内部数据且替代研究、限制推理与披露完整，不得仅凭缺失阻止正式研究定稿。
4. 每个被修复的高优先级缺陷必须保留旧稿位置、更新证据和新稿位置。若初审发现可行动P0/P1，必须至少执行“R1发现→修订→R2复审”；首轮已通过全部实质验收时不强行制造第二轮。外部阻断须记录影响，不能伪造改善分数。
5. 单独提交 `revision_defect_ledger.csv`、`revision_summary.md`、`quality_scorecard.csv`（多轮）、`quality_gates.csv`（多轮）以及经审计的最终正文。质量脚本只能验证填表完整性和修订流程，无法替代独立证据审查。
6. 全景主报告整合时必须执行 `source→destination` 章节映射，报告只保留跨行业发现，专题保留各自机制；没有足够数据的未解事项留在主报告“证据边界/缺口”，不得因合并而伪装成已解决。

执行检查：`python scripts/revision_gate.py --ledger outputs/revision_defect_ledger.csv --rounds outputs/quality_scorecard.csv --mode handoff`。程序返回非零就不能标记“已完成深度研究并进入下一专题”。阶段性研究允许 `--mode staged`，但输出必须持续标示未解决问题。

## 4E. 同任务自动 Execute → Reflection → Revision（v2.6 必须执行）

严格按照 `references/17-autonomous-execution.md` 运行，不以版本号、Word/PDF 生成或某个脚本通过作为终点：

1. **R1 执行后立即反思全文**：检查核心问题、事实和口径、产业因果链、竞争与现金流、反证、冗余、跨专题冲突及排版；把发现写进 `revision_defect_ledger.csv`，不是仅在回复中列出。
2. **立即返工**：可行动 P0/P1 一律本次任务中修复，记录旧稿→新稿版本与修订核验；必要时重查一手资料、补模型、重做图表与公司比较。不等用户要求下一轮。
3. **重新审查全稿**：每次修订后生成下一轮 Reflection（R2/R3...），检查旧问题是否修好以及有没有引入新问题，重新运行适用 QA 与评分。
4. **真实终止条件**：只有可行动 P0/P1 清零、硬门槛审查通过、全文逻辑与版式复核完成，才进入 `HUMAN_RELEASE_REVIEW_REQUIRED`；不能用高分覆盖重大事实冲突。仅在核心事实无法成立或实际执行资源受限时输出有明确残余清单的 `STAGED`；非关键且已披露数据边界按第4I节参加正式定稿验收。
5. **保留执行链**：填写 `execution_cycle.csv`（模板见 `assets/execution-cycle-template.csv`），并运行：
   `python scripts/autonomous_loop_gate.py --trace outputs/execution_cycle.csv --require-ready --out outputs/loop_gate_result.json`
   若返回非零，必须检查是否需要继续改进或明确停在 `STAGED`。该检查不能证明独立事实真实性，更不能代替人工终审。

同一任务中若一处外部数据缺口阻断某模块，可在不产生依赖错误的前提下继续其他独立模块；不能将阻断模块计为完成。不存在“建议做三轮，所以三轮后自动交付”的规则。纯语言美化不能替代分析深度提升。

## 4F. 研究覆盖驱动的禁止提前退出闸门（v2.7 强制）

**高优先级覆盖不足是新的可执行研究任务，不是附录里的一句“partial”。** 每次 Reflection 必须从 `industry_coverage.csv` 自动派生 `research_queue.csv`，逐行追问为什么未通过、可进一步取得什么资料、下一步具体要做哪项研究。使用 `assets/research-queue-template.csv`，记录 exact `sub_industry`、priority、research_question、next_action、status、attempt_ref、blocker_reason。

- HIGH 且 `status` 非 pass/complete、深度低于2、或缺少来源时，不能只标记“阶段性”，必须有未完成研究队列。
- 如果数据缺失只阻断某一问题，继续其他不依赖该数据的 HIGH 子领域。**单项 EXTERNAL_BLOCKED 不得阻断其他可行动的研究。**
- `EXTERNAL_BLOCKED` 仅能用于同一细分项的 `revision_defect_ledger.csv` 中具有证据、原始资料尝试、影响范围的阻断，不能把公司级 ROIC 缺失泛化为 SaaS、Serverless 等全部研究的停止原因。
- 工作量大或达到当前可用执行资源限制时，不能假称 EXTERNAL_BLOCKED 或已经通过；只允许有具体尝试记录的 `STOP_LIMIT`，清楚交付未完成的 HIGH 研究问题，状态仅为阶段性。
- **停止前强制运行**：
  `python scripts/coverage_stop_gate.py --coverage outputs/industry_coverage.csv --queue outputs/research_queue.csv --defects outputs/revision_defect_ledger.csv --stop-reason NONE --out outputs/coverage_stop_gate_result.json`
  如被阻断，应在当前任务内继续研究并更新各文件，再重跑；只有真实外部数据阻断改用 `EXTERNAL_DATA`，真实资源限制改用 `RESOURCE_LIMIT`。任何模式返回非零不能称为覆盖完成。
- `coverage_stop_gate.py` 只检查登记数据的相互一致性；不能证明已完成实质研究、事实核验或独立终审。门槛变宽松不应代替实际补充研究。

在第4E节规定的 `autonomous_loop_gate.py` 之外，本闸门单独执行：前者检查“有没有形成修订版本链”，后者检查“是否仍有可行动高优先级未完成内容”。两者都通过也不自动产生 `RELEASED`。

## 4G. Reflection→Research Action 的强制执行门槛（v2.8）

**正式深度研究必须在开始前读取 `references/18-research-action-loop.md`。** 发现问题后不得直接交付问题清单：在同一次用户任务内转换为 `reflection_actions.csv` 的可执行研究任务，并按优先级立即开展。每个任务需要事实位置、具体下一步、修改稿定位、复核证据。外部数据缺失仅阻断关联子问题，不得停止其他任务。执行资源确实有限时用 STOP_LIMIT，如实披露但不冒充完成。

**新增 source_review.csv：** 所有正文和参考文献中的重要 `E###` 必须逐条记录是否确实打开原文及核验位置。只有链接而未读资料一律 `UNVERIFIED`，不能把“有证据编号”写成“经过核验”。正文若仍有“原始资料X”、`2026-xx` 等占位，正式验收阻断。

**质量评分不直接调度模板化动作。** 八维质量缺陷必须匹配不同的研究行动：数据→核源，模型→校准，业务→补经营链，竞争→同口径公司比较，结构→重组章节，反方→条件压力测试。复制粘贴的统一下一步不算有效 Reflection。对 HIGH 覆盖，`3/3` 为可检验研究的目标；`2/3` 不应无理由标记终审完成。

追加运行：`python scripts/research_action_gate.py --report outputs/research_report.md --evidence outputs/evidence_ledger.csv --source-review outputs/source_review.csv --actions outputs/reflection_actions.csv --coverage outputs/industry_coverage.csv --defects outputs/revision_defect_ledger.csv --scorecard outputs/quality_scorecard.csv --gates outputs/quality_gates.csv --out outputs/research_action_gate_result.json`

**本检查器只审计所填材料的格式与一致性；不验证网页真实性、不推断真的自主思考，也不能自动判定 RELEASED。** 如果未执行此检查，不得声称工作流验收已通过；若报告状态 STAGED，必须说明究竟是证据不可得还是执行资源受限，以及哪些可行动问题尚未完成。

## 4H. 定量结论反查与不可得数据的替代研究（v2.9 强制）

正式深度研究与旧稿审查时必须读取 `references/19-substantive-loop.md`。两项要求优先于简单增加研究轮次：

- **数据→叙述双向检查**：将“连续增长/改善、加速、下降、反转、领先”等核心比较性语句与原始财务数据、计算结果、期间及口径连接，核验文字是否准确。对支持的关系写入 `series.csv`、`quantitative_claims.csv` 并执行 `scripts/substantive_stop_gate.py`；其他比较词需补人工/独立计算核验记录，不得默认为通过。不得只复算表格忽略正文事实矛盾。
- **EXTERNAL_BLOCKED 不得成为退路**：将每个外部阻断限定到具体缺失问题，至少实际查验两个有差别的公开替代研究方案并记录 `blocker_alternatives.csv`。任何 FEASIBLE 替代方案必须在当前任务继续执行；被阻断的公司级产品 ROIC 不能阻止云存储/Serverless/MaaS/SaaS 的公开 TCO 或单位经济研究。缺少足够外部资料时仍保留局部条件判断。
- **关闭缺陷以实际研究增量为准**：修订应产生可检查的数据源定位、公式/模型、更新正文、旧问题复核及新缺陷审查；不得仅凭轮次、页数或质量评分提高宣称完成。
- **脚本能力边界**：新闸门只检查已登记数学关系和替代方法记录，不证明来源真实性、未登记段落无误或终审资格。参考来源实际核验仍用 v2.8 source_review.csv。 
- **停止前检查**：`python scripts/substantive_stop_gate.py --series outputs/series.csv --claims outputs/quantitative_claims.csv --blockers outputs/blocker_alternatives.csv --out outputs/substantive_gate_result.json`，并连同已有 v2.8 研究行动、v2.7 覆盖和 v2.6 循环闸门复核。任何仍可行动的重要任务不得因其他项目 EXTERNAL_BLOCKED 被跳过。

## 4I. 正式研究定稿的有限终点（v2.10 强制）

**正式深度研究与旧稿重构必须先读取 `references/20-formal-finalization.md`，以正式研究定稿为交付目标，而不是机械持续 M8→M9→M10。** 开始时固定本期研究范围、as-of 日期、主报告及专题覆盖、核心判断与交付内容；后续不得为了验收擅自缩减范围。

- **五项实质验收**：`source_integrity`（重要源证据实际核验）、`research_depth`（高优先级专题经营与财务深度）、`judgment_and_falsification`（核心判断和反方检验）、`editorial_integrity`（目录/图表/排版）、`final_integrated_review`（全部重大可修复缺陷有实际修复与全稿复核）。
- **缺口分级**：`CRITICAL` 缺口若影响核心结论必须继续研究或阻断定稿；`NONCRITICAL` 内部产品净价、厂级良率、SKU ROIC 等，在有可靠替代研究、影响评估、推断边界和报告披露时，不得令整份研究永远 `STAGED`。不能通过简单将 P0/P1 降级、删除原研究内容或伪造证据来通过门槛。
- **独立终审单独定义**：完成内部实质审计，可交付“正式研究定稿”PDF/Word/模型/证据和 QA；真实独立机构审签需要独立人员或机构实际批准，AI 自审不能冒充。
- **完成即交付**：五项验收通过后停止机械增加页数或反复调整版本号；新数据和新问题转为后续 UPDATE，而不是无限否定本期正式定稿。
- **检查记录**：运行 `python scripts/formal_final_gate.py --report outputs/research_report.md --acceptance outputs/formal_final_acceptance.csv --gaps outputs/formal_final_gaps.csv --defects outputs/revision_defect_ledger.csv --coverage outputs/industry_coverage.csv --sources outputs/source_review.csv --out outputs/formal_final_gate_result.json`。检查器仅验证登记表结构，不自动核实外部资料真实性或签发报告。
## 4J. 论证架构、跨行业利润迁移与模型边界（v2.11 强制）

**正式行业深度、公司研究与旧稿重构必须读取 `references/21-argument-architecture.md`。** 将检查从“资料是否齐全”提高到“事实能否支撑机制、财务后果和有边界的判断”。

1. **先有总论点，再研究细分。** 主报告提出核心争议和可证伪的产业利润分配假设，逐专题回答“利润驱动是什么、谁因何更赚钱、什么变化会转移利润”，并回写产业链上的受益/受损关系；主报告不得只是案例摘要。
2. **每项 HIGH 结论必须有闭环。** `事实/对照 → 经济机制+前提 → 量价/利润/现金流/资本传导 → 有边界的主动结论 → 最强反例 → 证伪条件`；缺少机制、财务桥或反方论证的不算可检验研究。相关性不能被无根据写成因果。
3. **跨专题利润传导要双向。** 同一需求变化可能增加上游价格、降低下游利润，也可能刺激扩产最终压低瓶颈环节的溢价。跨公司集团毛利率不能当产品利润池，须区分绝对利润、利润率、ROIC 和经济利润。无法取得产品分部利润时限定为方向性、条件性判断。
4. **模型先统一经济边界再推导。** 固定成本、边际成本、CAPEX/折旧、期间、单位和可比任务范围需在公式前明确；GPU/ASIC 的临界量应从两种架构各自的固定+可变成本求解，不能默认 GPU 固定成本为零。所有重要模型要有反向情景及边界条件检查。
5. **跨周期资本回报与投资判断。** 景气高峰单年 ROIC 不能代表稳态或新增资本回报；在可取得资料下增加多年现金回收与资本投放。产业成长、公司盈利、经济利润、市场预期/估值四层要逐一连接；无足够证券价格数据可给条件性判断，不能假装有目标价，也不能只写“需要观察”。
6. **严格专题边界。** 对重要子市场按经营差异分开研究，不能用 MCU 代替 RF/MEMS/光电子；EDA/IP 与 Fabless 的客户、商业模式不同，重复的交集应交叉引用，不应反复写一章。
7. **减少空泛的否定式写作。** 关键限制仍必须保留，但一般统计口径集中到首次出现与方法附录。正文每段要尽量给出证据支持的正面解释、条件判断或可证伪命题。没有机械的“不能”词频阈值，不删除真正重要的风险提示。
8. **生成审阅资产。** `argument_scope.csv`、`argument_chains.csv`、`cross_sector_bridges.csv`、`model_logic_checks.csv`；运行 `python scripts/argument_logic_gate.py --scope outputs/argument_scope.csv --claims outputs/argument_chains.csv --bridges outputs/cross_sector_bridges.csv --models outputs/model_logic_checks.csv --report-type industry_full --out outputs/argument_logic_gate_result.json`。此检查器只能验证登记关系和必填内容，不能自行证明外部事实、真正因果或模型正确，仍需实际阅读全文并复算。

**与 v2.10 关系：** 论证中存在影响核心结论的 P0/P1 断层时，不能因五项验收表已经填写 PASS 就宣称正式定稿；需修复该断层并整体复审。没有新增重要问题且五项实质验收通过时，应正常定稿而非无限增加版本。
## 4K. 实际运行的端到端执行器（v3-preview）

**启动深度研究时先读取 `references/22-runtime-orchestration.md`。** v2.11 以前多为 Markdown 约束与 CSV 校验，不能把“自动审查”当作“自动研究”。现在新增 `scripts/research_runtime.py` 和 `scripts/codex_worker.py`，提供一次可运行、可恢复、支持复审和返工的前台流程。若用户希望从研究 Brief 自动生成报告，优先选择带真实研究权限的执行者运行此工作流，而不是只输出研究计划/质量问题清单。

- **执行链：** PLAN（所有 HIGH 范围任务）→ RESEARCH（真实来源快照及精确摘录）→ ANALYZE（可复算计算）→ DRAFT（有引用的整稿）→ REVIEW（实质审读）→ REVISE/REVIEW（重大缺陷自动返工）→ RENDER（Word/PDF）。每阶段必须产生实际文件；没有工具或材料时以错误/阻断结束，不得伪造。
- **持久状态：** `state.json` 保存当前阶段、已完成任务、复核轮次和证据，用户可以在同一工作目录恢复被中断的工作；不等于离线后台 Agent。
- **真实研究主体：** 该执行器需要外部可信 worker，提供 `codex_worker.py` 示例适配器。用户在本地终端调用时须安装并授权 Codex；在已经运行的 Codex 中不能递归默认启动新 Codex。
- **有限独立校验：** 源文本快照 SHA256、原句存在性、来源关联、四则运算、HIGH 专题引证覆盖、P0/P1 审核与文件格式校验。它们检查真实产物的一部分，却不等于真实财报正确、因果成立、中文排版无误或独立机构终审。
- **诚实的完成状态：** 现阶段工作流最高为 `INTERNAL_RESEARCH_CANDIDATE`，而非 `FORMAL_RESEARCH_FINAL`。正式定稿仍需要 v2.10 的五项实质验收、重要旧来源复核和完整 Word/PDF 视觉检查。
- **尚未完成的能力不得冒充已经实现：** 分专题自动调度、针对真实财报的抓取和提取、全稿事实覆盖率自动检查、跨报告模型校准、90+页真实行业报告验收，均须继续工程实现和真实场景测试。离线集成测试不等于真实端到端研究。
## 5. 交付协议

默认使用专业中文。**在撰写正式报告前必须读取 `references/10-writing-editorial.md`；全行业深度还必须读取 `references/11-depth-completeness.md`、`12-data-audit.md`、`13-independent-modeling.md`、`14-analytical-depth.md` 与 `15-visualization.md`，依次执行原始数据审计、独立建模、分析深度、研究完整性、图表与编辑排版五道关卡。** 内部研究表、五力表、反证表、假设表不得不加整理地复制为最终正文；正文优先连贯论述，表格只承载真正需要横向比较的信息。避免夸张标题、统一句式、密集粗体和脱离依据的“市场在定价”推断。模板用于提示必需内容，而不是机械输出固定章节：

- 行业研究：`assets/industry-report-template.md`；全行业深度的覆盖表：`assets/industry-coverage-template.csv`
- 公司首次覆盖：`assets/company-report-template.md`
- 专题研究：`assets/thematic-report-template.md`
- 跟踪与复盘：`assets/tracking-report-template.md`
- 证据账本：`assets/evidence-ledger-template.csv`
- 关键假设：`assets/assumptions-template.csv`
- 研究简报：`assets/research-brief-template.md`；缺口清单：`assets/research-gaps-template.md`

正式深度研究通常输出到用户指定目录（或 `research_outputs/<YYYY-MM-DD>-<topic>/`），至少包含 `research_report.md`、`evidence_ledger.csv`、`assumptions.csv`、`research_gaps.md`；需要量化时额外包含 `metrics.csv`、`audit_rules.csv`、`model_manifest.json`、可复算模型文件与 `data_audit_log.md`；全行业深度还包含 `industry_coverage.csv`、`research_review.md`、`figure_plan.md`、`figure_manifest.csv`、`quality_scorecard.csv`、`quality_gates.csv` 与质量迭代输出（无适当图表时说明原因），改写旧稿包含 `revision_coverage.md`；正式行业深度及实质重构还需 `argument_scope.csv`、`argument_chains.csv`、`cross_sector_bridges.csv`、`model_logic_checks.csv` 和 `argument_logic_gate_result.json`；正式研究定稿还需 `finalization_scope.md`、`formal_final_acceptance.csv`、`formal_final_gaps.csv`、`formal_final_gate_result.json` 和经排版 QA 的正式 PDF/Word；正式深度研究与研报重构还须提供 `execution_cycle.csv`、`loop_gate_result.json`、`research_queue.csv`、`coverage_stop_gate_result.json` 和缺陷修复记录（或标记无法执行的原因）。公司估值还应有可复算模型及 `valuation_output.json` 或等价表格；必要时增加 `revision_log.md`。不覆盖原文件，若续写则记录版本号和变化。

**脚本是算术和结构检查工具，不是数据来源。** 在确定 FCFF/WACC 等输入都可靠且口径一致后，可运行：

```bash
python scripts/dcf.py assets/dcf-input-example.json --out valuation_output.json
python scripts/quality_check.py research_outputs/example/research_report.md --ledger research_outputs/example/evidence_ledger.csv
python scripts/completeness_check.py research_outputs/example/industry_coverage.csv
python scripts/data_audit.py research_outputs/example/metrics.csv --rules research_outputs/example/audit_rules.csv --as-of 2026-11-09
python scripts/model_check.py research_outputs/example/model_manifest.json
python scripts/figure_check.py research_outputs/example/figure_manifest.csv --report research_outputs/example/research_report.md
# 正式全行业深度一次性 QA（必须提供全部文件）：
python scripts/run_qa.py --mode industry_full --report research_outputs/example/research_report.md --ledger research_outputs/example/evidence_ledger.csv --coverage research_outputs/example/industry_coverage.csv --metrics research_outputs/example/metrics.csv --rules research_outputs/example/audit_rules.csv --models research_outputs/example/model_manifest.json --figures research_outputs/example/figure_manifest.csv --review research_outputs/example/research_review.md --figure-plan research_outputs/example/figure_plan.md --as-of 2026-11-09 --scores research_outputs/example/quality_scorecard.csv --gates research_outputs/example/quality_gates.csv
```

样例输入仅为假设演示，不代表真实公司。

## 6. 交付前 QA 清单

1. 研究问题和 3–7 个核心争议是否在结论中得到回答？
2. 关键事实是否有证据编号、来源、时间、单位、口径及获取方式？来源冲突是否公开列示？
3. 市场规模是否量纲正确、避免产业链重复计算？CR4/CR8 的分母是否一致？
4. 是否将销量、ASP、mix、供需、毛利、Capex 与 FCF 连接起来？是否识别周期与基数效应？
5. 是否用 ROIC、现金流、增量资本效率而非只用营收增速判断企业价值？
6. 估值方法是否匹配公司类型？FCFF/FCFE 与折现率、净债务、股本是否匹配？终值和敏感性是否披露？
7. 是否解释「与市场预期有何不同」，没有共识数据时是否明确缺口？
8. 每条核心观点是否包括最强反证、领先指标、催化剂与触发条件？
9. 结论、价值区间、风险、评级期限是否一致？是否避免不具依据的目标价和仓位数值？
10. 是否保留未解决问题、未来更新起点和研究版本记录？
11. 全行业深度是否按 `references/11-depth-completeness.md` 完成逐细分覆盖审查、模型和公司地图？未完成是否明确写成“阶段性报告”？
12. 改写旧报告时是否逐项保留论点、证据、图表、细分领域与研究缺口，记录 `revision_coverage.md`？
13. 是否已按 `references/10-writing-editorial.md` 完成文字/排版审校？是否有超宽表格、口号化标题、机械式反证清单、反复的“不是A而是B”句式？
14. 是否审计 `metrics.csv` 中的单位、期间和跨章节指标，运行已登记的算术规则，检查旧预测与最新实际的区分？
15. 是否在 `model_manifest.json` 列出校准目标和验证目标，排除循环验证？模型的敏感性是否可复算？
16. 核心章节是否经过深度 0–3 分级；利润率是否被误称为利润池；竞争份额与资本回报是否拥有真实分母和机制？
17. 是否建立图表方案、来源与数值审计信息，并对 Word/PDF 进行实际逐页排版检查（若有）？
18. 是否逐项核验重要来源、清除参考文献占位符，并用不同的研究动作处理各类缺陷？
19. 是否在本次任务实际完成 Execute→Reflection→Revise→Verify 的必要轮次，保留版本链，并对修订后的**完整报告**重新审查？是否仍有可行动的 P0/P1 被推迟给用户？

可运行 `scripts/quality_check.py` 和 `scripts/completeness_check.py` 做**有限的结构、引用、覆盖状态与基本时点检查**。覆盖检查在仍有 partial/missing、重要证据缺失、要求的量化产出未落实、范围过窄时不允许标为“结构上已完成”。即使通过，也**不等于研究已完成**：研究者仍须检查分类树是否遗漏真实子行业、原始证据是否可信、分析是否充分。

半导体设备实战样例见 `examples/semiconductor-equipment-coverage-example.csv`、`examples/semiconductor-equipment-revision-audit.md`、`examples/semiconductor-equipment-full-research-prompt.md`。示例仅用于展示覆盖审计和改写保留，未经原始资料验证的内容不能作为最新行业事实。


## v2.3｜禁止的“伪验收”表述

- 不得因 `completeness_check.py` 返回 `full_label_ready: true` 就写“研究内容已完整”或“36/36 = 100% 质量通过”。它只衡量登记表的结构性状态。
- 不得因 `data_audit.py` 通过就写“数据已完成事实核实”；它只能检查**已录入数据与规则**的算术、单位与内部冲突。
- 不得因 `model_check.py` 通过就写“模型通过独立验证”；模型依赖关系若没有如实披露仍可能存在循环验证。
- 不得因 `figure_check.py` 通过就写“图表符合出版要求”；必须实际查看图形、中文字体、数值坐标、数据来源和 PDF/DOCX 排版。
- 报告最终状态取所有强约束中最差的一项；遇到重要未经核实事项，写阶段性成果和明确缺口，不得发布投资评级或目标价。
