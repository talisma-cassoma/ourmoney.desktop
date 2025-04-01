<p align="center"><img src="assets/appGUI.png"></p>


## Setup

Follow these steps to set up the project locally:

1. **Clone and Create a Virtual Environment** 
 
   Clone the project and use the following command to create a virtual environment:  
   ```bash
   python3 -m venv env
   ```

2. **Activate the Virtual Environment**  
   - On **Linux/macOS**:  
     ```bash
     source env/bin/activate
     ```
   - On **Windows**:  
     ```bash
     .\env\Scripts\activate
     ```

3. **Install Required Dependencies**  
   Run the following command to install the dependencies listed in the `requirements.txt` file:  
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Generate the Requirements File (Optional)**  
   If you need to update the `requirements.txt` file after adding new dependencies:  
   ```bash
   pip3 freeze > requirements.txt
   ```
   
5. **create a shortcut in terminal(Optional)** 
  ...

### Objectivos

- [x] criar GUI para anotocoes dos gastos
      features 
      [x]
- [x] gerar pdf com analises dos dados
   
   features :
   
   - [x] table dos os gastos mensais por categoria
   - [x] table dos gastos recurrentes
   - [x] table dos gastos com previsões

- [ ] criar um executavel(pyinstaller)
- [ ] criar um installer setup wizard(inno setup)
- [ ] automatizar a criaçao do setup wizard com CI/CD a cada commit na branch main 

project structure:
```php
.
├── assets/
│    └── logo_icon.icns
├── database/
│    └── database.db
├── dto/
│    └── transaction_dto.py
├── entities/
│    └── transactions_entity.py
├── env/
├── repositories/
│    └── transactions_repository.py
├── services/
│    ├── delete_transation_service.py
│    ├── GenerateAnalyticsReportService.py
│    ├── export_csv_file_service.py
│    ├── export_json_file_service.py
│    ├── export_json_file_service.py
│    ├── import_json_file_service.py
│    ├── insert_transaction_service.py
│    ├── list_transaction_service.py
│    └── update_transaction_service.py
├── utils/
│    ├── helppers.py
│    ├── logger.py       
│    └── shared/
├── .gitignore
├── GUI.py
├── README.md
├── app.spec
├── controller.py
├── requirements.txt
└── main.py
```