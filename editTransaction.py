from controller import Controller

controller = Controller()

transaction_id = "ec88a826-3a0d-4609-ba2b-xxxxxx"  # Replace with the actual transaction ID
updates = {
    "createdAt": "2024-05-26 09:40:38.343421"
}

controller.edit(transaction_id, updates)