import sqlite3
import uuid
from datetime import datetime
import logging

import os
import sys

from convertTimeFormat import convert_to_iso8601

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

class Model:
    def __init__(self):
        self.create_table()
        
    def create_table(self):
        db = sqlite3.connect(resource_path('database.db'))
        query = """
        CREATE TABLE IF NOT EXISTS Transactions (
            "id" TEXT NOT NULL,                           -- UUID gerado pelo Prisma
            "description" TEXT NOT NULL,                 -- Descrição da transação
            "type" TEXT NOT NULL,                        -- Tipo da transação 
            "category" TEXT NOT NULL,                    -- Categoria da transação
            "price" FLOAT NOT NULL,                      -- Float para alinhar com o Prisma
            "owner" TEXT NOT NULL DEFAULT 'talisma',     -- Valor padrão do Prisma
            "email" TEXT NOT NULL DEFAULT 'talisma@email.com', -- Valor padrão do Prisma
            "status" TEXT NOT NULL DEFAULT 'unsynced',   -- Valor pode ser synced | unsyced | updated | deleted 
            "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, -- TIMESTAMP sem precisão

            CONSTRAINT "Transactions_pkey" PRIMARY KEY ("id") -- Chave primária
        )
        """
        cur = db.cursor()
        cur.execute(query)
        db.commit()  # Confirma a criação da tabela no banco de dados
        db.close()

    def get_total(seelf):
        db = sqlite3.connect(resource_path('database.db'))
        cur= db.cursor()

        # Query to calculate total incomes
        cur.execute("SELECT SUM(price) as total_incomes FROM Transactions WHERE status != 'deleted' AND type = 'income'")
        total_income = cur.fetchone()[0] or 0.0  # Default to 0.0 if no income

        # Query to calculate total outcomes
        cur.execute("SELECT SUM(price) as total_outcomes FROM Transactions WHERE status != 'deleted' AND type = 'outcome'")
        total_outcome = cur.fetchone()[0] or 0.0  # Default to 0.0 if no outcome

        # Close the database connection
        db.close()

        return total_income, total_outcome

    def insert_one(self,description, type, category, price, owner, email, status):
        db = sqlite3.connect(resource_path('database.db'))

        query = """
        INSERT INTO Transactions (id, description, type, category, price, owner, email, status, createdAt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        # Data formatada corretamente
        createdAt = datetime.now().isoformat(timespec='milliseconds') + 'Z' # padrão ISO 8601 para datas

        cur = db.cursor()
        cur.execute(query, (str(uuid.uuid4()), description, type, category, price, owner, email, status, createdAt))
        db.commit()
        db.close()
        logging.info('Transação adicionada com sucesso!')

    def insert_many(self,transactions):
        db = sqlite3.connect(resource_path('database.db'))
        query = """
        INSERT INTO Transactions (id, description, type, category, price, owner, email, status, createdAt)
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
                    str(t['description']).strip().lower(),
                    t['type'],
                    str(t['category']).strip().lower(),
                    float(t['price']),  # Ensure price is a float
                    t.get('owner', 'talisma'),  # Default owner
                    t.get('email', 'talisma@email.com'),  # Default email
                    t['status'],  
                    convert_to_iso8601(t['createdAt']) #
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

    def insert_non_synced_transaction(self,id, description, type, category, price, createdAt, status, owner='talisma', email='talisma@email.com'):
        db = sqlite3.connect(resource_path('database.db'))
        cur = db.cursor()

        # Verifica se o id já existe no banco de dados
        cur.execute("SELECT COUNT(1) FROM Transactions WHERE id = ?", (id,))
        exists = cur.fetchone()[0]

        if exists:
            logging.warning(f'Transação com id {id} já existe no banco de dados.')
            return  # Sai da função sem inserir

        # Verifica se createdAt é None e define a data atual se necessário
        if createdAt is None:
            #createdAt = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            createdAt = datetime.now().isoformat(timespec='milliseconds') + 'Z'  #padrão ISO 8601 para datas

        # Consulta de inserção
        query = """
        INSERT INTO Transactions (id, description, type, category, price, owner, email, status, createdAt)
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
                status,            # Status de sincronização
                createdAt          # Data de criação
            ))
            db.commit()  # Confirma a transação no banco de dados
            logging.info(f'Transação com id {id} inserida com sucesso.')

        except sqlite3.Error as e:
            logging.error(f'Erro ao inserir transação: {e}')

        db.close()
        logging.info('Transação adicionada com sucesso!')

    def get_all_transactions(self):
        db = sqlite3.connect(resource_path('database.db'))
        statement = 'SELECT id, description, type, category, price, owner, email, createdAt, status FROM Transactions ORDER BY createdAt DESC'
        cur = db.cursor()
        transactions = cur.execute(statement).fetchall()
        db.close()

        return transactions

    def fetch_transactions(self,last_date):
        """
        Fetch 20 transactions.
        If last_date is None, fetch the latest 20 transactions.
        Otherwise, fetch transactions older than last_date.
        """
        query = """
        SELECT id, description, type, category, price, owner, email, createdAt, status 
        FROM Transactions 
        WHERE status != 'deleted' AND createdAt < ? 
        ORDER BY createdAt DESC 
        LIMIT 20;
        """ if last_date else """
        SELECT id, description, type, category, price, owner, email, createdAt, status 
        FROM Transactions 
        WHERE status != 'deleted' 
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

    def get_deleted_transactions():
        query = """
        SELECT id, description, type, category, price, owner, email, createdAt, status 
        FROM Transactions 
        WHERE status == 'deleted'
        """

        connection = sqlite3.connect('database.db')
        cur= connection.cursor()
        cur.execute(query)

        transactions = cur.fetchall()
        connection.close()
    
        return transactions
    
    def get_updated_transactions():
        query = """
        SELECT id, description, type, category, price, owner, email, createdAt, status 
        FROM Transactions 
        WHERE status == 'updated'
        ORDER BY createdAt DESC 
        """

        connection = sqlite3.connect('database.db')
        cur= connection.cursor()
        cur.execute(query)

        transactions = cur.fetchall()
        connection.close()
    
        return transactions

    def delete(self,transaction_id):
        db = sqlite3.connect(resource_path('database.db'))
        cur = db.cursor()
        # Execute a query
        query = "SELECT * FROM transactions WHERE id = ?"
        cur.execute(query, (transaction_id,))
        transaction = cur.fetchone()
        db.commit()
        db.close()

        if not transaction:
          logging.info(f'Transação com id {transaction_id} nao foi encontrada!')
          return 
        
        status = transaction[7] # status is the 7º position 

        if status == "unsynced":
            self._delete_transaction_from_db(transaction_id)
        elif status == "synced":
            self._mark_transaction_as_deleted(transaction_id)
        else:
             logging.info(f"transaçao com status invalido")
    
    def _delete_transaction_from_db(self, transaction_id):
        db = sqlite3.connect(resource_path('database.db'))
        query = "DELETE FROM Transactions WHERE id = ?"
        db.execute(query, (transaction_id,))
        db.commit()
        db.close()
        logging.info(f'Transação com id {transaction_id} deletada com sucesso!')

    def _mark_transaction_as_deleted(self, transaction_id):
        db = sqlite3.connect(resource_path('database.db'))
        query = "UPDATE transactions SET status = ? WHERE id = ?"
        db.execute(query, ("deleted", transaction_id))
        db.commit()
        db.close()
        logging.info(f'Transação com id {transaction_id} updeleted com sucesso!')

    def get_unsynced_transactions(self):
        db = sqlite3.connect(resource_path('database.db'))
        query = """
        SELECT id, description, type, category, price, owner, email, createdAt, status 
        FROM Transactions 
        WHERE status == 'unsynced' OR status == 'deleted' OR status == 'updated'
        """
        cur = db.cursor()
        unsynced_transactions = cur.execute(query).fetchall()
        db.close()
        return unsynced_transactions

    def mark_as_synced(self,transactions):
        db = sqlite3.connect(resource_path('database.db'))
        cur = db.cursor()

        for transaction in transactions:
            query = "UPDATE Transactions SET status = 'synced' WHERE id = ?"
            cur.execute(query, (transaction['id'],))  # Marcar cada transação como sincronizada
            logging.info(f'Transação {transaction["id"]} marcada como sincronizada.')

        db.commit()
        db.close()

    def update_many(self, transactions):
        """
        Atualiza múltiplas transações no banco de dados local.
        """
        db = sqlite3.connect(resource_path('database.db'))
        cur = db.cursor()
        try:
            for transaction in transactions:
                query = "UPDATE transactions SET "
                fields = []
                values = []

                # Construir query dinâmica com base nos campos do dicionário
                for key, value in transaction.items():
                    if key != "id":  # 'id' é usado como identificador para WHERE
                        fields.append(f"{key} = ?")
                        values.append(value)

                # Adicionar cláusula WHERE para identificar a transação
                query += ", ".join(fields) + " WHERE id = ?"
                values.append(transaction["id"])

                # Executando a query para cada transação
                cur.execute(query, values)

            # Commit no banco de dados após atualizar todas as transações
            db.commit()
            db.close()
            logging.info(f'{len(transactions)} transações atualizadas com sucesso!')
        except KeyError:
            logging.error("O campo 'id' é obrigatório para atualizar uma transação.")
        except Exception as e:
            logging.error(f"Erro ao atualizar transações: {e}")

    def delete_many(self, transaction_ids):
        """
        Deleta múltiplas transações no banco de dados local.
        """
        db = sqlite3.connect(resource_path('database.db'))
        cur = db.cursor()
        try:
            # Construir a query para deletar múltiplos registros
            query = "DELETE FROM transactions WHERE id IN ({})".format(
                ",".join(["?" for _ in transaction_ids])
            )
            # Executando a query para deletar as transações
            cur.execute(query, transaction_ids)
            db.commit()
            db.close()
            logging.info(f'{len(transaction_ids)} transações deletadas com sucesso!')
        except Exception as e:
            logging.error(f"Erro ao deletar transações: {e}")


    def update(self, transaction):
        """
        Atualiza uma transação no banco de dados local.
        """
        db = sqlite3.connect(resource_path('database.db'))
        cur = db.cursor()
        try:
            query = "UPDATE transactions SET "
            fields = []
            values = []

            # Construir query dinâmica com base nos campos do dicionário
            for key, value in transaction.items():
                if key != "id":  # 'id' é usado como identificador para WHERE
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            # Adicionar cláusula WHERE para identificar a transação
            query += ", ".join(fields) + " WHERE id = ?"
            values.append(transaction["id"])

            # Executando a query
            cur.execute(query, values)
            db.commit()
            db.close()
            logging.info(f'Transação com id {transaction["id"]} atualizada com sucesso!')
            
            logging.info(f"Transação {transaction['id']} atualizada com sucesso no banco de dados.")
        except KeyError:
            logging.error("O campo 'id' é obrigatório para atualizar uma transação.")
        except Exception as e:
            logging.error(f"Erro ao atualizar transação {transaction.get('id', 'desconhecida')}: {e}")

