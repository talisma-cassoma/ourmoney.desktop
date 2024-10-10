import sqlite3
import uuid
from datetime import datetime
import logging

import os
import sys

from convertTimeFormat import convert_time_format

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS2
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# Configuração do logging
logging.basicConfig(
    filename=resource_path('app.log'),          # Nome do arquivo de log
    filemode='a',                # Modo de abertura (a: anexar)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Formato das mensagens
    level=logging.INFO            # Nível de log padrão
)

def create_table():
    db = sqlite3.connect(resource_path('database.db'))
    query = """
    CREATE TABLE IF NOT EXISTS Transactions (
        id TEXT PRIMARY KEY,          -- Mantenha TEXT se o ID for uma string (UUID ou similar)
        description TEXT NOT NULL,
        type TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        owner TEXT NOT NULL DEFAULT 'talisma',  -- Definido um valor padrão
        email TEXT NOT NULL DEFAULT 'talisma@email.com',  -- Definido um valor padrão
        synced BOOLEAN NOT NULL CHECK (synced IN (0, 1)),  -- Assegura que synced seja 0 ou 1
        createdAt DATETIME default current_timestamp
    )
    """
    cur = db.cursor()
    cur.execute(query)
    db.commit()  # Confirma a criação da tabela no banco de dados
    db.close()

create_table()

def insert_transaction(description, type, category, price, owner='talisma', email='talisma@email.com', synced=False):
    logging.info({resource_path('database.db')})
    db = sqlite3.connect(resource_path('database.db'))
    
    query = """
    INSERT INTO Transactions (id, description, type, category, price, owner, email, synced, createdAt)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    # Data formatada corretamente
    createdAt = datetime.now()
    
    cur = db.cursor()
    cur.execute(query, (str(uuid.uuid4()), description, type, category, price, owner, email, synced, createdAt))
    db.commit()
    db.close()
    # print('Transaction added successfully!')
    logging.info('Transação adicionada com sucesso!')


def insert_many_transactions(transactions):
    db = sqlite3.connect(resource_path('database.db'))
    query = """
    INSERT INTO Transactions (id, description, type, category, price, owner, email, synced, createdAt)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cur = db.cursor()

    # Parse transactions and format them correctly
    data = [
        (
            t.get('id', str(uuid.uuid4())),  # Use the id from the JSON or generate a new one if not available
            t['description'],
            t['type'],
            t['category'],
            float(t['price']),  # Ensure price is a float
            t.get('owner', 'talisma'),  # Default owner
            t.get('email', 'talisma@email.com'),  # Default email
            1 if t['synced'] else 0,  # Convert boolean to 1/0 for the database
            convert_time_format(t['createdAt'])  # Convert time correctly
        )
        for t in transactions
    ]

    try:
        cur.executemany(query, data)
        db.commit()
        logging.info(f'{len(transactions)} transações inseridas com sucesso!')
    except sqlite3.Error as e:
        logging.error(f'Erro ao inserir transações em lote: {e}')
    finally:
        db.close()


def insert_non_synced_transaction(id, description, type, category, price, createdAt, synced, owner='talisma', email='talisma@email.com'):
    db = sqlite3.connect(resource_path('database.db'))
    cur = db.cursor()

    # Verifica se o id já existe no banco de dados
    cur.execute("SELECT COUNT(1) FROM Transactions WHERE id = ?", (id,))
    exists = cur.fetchone()[0]

    if exists:
        # print(f"Transação com id {id} já existe no banco de dados.")
        logging.warning(f'Transação com id {id} já existe no banco de dados.')
        return  # Sai da função sem inserir

    # Verifica se createdAt é None e define a data atual se necessário
    if createdAt is None:
        createdAt = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    # Consulta de inserção
    query = """
    INSERT INTO Transactions (id, description, type, category, price, owner, email, synced, createdAt)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    try:
        cur.execute(query, (
            id,                # ID da transação
            description,       # Descrição da transação
            type,              # Tipo da transação (Entrada/Saída)
            category,          # Categoria da transação
            price,             # Valor da transação
            owner,             # Proprietário (padrão 'talisma')
            email,             # Email do proprietário (padrão 'talisma@email.com')
            synced,            # Status de sincronização
            createdAt          # Data de criação
        ))
        db.commit()  # Confirma a transação no banco de dados
        # print(f"Transação com id {id} inserida com sucesso.")
        logging.info(f'Transação com id {id} inserida com sucesso.')
    
    except sqlite3.Error as e:
        # print(f"Erro ao inserir transação: {e}")
        logging.error(f'Erro ao inserir transação: {e}')

    db.close()
    # print('Transaction added successfully!')
    logging.info('Transação adicionada com sucesso!')

def get_all_transactions():
    db = sqlite3.connect(resource_path('database.db'))
    statement = 'SELECT id, description, type, category, price, owner, email, createdAt, synced FROM Transactions ORDER BY createdAt DESC'
    cur = db.cursor()
    transactions = cur.execute(statement).fetchall()
    db.close()

    return transactions

def delete_transaction(trans_id):
    db = sqlite3.connect(resource_path('database.db'))
    query = "DELETE FROM Transactions WHERE id = ?"
    db.execute(query, (trans_id,))
    db.commit()
    db.close()
    # print(f'Transação com id {trans_id} deletada com sucesso!')
    logging.info(f'Transação com id {trans_id} deletada com sucesso!')

def get_unsynced_transactions():
    db = sqlite3.connect(resource_path('database.db'))
    query = 'SELECT * FROM Transactions WHERE synced = 0'  # 0 para false
    cur = db.cursor()
    unsynced_transactions = cur.execute(query).fetchall()
    db.close()
    return unsynced_transactions

def mark_as_synced(transactions):
    db = sqlite3.connect(resource_path('database.db'))
    cur = db.cursor()
    
    for transaction in transactions:
        query = 'UPDATE Transactions SET synced = 1 WHERE id = ?'
        cur.execute(query, (transaction['id'],))  # Marcar cada transação como sincronizada
        logging.info(f'Transação {transaction["id"]} marcada como sincronizada.')

    db.commit()
    db.close()

def update_transaction(trans_id, description=None, trans_type=None, category=None, price=None, owner=None, email=None):
    db = sqlite3.connect(resource_path('database.db'))
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

    # print(f'Transação com id {trans_id} atualizada com sucesso!')
    logging.info(f'Transação com id {trans_id} atualizada com sucesso!')
