from fastmcp import FastMCP
import os
import sqlite3
from typing import Annotated
import datetime
from pydantic import Field

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP(name="Expense Tracker")

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT DEFAULT '',
            note TEXT DEFAULT ''
            )"""
        )

init_db()

@mcp.tool
def add_expense(
    date: Annotated[datetime.date, Field(..., description="date of expense, refer IST for logging, YYYY-MM-DD")],
    amount: Annotated[float, Field(...,ge=0, description="Amount in rupees")],
    category: Annotated[str, Field(..., description="Top-level category, refer categories resource")],
    subcategory: Annotated[str, Field(..., description="Subcategory, refer categories resource")],
    note: Annotated[str, Field(description="Exact note text describing the expense")] = ""):

    '''Add a new expense entry in the database as per IST'''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
            (date, amount, category, subcategory, note))

        return {"status": "ok", "id": cur.lastrowid}


@mcp.tool
def list_expenses(
    start_date: Annotated[datetime.date, Field(..., description="start date, YYYY-MM-DD")],
    end_date: Annotated[datetime.date, Field(..., description="end date, YYYY-MM-DD")]):

    '''list all the expenses from the database'''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses WHERE date BETWEEN ? and ? ORDER BY id ASC
            """,
            (start_date, end_date))

        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


@mcp.tool
def delete_expense(
    id: Annotated[int | None, Field(description="Expense id from list_expenses")] = None,
    date: Annotated[datetime.date | None, Field(description="Expense date, YYYY-MM-DD")] = None,
    amount: Annotated[float | None, Field(ge=0, description="Amount in rupees")] = None,
    category: Annotated[str | None, Field(description="Top-level category, refer categories resource")] = None,
    subcategory: Annotated[str | None, Field(description="Subcategory, refer categories resource")] = None,
    note: Annotated[str | None, Field(description="Exact note text")] = None):

    '''Remove expense entries matching the given fields.'''
    filters = {"date": date, "amount": amount, "category": category, "subcategory": subcategory, "note": note}
    active = {k: v for k, v in filters.items() if v is not None}

    if id is not None and active:
        return {"status": "error", "message": "Pass either id or other filters, not both."}

    with sqlite3.connect(DB_PATH) as c:
        if id is not None:
            cur = c.execute("DELETE FROM expenses WHERE id = ?", (id,))
            if cur.rowcount == 0:
                return {"status": "not_found", "message": f"No entry with id {id}"}
            return {"status": "success", "message": f"Deleted entry id {id}"}

        if not active:
            return {"status": "error", "message": "No filters given. Ask the user to clarify which entry to delete."}

        where = " AND ".join(f"{k} = ?" for k in active)
        cur = c.execute(f"DELETE FROM expenses WHERE {where}", list(active.values()))
        n = cur.rowcount
        if n == 0:
            return {"status": "not_found", "message": "No matching expense found"}
        return {"status": "success", "message": f"Deleted {n} expense entr{'y' if n == 1 else 'ies'}"}

@mcp.tool
def update_expense(
    id: Annotated[int, Field(description="Expense id from list_expenses")],
    date: Annotated[datetime.date | None, Field(description="New date, YYYY-MM-DD")] = None,
    amount: Annotated[float | None, Field(ge=0, description="New amount in rupees")] = None,
    category: Annotated[str | None, Field(description="New top-level category, refer categories resource")] = None,
    subcategory: Annotated[str | None, Field(description="New subcategory, refer categories resource")] = None,
    note: Annotated[str | None, Field(description="New note text")] = None,
) -> dict:
    '''Update one expense entry by id. Only the fields passed are changed.'''
    changes = {
        "date": date.isoformat() if date is not None else None,
        "amount": amount,
        "category": category,
        "subcategory": subcategory,
        "note": note,
    }
    changes = {col: val for col, val in changes.items() if val is not None}

    if not changes:
        return {"status": "error",
                "message": "No fields to update. Pass at least one field to change."}

    # Column names come from the fixed dict above, never from user input,
    # so building the SET clause this way is safe.
    assignments = ", ".join(f"{col} = ?" for col in changes)
    params = [*changes.values(), id]

    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(f"UPDATE expenses SET {assignments} WHERE id = ?", params)
        if cur.rowcount == 0:
            return {"status": "not_found", "message": f"No entry with id {id}"}

    return {"status": "success",
            "message": f"Updated entry id {id}: {', '.join(changes)}"}

@mcp.tool
def summarize(
    start_date: Annotated[datetime.date, Field(..., description="start date, YYYY-MM-DD")],
    end_date: Annotated[datetime.date, Field(..., description="start date, YYYY-MM-DD")],
    category: Annotated[str | None, Field(description="top-level category to summarize, refer categories resource")] = None):
    '''summarize expenses by category within an inclusive date range'''
    with sqlite3.connect(DB_PATH) as c:
        query = (
            """
            SELECT category, SUM(amount) AS total_amount
            FROM expenses WHERE date BETWEEN ? and ?
            """
        )
        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " GROUP BY category ORDER BY category ASC"

        cur = c.execute(query, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.resource("expense://categories", mime_type="applications/json")
def categories():
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
