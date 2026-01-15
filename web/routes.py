from pathlib import Path
from fastapi import APIRouter, Request, Form, Body
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime

from ..parser.sql_parser import SQLParser
from ..repl import execute
from ..db.sql_logger import log_sql
from ..db.store import db

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# ================= DASHBOARD =================
@router.get("/")
async def dashboard(request: Request):
    wallets = db.t("wallets").rows
    ledger = db.t("ledger").rows if "ledger" in db.tables else []

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "drivers": wallets,
            "recent_transactions": ledger[-10:],
            "total_drivers": len(wallets),
            "active_drivers": len([w for w in wallets if w["status"] == "active"]),
            "total_balance": sum(w["balance"] for w in wallets),
            "total_spent": sum(tx["amount"] for tx in ledger if tx["direction"] == "debit"),
        }
    )


# ================= CREATE =================
@router.post("/wallet/new")
async def create_wallet(
    wallet_id: int = Form(...),
    owner: str = Form(...),
    balance: float = Form(...)
):
    wallets = db.t("wallets")

    if wallets.find("wallet_id", wallet_id):
        return RedirectResponse("/?error=Wallet exists", status_code=303)

    wallets.insert({
        "wallet_id": wallet_id,
        "owner": owner,
        "balance": balance,
        "status": "active"
    })

    return RedirectResponse("/?message=Wallet created", status_code=303)


# ================= UPDATE (PUT) =================
@router.put("/wallet/edit")
async def edit_wallet(payload: dict = Body(...)):
    wallets = db.t("wallets")

    wallet = wallets.find("wallet_id", payload["wallet_id"])
    if not wallet:
        return JSONResponse({"error": "Wallet not found"}, status_code=404)
    
    if "owner" in payload and payload["owner"]:
        wallet["owner"] = payload["owner"]

    if payload.get("topup", 0) > 0:
        wallet["balance"] += payload["topup"]

    return {"message": "Wallet updated"}


# ================= DELETE =================
@router.delete("/wallet/delete")
async def delete_wallet(payload: dict = Body(...)):
    wallets = db.t("wallets")
    wallet = wallets.find("wallet_id", payload["wallet_id"])

    if not wallet:
        return JSONResponse({"error": "Wallet not found"}, status_code=404)

    wallet["status"] = "inactive"
    return {"message": "Wallet deactivated"}


# ================= PAY =================
@router.post("/wallet/pay")
async def pay_wallet(
    wallet_id: int = Form(...),
    amount: int = Form(...)
):
    wallets = db.t("wallets")
    wallet = wallets.find("wallet_id", wallet_id)

    if not wallet or wallet["status"] != "active":
        return RedirectResponse("/?error=Wallet inactive", status_code=303)

    if wallet["balance"] < amount:
        return RedirectResponse("/?error=Insufficient funds", status_code=303)

    wallet["balance"] -= amount

    db.t("ledger").insert({
        "wallet_id": wallet_id,
        "owner": wallet["owner"],
        "amount": amount,
        "direction": "debit",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    return RedirectResponse("/?message=Payment successful", status_code=303)


@router.post("/sql")
def run_sql(payload: dict = Body(...)):
    sql = payload.get("sql")

    if not sql:
        return JSONResponse(
            {"error": "SQL is required"},
            status_code=400
        )

    try:
        parsed = SQLParser.parse(sql)
        log_sql(sql, source="HTTP")
        return execute(parsed)

    except Exception as e:
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=400
        )
