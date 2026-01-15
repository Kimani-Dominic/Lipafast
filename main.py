from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from .web.routes import router
from .parser.sql_parser import SQLParser
from .repl import execute
from .db.store import db

db = db

app = FastAPI(title="LipaFast RDBMS")
app.include_router(router)

class SQLQuery(BaseModel):
    query: str

@app.post("/sql")
def run_sql(q: SQLQuery):
    try:
        parsed = SQLParser.parse(q.query)
        result = execute(parsed)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)