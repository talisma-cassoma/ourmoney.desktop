from entities.transactions_entity import TransactionEntity
from repositories.transactions_repository import TransactionsRepository
from utils.logger import get_logger
from dto.transaction_dto import TransactionDTO

class UpdateTransactionService:
    def __init__(self):
        self._repository = TransactionsRepository()  # Convenção para atributo protegido
        self._logger = get_logger("UpadateTransactionService")

    def one(self, transaction_dto:TransactionDTO):

        transaction = TransactionEntity(
            description=transaction_dto.description,
            type=transaction_dto.type,
            category=transaction_dto.category,
            price=transaction_dto.price,
            created_at= transaction_dto.created_at,
            status=transaction_dto.status
        )
        self._repository.update_one(transaction)
    
    def many(self, transactions_dto: list[TransactionDTO]):
       
        transactions_entity = [
            TransactionEntity(
                id=transaction_dto.id,
                description=transaction_dto.description,
                type=transaction_dto.type,
                category=transaction_dto.category,
                price=transaction_dto.price,  # Converter para formato seguro
                created_at= transaction_dto.created_at,
                status= transaction_dto.status 
            )
            for transaction_dto in transactions_dto
        ]
        self._repository.update_many(transactions_entity)
    
    def mark_as_synced(self,transactions):
        self._repository.mark_as_synced(transactions)
    
    def mark_as_deleted(self, transactions_ids: str):
        
        self._repository.mark_as_deleted(transactions_ids)
    