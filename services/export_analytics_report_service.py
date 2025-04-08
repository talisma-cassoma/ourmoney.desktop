import subprocess
from utils.logger import get_logger

def export_analytics_report():
    logging = get_logger("analyticsReport")
    try:
        result = subprocess.run(
            ["quarto", "render", "report.qmd", "--to", "pdf"],
            check=True,
            capture_output=True,
            text=True
        )
        print("PDF export successful:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error during PDF export:", e.stderr)
