from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import pandas as pd

@dataclass(frozen=True)
class AnalysisResult:
    operation:str
    value:Any
    metadata:dict[str,Any]

class DataFrameTool:
    """Read-only deterministic tabular analysis primitives."""
    def __init__(self, frame:pd.DataFrame):
        self.frame=frame.copy(deep=True)

    def profile(self)->AnalysisResult:
        f=self.frame
        value={
            "rows":int(len(f)),
            "columns":list(map(str,f.columns)),
            "missing_by_column":{str(k):int(v) for k,v in f.isna().sum().items()},
            "duplicate_rows":int(f.duplicated().sum()),
        }
        return AnalysisResult("profile",value,{})

    def group_metric(self,group:str,metric:str,agg:str="mean")->AnalysisResult:
        if agg not in {"mean","sum","median","count","min","max"}: raise ValueError("unsupported aggregation")
        if group not in self.frame or metric not in self.frame: raise KeyError("missing column")
        s=getattr(self.frame.groupby(group,dropna=False)[metric],agg)()
        value={str(k):(float(v) if hasattr(v,"item") else v) for k,v in s.items()}
        return AnalysisResult("group_metric",value,{"group":group,"metric":metric,"agg":agg})

    def correlation(self,x:str,y:str)->AnalysisResult:
        if x not in self.frame or y not in self.frame: raise KeyError("missing column")
        value=float(self.frame[[x,y]].corr().iloc[0,1])
        return AnalysisResult("correlation",value,{"x":x,"y":y})

    def before_after(self,time_col:str,metric:str,cutoff:Any)->AnalysisResult:
        f=self.frame
        before=f.loc[f[time_col] < cutoff,metric]
        after=f.loc[f[time_col] >= cutoff,metric]
        value={"before_mean":float(before.mean()),"after_mean":float(after.mean()),
               "before_n":int(before.notna().sum()),"after_n":int(after.notna().sum())}
        return AnalysisResult("before_after",value,{"time_col":time_col,"metric":metric,"cutoff":str(cutoff)})
