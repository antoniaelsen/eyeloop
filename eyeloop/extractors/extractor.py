from abc import abstractmethod
import time

import cv2
import numpy as np


class Extractor():
    def __init__(self, x: int = 50, y: int = 50, w: int = 50, h: int = 50) -> None:
        self.x, self.y, self.width, self.height = x, y, w, h

    @abstractmethod
    def activate(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def fetch(self, engine):
        raise NotImplementedError

    @abstractmethod
    def release(self):
        raise NotImplementedError

