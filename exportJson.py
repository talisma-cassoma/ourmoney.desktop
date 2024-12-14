import json
import os
from datetime import datetime
from model import Model

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
    
    # Get the current timestamp in the desired format
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"myTransactions_{timestamp}.json"
    # Check if the file already exists
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as json_file:
            json.dump(transactions_list, json_file, indent=4, ensure_ascii=False)