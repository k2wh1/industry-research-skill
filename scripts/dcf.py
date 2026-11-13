#!/usr/bin/env python3
"""Deterministic, offline FCFF DCF calculator for documented hypothetical/verified inputs.

No financial-data access. Discount convention is year-end, FCFF discounted by WACC.
Amount units for FCFF, net debt, and equity adjustments must match; shares use
that same scaling (e.g., millions -> currency per share).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def require_number(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number, not {type(value).__name__}.")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")
    return value


def compute_dcf(fcff: list[float], wacc: float, growth: float,
                net_debt: float, shares: float, adjustments: float = 0.0) -> dict[str, Any]:
    """Calculate FCFF DCF using year-end discounting and a Gordon terminal value.

    other equity adjustments must already be signed appropriately: positive adds
    to equity value, negative subtracts. Preventing double counting is the user's
    responsibility and must be explained in the research model.
    """
    if not isinstance(fcff, list) or not fcff:
        raise ValueError("forecast_fcff must be a non-empty list.")
    cash_flows = [require_number(f"forecast_fcff[{i}]", v) for i, v in enumerate(fcff)]
    wacc = require_number("wacc", wacc)
    growth = require_number("terminal_growth", growth)
    net_debt = require_number("net_debt", net_debt)
    shares = require_number("diluted_shares", shares)
    adjustments = require_number("other_equity_adjustments", adjustments)
    if wacc <= 0:
        raise ValueError("wacc must be positive.")
    if growth <= -1:
        raise ValueError("terminal_growth must be greater than -100%.")
    if wacc <= growth:
        raise ValueError("wacc must exceed terminal_growth for a Gordon terminal value.")
    if shares <= 0:
        raise ValueError("diluted_shares must be positive.")

    discounted = [v / (1 + wacc) ** (i + 1) for i, v in enumerate(cash_flows)]
    pv_explicit = math.fsum(discounted)
    terminal_fcff = cash_flows[-1] * (1 + growth)
    terminal_value = terminal_fcff / (wacc - growth)
    pv_terminal = terminal_value / (1 + wacc) ** len(cash_flows)
    enterprise_value = pv_explicit + pv_terminal
    equity_value = enterprise_value - net_debt + adjustments
    per_share = equity_value / shares
    return {
        "pv_forecast_fcff": pv_explicit,
        "pv_terminal_value": pv_terminal,
        "terminal_value_undiscounted": terminal_value,
        "enterprise_value": enterprise_value,
        "net_debt": net_debt,
        "other_equity_adjustments": adjustments,
        "equity_value": equity_value,
        "per_share_value": per_share,
        "pv_terminal_share_of_ev": (pv_terminal / enterprise_value if enterprise_value else None),
        "discounted_fcff": discounted,
    }


def calculate_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object.")
    if payload.get("discount_timing", "year_end") != "year_end":
        raise ValueError("Only year_end discount_timing is supported.")
    fcff = payload.get("forecast_fcff")
    wacc = require_number("wacc", payload.get("wacc"))
    growth = require_number("terminal_growth", payload.get("terminal_growth"))
    debt = require_number("net_debt", payload.get("net_debt"))
    shares = require_number("diluted_shares", payload.get("diluted_shares"))
    adj = require_number("other_equity_adjustments", payload.get("other_equity_adjustments", 0))
    main = compute_dcf(fcff, wacc, growth, debt, shares, adj)
    sensitivity = payload.get("sensitivity", {})
    if not isinstance(sensitivity, dict):
        raise ValueError("sensitivity must be an object if present.")
    wacc_delta = sensitivity.get("wacc_delta", [-0.01, 0, 0.01])
    growth_delta = sensitivity.get("growth_delta", [-0.005, 0, 0.005])
    if (not isinstance(wacc_delta, list) or not isinstance(growth_delta, list)
            or len(wacc_delta) > 20 or len(growth_delta) > 20):
        raise ValueError("sensitivity delta arrays must be lists of up to 20 numbers.")
    matrix: list[dict[str, Any]] = []
    for wi in wacc_delta:
        test_wacc = wacc + require_number("sensitivity.wacc_delta", wi)
        row = {"wacc": test_wacc, "values": []}
        for gi in growth_delta:
            test_growth = growth + require_number("sensitivity.growth_delta", gi)
            if test_wacc <= max(0, test_growth) or test_growth <= -1:
                row["values"].append({"terminal_growth": test_growth, "per_share_value": None,
                                      "error": "Invalid discount rate or terminal growth combination"})
                continue
            test = compute_dcf(fcff, test_wacc, test_growth, debt, shares, adj)
            row["values"].append({"terminal_growth": test_growth, "per_share_value": test["per_share_value"]})
        matrix.append(row)
    return {
        "company": payload.get("company", "unspecified"),
        "currency": payload.get("currency", "unspecified"),
        "amount_unit": payload.get("amount_unit", "unspecified"),
        "method": "FCFF DCF, year-end discounting, Gordon terminal value",
        "assumptions": {
            "forecast_fcff": fcff,
            "wacc": wacc,
            "terminal_growth": growth,
            "net_debt": debt,
            "other_equity_adjustments": adj,
            "diluted_shares": shares,
            "discount_timing": "year_end",
        },
        "result": main,
        "sensitivity": {"growth_rates": [growth + require_number("sensitivity.growth_delta", g) for g in growth_delta],
                        "rows": matrix},
        "limitations": [
            "The input values are user-supplied and not independently verified.",
            "All forecast FCFF, net debt, equity adjustments, and shares must use consistent scaling.",
            "Net debt must include the relevant liabilities; other equity adjustments must address minority interest/non-operating assets without double counting.",
            "DCF is a valuation scenario, not a prediction of realized market returns.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON input containing annual FCFF, WACC, g, net debt, diluted shares")
    parser.add_argument("--out", type=Path, help="Optional output JSON path")
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8-sig"))
        result = calculate_from_payload(payload)
        content = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(content + "\n", encoding="utf-8")
            print(f"Saved result: {args.out}")
        print(f"Enterprise value: {result['result']['enterprise_value']:.4f} ({result['amount_unit']} {result['currency']})")
        print(f"Equity value: {result['result']['equity_value']:.4f} ({result['amount_unit']} {result['currency']})")
        print(f"Per-share value: {result['result']['per_share_value']:.4f} ({result['currency']}/share)")
        pct = result["result"]["pv_terminal_share_of_ev"]
        print(f"PV terminal / enterprise value: {pct:.1%}" if pct is not None else "PV terminal / enterprise value: undefined")
        return 0
    except (OSError, ValueError, TypeError, json.JSONDecodeError, OverflowError, ZeroDivisionError) as exc:
        parser.exit(2, f"DCF input error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
