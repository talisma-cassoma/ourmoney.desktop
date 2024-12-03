# services/transaction_service.py
import csv
from model import Model


def export_transactions_to_csv(file_path="transactions.csv"):
    """Fetch all transactions and save them as a CSV file."""
    model= Model()
    transactions = model.get_all_transactions()
    
    # Define the CSV header
    header = ["id", "description", "type", "category", "price", "owner", "email", "createdAt", "synced"]
    
    # Write to CSV file
    with open(file_path, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(header)  # Write the header
        writer.writerows(transactions)  # Write the rows
