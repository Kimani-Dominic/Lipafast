from datetime import datetime
from pathlib import Path

LOG_FILE = Path("data/sql.log")

def log_sql(sql: str, source="REPL"):
    LOG_FILE.parent.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    LOG_FILE.write_text(
        LOG_FILE.read_text() + f"[{timestamp}] [{source}] {sql}\n"
        if LOG_FILE.exists()
        else f"[{timestamp}] [{source}] {sql}\n"
    )
