import logging
import requests
import json

from utils.shared.convertTimeFormat import convert_to_iso8601
from datetime import datetime
from dto.transaction_dto import TransactionDTO
from services.list_transaction_service import ListTransactions
from services.delete_transation_service import DeleteTransactionService
from services.update_transaction_service import UpdateTransactionService
from services.insert_transaction_service import InsertTransactionService
from services.export_json_file_service import export_transactions_to_json
from services.export_csv_file_service import export_transactions_to_csv
from services.export_xlsx_file_service import export_transactions_to_excel


# Configuração do logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')


class Controller:
    def __init__(self, main_window=None):
        self.main_window = main_window
        self._transactions = ListTransactions()
        self._delete = DeleteTransactionService()
        self._update = UpdateTransactionService()
        self._insert = InsertTransactionService()

        self.api_url = "https://our-money-bkd.onrender.com"
        #self.api_url = "http://localhost:3000"
        self.timeout = 10

    def is_online(self):
        """Checa se a máquina está conectada ao servidor."""
        try:
            response = requests.get(f"{self.api_url}/api/ping", timeout=self.timeout)
            if response.status_code == 200:
                return True
        except (requests.ConnectionError, requests.Timeout):
            return False

    def fetch_transactions(self, last_date=None):
        
        if last_date:
            date=str(last_date)
            format = "%d-%m-%Y"
            last_date = datetime.strptime(date, format).strftime("%Y-%m-%d") # convert %Y-%m-%d in to search

        transactions = self._transactions.fetch(last_date=last_date)
        dtos = [
            TransactionDTO(
                id=transaction.id,
                description=transaction.description,
                type=transaction.type,
                category=transaction.category,
                price=f"{transaction.price:.2f} DH$",  # Converter para formato seguro
                status= "synced" if transaction.status == "synced" else "unsynced",
                created_at=datetime.strptime(
                    convert_to_iso8601(transaction.created_at)
                    , '%Y-%m-%dT%H:%M:%S.%fZ').strftime("%d-%m-%Y")
            )
            for transaction in transactions
        ]
        return dtos
    
    def insert_transaction(self, description, 
                            type, category, price, 
                            status='unsynced'):
        # Criar o DTO
        transaction_dto = TransactionDTO(
                description=description,
                type=type,
                category=category,
                price=float(price),
                status=status
            )
        
        self._insert.one(transaction_dto)

    def delete_transaction(self, transaction_id):
        self._delete.one(transaction_id)

    def edit_transaction(self, id:str, description:str, type_input:str, category:str, price:float, status: str, date:str)->None:
        
        # Check if the input is a string
        if isinstance(date, str):
            try:
                # Attempt to parse the string in %d-%m-%Y format
                dt = datetime.strptime(date, "%d-%m-%Y")
            except ValueError:
                try:
                    # Attempt to parse the string in %Y-%m-%d format
                    dt = datetime.strptime(date, "%Y-%m-%d")
                except ValueError:
                    # Raise an error if neither format matches
                    logging.error("The date string must be in %d-%m-%Y or %Y-%m-%d format.")

            date = str(dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))[:-4] + "Z"
           
            # Criar o DTO
            transaction_dto = TransactionDTO(
                id=id,
                description=description,
                type= type_input,
                category=category,
                price=price,
                status= status,
                created_at= date
            )
            self._update.one(transaction_dto)
        else:
            raise ValueError("Input must be a string or a date instance.")

    def get_total_of_transactions(self):
         total_income, total_outcome = self._transactions.total()
         return total_income, total_outcome
    
    def insert_many(self, transactions):
         self._insert.many(transactions)

    def synchronize_data(self):
         """Baixa dados do servidor para o SQLite local e sincroniza as transações baixadas."""
         if not self.is_online():
             logging.info("Sem conexão. Dados não puxados.")
             return None
           
         try:
             response = requests.get(f"{self.api_url}/api/transactions/unsynced", timeout=self.timeout)
             if response.status_code == 200:
                 data = response.json()
                 self.store_in_local_db(data)
                 self.push_local_transactions()
                 return data
             else:
                 logging.error(f"Erro na resposta do servidor: {response.status_code}")
                 return None
         except Exception as e:
             logging.error(f"Erro ao puxar dados: {e}")
             return None

    def upadate_status(self, transactions):
        """Atualiza o status de 'synced' das transações baixadas no servidor."""
        for transaction in transactions:
            try:
                response = requests.patch(
                    f"{self.api_url}/api/transactions/{transaction['id']}",
                    json={'status': 'synced'},
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    logging.info(f"Transação {transaction['id']} marcada como sincronizada no servidor.")
                else:
                    logging.error(f"Erro ao marcar transação {transaction['id']} como sincronizada: {response.status_code}")
            except Exception as e:
                logging.error(f"Erro ao atualizar status de sincronização no servidor para a transação {transaction['id']}: {e}")

    def push_local_transactions(self):
        """Envia transações locais para o servidor, convertendo o createdAt para o formato ISO 8601 (UTC)."""
        if self.is_online():
            unsynced_transactions = self._transactions.fetch_unsynced()

            transactions_to_push = []
            deleted_transactions_ids = []  # To store transactions with status 'deleted'
            updated_transactions_dto:list[TransactionDTO] = [] 
            
            try:
                for transaction in unsynced_transactions:
                    if transaction.status == 'deleted':
                        deleted_transactions_ids.append(transaction.id)
                    if transaction.status == 'updated':
                        updated_transactions_dto.append(TransactionDTO(
                            id=transaction.id,
                            description=transaction.description,
                            type=transaction.type,
                            category=transaction.category,
                            price=transaction.price,
                            status="synced",
                            created_at=transaction.created_at  
                        ))

                    transaction_dict = {
                        "id": transaction.id,
                        "description": transaction.description,
                        "type": transaction.type,
                        "category": transaction.category,
                        "price": transaction.price,
                        "owner": transaction.owner,
                        "email": transaction.email,
                        "status": "synced" if transaction.status== "unsynced" else transaction.status,
                        "createdAt": transaction.created_at
                    }
                    transactions_to_push.append(transaction_dict)
            except Exception as e:
                logging.error(f"erros ao pegar Dados: {e}")
            try:
                # Sending transactions in chunks
                chunk_size = 100  # Define your chunk size
                for i in range(0, len(transactions_to_push), chunk_size):
                    chunk = transactions_to_push[i:i + chunk_size]

                    try:
                        response = requests.post(f"{self.api_url}/api/offline/transactions", json=chunk, timeout=self.timeout)
                        if response.status_code == 200:
                            self._update.mark_as_synced(chunk)  # Mark only the successfully sent chunk as synced
                            logging.info(f"{len(chunk)} transações enviadas com sucesso!")
                        else:
                            logging.error(f"Erro ao enviar dados. Status Code: {response.status_code}")
                    except Exception as e:
                        logging.error(f"Erro ao enviar transações offline: {e}")
            except:
                logging.error("erros ao enviar Dados ao server.")
            self._update.many(updated_transactions_dto)
            self._delete.many(deleted_transactions_ids)
        else:
            logging.info("Sem conexão. Dados não enviados.")
   
    def store_in_local_db(self, data):
        """Armazena as transações baixadas no banco de dados local."""
        for transaction in data:
            created_at = transaction.get('created_at')
            if created_at is not None:
                try: 
                    convertedTime = convert_to_iso8601(created_at)
                    # Criar o DTO
                    transactions_dto = [
                        TransactionDTO(
                        id= transaction['id'],
                        description=str(transaction['description']).strip().lower(),
                        category=str(transaction['category']).strip().lower(),
                        type=transaction['type'],
                        price=float(transaction['price']),
                        created_at=convertedTime,
                        status='synced'
                        )
                    for transaction in transactions_dto
                    ]
                    self._insert.many(transactions_dto)

                except ValueError as ve:
                    logging.error(f"Erro ao analisar a data: {ve}")
                except KeyError as ke:
                    logging.error(f"Chave ausente na transação: {ke}")
                except Exception as e:
                    logging.error(f"Erro ao inserir a transação: {e}")
                    
    def export_file(self, index):
        # index 0 for json 
        # index 1 for csv
        # index 2 for xlsx
        if index == 0:
            try:
                export_transactions_to_json()
                logging.info("status: success, Transactions saved successfully.")
            except Exception as e:
                logging.error(f"status: error:{ str(e)}")
        if index == 1:
            try:
                export_transactions_to_csv()
                logging.info("status: success, Transactions exported to CSV successfully.")
            except Exception as e:
                logging.error(f"status: error:{ str(e)}")
        if index == 2:
            try:
                export_transactions_to_excel()
                logging.info("status: success, Transactions exported to excel successfully.")
            except Exception as e:
                logging.error(f"status: error:{ str(e)}")
     