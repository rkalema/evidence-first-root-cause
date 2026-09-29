from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SQLResult:
    columns: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...]
    truncated: bool = False


class ReadOnlySQLTool:
    _blocked = re.compile(
        r"\b(insert|update|delete|drop|alter|create|replace|attach|detach|vacuum|pragma)\b",
        re.IGNORECASE,
    )

    """Execute bounded read-only SQLite queries.

    Safety does not rely on SQL string matching. SQLite's authorizer rejects
    every operation except reads/selects/functions/recursive CTE evaluation.
    """

    _ALLOWED_ACTIONS = {
        sqlite3.SQLITE_SELECT,
        sqlite3.SQLITE_READ,
        sqlite3.SQLITE_FUNCTION,
        getattr(sqlite3, "SQLITE_RECURSIVE", -1),
    }

    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        max_rows: int = 10_000,
        progress_steps: int = 1_000,
    ):
        if max_rows < 1:
            raise ValueError("max_rows must be positive")
        if progress_steps < 1:
            raise ValueError("progress_steps must be positive")
        self.connection = connection
        self.max_rows = max_rows
        self.progress_steps = progress_steps

    @staticmethod
    def _authorizer(action, arg1, arg2, db_name, trigger_name):
        return (
            sqlite3.SQLITE_OK
            if action in ReadOnlySQLTool._ALLOWED_ACTIONS
            else sqlite3.SQLITE_DENY
        )

    def query(self, sql: str, params: tuple[Any, ...] = ()) -> SQLResult:
        statement = sql.strip()
        if not statement:
            raise ValueError("SQL cannot be empty")
        if self._blocked.search(statement):
            raise ValueError("only read-only SQL queries are allowed")

        budget = {"ticks": 0}

        def progress() -> int:
            budget["ticks"] += 1
            return 1 if budget["ticks"] > self.progress_steps else 0

        self.connection.set_authorizer(self._authorizer)
        self.connection.set_progress_handler(progress, 1000)
        try:
            try:
                cursor = self.connection.execute(statement, params)
                columns = tuple(d[0] for d in cursor.description or ())
                rows = tuple(cursor.fetchmany(self.max_rows + 1))
            except sqlite3.DatabaseError as exc:
                message = str(exc).lower()
                if "not authorized" in message or "authorization denied" in message:
                    raise ValueError("only read-only SQL queries are allowed") from exc
                if "interrupted" in message:
                    raise ValueError("SQL query exceeded execution budget") from exc
                raise

            if not columns:
                raise ValueError("query did not produce a read-only result set")

            truncated = len(rows) > self.max_rows
            if truncated:
                rows = rows[: self.max_rows]
            return SQLResult(columns, rows, truncated)
        finally:
            self.connection.set_progress_handler(None, 0)
            self.connection.set_authorizer(None)
