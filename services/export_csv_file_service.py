# services/transaction_service.py
import csv
from typing import List
from repositories.transactions_repository import TransactionsRepository


def export_transactions_to_csv(file_path="transactions.csv"):
    """Fetch all transactions and save them as a CSV file."""
    model = TransactionsRepository()
    transactions = model.get_all()
    
    # Define the CSV header
    header = ["id", "description", "type", "category", "price", "owner", "email", "createdAt", "status"]
    
    # Convert TransactionEntity objects to lists
    rows = [
        [
            transaction.id,
            transaction.description,
            transaction.type,
            transaction.category,
            transaction.price,
            transaction.owner,
            transaction.email,
            transaction.created_at,
            transaction.status
        ]
        for transaction in transactions
    ]
    
    # Write to CSV file
    with open(file_path, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(header)  # Write the header
        writer.writerows(rows)  # Write the rows
