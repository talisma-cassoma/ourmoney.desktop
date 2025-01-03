import subprocess

def generate_pdf(input_file, output_file):
    try:
        # Run the Quarto render command
        subprocess.run(
            ["quarto", "render", input_file, "--to", "pdf", "--output", output_file],
            check=True,
        )
        print(f"PDF report generated: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error generating PDF: {e}")

input_qmd = "report.qmd"  # Path to your Quarto file
output_pdf = "report.pdf"  # Desired output PDF file name

generate_pdf(input_qmd, output_pdf)
