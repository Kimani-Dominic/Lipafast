from .database import Database

db = Database("data/db.json")

db.create_table(
    "wallets",
    columns= {
        "wallet_id": int, 
        "owner": str,
        # "phone": str,
        "balance": float,
        "status": str
        },
    primary_key="wallet_id",
)

db.create_table(
    "ledger",
    columns= {
        "transaction_id": int,
        "wallet_id": int,
        "owner": str,
        "amount": float,
        "direction": str,
        "timestamp": str
        },
    primary_key="transaction_id",
)
