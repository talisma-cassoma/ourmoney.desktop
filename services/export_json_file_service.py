from repositories.transactions_repository import TransactionsRepository
from datetime import datetime
import json
import os


# Convert transactions to a JSON-compatible format and save
def export_transactions_to_json():
    model = TransactionsRepository()
    transactions = model.get_all()
    
    # Convert transactions to a list of dictionaries
    transactions_list = [
        {
            "id": transaction.id,
            "description": transaction.description,
            "type": transaction.type,
            "category": transaction.category,
            "price": transaction.price,
            "owner": transaction.owner,
            "email": transaction.email,
            "createdAt": transaction.created_at,
            "status": transaction.status,
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
