import logging
import math
from pathlib import Path
import time
from typing import Any, Optional, Callable

import cv2
import numpy as np
from pypylon import pylon

import eyeloop.config as config
from eyeloop.sources.source import Source

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 100

class PylonSource(Source):
    def __init__(self, on_frame) -> None:
        super().__init__(on_frame)

    def __del__(self):
        if (self.capture):
            self.capture.Close()

    def init(self) -> None:
        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputPixelFormat = pylon.PixelType_Mono8
        # self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

        self.capture = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.capture.RegisterConfiguration(pylon.SoftwareTriggerConfiguration(), pylon.RegistrationMode_ReplaceAll, pylon.Cleanup_Delete)

        self.capture.Open()
        self.capture.StopGrabbing()
        self.capture.Width.SetValue(640)
        self.capture.Height.SetValue(512)

        i = 0
        live = False
        image = None
        while (i < MAX_ATTEMPTS and not live):
            image = self.grab_image()
            print(f"Pix {image[0, 0]}")
            print(image)
            live = np.any(image)
            i += 1

        if not (self.capture.IsOpen() and live):
            raise ValueError(
                "Failed to initialize video stream.\n"
                "Make sure that your camera is plugged in and compatible with pylon.")
            

        width = self.capture.Width.GetValue()
        height = self.capture.Height.GetValue()
        print(f"Using Pylon device {self.capture.GetDeviceInfo().GetModelName()}: {width} x {height}")
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

    def grab_image(self) -> Any:
        TIMEOUT = 50

        self.capture.StartGrabbing(pylon.GrabStrategy_LatestImageOnly) 
        ready = self.capture.WaitForFrameTriggerReady(1, pylon.TimeoutHandling_ThrowException)
        self.capture.ExecuteSoftwareTrigger()
        result = self.capture.RetrieveResult(TIMEOUT, pylon.TimeoutHandling_Return)

        self.capture.StopGrabbing()
        if not result.GrabSucceeded():
            return False

        image = result.Array

        return image

    def route_frame(self) -> Any:
        """
        Routes the capture frame to:
        1: eyeloop for online processing
        2: frame save for offline processing
        """
        image = self.grab_image()
        self.proceed(image)

    def release(self) -> None:
        if self.capture is not None:
            self.capture.Close()
        super().release()

