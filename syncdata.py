import requests
from db import (insert_non_synced_transaction, delete_transaction, get_unsynced_transactions, mark_as_synced)
from datetime import datetime
import json

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
        """Baixa dados do servidor para o SQLite local e sincroniza as transações baixadas."""
        if self.is_online():
            try:
                # Baixa as transações não sincronizadas
                response = requests.get(f"{self.api_url}/api/transactions/unsynced", timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()

                    # Salva no banco de dados local
                    self.store_in_local_db(data)


                    # Após puxar os dados, sincroniza no servidor
                    self.push_downloaded_data(data)

                    # Envia as transações offline para o servidor
                    self.push_local_transactions()

                    # Atualiza a GUI com as novas transações
                    self.main_window.load_collection()
                    
            except Exception as e:
                print(f"Erro ao puxar dados: {e}")
        else:
            print("Sem conexão. Dados não puxados.")

    def push_downloaded_data(self, transactions):
        """Atualiza o status de 'synced' das transações baixadas no servidor."""
        for transaction in transactions:
            try:
                response = requests.patch(
                    f"{self.api_url}/api/transactions/{transaction['id']}/sync",
                    json={'synced': True},  # Atualiza para synced=True
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    print(f"Transação {transaction['id']} marcada como sincronizada no servidor.")
                else:
                    print(f"Erro ao marcar transação {transaction['id']} como sincronizada: {response.status_code}")
            except Exception as e:
                print(f"Erro ao atualizar status de sincronização no servidor para a transação {transaction['id']}: {e}")

    def push_local_transactions(self):
        """Envia transações locais para o servidor, convertendo o createdAt para o formato ISO 8601 (UTC)."""
        if self.is_online():
            unsynced_transactions = get_unsynced_transactions()
    
            transactions_to_push = []
            for transaction in unsynced_transactions:
                # Converter o createdAt de %Y-%m-%d %H:%M:%S.%f para ISO 8601
                created_at_str = transaction[8]  # Pega o valor de createdAt da tupla
                created_at_dt = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S.%f')  # Converte para datetime
                created_at_iso = created_at_dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-4] + 'Z'  # Converte para ISO 8601 (com sufixo 'Z')
    
                transaction_dict = {
                    "id": transaction[0],           # ID da transação
                    "description": transaction[1],  # Descrição
                    "type": transaction[2],         # Tipo (Entrada/Saída)
                    "category": transaction[3],     # Categoria
                    "price": transaction[4],        # Valor
                    "owner": transaction[5],        # Proprietário
                    "email": transaction[6],        # Email do proprietário
                    "synced": True,                 # Status de sincronização
                    "createdAt": created_at_iso     # Data de criação no formato ISO 8601
                }
    
                transactions_to_push.append(transaction_dict)
    
            # Verificar o formato JSON com aspas duplas
            transactions_json = json.dumps(transactions_to_push, indent=4)  # Apenas para debug
            print("Dados a serem enviados para a API (formato JSON):", transactions_json)
    
            try:
                # Enviar os dados para a API (requests.post já converte o dicionário para JSON corretamente)
                response = requests.post(f"{self.api_url}/api/offline/transactions", json=transactions_to_push, timeout=self.timeout)
    
                if response.status_code == 200:
                    # Marcar as transações como sincronizadas
                    mark_as_synced(transactions_to_push)
                    print("Dados enviados com sucesso!")
                else:
                    print(f"Erro ao enviar dados. Status Code: {response.status_code}")
    
            except Exception as e:
                print(f"Erro ao enviar transações offline: {e}")
        else:
            print("Sem conexão. Dados não enviados.")

    def store_in_local_db(self, data):
        """Armazena as transações baixadas no banco de dados local."""
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
                        synced=True  # Definido como sincronizado
                    )
                except ValueError as ve:
                    print(f"Erro ao analisar a data: {ve}")
                except KeyError as ke:
                    print(f"Chave ausente na transação: {ke}")
                except Exception as e:
                    print(f"Erro ao inserir a transação: {e}")
