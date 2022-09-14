import cv2
import numpy as np

import eyeloop.config as config
from eyeloop.utilities.general_operations import tuple_int


class Source:
    def __init__(self, on_frame = None):
        self.on_frame = on_frame
        self.scale = config.arguments.scale

        self.frame = 0
        self.vid_path = config.arguments.video
        self.capture = None
        self.angle = 0

    def arm(self, width, height, image):
        self.dimensions = tuple_int((width * self.scale, height * self.scale))
        width, height = self.dimensions
        self.center = (width // 2, height // 2)

    def proceed(self, image) -> None:
        image = self.resize(image)
        self.rotate(image, self.angle)
        self.on_frame(image)
        self.save(image)
        self.frame += 1

    def rotate(self, image: np.ndarray, angle: int) -> np.ndarray:
        """
        Performs rotaiton of the image to align visual axes.
        """
        if config.arguments.rotation != 1:
            return
    
        if angle == 0:
            return

        M = cv2.getRotationMatrix2D(self.center, angle, 1)

        image[:] = cv2.warpAffine(image, M, self.dimensions, cv2.INTER_NEAREST)

    def resize(self, image: np.ndarray) -> np.ndarray:
        """
        Resizes image to scale value. -sc 1 (default)
        """

        return cv2.resize(image, None, fx=self.scale, fy=self.scale, interpolation=cv2.INTER_NEAREST)

    def save(self, image: np.ndarray) -> None:
        if config.arguments.save != 1:
            return
        config.file_manager.save_image(image, self.frame)

    def release(self):
        self.release = lambda:None
        
