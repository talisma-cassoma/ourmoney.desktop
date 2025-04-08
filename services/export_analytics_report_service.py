import subprocess
from utils.logger import get_logger

def export_analytics_report():
    logger = get_logger("analyticsReport")
    #logger.info("Iniciando a exportação do relatório em PDF...")

    try:
        result = subprocess.run(
            ["quarto", "render", "report.qmd", "--to", "pdf"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Exportação para PDF bem-sucedida: {result.stdout.strip()}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao exportar PDF: {e.stderr.strip()}")
