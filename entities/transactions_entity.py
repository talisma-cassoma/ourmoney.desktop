from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

@dataclass
class TransactionEntity:
    id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    type: str = ""  # income | outcome
    category: str = ""
    price: float = 0.0
    owner: str = "talisma"
    email: str = "talisma@email.com"
    status: str = "unsynced"
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat(timespec="milliseconds") + "Z"
