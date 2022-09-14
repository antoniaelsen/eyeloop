import logging
from typing import Any

import cv2
import numpy as np
from pypylon import pylon

import eyeloop.config as config
from eyeloop.sources.source import Source

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 10

class PylonSource(Source):
    def __init__(self, on_frame) -> None:
        super().__init__(on_frame)
        self.active = False

    def __del__(self):
        self.release()


    # class SampleImageEventHandler(pylon.ImageEventHandler):
    #     def OnImageGrabbed(self, camera, result):
    #         # print("CSampleImageEventHandler::OnImageGrabbed called.")
    #         # print()
    #         # print()
    #         self.proceed.
    #         pass


    def init(self) -> None:
        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputPixelFormat = pylon.PixelType_Mono8
        # self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

        self.capture = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.capture.RegisterConfiguration(pylon.SoftwareTriggerConfiguration(), pylon.RegistrationMode_ReplaceAll, pylon.Cleanup_Delete)

        self.capture.Open()
        self.capture.StopGrabbing()
        # self.capture.Width.SetValue(640)
        # self.capture.Height.SetValue(512)

        self.capture.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

        i = 0

        image = None
        while (i < MAX_ATTEMPTS and not self.active):
            image = self.grab_image()
            if (image is not None):
                print(f"Pix {image[0, 0]}")
                print(image)
                self.active = np.any(image)
            i += 1

        if not (self.capture.IsOpen() and self.active):
            raise ValueError(
                "Failed to initialize video stream.\n"
                "Make sure that your camera is plugged in and compatible with pylon.")


        width = self.capture.Width.GetValue()
        height = self.capture.Height.GetValue()
        print(f"Using Pylon device {self.capture.GetDeviceInfo().GetModelName()}: {width} x {height}")

        # self.capture.RegisterImageEventHandler(, pylon.RegistrationMode_Append, pylon.Cleanup_Delete)
        # self.capture.StartGrabbing(pylon.GrabStrategy_OneByOne, pylon.GrabLoop_ProvidedByInstantCamera)
        return (width, height), image

    def route(self) -> None:
        while self.active:
            if self.route_frame is not None:
                self.route_frame()
            else:
                break

    def grab_image(self) -> Any:
        TIMEOUT = 10

        self.capture.WaitForFrameTriggerReady(1, pylon.TimeoutHandling_Return)
        self.capture.ExecuteSoftwareTrigger()
        result = self.capture.RetrieveResult(1, pylon.TimeoutHandling_Return)

        if not result or not result.GrabSucceeded():
            return None

        image = result.Array

        return image

    def route_frame(self) -> Any:
        """
        Routes the capture frame to:
        1: eyeloop for online processing
        2: frame save for offline processing
        """
        image = self.grab_image()
        if (image is None):
            return
        self.proceed(image)

    def release(self) -> None:
        print(f'Pylon releasing...')
        if (self.capture is not None):
            self.capture.StopGrabbing()
            self.capture.Close()
        super().release()

