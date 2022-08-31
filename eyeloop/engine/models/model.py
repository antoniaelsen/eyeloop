from abc import ABCMeta, abstractmethod


class Shape:
    center: tuple[float, float]
    width: float
    height: float
    angle: float


class Model:
    def __init__(self, metaclass=ABCMeta):
        self.params: Shape = None

    @abstractmethod
    def fit(self, r: float) -> tuple[float, float]:
        raise NotImplementedError
