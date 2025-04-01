from openpyxl import Workbook
from repositories.transactions_repository import TransactionsRepository
from utils.shared.convertTimeFormat import convert_time_format
from utils.shared.convertTimeFormat import convert_to_iso8601
from datetime import datetime

def export_transactions_to_excel(file_path="transactions.xlsx"):
    """Fetch all transactions and save them as an Excel file."""
    model = TransactionsRepository()
    transactions = model.get_all()
    
    # Define the Excel header
    header = ["id", "description", "type", "category", "price", "owner", "email", "createdAt", "status"]
    
    # Create a new Excel workbook and add a worksheet
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Transactions"
    
    # Write the header to the first row
    sheet.append(header)
    
    # Write the data rows
    for transaction in transactions:
        # Extract attributes from the TransactionEntity object
        formatted_transaction = [
            transaction.id,
            transaction.description,
            transaction.type,
            transaction.category,
            transaction.price,
            transaction.owner,
            transaction.email,
            datetime.strptime(
                    convert_to_iso8601(transaction.created_at)
                    , '%Y-%m-%dT%H:%M:%S.%fZ').strftime("%d-%m-%Y"),
            transaction.status,
        ]
        
        # Format the createdAt field
        try:
            formatted_transaction[7] = convert_time_format(transaction.createdAt)
        except (ValueError, AttributeError):
            pass  # Leave the original value if formatting fails
        
        # Append the formatted transaction to the sheet
        sheet.append(formatted_transaction)
    
    # Save the workbook to the specified file path
    workbook.save(file_path)
