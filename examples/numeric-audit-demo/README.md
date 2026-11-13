# 数据审计负例：演示如何拦截分项加总错误

此目录中的数字用于演示从待审报告中提取的加总关系，**不代表经过核实的半导体设备市场数据**。

执行：

```bash
python scripts/data_audit.py examples/numeric-audit-demo/metrics.csv --rules examples/numeric-audit-demo/audit_rules.csv --as-of 2026-11-09
```

预期结果：检查器以非零状态退出，指出已登记的九个分项实际加总为 1185，而表中写作 1165。脚本只能检验你录入的指标；如果漏掉某条数据或算式，它不会自动从正文寻找缺口。
