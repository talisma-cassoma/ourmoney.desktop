import logging
import requests
from db import (insert_non_synced_transaction, delete_transaction, get_unsynced_transactions, mark_as_synced, get_all_transactions)
from datetime import datetime
import json

# Configuração do logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

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
            self.transactions_list.addItem(f"{transaction['description']} - {transaction['price']} - {transaction['createdAt']}")

    def pull_data(self):
        """Baixa dados do servidor para o SQLite local e sincroniza as transações baixadas."""
        if self.is_online():
            try:
                response = requests.get(f"{self.api_url}/api/transactions/unsynced", timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    self.store_in_local_db(data)
                    self.push_downloaded_data(data)
                    self.push_local_transactions()
                    self.main_window.load_collection()
            except Exception as e:
                logging.error(f"Erro ao puxar dados: {e}")
                #print(f"Erro ao puxar dados: {e}")
        else:
            logging.info("Sem conexão. Dados não puxados.")
             #print("Sem conexão. Dados não puxados.")

    def push_downloaded_data(self, transactions):
        """Atualiza o status de 'synced' das transações baixadas no servidor."""
        for transaction in transactions:
            try:
                response = requests.patch(
                    f"{self.api_url}/api/transactions/{transaction['id']}/sync",
                    json={'synced': True},
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    logging.info(f"Transação {transaction['id']} marcada como sincronizada no servidor.")
                    #print(f"Transação {transaction['id']} marcada como sincronizada no servidor.")
                else:
                    logging.error(f"Erro ao marcar transação {transaction['id']} como sincronizada: {response.status_code}")
                    #print(f"Erro ao marcar transação {transaction['id']} como sincronizada: {response.status_code}")
            except Exception as e:
                logging.error(f"Erro ao atualizar status de sincronização no servidor para a transação {transaction['id']}: {e}")
                #print(f"Erro ao atualizar status de sincronização no servidor para a transação {transaction['id']}: {e}")

    def push_local_transactions(self):
        """Envia transações locais para o servidor, convertendo o createdAt para o formato ISO 8601 (UTC)."""
        if self.is_online():
            unsynced_transactions = get_unsynced_transactions()

            transactions_to_push = []
            for transaction in unsynced_transactions:
                created_at_str = transaction[8]
                created_at_dt = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S.%f')
                created_at_iso = created_at_dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-4] + 'Z'

                transaction_dict = {
                    "id": transaction[0],
                    "description": transaction[1],
                    "type": transaction[2],
                    "category": transaction[3],
                    "price": transaction[4],
                    "owner": transaction[5],
                    "email": transaction[6],
                    "synced": True,
                    "createdAt": created_at_iso
                }

                transactions_to_push.append(transaction_dict)

            try:
                response = requests.post(f"{self.api_url}/api/offline/transactions", json=transactions_to_push, timeout=self.timeout)
                if response.status_code == 200:
                    mark_as_synced(transactions_to_push)
                    logging.info("Dados enviados com sucesso!")
                    #print("Dados enviados com sucesso!")
                else:
                    logging.error(f"Erro ao enviar dados. Status Code: {response.status_code}")
                    #print(f"Erro ao enviar dados. Status Code: {response.status_code}")
            except Exception as e:
                logging.error(f"Erro ao enviar transações offline: {e}")
                #print(f"Erro ao enviar transações offline: {e}")
        else:
            logging.info("Sem conexão. Dados não enviados.")
            #print("Sem conexão. Dados não enviados.")

    def store_in_local_db(self, data):
        """Armazena as transações baixadas no banco de dados local."""
        for transaction in data:
            createdAt = transaction.get('createdAt')
            if createdAt is not None:
                try:
                    convertedTimeZ = datetime.strptime(createdAt[:-1], '%Y-%m-%dT%H:%M:%S.%f')
                    convertedTime = convertedTimeZ.strftime('%Y-%m-%d %H:%M:%S.%f')
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
                    logging.error(f"Erro ao analisar a data: {ve}")
                    #print(f"Erro ao analisar a data: {ve}")
                except KeyError as ke:
                    logging.error(f"Chave ausente na transação: {ke}")
                    #print(f"Chave ausente na transação: {ke}")
                except Exception as e:
                    logging.error(f"Erro ao inserir a transação: {e}")
                    #print(f"Erro ao inserir a transação: {e}")
    
    def get_total_of_income_transactons(self):
        total= 0
        transactions = get_all_transactions()
        for transaction in transactions:
            if transaction[2] == 'income':
                total+= transaction[4]
        return total
    def get_total_of_outcome_transactons(self):
        total= 0
        transactions = get_all_transactions()
        for transaction in transactions:
            if transaction[2] == 'outcome':
                total+= transaction[4]
        return total    