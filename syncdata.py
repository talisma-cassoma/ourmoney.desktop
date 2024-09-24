import requests
from db import (insert_non_synced_transaction, delete_transaction, get_unsynced_transactions, mark_as_synced)
from datetime import datetime

class SyncManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.api_url = "https://our-money-bkd.onrender.com"
        self.timeout = 10

    def is_online(self):
        """Checa se a máquina está conectada ao servidor."""
        try:
            response = requests.get(f"{self.api_url}/api/ping", timeout=self.timeout)
            if response.status_code == 200:
                return True
        except (requests.ConnectionError, requests.Timeout):
            return False

    def refresh_transaction_view(self):
        """Atualiza a exibição das transações na GUI."""
        self.transactions_list.clear()  # Limpa a lista atual
        transactions = self.get_all_transactions()  # Método para obter todas as transações do DB
        for transaction in transactions:
            # Adicione cada transação à lista na GUI
            self.transactions_list.addItem(f"{transaction['description']} - {transaction['price']} - {transaction['createdAt']}")

    def pull_data(self):
        """Baixa dados do servidor para o SQLite local."""
        if self.is_online():
            try:
                response = requests.get(f"{self.api_url}/api/transactions/unsynced", timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    self.store_in_local_db(data)
                    self.main_window.load_collection()  # Atualiza a GUI com as novas transações
            except Exception as e:
                print(f"Erro ao puxar dados: {e}")
        else:
            print("Sem conexão. Dados não puxados.")

    def push_data(self):
        """Envia transações locais para o servidor."""
        if self.is_online():
            unsynced_transactions = get_unsynced_transactions()
            try:
                response = requests.post(f"{self.api_url}/transactions", json=unsynced_transactions, timeout=self.timeout)
                if response.status_code == 200:
                    mark_as_synced(unsynced_transactions)
                    print("Dados enviados com sucesso!")
            except Exception as e:
                print(f"Erro ao enviar dados: {e}")
        else:
            print("Sem conexão. Dados não enviados.")

    def store_in_local_db(self, data):
        for transaction in data:
            createdAt = transaction.get('createdAt')
        
            if createdAt is not None:
                try:
                    # Conversão do formato da data
                    convertedTimeZ = datetime.strptime(createdAt[:-1], '%Y-%m-%dT%H:%M:%S.%f')
                    convertedTime = convertedTimeZ.strftime('%Y-%m-%d %H:%M:%S.%f')

                    # Inserção no banco de dados
                    insert_non_synced_transaction(
                        transaction['id'],
                        transaction['description'],
                        transaction['type'],
                        transaction['category'],
                        transaction['price'],
                        convertedTime,  
                        synced=True
                    )
                except ValueError as ve:
                    print(f"Erro ao analisar a data: {ve}")
                except KeyError as ke:
                    print(f"Chave ausente na transação: {ke}")
                except Exception as e:
                    print(f"Erro ao inserir a transação: {e}")
   