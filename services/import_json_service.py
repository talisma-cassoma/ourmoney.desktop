import ijson
from entities.transactions_entity import TransactionEntity
from repositories.transactions_repository import TransactionsRepository
from utils.logger import get_logger

def import_transactions_from_json():
    logger = get_logger("importJsonFile")
    model = TransactionsRepository()

    if model.is_database_empty():
        try:
            batch_size = 1000
            transactions: list[TransactionEntity] = []

            with open('myTransactions_20251011.json', 'r', encoding='utf-8') as file:
                parser = ijson.items(file, 'item')  # Ajuste conforme a estrutura do JSON

                for transaction in parser:
                    transactions.append(TransactionEntity(
                        id=transaction["id"],
                        description=transaction["description"],
                        type=transaction["type"],
                        category=transaction["category"],
                        price=float(transaction["price"]),
                        owner=transaction["owner"],
                        email=transaction["email"],
                        created_at=transaction["createdAt"],
                        status=transaction["status"],
                    ))

                    if len(transactions) >= batch_size:
                        model.insert_many(transactions)
                        #print(model.insert_many)  # Deve imprimir algo como <bound method ...> e não None

                        transactions.clear()  # Melhor que transactions = []

                if transactions:  # Insere o restante dos dados
                    model.insert_many(transactions)
        except FileNotFoundError as e:
            #print(f"Erro ao importar o arquivo JSON: {str(e)}")
            logger.error(f"Erro ao importar o arquivo JSON: {str(e)}")
        except KeyError as e:
            #print(f"Chave ausente no JSON: {str(e)}")
            logger.error(f"Chave ausente no JSON: {str(e)}")
        except Exception as e:
            #print(f"Erro inesperado: {str(e)}")
            logger.error(f"Erro inesperado: {str(e)}")
