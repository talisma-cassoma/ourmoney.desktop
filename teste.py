from services.insert_transaction_service import InsertTransactionService
from dto.transaction_dto import TransactionDTO

# Criar o DTO
model = InsertTransactionService()
transaction_dto = TransactionDTO(
                description="testes teste john teste",
                type="income teste",
                price=float(10),
                category="teste",
                status="unsynced"
            )
        
model.one(transaction_dto)