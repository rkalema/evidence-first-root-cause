from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import math
import pandas as pd
from pandas.api.types import is_numeric_dtype


@dataclass(frozen=True)
class AnalysisResult:
    operation: str
    value: Any
    metadata: dict[str, Any]


class DataFrameTool:
    """Read-only deterministic tabular analysis primitives."""

    def __init__(self, frame: pd.DataFrame):
        self.frame = frame.copy(deep=True)

    def profile(self) -> AnalysisResult:
        frame = self.frame
        value = {
            "rows": int(len(frame)),
            "columns": list(map(str, frame.columns)),
            "missing_by_column": {
                str(k): int(v) for k, v in frame.isna().sum().items()
            },
            "duplicate_rows": int(frame.duplicated().sum()),
        }
        return AnalysisResult("profile", value, {})

    def _require_numeric(self, column: str) -> None:
        if column not in self.frame:
            raise KeyError(column)
        if not is_numeric_dtype(self.frame[column]):
            raise ValueError(f"column {column!r} is not numeric")

    def group_metric(
        self,
        group: str,
        metric: str,
        agg: str = "mean",
    ) -> AnalysisResult:
        if agg not in {"mean", "sum", "median", "count", "min", "max"}:
            raise ValueError("unsupported aggregation")
        if group not in self.frame or metric not in self.frame:
            raise KeyError("missing column")
        if agg != "count":
            self._require_numeric(metric)

        series = getattr(
            self.frame.groupby(group, dropna=False)[metric],
            agg,
        )()
        value: dict[str, Any] = {}
        for key, raw in series.items():
            label = "<MISSING>" if pd.isna(key) else str(key)
            if label in value:
                label = f"<LITERAL:{label}>"
            if hasattr(raw, "item"):
                raw = raw.item()
            value[label] = raw
        return AnalysisResult(
            "group_metric",
            value,
            {"group": group, "metric": metric, "agg": agg},
        )

    def correlation(self, x: str, y: str) -> AnalysisResult:
        self._require_numeric(x)
        self._require_numeric(y)
        value = float(self.frame[[x, y]].corr().iloc[0, 1])
        if not math.isfinite(value):
            return AnalysisResult(
                "correlation",
                None,
                {
                    "x": x,
                    "y": y,
                    "defined": False,
                    "reason": "correlation undefined because variance or usable pairs are insufficient",
                },
            )
        return AnalysisResult(
            "correlation",
            value,
            {"x": x, "y": y, "defined": True},
        )

    def before_after(
        self,
        time_col: str,
        metric: str,
        cutoff: Any,
    ) -> AnalysisResult:
        if time_col not in self.frame:
            raise KeyError(time_col)
        self._require_numeric(metric)
        frame = self.frame
        before = frame.loc[frame[time_col] < cutoff, metric]
        after = frame.loc[frame[time_col] >= cutoff, metric]
        if before.empty or after.empty:
            raise ValueError("before/after comparison requires observations on both sides")
        value = {
            "before_mean": float(before.mean()),
            "after_mean": float(after.mean()),
            "before_n": int(before.notna().sum()),
            "after_n": int(after.notna().sum()),
        }
        return AnalysisResult(
            "before_after",
            value,
            {"time_col": time_col, "metric": metric, "cutoff": str(cutoff)},
        )
