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
   
### create a shortcut in terminal`
5. create a entrypoint.sh to run the app:
6. open new terminal and tape:
```bash
alias ourmoney_desktop='zsh  ~/desktop/entrypoint.sh'
```
7. run : ```ourmoney_desktop```

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