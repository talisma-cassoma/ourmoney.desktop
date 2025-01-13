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
        elif status == "synced":
            self._repository.mark_as_deleted(transaction_id)
        else:
            self._logger.info("transação com status inválido")
    
    def many(self, transaction_ids: list[str]):
        self._repository.delete_many( transaction_ids)

