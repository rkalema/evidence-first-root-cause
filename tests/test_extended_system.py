import sqlite3
from evidence_first.tools.sql import ReadOnlySQLTool
from evidence_first.tools.statistics import difference,weighted_mean,slope
from evidence_first.connectors import InMemorySource

def test_read_only_sql():
    c=sqlite3.connect(':memory:'); c.execute('create table t(x integer)'); c.execute('insert into t values (1),(2)')
    assert ReadOnlySQLTool(c).query('select sum(x) from t').rows[0][0]==3
    try: ReadOnlySQLTool(c).query('delete from t'); assert False
    except ValueError: pass

def test_statistics():
    assert difference(100,80).absolute==-20
    assert weighted_mean([1,3],[1,1])==2
    assert slope([0,1,2],[0,2,4])==2

def test_connector():
    s=InMemorySource({'a.csv':b'x\\n1\\n'})
    assert s.list_sources()==('a.csv',)
