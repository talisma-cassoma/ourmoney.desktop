from entities.transactions_entity import TransactionEntity
from repositories.transactions_repository import TransactionsRepository
from utils.logger import get_logger

class ListTransactions:
    def __init__(self):
        self._transactions: list[TransactionEntity] = []
        self._repository = TransactionsRepository()  # Convenção para atributo protegido
        self._logger = get_logger("ListTransactionsOnDemande")
        
    def fetch_all(self)-> list[TransactionEntity]:
        return self._repository.get_all()
        
    def fetch(self,last_date=None,order_direction = "asc",limit = None) -> list[TransactionEntity]:
        return self._repository.fetch_somes(last_date)
    
    def  fetch_deleted(self)-> list[TransactionEntity]:
        return self._repository.get_deleted_transactions()
    
    def fetch_updated(self)-> list[TransactionEntity]:
        return self._repository.get_updated_transactions()
    
    def fetch_unsynced(self)-> list[TransactionEntity]:
        return self._repository.get_unsynced_transactions()
    
    def total(self):
        return self._repository.get_total()
    