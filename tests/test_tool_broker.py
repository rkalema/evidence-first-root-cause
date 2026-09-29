import pandas as pd
from evidence_first.runtime.tool_broker import ToolExecutionBroker,ToolRequest
from evidence_first.tools.factory import dataframe_registry
from evidence_first.tools.registry import ToolRegistry,ToolSpec

def test_broker_executes_read_only_dataframe_tool():
    b=ToolExecutionBroker(dataframe_registry(pd.DataFrame({'g':['a','a'],'x':[1,3]})))
    out=b.execute(ToolRequest('dataframe.group_metric',{'group':'g','metric':'x'}))
    assert out.ok and out.value.value['a']==2.0

def test_broker_refuses_write_tool():
    r=ToolRegistry(); r.register(ToolSpec('write','x',False,lambda:1))
    out=ToolExecutionBroker(r).execute(ToolRequest('write',{}))
    assert not out.ok and 'denied' in out.error
