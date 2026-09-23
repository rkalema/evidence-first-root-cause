from __future__ import annotations
import re, sqlite3
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class SQLResult:
    columns: tuple[str,...]
    rows: tuple[tuple[Any,...],...]

class ReadOnlySQLTool:
    _blocked=re.compile(r'\\b(insert|update|delete|drop|alter|create|replace|attach|detach|vacuum|pragma)\\b',re.I)
    def __init__(self,connection:sqlite3.Connection): self.connection=connection
    def query(self,sql:str,params:tuple[Any,...]=())->SQLResult:
        s=sql.strip()
        if not s.lower().startswith(('select','with')) or self._blocked.search(s): raise ValueError('only read-only SELECT/CTE queries are allowed')
        cur=self.connection.execute(s,params)
        return SQLResult(tuple(d[0] for d in cur.description or ()),tuple(cur.fetchall()))
