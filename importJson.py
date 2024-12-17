import ijson
from model import Model


def import_transactions_to_json():

    batch_size = 1000
    transactions = []

    model = Model()

    with open('myTransactions_20241217.json', 'r') as file:
        parser = ijson.items(file, 'item')  # Parse the array of transactions

        for transaction in parser:
            transactions.append(transaction)
            if len(transactions) >= batch_size:
                model.insert_many(transactions)
                transactions = []

        # Insert any remaining transactions
        if transactions:
            model.insert_many(transactions) 

import_transactions_to_json()