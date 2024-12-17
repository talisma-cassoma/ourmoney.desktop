import logging
from datetime import datetime, timezone


# Configuração do logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')


def convert_to_iso8601(date):
    # Verifica se a data é um int (timestamp em milissegundos)
    if isinstance(date, int):
        dt = datetime.fromtimestamp(date / 1000, tz=timezone.utc)
        # Substitui +00:00 por Z para indicar UTC
        return dt.isoformat(timespec='milliseconds').replace("+00:00", "Z")
    # Verifica se a data já está no formato string
    elif isinstance(date, str):
        return date  # Assume que está correta
    else:
         logging.error("Formato de data inválido: esperado int ou string.")
