# repl.py
from lipafast.db.store import db
from lipafast.parser.sql_parser import SQLParser
# from .db.database import Database
from .db.sql_logger import log_sql

TYPE_MAP = {
    "INT": int,
    "STR": str,
    "FLOAT": float,
}

def read_sql():
    """
    Read multi-line SQL until a semicolon is found.
    Handles help/exit commands without requiring a semicolon.
    """
    lines = []
    while True:
        prompt = "lipafast> " if not lines else "... "
        line = input(prompt).strip()

        # Special commands
        if not lines and line.lower() in ("help", "exit", "quit"):
            return line.lower()

        if not line:
            continue

        lines.append(line)

        # Only break if the last line ends with semicolon
        if line.endswith(";"):
            break

    sql = "\n".join(lines).strip()
    # Remove trailing semicolon for parser
    if sql.endswith(";"):
        sql = sql[:-1]
    return sql



def print_rows(rows):
    if not rows:
        print("No rows")
        return

    headers = rows[0].keys()
    print(" | ".join(headers))
    print("-" * 70)
    for r in rows:
        print(" | ".join(str(r[h]) for h in headers))


def execute(parsed):
    qtype = parsed["type"]
    
    # ---------------- CREATE TABLE ----------------
    if qtype == "CREATE_TABLE":
        columns = {}
        primary_key = None
        unique_keys = []

        for col in parsed["columns"]:
            col_type = TYPE_MAP[col["type"].upper()]
            columns[col["name"]] = col_type
            if col["primary"]:
                primary_key = col["name"]
            if col["unique"]:
                unique_keys.append(col["name"])

        db.create_table(
            parsed["table_name"],
            columns,
            primary_key=primary_key,
            unique_keys=unique_keys,
        )

        return {"message": f"Table '{parsed['table_name']}' created"}

    # ---------------- INSERT ----------------
    elif qtype == "INSERT":
        table = db.t(parsed["table_name"])
        values_raw = eval(f"[{parsed['values_str']}]")
        cols = parsed["columns"] or list(table.columns.keys())
        row = {}

        for col_name, val in zip(cols, values_raw):
            col_type = table.columns[col_name]
            if not isinstance(val, col_type):
                try:
                    val = col_type(val)
                except Exception:
                    raise TypeError(
                        f"Column '{col_name}' expects type {col_type.__name__}, got {type(val).__name__}"
                    )
            row[col_name] = val

        table.insert(row)
        return {"rows_affected": 1}

    # ---------------- SELECT ----------------
    elif qtype == "SELECT":
        table = db.t(parsed["table_name"])
        return table.rows

    # ---------------- JOIN ----------------
    elif qtype == "JOIN":
        t1 = db.t(parsed["table1"])
        t2 = db.t(parsed["table2"])

        # left, right = [x.strip() for x in parsed["join_condition"].split("=")]
        condition = parsed["join_condition"]
        if "=" not in condition:
            raise ValueError("Invalid JOIN condition. Expected format: table1.col1 = table2.col2")
        
        left, right = map(str.strip, condition.split("=", 1))
        
        lcol = left.split(".", 1)[1] if "." in left else left
        rcol = right.split(".", 1)[1] if "." in right else right

        results = []
        for r1 in t1.rows:
            for r2 in t2.rows:
                if r1[lcol] == r2[rcol]:
                    results.append({**r1, **r2})

        return results

    # ---------------- UPDATE ----------------
    elif qtype == "UPDATE":
        table = db.t(parsed["table_name"])

        if not parsed["where_clause"]:
            raise ValueError("UPDATE requires WHERE clause")

        wcol, wval = [x.strip() for x in parsed["where_clause"].split("=")]
        wval = table.columns[wcol](eval(wval))

        updates = {}
        for pair in parsed["set_pairs"]:
            updates[pair["column"]] = table.columns[pair["column"]](eval(pair["value"]))

        table.update(wcol, wval, updates)
        return {"rows_affected": 1}

    # ---------------- DELETE ----------------
    elif qtype == "DELETE":
        table = db.t(parsed["table_name"])

        if not parsed["where_clause"]:
            raise ValueError("DELETE requires WHERE clause")

        col, val = [x.strip() for x in parsed["where_clause"].split("=")]
        table.delete(col, table.columns[col](eval(val)))
        return {"rows_affected": 1}
    
    elif qtype == "SHOW_TABLES":
        return list(db.tables.keys())    

    else:
        raise ValueError(f"Unsupported query type: {qtype}")
    
   


def start_repl():
    print("LipaFast SQL REPL")
    print("Type HELP for commands")
    print("-" * 50)

    while True:
        try:
            sql = read_sql()

            if sql.lower() in ("exit", "quit"):
                print("Goodbye!")
                break

            if sql.lower() == "help":
                print("""
Supported SQL commands:
  CREATE TABLE wallets (wallet_id INT PRIMARY KEY, owner STR, balance FLOAT, status STR);
  INSERT INTO wallets VALUES (6, 'Kim', 500.0, 'active');
  SELECT * FROM wallets;
  SELECT * FROM wallets JOIN ledger ON wallets.wallet_id = ledger.wallet_id;
  UPDATE wallets SET balance = 200.0 WHERE wallet_id = 3;
  DELETE FROM wallets WHERE wallet_id = 3;
  HELP
  EXIT
""")
                continue

            parsed = SQLParser.parse(sql)
            log_sql(sql, source="REPL")  # Log the executed SQL 
            # execute(parsed)
            result = execute(parsed)
            if parsed["type"] == "SHOW_TABLES":
                print("\n".join(result))
            if isinstance(result, list):
                print_rows(result)
            elif isinstance(result, dict):
                print(result)    

        except KeyboardInterrupt:
            print("\nUse EXIT to quit")
        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    start_repl()
