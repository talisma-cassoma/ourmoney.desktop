
import json
from db import get_all_transactions 

# Convert transactions to a JSON-compatible format and save
def save_transactions_to_json():
    transactions = get_all_transactions()
    transactions_list = [
        {
            "id": transaction[0],
            "description": transaction[1],
            "type": transaction[2],
            "category": transaction[3],
            "price": transaction[4],
            "owner": transaction[5],
            "email": transaction[6],
            "createdAt": transaction[7],
            "synced": transaction[8]
        }
        for transaction in transactions
    ]
    with open("myTransactions.json", "w", encoding="utf-8") as json_file:
        json.dump(transactions_list, json_file, indent=4, ensure_ascii=False)


