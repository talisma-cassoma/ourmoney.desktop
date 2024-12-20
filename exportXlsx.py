from openpyxl import Workbook
from model import Model
from datetime import datetime
from convertTimeFormat import convert_time_format


def export_transactions_to_excel(file_path="transactions.xlsx"):
    """Fetch all transactions and save them as an Excel file."""
    model = Model()
    transactions = model.get_all_transactions()
    
    # Define the Excel header
    header = ["id", "description", "type", "category", "price", "owner", "email", "createdAt", "synced"]
    
    # Create a new Excel workbook and add a worksheet
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Transactions"
    
    # Write the header to the first row
    sheet.append(header)
    
    # Format createdAt and write the data rows
    for transaction in transactions:
        formatted_transaction = list(transaction)  # Convert tuple to list if needed
        # Format the createdAt field
        try:
            formatted_transaction[7] = convert_time_format(formatted_transaction[7])           
        except (ValueError, IndexError):
            pass  # Leave the original value if formatting fails
        
        sheet.append(formatted_transaction)
    
    # Save the workbook to the specified file path
    workbook.save(file_path)
