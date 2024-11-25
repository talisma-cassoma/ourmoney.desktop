import ijson
from controller import Controller

batch_size = 1000
transactions = []

controller = Controller()

with open('response.json', 'r') as file:
    parser = ijson.items(file, 'item')  # Parse the array of transactions

    for transaction in parser:
        transactions.append(transaction)
        if len(transactions) >= batch_size:
            controller.insert_many(transactions)
            transactions = []

    # Insert any remaining transactions
    if transactions:
        controller.insert_many(transactions)
