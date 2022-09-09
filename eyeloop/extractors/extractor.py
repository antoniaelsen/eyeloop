from abc import abstractmethod
from typing import Any


class Extractor():
    def __init__(self) -> None:
        pass

    @abstractmethod
    def activate(self) -> None:
        return

    @abstractmethod
    def fetch(self, engine) -> Any:
        return

    @abstractmethod
    def release(self) -> None:
        return

