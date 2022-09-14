import logging
import math
from pathlib import Path
import time
from typing import Optional, Callable

import cv2

import eyeloop.config as config
from eyeloop.sources.source import Source

logger = logging.getLogger(__name__)

FRAME_RATE_COEFF = 0.5

class CvOfflineSource(Source):
    def __init__(self, on_frame) -> None:
        super().__init__(on_frame)
        self.route_frame: Optional[Callable] = None  # Dynamically assigned at runtime depending on input type
        self.last_frame_time = time.time()
        self.fps = 30

    def init(self) -> None:
        self.vid_path = Path(config.arguments.video)

        if self.vid_path.is_file():
            self.capture = cv2.VideoCapture(str(self.vid_path))

            # width = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)
            # height = self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            self.fps = self.capture.get(cv2.CAP_PROP_FPS)
            self.route_frame = self.route_cam
            logger.info(f"Video FPS: {self.fps}")

            _, image = self.capture.read()
            image = self.resize(image)
            width = image.shape[1]
            height = image.shape[0]
            print(f"SHape: {image.shape}")

            if self.capture.isOpened():
                try:
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                except:
                    image = image[..., 0]
            else:
                raise ValueError(
                    "Failed to initialize video stream.\n"
                    "Make sure that the video path is correct, or that your webcam is plugged in and compatible with opencv.")

        elif self.vid_path.is_dir():
            config.file_manager.input_folderpath = self.vid_path
            config.file_manager.input_folderpath = self.vid_path
            image = config.file_manager.read_image(self.frame)

            try:
                height, width, _ = image.shape
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                self.route_frame = self.route_sequence_sing
            except Exception:  # TODO fix bare except
                logger.exception("first_frame() error: ")
                height, width = image.shape
                self.route_frame = self.route_sequence_flat

        else:
            raise ValueError(f"Video path at {self.vid_path} is not a file or directory!")

        width = math.floor(width)
        height = math.floor(height)
        return (width, height), image

    def route(self) -> None:
        period = 1 / (self.fps * FRAME_RATE_COEFF)
        while True:
            now = time.time()
            if (now - self.last_frame_time < period):
                continue

            self.last_frame_time = now
            if self.route_frame is not None:
                self.route_frame()

            else:
                break

    def route_sequence_sing(self) -> None:
        image = config.file_manager.read_image(self.frame)
        self.proceed(image[..., 0])

    def route_sequence_flat(self) -> None:
        image = config.file_manager.read_image(self.frame)
        self.proceed(image)

    def route_cam(self) -> None:
        """
        Routes the capture frame to:
        1: eyeloop for online processing
        2: frame save for offline processing
        """
        _, image = self.capture.read()
        if image is not None:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            self.proceed(image)
        else:
            if config.arguments.loop:
                self.capture.release()
                self.capture = cv2.VideoCapture(str(self.vid_path))
                logger.info("No more frames to process, restarting video.")
            else:
                logger.info("No more frames to process, exiting.")

    def release(self) -> None:
        if self.capture is not None:
            self.capture.release()

        self.route_frame = None
        cv2.destroyAllWindows()
        super().release()
