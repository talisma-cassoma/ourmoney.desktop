import requests

class SyncManager:
    def __init__(self):
        self.api_url = "https://our-money-bkd.onrender.com"
        self.timeout = 5

    def is_online(self):
        """Checa se a máquina está conectada ao servidor."""
        try:
            response = requests.get(f"{self.api_url}/ping", timeout=self.timeout)
            if response.status_code == 200:
                print('Está online: ')
                return True
        except (requests.ConnectionError, requests.Timeout):
            print('Está offline'+ requests.ConnectionError)
            return False

    def pull_data(self):
        """Baixa dados do servidor para o SQLite local."""
        if self.is_online():
            try:
                response = requests.get(f"{self.api_url}/api/all/transactions?_sort=createdAt&_order=desc", timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    self.store_in_local_db(data)
                    print("Dados sincronizados do servidor!")
            except Exception as e:
                print(f"Erro ao puxar dados: {e}")
        else:
            print("Sem conexão. Dados não puxados.")

    def push_data(self):
        """Envia transações locais para o servidor."""
        if self.is_online():
            unsynced_transactions = self.get_unsynced_transactions()
            try:
                response = requests.post(f"{self.api_url}/transactions", json=unsynced_transactions, timeout=self.timeout)
                if response.status_code == 200:
                    self.mark_as_synced(unsynced_transactions)
                    print("Dados enviados com sucesso!")
            except Exception as e:
                print(f"Erro ao enviar dados: {e}")
        else:
            print("Sem conexão. Dados não enviados.")

    def store_in_local_db(self, data):
        """Guarda dados do servidor no banco SQLite."""
        # Lógica de inserção no SQLite
        pass

    def get_unsynced_transactions(self):
        """Busca transações locais que ainda não foram sincronizadas."""
        # Lógica para obter transações do SQLite
        pass

    def mark_as_synced(self, transactions):
        """Marca transações como sincronizadas no SQLite."""
        # Lógica para marcar transações sincronizadas
        pass
