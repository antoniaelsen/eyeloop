import os
from pathlib import Path
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
CV_IMAGE_PERIOD = 50

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

class GUI:
    def __init__(self, on_angle = None, on_center = None, on_quit = None) -> None:
        self.on_angle = on_angle
        self.on_center = on_center
        self.on_quit = on_quit
        self.tooltips = tooltips.copy()
        dir_path = os.path.dirname(os.path.realpath(__file__))

        for key, entry in self.tooltips.items():
            name = entry["name"]
            self.tooltips[key]["src"] = cv2.imread(f'{dir_path}/graphics/{name}.png', 0)
        self.first_tool_tip = self.tooltips["0"]["src"]

        self._state = "configuration"
        self.inquiry = "none"
        self.terminate = -1
        self.update = self.update_configure
        self.skip = 0
        self.first_run = True
        self.cr_index = 0
        self.cr_processor_index = 0
        self.cr_processors = []

        self.out = None

        self.crs_ = [lambda _: False]


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
        cv2.moveWindow(WINDOW_BINARY, 105 + width, 100)
        cv2.moveWindow(WINDOW_CONFIGURATION, 100, 100)
        cv2.moveWindow(WINDOW_TOOLTIP, 100, height + 148)
 
        self.add_mouse_events()

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

        if self.inquiry == "track":
            if "y" == key:
                print("Initiating tracking..")
                self.destroy()

                cv2.imshow(WINDOW_TRACKING, self.bin_stock)
                cv2.moveWindow(WINDOW_TRACKING, 100, 100)

                self._state = "tracking"
                self.inquiry = "none"
                self.update = self.update_track
                return

            elif "n" == key:
                print("Adjustments resumed.")
                self._state = "configuration"
                self.inquiry = "none"
                return

        if self._state == "configuration":
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

        if "q" == key:
            self.on_quit()

    def arm(self, image_dimensions, pupil_processor, cr_processors = []) -> None:
        self.frequency_track = np.round(1 / config.arguments.fps, 2)
        self.pupil_processor = pupil_processor

        self.cr_index = 0
        self.cr_processor_index = 0  # primary corneal reflection
        self.cr_processors = cr_processors

        width, height = image_dimensions
        self.width, self.height = width, height
        self.binary_width = max(width, 300)
        self.binary_height = max(height, 200)

        # Initialize windows
        self.init(width, height)

        fourcc = cv2.VideoWriter_fourcc(*'MPEG')
        output_vid = Path(config.file_manager.new_folderpath, "output.avi")
        self.out = cv2.VideoWriter(str(output_vid), fourcc, 50.0, (self.width, self.height))

        self.bin_stock = np.zeros((self.binary_height, self.binary_width))
        self.bin_P = self.bin_stock.copy()
        self.bin_CR = self.bin_stock.copy()
        #self.CRStock = self.bin_stock.copy()

        self.src_txt = np.zeros((20, width, 3))
        self.prev_txt = self.src_txt.copy()
        cv2.putText(self.src_txt, 'Source', (15, 12), font, .7, (255, 255, 255), 0, cv2.LINE_4)
        cv2.putText(self.prev_txt, 'Preview', (15, 12), font, .7, (255, 255, 255), 0, cv2.LINE_4)
        cv2.putText(self.prev_txt, 'EyeLoop', (width - 50, 12), font, .5, (255, 255, 255), 0, cv2.LINE_8)

        self.bin_stock_txt = np.zeros((20, self.binary_width))
        self.bin_stock_txt_selected = self.bin_stock_txt.copy()
        self.crstock_txt = self.bin_stock_txt.copy()
        self.crstock_txt[0:1, 0:self.binary_width] = 1
        self.crstock_txt_selected = self.crstock_txt.copy()

        cv2.putText(self.bin_stock_txt, 'P | R/F | T/G || bin/blur', (10, 15), font, .7, 1, 0, cv2.LINE_4)
        cv2.putText(self.bin_stock_txt_selected, '(*) P | R/F | T/G || bin/blur', (10, 15), font, .7, 1, 0, cv2.LINE_4)

        cv2.putText(self.crstock_txt, 'CR | W/S | E/D || bin/blur', (10, 15), font, .7, 1, 0, cv2.LINE_4)
        cv2.putText(self.crstock_txt_selected, '(*) CR | W/S | E/D || bin/blur', (10, 15), font, .7, 1, 0, cv2.LINE_4)

        cv2.imshow(WINDOW_CONFIGURATION, np.hstack((self.bin_stock, self.bin_stock)))
        cv2.imshow(WINDOW_BINARY, np.vstack((self.bin_stock, self.bin_stock)))
        cv2.imshow(WINDOW_TOOLTIP, self.first_tool_tip)

    def draw_cross(self, source: np.ndarray, point: tuple, color: tuple) -> None:
        # print(f"Draw cross: source {source}, point: {point}, color: {color}")
        source[to_int(point[1] - 3):to_int(point[1] + 4), to_int(point[0])] = color
        source[to_int(point[1]), to_int(point[0] - 3):to_int(point[0] + 4)] = color

    def draw_pupil(self, frame_rgb):
        params = self.pupil_processor.fit_model.params
        if (params == None):
            return

        try:
            center, width, height, angle = params
            if (not center):
                return False
            cv2.ellipse(frame_rgb, tuple_int(center), tuple_int((width, height)), angle, 0, 360, red, 1)
            self.draw_cross(frame_rgb, center, red)
            return True
        except Exception as e:
            logger.info(f"pupil not found: {e} - {self.pupil_processor.fit_model.params}")
            return False

    def draw_corneal_reflection(self, frame_rgb, index):
        if (index >= len(self.cr_processors)):
            logger.warn(f'Error drawing corneal reflection #{index} - no processor')
            return

        params = self.cr_processors[index].fit_model.params
        if (params == None):
            return

        try:
            center, width, height, angle = params
            if (not center):
                return False 
            cv2.ellipse(frame_rgb, tuple_int(center), tuple_int((width, height)), angle, 0, 360, green, 1)
            self.draw_cross(frame_rgb, center, green)
            return True
        except Exception as e:
            logger.warn(f'Error processing corneal reflection #{index} - {e} {params}')
            return False
    
    def generate_pupil_binarization(self):
        src = self.pupil_processor.src
        if (type(src) is not np.ndarray):
            return

        try:
            offset_y = int((self.binary_height - src.shape[0]) / 2)
            offset_x = int((self.binary_width - src.shape[1]) / 2)
            self.bin_P[offset_y:min(offset_y + src.shape[0], self.binary_height),
            offset_x:min(offset_x + src.shape[1], self.binary_width)] = src
        except Exception as e:
            logger.warn(f'Failed to calculate the binarized data for the pupil processor - {e}')
            
    def generate_corneal_reflection_binarization(self):
        self.bin_CR = self.bin_stock.copy()
        src = self.cr_processors[self.cr_processor_index].src
        if (type(src) is not np.ndarray):
            return

        try:
            offset_y = int((self.binary_height - src.shape[0]) / 2)
            offset_x = int((self.binary_width - src.shape[1]) / 2)
            self.bin_CR[offset_y:min(offset_y + src.shape[0], self.binary_height),
            offset_x:min(offset_x + src.shape[1], self.binary_width)] = src
            self.bin_CR[0:20, 0:self.binary_width] = self.crstock_txt_selected
        except Exception as e:
            logger.warn(f'Failed to calculate the binarized data for the corneal reflect processor - {src} {e}')
            self.bin_CR[0:20, 0:self.binary_width] = self.crstock_txt
    

    def skip_track(self):
        self.update = self.update_track

    def update_configure(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        self.bin_P = self.bin_stock.copy()

        if self.draw_pupil(frame_rgb):
            self.bin_P[0:20, 0:self.binary_width] = self.bin_stock_txt_selected
        else:
            self.bin_P[0:20, 0:self.binary_width] = self.bin_stock_txt
        self.generate_pupil_binarization()
        

        self.draw_corneal_reflection(frame_rgb, self.cr_processor_index)
        self.generate_corneal_reflection_binarization()


        cv2.imshow(WINDOW_BINARY, np.vstack((self.bin_P, self.bin_CR)))
        cv2.imshow(WINDOW_CONFIGURATION, frame_rgb)

        key = cv2.waitKey(CV_IMAGE_PERIOD)
        self.key_listener(key)
        if self.first_run:
            self.first_run = False

    def update_record(self, frame_preview) -> None:
        cv2.imshow(WINDOW_RECORDING, frame_preview)
        if cv2.waitKey(1) == ord('q'):
            self.on_quit()

    def update_track(self, frame) -> None:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        self.draw_pupil(frame_rgb)
        for i in range(len(self.cr_processors)):
            self.draw_corneal_reflection(frame_rgb, i)

        cv2.imshow(WINDOW_TRACKING, frame_rgb)

        threading.Timer(self.frequency_track, self.skip_track).start() #run feed every n secs (n=1)
        self.update = lambda _: None

        if cv2.waitKey(1) == ord("q"):
            self.on_quit()
