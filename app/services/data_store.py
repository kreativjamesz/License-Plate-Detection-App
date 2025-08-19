from typing import Optional, Dict
from abc import ABC, abstractmethod

class IDataStore(ABC):
    @abstractmethod
    def create_user(self, username: str, password_hash: bytes) -> int: ...
    @abstractmethod
    def get_user(self, username: str) -> Optional[Dict]: ...
