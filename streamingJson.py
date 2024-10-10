import ijson
from db import insert_many_transactions

batch_size = 1000
transactions = []

with open('transactions2.json', 'r') as file:
    parser = ijson.items(file, 'item')  # Parse the array of transactions

    for transaction in parser:
        transactions.append(transaction)
        if len(transactions) >= batch_size:
            insert_many_transactions(transactions)
            transactions = []

    # Insert any remaining transactions
    if transactions:
        insert_many_transactions(transactions)
