import json
from model import Model
from convertTimeFormat import convert_time_format


# Convert transactions to a JSON-compatible format and save
def export_transactions_to_json():
    model = Model()
    transactions = model.get_all_transactions()
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
    with open("myTransactions123.json", "w", encoding="utf-8") as json_file:
        json.dump(transactions_list, json_file, indent=4, ensure_ascii=False)



