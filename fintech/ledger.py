from datetime import datetime

def debit_wallet(db, wallet, amount):
    if wallet["status"] != "active":
        raise ValueError("Wallet inactive")

    if wallet["balance"] < amount:
        raise ValueError("Insufficient funds")

    wallet["balance"] -= amount

    db.t("ledger").insert({
        "wallet_id": wallet["wallet_id"],
        "owner": wallet["owner"],
        "amount": amount,
        "direction": "debit",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
