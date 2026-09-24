import pandas as pd
from evidence_first.tools.dataframe import DataFrameTool

df=pd.DataFrame({
    "depot":["A","A","B","B"],
    "labor_hours":[100,85,100,100],
    "sla":[91,64,92,86],
})
tool=DataFrameTool(df)
print(tool.profile())
print(tool.correlation("labor_hours","sla"))
