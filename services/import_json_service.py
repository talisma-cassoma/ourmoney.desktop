import ijson
from entities.transactions_entity import TransactionEntity
from repositories.transactions_repository import TransactionsRepository


def import_transactions_to_json():

    batch_size = 1000
    transactions: list[TransactionEntity] = []

    model = TransactionsRepository()

    with open('myTransactions_20250113.json', 'r') as file:
        parser = ijson.items(file, 'item')  # Parse the array of transactions

        for transaction in parser:
            transaction = TransactionEntity(
                id=transaction["id"],
                description=transaction["description"],
                type=transaction["type"],
                category=transaction["category"],
                price=float(transaction["price"]),
                owner=transaction["owner"],
                email=transaction["email"],
                created_at=transaction["createdAt"],
                status=transaction["status"],
            )
            transactions.append(transaction)
            if len(transactions) >= batch_size:
                model.insert_many(transactions)
                transactions = []

        # Insert any remaining transactions
        if transactions:
            model.insert_many(transactions) 

