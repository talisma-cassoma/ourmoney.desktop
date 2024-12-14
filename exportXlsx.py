from openpyxl import Workbook
from model import Model
from datetime import datetime


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
            created_at = datetime.strptime(formatted_transaction[7], "%Y-%m-%d %H:%M:%S.%f")
            formatted_transaction[7] = created_at.strftime("%d-%m-%Y")  # Format as day-month-year
        except (ValueError, IndexError):
            pass  # Leave the original value if formatting fails
        
        sheet.append(formatted_transaction)
    
    # Save the workbook to the specified file path
    workbook.save(file_path)
