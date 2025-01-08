import sqlite3
import logging
import uuid
from datetime import datetime
from utils.logger import get_logger
from utils.helppers import resource_path
from entities.transactions_entity import TransactionEntity



class TransactionsRepository:
    def __init__(self):
        self._db_path = resource_path('database/database.db')
        self.logger = get_logger("TransactionsRepository")
        self.create_table()

    def _connect(self):
        return sqlite3.connect(self._db_path)

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS Transactions (
            id TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            owner TEXT NOT NULL DEFAULT 'talisma',
            email TEXT NOT NULL DEFAULT 'talisma@email.com',
            status TEXT NOT NULL DEFAULT 'unsynced',
            createdAt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
        with self._connect() as conn:
            conn.execute(query)

#insert methods
    def insert_one(self, transaction: TransactionEntity):
        query = """
        INSERT INTO Transactions (id, description, type, category, price, owner, email, status, createdAt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        createdAt = datetime.now().isoformat(timespec='milliseconds') + 'Z' # padrão ISO 8601 para datas
        with self._connect() as conn:
            try:


                # Solução 1: Fechando a string em cada linha
                print(f"description: {transaction.description}, "
                      f"type: {transaction.type}, "
                      f"category: {transaction.category}, "
                      f"price: {transaction.price}, "
                      f"createdAt: {transaction.created_at}, "
                      f"status: {transaction.status}")

                conn.execute(query, (
                    str(uuid.uuid4()),
                    transaction.description,
                    transaction.type,
                    transaction.category,
                    transaction.price,
                    transaction.owner,
                    transaction.email,
                    transaction.status,
                    createdAt 
                ))
                self.logger.info(f"Transaction with ID {transaction.id} inserted successfully!")
            except sqlite3.Error as e:
                self.logger.error(f"Error inserting transaction: {e}")

    def insert_many(self, transactions: list[TransactionEntity]):
        query = """
        INSERT INTO Transactions (id, description, type, category, price, owner, email, status, createdAt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        successful_insertions = 0
        failed_transactions = []

        with self._connect() as conn:
            cur = conn.cursor()
            for transaction in transactions:
                try:
                    cur.execute(query, (
                        transaction.id,
                        transaction.description,
                        transaction.type,
                        transaction.category,
                        transaction.price,
                        transaction.owner,
                        transaction.email,
                        transaction.status,
                        transaction.created_at
                    ))
                    successful_insertions += 1
                except sqlite3.Error as e:
                    self.logger.error(f"Error inserting transaction: {transaction}. Details: {e}")
                    failed_transactions.append(transaction)

            conn.commit()
            self.logger.info(f"{successful_insertions} transactions inserted successfully.")
            if failed_transactions:
                self.logger.warning(f"{len(failed_transactions)} transactions failed and were ignored.")

    def insert_non_synced(self, transaction: TransactionEntity):
        query = """
        INSERT INTO Transactions (id, description, type, category, price, owner, email, status, createdAt)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'unsynced', ?)
        """
        with self._connect() as conn:
            try:
                conn.execute(query, (
                    transaction.id,
                    transaction.description,
                    transaction.type,
                    transaction.category,
                    transaction.price,
                    transaction.owner,
                    transaction.email,
                    transaction.created_at
                ))
                self.logger.info(f"Non-synced transaction with ID {transaction.id} inserted successfully!")
            except sqlite3.Error as e:
                self.logger.error(f"Error inserting non-synced transaction: {e}")

#fetch methods
    def fetch_somes(self, last_date) -> list[TransactionEntity]:
        query = """
        SELECT id, description, type, category, price, owner, email, status, createdAt
        FROM Transactions 
        WHERE status != 'deleted' AND createdAt < ? 
        ORDER BY createdAt DESC 
        LIMIT 20
        """ if last_date else """
        SELECT id, description, type, category, price, owner, email, status, createdAt
        FROM Transactions 
        WHERE status != 'deleted' 
        ORDER BY createdAt DESC 
        LIMIT 20
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(query, (last_date,) if last_date else ())
            transactions = cur.fetchall()

        return [TransactionEntity(*t) for t in transactions]
        
    def get_all(self) -> list[TransactionEntity]:
        query = 'SELECT id, description, type, category, price, owner, email, status, createdAt FROM Transactions ORDER BY createdAt DESC'
        with self._connect() as conn:
            cur = conn.cursor()
            transactions = cur.execute(query).fetchall()
            return [TransactionEntity(*t) for t in transactions]
    
    def get_deleted_transactions(self) -> list[TransactionEntity]:
        query = """
        SELECT id, description, type, category, price, owner, email, status, createdAt
        FROM Transactions 
        WHERE status == 'deleted'
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(query)
            transactions = cur.fetchall()

        return [TransactionEntity(*t) for t in transactions]
    
    def get_updated_transactions(self) -> list[TransactionEntity]:
        query = """
        SELECT id, description, type, category, price, owner, email, status, createdAt 
        FROM Transactions 
        WHERE status == 'updated'
        ORDER BY createdAt DESC 
        """

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(query)
            transactions = cur.fetchall()

        return [TransactionEntity(*t) for t in transactions]

    def get_unsynced_transactions(self) -> list[TransactionEntity]:
        query = """
        SELECT id, description, type, category, price, owner, email, status, createdAt
        FROM Transactions 
        WHERE status == 'unsynced' OR status == 'deleted' OR status == 'updated'
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(query)
            transactions = cur.fetchall()

        return [TransactionEntity(*t) for t in transactions]

    def get_total(self):
        with self._connect() as conn:
            cur = conn.cursor()

            # Query to calculate total incomes
            cur.execute("SELECT SUM(price) as total_incomes FROM Transactions WHERE status != 'deleted' AND type = 'income'")
            total_income = cur.fetchone()[0] or 0.0  # Default to 0.0 if no income

            # Query to calculate total outcomes
            cur.execute("SELECT SUM(price) as total_outcomes FROM Transactions WHERE status != 'deleted' AND type = 'outcome'")
            total_outcome = cur.fetchone()[0] or 0.0  # Default to 0.0 if no outcome

            return total_income, total_outcome

#delete methods
    def delete_many(self, transaction_ids: list[str]):
        """
        Deleta múltiplas transações no banco de dados local.
        """
        with self._connect() as conn:
            cur = conn.cursor()
            try:
                # Construir a query para deletar múltiplos registros
                query = "DELETE FROM transactions WHERE id IN ({})".format(
                ",".join(["?" for _ in transaction_ids])
                )
                # Executando a query para deletar as transações
                cur.execute(query, transaction_ids)
                logging.info(f'{len(transaction_ids)} transações deletadas com sucesso!')
            except Exception as e:
                logging.error(f"Erro ao deletar transações: {e}")

    def check_status(self,transaction_id: str):
        with self._connect() as conn:
            cur = conn.cursor()
            # Execute a query
            query = "SELECT * FROM transactions WHERE id = ?"
            cur.execute(query, (transaction_id,))
            transaction = cur.fetchone()
            if not transaction:
                logging.info(f'Transação com id {transaction_id} nao foi encontrada!')
                return 
            return transaction[7] # status is the 7º position 
      
    def delete_transaction_from_db(self, transaction_id: str):
        with self._connect() as conn:
            cur = conn.cursor()
            query = "DELETE FROM Transactions WHERE id = ?"
            cur.execute(query, (transaction_id,))
            logging.info(f'Transação com id {transaction_id} deletada com sucesso!')

    def mark_as_deleted(self, transaction_id: str):
        with self._connect() as conn:
            cur = conn.cursor()
            query = "UPDATE transactions SET status = ? WHERE id = ?"
            cur.execute(query, ("deleted", transaction_id))
            logging.info(f'Transação com id {transaction_id} updeleted com sucesso!')

#update methods 
    def update_many(self, transactions: list[TransactionEntity]):
        query = """
        UPDATE Transactions SET 
        description = ?, type = ?, category = ?, price = ?, owner = ?, email = ?, status = ?, createdAt = ?
        WHERE id = ?
        """
        with self._connect() as conn:
            cur = conn.cursor()
            for transaction in transactions:
                try:
                    cur.execute(query, (
                        transaction.description,
                        transaction.type,
                        transaction.category,
                        transaction.price,
                        transaction.owner,
                        transaction.email,
                        transaction.status,
                        transaction.created_at,
                        transaction.id
                    ))
                except sqlite3.Error as e:
                    self.logger.error(f"Error updating transaction ID {transaction.id}: {e}")
            conn.commit()

        self.logger.info(f"Updated {len(transactions)} transactions successfully.")

    def update_one(self, transaction: TransactionEntity):
        query = """
        UPDATE Transactions SET 
        description = ?, type = ?, category = ?, price = ?, owner = ?, email = ?, status = ?, createdAt = ?
        WHERE id = ?
        """
        with self._connect() as conn:
            try:
                conn.execute(query, (
                    transaction.description,
                    transaction.type,
                    transaction.category,
                    transaction.price,
                    transaction.owner,
                    transaction.email,
                    transaction.status,
                    transaction.created_at,
                    transaction.id
                ))
                self.logger.info(f"Transaction with ID {transaction.id} updated successfully!")
            except sqlite3.Error as e:
                self.logger.error(f"Error updating transaction: {e}")

    def mark_as_synced(self,transactions):
      with self._connect() as conn:
            cur = conn.cursor()
            
            for transaction in transactions:
                query = "UPDATE Transactions SET status = 'synced' WHERE id = ?"
                cur.execute(query, (transaction['id'],))  # Marcar cada transação como sincronizada
                logging.info(f'Transação {transaction['id']} marcada como sincronizada.')