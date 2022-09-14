from enum import Enum
import math
import os
from pathlib import Path
import time
from eyeloop.utilities.target_type import TargetType

import numpy as np

import eyeloop.config as config
from eyeloop.constants.minimum_gui_constants import *
from eyeloop.utilities.general_operations import to_int, tuple_int
import threading

import logging
logger = logging.getLogger(__name__)


WINDOW_BINARY = "Binarization"
WINDOW_CONFIGURATION = "Raw Video"
WINDOW_TOOLTIP = "Instructions"
WINDOW_TRACKING = "Tracking"
WINDOW_RECORDING = "Recording"
CV_IMAGE_PERIOD = 1

WINDOW_BINARY_SCALE = 1 # percent of original size

tooltips = {
    "0": {
        "name": "tip_1_cr_first",
        "src": None
    },
    "1": {
        "name": "tip_1_cr",
        "src": None
    },
    "1_error": {
        "name": "tip_1_cr_error",
        "src": None
    },
    "2": {
        "name": "tip_2_cr",
        "src": None
    },
    "3": {
        "name": "tip_3_pupil",
        "src": None
    },
    "3_error": {
        "name": "tip_3_pupil_error",
        "src": None
    },
    "4": {
        "name": "tip_4_pupil",
        "src": None
    },
    "5": {
        "name": "tip_5_start",
        "src": None
    },
}

class GuiState(Enum):
    CONFIGURATION = "CONFIGURATION"
    TRACKING = "TRACKING"
    RECORDING = "RECORDING"

class GUI:
    def __init__(self, on_angle = None, on_quit = None, on_record = None) -> None:
        self.on_angle = on_angle
        self.on_record = on_record
        self.on_quit = on_quit
        self.tooltips = tooltips.copy()
        dir_path = os.path.dirname(os.path.realpath(__file__))

        for key, entry in self.tooltips.items():
            name = entry["name"]
            self.tooltips[key]["src"] = cv2.imread(f'{dir_path}/graphics/{name}.png', 0)
        self.first_tool_tip = self.tooltips["0"]["src"]

        self._state = GuiState.CONFIGURATION
        self.inquiry = "none"
        self.last_time = time.time()
        self.first_run = True
        self.cr_index = 0
        self.cr_processor_index = 0
        self.cr_processors = []

    def release(self):
        cv2.destroyAllWindows()

    def on_mouse_move(self, event, x, y, flags, params) -> None:
        # logger.info(f'Mouse move {x} {y}')
        x = x % self.width
        self.cursor = (x, y)

    def on_mouse_move_tooltips(self, event, x: int, y: int, flags, params) -> None:
        if event == cv2.EVENT_LBUTTONDOWN:
            if 10 < y < 35:
                if 20 < x < 209:
                    x -= 27
                    x = int(x / 36) + 1

                    self.update_tool_tip(x)

    def update_tool_tip(self, index: int, error: bool = False) -> None:
        key = str(index) if not error else f'{str(index)}_error'
        cv2.imshow(WINDOW_TOOLTIP, self.tooltips[key]["src"])

    def add_mouse_events(self) -> None:
        try:
            cv2.setMouseCallback(WINDOW_CONFIGURATION, self.on_mouse_move)
            cv2.setMouseCallback(WINDOW_TOOLTIP, self.on_mouse_move_tooltips)
        except:
            logger.error("Could not bind mouse-buttons")

    def remove_mouse_events(self) -> None:
        cv2.setMouseCallback(WINDOW_CONFIGURATION, lambda *args: None)
        cv2.setMouseCallback(WINDOW_TOOLTIP, lambda *args: None)

    def init(self, width: int, height: int):
        cv2.namedWindow(WINDOW_BINARY)
        cv2.namedWindow(WINDOW_CONFIGURATION)
        cv2.namedWindow(WINDOW_TOOLTIP)
        cv2.moveWindow(WINDOW_BINARY, width, 0)
        cv2.moveWindow(WINDOW_CONFIGURATION, 0, 0)
        cv2.moveWindow(WINDOW_TOOLTIP, 0, height + 20)

        self.add_mouse_events()

        self.bin_stock = np.zeros(self.binary_size, np.uint8)
        self.bin_P = self.bin_stock.copy()
        self.bin_CR = self.bin_stock.copy()

        cv2.imshow(WINDOW_CONFIGURATION, np.hstack((self.bin_stock, self.bin_stock)))
        cv2.imshow(WINDOW_BINARY, np.vstack((self.bin_stock, self.bin_stock)))
        cv2.imshow(WINDOW_TOOLTIP, self.first_tool_tip)


    def destroy(self):
        self.remove_mouse_events()
        cv2.destroyWindow(WINDOW_CONFIGURATION)
        cv2.destroyWindow(WINDOW_BINARY)
        cv2.destroyWindow(WINDOW_TOOLTIP)


    def key_listener(self, key: int) -> None:
        try:
            key = chr(key)
        except:
            return

        if "q" == key:
            self.on_quit()

        if "c" == key:
            action = "recording" if self._state == GuiState.RECORDING else "tracking"
            print(f"Stop {action}? (y/n)")
            self.inquiry = "configure"

        if self.inquiry == "configure":
            if "y" == key:
                print("Configuring..")

                self.init(self.width, self.height)
                self._state = GuiState.CONFIGURATION
                self.on_record(False)
                self.inquiry = "none"
                return

            elif "n" == key:
                print("Adjustments resumed.")
                self._state = GuiState.CONFIGURATION
                self.inquiry = "none"
                return

        if self.inquiry == "record":
            if "y" == key:
                print("Initiating recording..")
                self.destroy()

                cv2.imshow(WINDOW_RECORDING, self.bin_stock)

                self._state = GuiState.RECORDING
                self.on_record(True)
                self.inquiry = "none"
                return

            elif "n" == key:
                print("Adjustments resumed.")
                self._state = GuiState.CONFIGURATION
                self.inquiry = "none"
                return
            
        if self.inquiry == "track":
            if "y" == key:
                print("Initiating tracking..")
                self.destroy()

                cv2.imshow(WINDOW_TRACKING, self.bin_stock)
                cv2.moveWindow(WINDOW_TRACKING, 100, 100)

                self._state = GuiState.TRACKING
                self.inquiry = "none"
                return

            elif "n" == key:
                print("Adjustments resumed.")
                self._state = GuiState.CONFIGURATION
                self.inquiry = "none"
                return

        if self._state == GuiState.CONFIGURATION:
            current_cr_processor = self.cr_processors[self.cr_processor_index]

            if key == "p":
                self.on_angle(-3)

            elif key == "o":
                self.on_angle(+3)

            elif "1" == key:
                try:
                    self.pupil_processor.set_center(self.cursor)
                    self.update_tool_tip(4)
                    print("Pupil selected.\nAdjust binarization via R/F (threshold) and T/G (smoothing).")

                except Exception as e:
                    self.update_tool_tip(3, True)
                    logger.info(f"Failed selecting pupil - {e}")

            elif "2" == key:
                try:
                    current_cr_processor.set_center(self.cursor)
                    self.cr_processor_index = 0
                    self.update_tool_tip(2)
                    print("Corneal reflex 1 selected.\nAdjust binarization via W/S (threshold) and E/D (smoothing).")

                except Exception as e:
                    self.update_tool_tip(1, True)
                    logger.info(f"Failed selecting corneal reflection - {e}")

            elif "3" == key:
                try:
                    current_cr_processor.set_center(self.cursor)
                    self.cr_processor_index = 1
                    self.update_tool_tip(2)

                    print("\nCorneal reflex 2 selected.")
                    print("Adjust binarization via W/S (threshold) and E/D (smoothing).")

                except:
                    self.update_tool_tip(1, True)
                    print("Hover and click on the corneal reflex, then press 3.")


            elif "x" == key:
                print("Start recording? (y/n)")
                self.inquiry = "record"

            elif "z" == key:
                print("Start tracking? (y/n)")
                self.inquiry = "track"

            elif "w" == key:
                current_cr_processor.binarythreshold += 1
                print("Corneal reflex binarization threshold increased (%s)." % current_cr_processor.binarythreshold)

            elif "s" == key:
                current_cr_processor.binarythreshold -= 1
                print("Corneal reflex binarization threshold decreased (%s)." % current_cr_processor.binarythreshold)

            elif "e" == key:
                current_cr_processor.blur = [x + 2 for x in current_cr_processor.blur]
                print("Corneal reflex blurring increased (%s)." % current_cr_processor.blur)

            elif "d" == key:
                if current_cr_processor.blur[0] > 1:
                    current_cr_processor.blur = [x - 2 for x in current_cr_processor.blur]
                print("Corneal reflex blurring decreased (%s)." % current_cr_processor.blur)

            elif "r" == key:
                self.pupil_processor.binarythreshold += 1
                print("Pupil binarization threshold increased (%s)." % self.pupil_processor.binarythreshold)

            elif "f" == key:

                self.pupil_processor.binarythreshold -= 1
                print("Pupil binarization threshold decreased (%s)." % self.pupil_processor.binarythreshold)

            elif "t" == key:
                self.pupil_processor.blur = [x + 2 for x in self.pupil_processor.blur]
                print("Pupil blurring increased (%s)." % self.pupil_processor.blur)

            elif "g" == key:
                if self.pupil_processor.blur[0] > 1:
                    self.pupil_processor.blur = [x - 2 for x in self.pupil_processor.blur]
                print("Pupil blurring decreased (%s)." % self.pupil_processor.blur)


    def arm(self, image_dimensions, pupil_processor, cr_processors = []) -> None:
        self.frequency_track = np.round(1 / config.arguments.fps, 2)
        self.pupil_processor = pupil_processor

        self.cr_index = 0
        self.cr_processor_index = 0  # primary corneal reflection
        self.cr_processors = cr_processors

        width, height = image_dimensions
        self.width, self.height = width, height
        self.binary_size = (int(height * WINDOW_BINARY_SCALE), int(width * WINDOW_BINARY_SCALE))

        # Initialize windows
        self.init(width, height)

    def draw_cross(self, source: np.ndarray, point: tuple, color: tuple) -> None:
        source[to_int(point[1] - 3):to_int(point[1] + 4), to_int(point[0])] = color
        source[to_int(point[1]), to_int(point[0] - 3):to_int(point[0] + 4)] = color

    def draw_target(self, frame_rgb, params, color):
        try:
            center, width, height, angle = params
            if (not center):
                return False
            cv2.ellipse(frame_rgb, tuple_int(center), tuple_int((width, height)), angle, 0, 360, color, 1)
            # self.draw_cross(frame_rgb, center, color)
            return True
        except Exception as e:
            return False

    def generate_pupil_binarization(self):
        src = self.pupil_processor.src
        if (type(src) is not np.ndarray):
            self.bin_P = self.bin_stock.copy()
            return

        self.bin_P = np.copy(src)
        try:
            # offset_y = int((self.binary_height - src.shape[0]) / 2)
            # offset_x = int((self.binary_width - src.shape[1]) / 2)
            # self.bin_P[offset_y:min(offset_y + src.shape[0], self.binary_height),
            # offset_x:min(offset_x + src.shape[1], self.binary_width)] = src
            pass

        except Exception as e:
            logger.warn(f'Failed to calculate the binarized data for the pupil processor - {e}')

    def generate_corneal_reflection_binarization(self):
        src = self.cr_processors[self.cr_processor_index].src
        if (type(src) is not np.ndarray):
            self.bin_CR = self.bin_stock.copy()
            return

        self.bin_CR = np.copy(src)
        try:
            # offset_y = int((self.binary_height - src.shape[0]) / 2)
            # offset_x = int((self.binary_width - src.shape[1]) / 2)
            # self.bin_CR[offset_y:min(offset_y + src.shape[0], self.binary_height),
            # offset_x:min(offset_x + src.shape[1], self.binary_width)] = src
            # self.bin_CR[0:20, 0:self.binary_width] = self.crstock_txt_selected
            pass
        except Exception as e:
            logger.warn(f'Failed to calculate the binarized data for the corneal reflect processor - {src} {e}')

    def render_fps(self, frame, data):
        key = "FpsExtractor"
        if (not key in data):
            return
        fps = data[key]
        cv2.putText(frame, f'FPS: {fps}', (10, 15), font, .7, 1, 0, cv2.LINE_4)

    def update(self, frame, data):
        if (self._state == GuiState.RECORDING):
            self.update_record(frame, data)
        elif (self._state == GuiState.TRACKING):
            self.update_track(frame, data)
        else:
            self.update_configure(frame, data)

        key = cv2.waitKey(CV_IMAGE_PERIOD)
        self.key_listener(key)

    def update_configure(self, frame, data):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        # Pupil
        self.generate_pupil_binarization()
        self.bin_P_BGA = cv2.cvtColor(self.bin_P, cv2.COLOR_GRAY2BGR, 3)
        pupil_params = self.pupil_processor.fit_model.params
        if (pupil_params is not None):
            self.draw_target(frame_rgb, pupil_params, red)
            self.draw_target(self.bin_P_BGA, pupil_params, red)
        cv2.putText(self.bin_P_BGA , 'P | R/F | T/G || bin/blur', (10, 15), font, .7, 1, 0, cv2.LINE_4)

        # Corneal Reflection
        self.generate_corneal_reflection_binarization()
        self.bin_CR_BGA = cv2.cvtColor(self.bin_CR, cv2.COLOR_GRAY2BGR, 3)
        cr_params = self.cr_processors[self.cr_processor_index].fit_model.params
        if (cr_params is not None):
            self.draw_target(frame_rgb, cr_params, green)
            self.draw_target(self.bin_CR_BGA, cr_params, green)
        cv2.putText(self.bin_CR_BGA, 'CR | W/S | E/D || bin/blur', (10, 15), font, .7, 1, 0, cv2.LINE_4)

        self.render_fps(frame_rgb, data)

        cv2.imshow(WINDOW_BINARY, np.concatenate((self.bin_P_BGA, self.bin_CR_BGA), axis=0))
        cv2.imshow(WINDOW_CONFIGURATION, frame_rgb)


        if self.first_run:
            self.first_run = False

    def update_record(self, frame, data) -> None:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        self.render_fps(frame_rgb, data)
        cv2.imshow(WINDOW_RECORDING, frame_rgb)

    def update_track(self, frame, data) -> None:
        diff = time.time() - self.last_time
        if (diff < self.frequency_track):
            return
        self.last_time = time.time()

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        pupil_params = self.pupil_processor.fit_model.params
        if (pupil_params is not None):
            self.draw_target(frame_rgb, pupil_params, red)
            self.draw_target(self.bin_P_BGA, pupil_params, red)

        for i in range(len(self.cr_processors)):
            cr_params = self.cr_processors[i].fit_model.params
            if (cr_params is not None):
                self.draw_target(frame_rgb, cr_params, green)
                self.draw_target(self.bin_CR_BGA, cr_params, green)

        self.render_fps(frame_rgb, data)
        cv2.imshow(WINDOW_TRACKING, frame_rgb)

