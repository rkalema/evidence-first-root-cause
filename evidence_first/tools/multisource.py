from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .dataframe import DataFrameTool
from .registry import ToolRegistry, ToolSpec


@dataclass(frozen=True)
class MultiSourceDataFrames:
    frames: dict[str, pd.DataFrame]

    def _tool(self, source_id: str) -> DataFrameTool:
        if source_id not in self.frames:
            raise KeyError(f"unknown tabular source: {source_id}")
        return DataFrameTool(self.frames[source_id])

    def profile(self, source_id: str):
        return self._tool(source_id).profile()

    def group_metric(self, source_id: str, group: str, metric: str, agg: str = "mean"):
        return self._tool(source_id).group_metric(group, metric, agg)

    def correlation(self, source_id: str, x: str, y: str):
        return self._tool(source_id).correlation(x, y)

    def before_after(self, source_id: str, time_col: str, metric: str, cutoff):
        return self._tool(source_id).before_after(time_col, metric, cutoff)


def multisource_dataframe_registry(
    frames: dict[str, pd.DataFrame],
) -> ToolRegistry:
    tools = MultiSourceDataFrames(frames)
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            "dataframe.profile",
            "Profile a named tabular source.",
            True,
            tools.profile,
        )
    )
    registry.register(
        ToolSpec(
            "dataframe.group_metric",
            "Aggregate a metric by group within a named tabular source.",
            True,
            tools.group_metric,
        )
    )
    registry.register(
        ToolSpec(
            "dataframe.correlation",
            "Compute correlation within a named tabular source.",
            True,
            tools.correlation,
        )
    )
    registry.register(
        ToolSpec(
            "dataframe.before_after",
            "Compare a metric before and after a cutoff within a named tabular source.",
            True,
            tools.before_after,
        )
    )
    return registry
