#Data Transfer Object for Transactions (controller <-> services)
from datetime import datetime

class TransactionDTO:
    def __init__(self, id=None, description=None, type=None, category=None, price=0.0, status="unsynced", 
                 created_at= datetime.now().isoformat(timespec='milliseconds') + 'Z'):
        
        self.id = id
        self.description = description
        self.type = type
        self.category = category
        self.price = price  
        self.status = status 
        self.created_at = created_at
    
    def __repr__(self):
        return (
            f"TransactionDTO("
            f"id={self.id}, description='{self.description}', type='{self.type}', "
            f"category='{self.category}', price={self.price}, status='{self.status}',"
            f"created_at='{self.created_at}')"
        )