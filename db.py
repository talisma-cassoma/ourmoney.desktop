
import sqlite3
import uuid

import datetime

def create_table():
    db = sqlite3.connect('database.db')
    query = """
    CREATE TABLE IF NOT EXISTS Transactions (
        id TEXT PRIMARY KEY,
        description TEXT NOT NULL,
        type TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        owner TEXT NOT NULL,
        email TEXT NOT NULL,
        createdAt DATETIME default current_timestamp
    )
    """
    cur = db.cursor()
    cur.execute(query)
    db.close()


create_table()


def insert_transaction(description, type, category, price, owner='talisma', email='talisma@email.com'):
    

    db = sqlite3.connect('database.db')
    query = """
    INSERT INTO Transactions (id, description, type, category, price, owner, email, createdAt)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    cur = db.cursor()
    cur.execute(query, (str(uuid.uuid4()), description, type, category, price, owner, email, datetime.datetime.now()))
    db.commit()
    db.close()
    print('Transaction added successfully!')

def get_all_transactions():
    db = sqlite3.connect('database.db')
    statement = 'SELECT id, description, type, category, price, owner, email, createdAt FROM Transactions'
    cur = db.cursor()
    transactions = cur.execute(statement).fetchall()
    db.close()
    return transactions

def delete_transaction(trans_id):
    db = sqlite3.connect('database.db')
    query = "DELETE FROM Transactions WHERE id = ?"
    db.execute(query, (trans_id,))
    db.commit()
    db.close()
    print(f'Transação com id {trans_id} deletada com sucesso!')

def update_transaction(trans_id, description=None, trans_type=None, category=None, price=None, owner=None, email=None):
    db = sqlite3.connect('database.db')
    cur = db.cursor()

    # Construir a query de update dinamicamente com base nos parâmetros fornecidos
    fields_to_update = []
    values = []

    if description:
        fields_to_update.append("description = ?")
        values.append(description)

    if trans_type:
        fields_to_update.append("type = ?")
        values.append(trans_type)

    if category:
        fields_to_update.append("category = ?")
        values.append(category)

    if price:
        fields_to_update.append("price = ?")
        values.append(price)

    if owner:
        fields_to_update.append("owner = ?")
        values.append(owner)

    if email:
        fields_to_update.append("email = ?")
        values.append(email)

    # Adicionando o ID da transação para a condição do WHERE
    values.append(trans_id)

    # Construindo a query final
    query = f"UPDATE Transactions SET {', '.join(fields_to_update)} WHERE id = ?"

    # Executando a query
    cur.execute(query, values)
    db.commit()
    db.close()

    print(f'Transação com id {trans_id} atualizada com sucesso!')
