#apple trackpad 1 finger left mouse button
# 2 fingers right mouse button. How is that intuitive?

import cv2
import numpy as np


def mouse_capture(event, x, y, flags, param):
    if event==cv2.EVENT_LBUTTONDOWN:
        print('left mouse button')
    elif event==cv2.EVENT_RBUTTONDOWN:
        print('right mouse button')
   

vc = cv2.VideoCapture('/Users/antoniae/projects/eyeloop_playground/examples/human/human.mp4')

ret_code, first_frame = vc.read()

cv2.namedWindow('show_firstFrame')
cv2.setMouseCallback('show_firstFrame', mouse_capture)

while True:
    ret_code, first_frame = vc.read()
    cv2.imshow('show_firstFrame', first_frame)
    waitKey = cv2.waitKey(1) & 0xFF
    if waitKey == ord('q'):
        break

cv2.destroyAllWindows()
cv2.waitKey(1)
cv2.waitKey(1)
cv2.waitKey(1)

print('done')