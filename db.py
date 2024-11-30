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

def get_total():
    db = sqlite3.connect(resource_path('database.db'))
    cur= db.cursor()

    # Query to calculate total incomes
    cur.execute("SELECT SUM(price) as total_incomes FROM Transactions WHERE type = 'income'")
    total_income = cur.fetchone()[0] or 0.0  # Default to 0.0 if no income

    # Query to calculate total outcomes
    cur.execute("SELECT SUM(price) as total_outcomes FROM Transactions WHERE type = 'outcome'")
    total_outcome = cur.fetchone()[0] or 0.0  # Default to 0.0 if no outcome

    # Close the database connection
    db.close()

    return total_income, total_outcome


def insert_one(description, type, category, price, owner, email, synced):
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


def insert_many(transactions):
    db = sqlite3.connect(resource_path('database.db'))
    query = """
    INSERT INTO Transactions (id, description, type, category, price, owner, email, synced, createdAt)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cur = db.cursor()

    successful_insertions = 0
    failed_transactions = []

    # Process the chunk
    for t in transactions:
        try:
            data = (
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
            cur.execute(query, data)
            successful_insertions += 1
        except (sqlite3.Error, KeyError, ValueError) as e:
            logging.error(f"Erro ao inserir transação: {t}. Detalhes do erro: {e}")
            failed_transactions.append(t)

    # Commit only once per chunk
    try:
        db.commit()
        logging.info(f"{successful_insertions} transações inseridas com sucesso nesta fatia!")
        if failed_transactions:
            logging.warning(f"{len(failed_transactions)} transações falharam nesta fatia e foram ignoradas.")
    except sqlite3.Error as commit_error:
        logging.error(f"Erro ao commitar a fatia: {commit_error}")
    finally:
        db.close()
        
    logging.info(f"all failed transactions: {failed_transactions}")  # failed transactions for further inspection


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
import sqlite3

def patch_transaction(transaction_id, updates):
    """
    Updates a transaction in the SQLite database with the specified ID.

    :param db_path: Path to the SQLite database.
    :param transaction_id: The ID of the transaction to update.
    :param updates: Dictionary containing column-value pairs to update.
    """
    try:
        # Connect to the database
        db = sqlite3.connect(resource_path('database.db'))
        cur= db.cursor()

        # Build the update query dynamically
        set_clause = ", ".join([f"{col} = ?" for col in updates.keys()])
        query = f"UPDATE transactions SET {set_clause} WHERE id = ?"

        # Execute the query
        cur.execute(query, (*updates.values(), transaction_id))
        
        # Commit the changes and close the connection
        db.commit()
        logging.info(f"Transaction with ID {transaction_id} has been updated successfully.")
    
    except sqlite3.Error as e:
        logging.error(f"erro ao modificar a transaction: {e}")
    
    finally:
        if db:
            db.close()

def get_all_transactions():
    db = sqlite3.connect(resource_path('database.db'))
    statement = 'SELECT id, description, type, category, price, owner, email, createdAt, synced FROM Transactions ORDER BY createdAt DESC'
    cur = db.cursor()
    transactions = cur.execute(statement).fetchall()
    db.close()

    return transactions

def fetch_transactions(last_date):
    """
    Fetch 20 transactions.
    If last_date is None, fetch the latest 20 transactions.
    Otherwise, fetch transactions older than last_date.
    """
    query = """
    SELECT id, description, type, category, price, owner, email, createdAt, synced FROM Transactions 
    WHERE createdAt < ? 
    ORDER BY createdAt DESC 
    LIMIT 20;
    """ if last_date else """
    SELECT id, description, type, category, price, owner, email, createdAt, synced FROM Transactions 
    ORDER BY createdAt DESC 
    LIMIT 20;
    """

    connection = sqlite3.connect('database.db')
    cur= connection.cursor()

    # Execute the query with or without the last_date parameter
    if last_date:
        cur.execute(query, (last_date,))
    else:
        cur.execute(query)

    transactions = cur.fetchall()
    connection.close()
  
    return transactions

def delete(trans_id):
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
