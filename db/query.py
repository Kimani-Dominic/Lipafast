# def join(wallets, ledger):
#     results = []

#     wallet_index = {
#         w["wallet_id"]: w for w in wallets.rows
#     }

#     for tx in ledger.rows:
#         w = wallet_index.get(tx["wallet_id"])
#         if not w:
#             continue

#         results.append({
#             "transaction_id": tx.get("transaction_id"),
#             "wallet_id": tx["wallet_id"],
#             "owner": w["owner"],
#             "amount": tx["amount"],
#             "direction": tx["direction"],
#             "timestamp": tx["timestamp"],
#         })

#     return results
