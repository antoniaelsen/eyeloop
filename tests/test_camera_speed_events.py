import cv2
from pypylon import genicam
from pypylon import pylon

import math
import time


def getkey():
    return input("Enter \"t\" to trigger the camera or \"e\" to exit and press enter? (t/e) ")


class EventHandler(pylon.ImageEventHandler):
    def __init__(self):
        super().__init__()
        self.last_time = time.time()

    def OnImagesSkipped(self, camera, n_skipped):
        print(n_skipped, " images have been skipped.")

    def OnImageGrabbed(self, camera, result):
        if not result:
            print("NO RESULT")
    
        if result.GrabSucceeded():
            diff = time.time() - self.last_time
            self.last_time = time.time()
            print(f"FPS {math.floor(1 / diff)}")
            print(f"Image: {result.Array.shape}")
            cv2.imshow("window", result.Array)
            cv2.waitKey(1)

        else:
            print("Error: ", result.GetErrorCode(), result.GetErrorDescription())


if __name__ == '__main__':
    try:
        camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        camera.StopGrabbing()
        
        camera.RegisterConfiguration(pylon.SoftwareTriggerConfiguration(), pylon.RegistrationMode_ReplaceAll,
                                     pylon.Cleanup_Delete)
        camera.RegisterImageEventHandler(EventHandler(), pylon.RegistrationMode_Append, pylon.Cleanup_Delete)

        # camera.StartGrabbing(pylon.GrabStrategy_OneByOne, pylon.GrabLoop_ProvidedByInstantCamera);
        camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly, pylon.GrabLoop_ProvidedByInstantCamera)

        while True:
            time.sleep(0.0001) # need a small wait or else fps is erratic, slower
            if camera.WaitForFrameTriggerReady(1, pylon.TimeoutHandling_Return):
                camera.ExecuteSoftwareTrigger()
            else:
                # print(f"frame trigger not ready")
                pass

    except genicam.GenericException as e:
        print("An exception occurred.", e.GetDescription())
