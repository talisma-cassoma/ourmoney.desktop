from repositories.transactions_repository import TransactionsRepository
from utils.logger import get_logger

class DeleteTransactionService:
    def __init__(self):
        self._repository = TransactionsRepository()  # Convenção para atributo protegido
        self._logger = get_logger("DeleteTransactionsRepository")

    def one(self, transaction_id: str):
        status = self._repository.check_status(transaction_id)
        if status == "unsynced":
            self._repository.delete_transaction_from_db(transaction_id)
        else:
            "for synced or updated status "
            self._repository.mark_as_deleted(transaction_id)

    
    def many(self, transaction_ids: list[str]):
        self._repository.delete_many( transaction_ids)

