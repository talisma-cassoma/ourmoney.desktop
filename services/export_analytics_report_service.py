import subprocess
from utils.logger import get_logger
from services.export_xlsx_file_service import export_transactions_to_excel
import os
import platform

def export_analytics_report():
    logger = get_logger("analyticsReport")
    #logger.info("Iniciando a exportação do relatório em PDF...")
    
    # Primeiro, exporta as transações para o Excel
    export_transactions_to_excel()
    
    try:
        pdf_path = "report.pdf"
        result = subprocess.run(
            ["quarto", "render", "report.qmd", "--to",  "pdf", "--output", pdf_path],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Exportação para PDF bem-sucedida: {result.stdout.strip()}")


        # Abre o PDF dependendo do sistema operacional
        # Abrir o PDF após gerar
        if platform.system() == "Windows":
            os.startfile(pdf_path)
        elif platform.system() == "Darwin":  # macOS
            os.system(f"open '{pdf_path}'")
        else:  # Linux
            os.system(f"xdg-open '{pdf_path}'")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao exportar PDF: {e.stderr.strip()}")
