from abc import abstractmethod
from typing import Any


class Extractor():
    def __init__(self, x: int = 50, y: int = 50, w: int = 50, h: int = 50) -> None:
        self.x, self.y, self.width, self.height = x, y, w, h

    @abstractmethod
    def activate(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def fetch(self, engine) -> Any:
        raise NotImplementedError

    @abstractmethod
    def release(self) -> None:
        raise NotImplementedError

