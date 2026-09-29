from __future__ import annotations
import sqlite3
import pandas as pd
from .dataframe import DataFrameTool
from .registry import ToolRegistry,ToolSpec
from .sql import ReadOnlySQLTool

def dataframe_registry(frame:pd.DataFrame)->ToolRegistry:
    tool=DataFrameTool(frame); r=ToolRegistry()
    r.register(ToolSpec('dataframe.profile','Profile rows, columns, missingness, and duplicates.',True,lambda:tool.profile()))
    r.register(ToolSpec('dataframe.group_metric','Aggregate a metric by group.',True,tool.group_metric))
    r.register(ToolSpec('dataframe.correlation','Compute Pearson correlation for two numeric columns.',True,tool.correlation))
    r.register(ToolSpec('dataframe.before_after','Compare metric means before and after a cutoff.',True,tool.before_after))
    return r

def sql_registry(connection:sqlite3.Connection)->ToolRegistry:
    tool=ReadOnlySQLTool(connection); r=ToolRegistry()
    r.register(ToolSpec('sql.query','Execute a read-only SELECT or CTE query.',True,tool.query))
    return r
