import cv2
from pypylon import genicam
from pypylon import pylon

import math
import time

if __name__ == '__main__':
    try:
        last_time = time.time()
        camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        camera.StopGrabbing()
        camera.RegisterConfiguration(pylon.SoftwareTriggerConfiguration(), pylon.RegistrationMode_ReplaceAll,
                                     pylon.Cleanup_Delete)


        # camera.StartGrabbing(pylon.GrabStrategy_OneByOne)
        # camera.StartGrabbing(pylon.GrabStrategy_LatestImages)
        camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

        TIMEOUT = 1
        while True:
            if camera.WaitForFrameTriggerReady(1, pylon.TimeoutHandling_Return):
                camera.ExecuteSoftwareTrigger()
                result = camera.RetrieveResult(TIMEOUT, pylon.TimeoutHandling_Return)
                if (not result or not result.GrabSucceeded()):
                    print("NO RESULT")
                else:
                    print(f"FPS {math.floor(1 / (time.time() - last_time))}")
                    last_time = time.time()
                    print(f"Image: {result.Array.shape}")
                    cv2.imshow("window", result.Array)
                    cv2.waitKey(1)

            else:
                print(f"frame trigger not ready")

    except genicam.GenericException as e:
        print("An exception occurred.", e.GetDescription())
