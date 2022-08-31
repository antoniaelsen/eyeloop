import logging
import math
from pathlib import Path
import time
from typing import Optional, Callable

import cv2
import numpy as np

import eyeloop.config as config
from eyeloop.sources.source import Source

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 100

class CvStreamSource(Source):
    def __init__(self, on_frame) -> None:
        super().__init__(on_frame)
    
    def init(self) -> None:
        self.camera_id = int(config.arguments.device)
        self.capture = cv2.VideoCapture(self.camera_id)
        # self.capture.set(3, 640)
        # self.capture.set(4, 480)

        # load first frame
        width = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)

        live = False
        i = 0
        while (i < MAX_ATTEMPTS and not live):
            _, image = self.capture.read()
            live = np.any(image)
            i += 1

        if self.capture.isOpened() and live:
            try:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            except:
                image = image[..., 0]
        else:
            raise ValueError(
                "Failed to initialize video stream.\n"
                "Make sure that your webcam is plugged in and compatible with opencv.")
            

        width = math.floor(width)
        height = math.floor(height)
        return (width, height), image

    def route(self) -> None:
        while True:
            if self.route_frame is not None:
                self.route_frame()
            else:
                break

    def proceed(self, image) -> None:
        image = self.resize(image)
        self.rotate_(image, self.angle)
        self.on_frame(image)
        self.save_(image)
        self.frame += 1

    def route_frame(self) -> None:
        """
        Routes the capture frame to:
        1: eyeloop for online processing
        2: frame save for offline processing
        """

        _, image = self.capture.read()
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        self.proceed(image)

    def release(self) -> None:
        if self.capture is not None:
            self.capture.release()
        super().release()

