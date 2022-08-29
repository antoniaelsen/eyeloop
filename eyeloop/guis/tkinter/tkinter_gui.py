import os
from pathlib import Path
from tkinter.tix import WINDOW

import cv2
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk

import eyeloop.config as config
from eyeloop.constants.minimum_gui_constants import *
from eyeloop.utilities.general_operations import to_int, tuple_int
import threading

import logging
logger = logging.getLogger(__name__)

WINDOW_BINARY = "BINARY"
WINDOW_CONFIGURATION = "CONFIGURATION"
WINDOW_TOOLTIP = "TOOLTIP"
WINDOW_TRACKING = "TRACKING"
CV_IMAGE_PERIOD = 50

class GUI:
    def __init__(self) -> None:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        tool_tip_dict = ["tip_1_cr", "tip_2_cr", "tip_3_pupil", "tip_4_pupil", "tip_5_start", "tip_1_cr_error", "",
                         "tip_3_pupil_error"]
        self.first_tool_tip = cv2.imread("{}/graphics/{}.png".format(dir_path, "tip_1_cr_first"), 0)
        self.tool_tips = [cv2.imread("{}/graphics/{}.png".format(dir_path, tip), 0) for tip in tool_tip_dict]

        self._state = "adjustment"
        self.inquiry = "none"
        self.terminate = -1
        self.update = self.adj_update#real_update
        self.skip = 0
        self.first_run = True

        self.pupil_ = lambda _: False
        self.cr1_ = lambda _: False
        self.cr2_ = lambda _: False


    def tip_mousecallback(self, event, x: int, y: int, flags, params) -> None:
        logger.info(f'tooltip mouse callback {x} {y}')
        if event == cv2.EVENT_LBUTTONDOWN:
            if 10 < y < 35:
                if 20 < x < 209:
                    x -= 27
                    x = int(x / 36) + 1

                    self.update_tool_tip(x)


    def release(self):
        #self.out.release()
        # cv2.destroyAllWindows()
        pass

    def update_tool_tip(self, index: int, error: bool = False) -> None:
        if error:
            # cv2.imshow(WINDOW_TOOLTIP, self.tool_tips[index + 4])
            self.render(WINDOW_TOOLTIP, self.tool_tips[index + 4])
        else:
            # cv2.imshow(WINDOW_TOOLTIP, self.tool_tips[index - 1])
            self.render(WINDOW_TOOLTIP, self.tool_tips[index - 1])


    def on_click(self, e) -> None:
        x = e.x
        y = e.y
        print(f'click - {x} {y}')
        x = x % self.width
        self.cursor = (x, y)

    def on_key(self, e) -> None:
        try:
            key = e.char
            self.key_process(key)
        except:
            return

    def key_listener(self, key: int) -> None:
        try:
            key = chr(key)
            self.key_process(key)
        except:
            return

    def key_process(self, key: str) -> None:
        print(f'key - {key}')
        if self.inquiry == "track":
            if "y" == key:
                logger.info("Initiating tracking..")
                # self.remove_mousecallback()
                # cv2.destroyWindow(WINDOW_CONFIGURATION)
                # cv2.destroyWindow(WINDOW_BINARY)
                # cv2.destroyWindow(WINDOW_TOOLTIP)

                self.render(WINDOW_TRACKING, self.bin_stock)
                # cv2.imshow(WINDOW_TRACKING, self.bin_stock)
                # cv2.moveWindow(WINDOW_TRACKING, 100, 100)

                self._state = "tracking"
                self.inquiry = "none"

                self.update = self.real_update

                config.engine.activate()

                return
            elif "n" == key:
                logger.info("Adjustments resumed.")
                self._state = "adjustment"
                self.inquiry = "none"
                return

        if self._state == "adjustment":
            if key == "p":
                config.engine.angle -= 3

            elif key == "o":
                config.engine.angle += 3

            elif "1" == key:
                try:
                    #config.engine.pupil = self.cursor
                    self.pupil_processor.reset(self.cursor)
                    self.pupil_ = self.pupil

                    self.update_tool_tip(4)

                    logger.info("Pupil selected.\nAdjust binarization via R/F (threshold) and T/G (smoothing).")
                except Exception as e:
                    self.update_tool_tip(3, True)
                    logger.info(f"pupil selection failed; {e}")

            elif "2" == key:
                try:

                    self.cr_processor_1.reset(self.cursor)
                    self.cr1_ = self.cr_1

                    self.current_cr_processor = self.cr_processor_1

                    self.update_tool_tip(2)

                    logger.info("Corneal reflex selected.\nAdjust binarization via W/S (threshold) and E/D (smoothing).")

                except Exception as e:
                    self.update_tool_tip(1, True)
                    logger.info(f"CR selection failed; {e}")

            elif "3" == key:
                try:
                    self.update_tool_tip(2)
                    self.cr_processor_2.reset(self.cursor)
                    self.cr2_ = self.cr_2

                    self.current_cr_processor = self.cr_processor_2

                    logger.info("\nCorneal reflex selected.")
                    logger.info("Adjust binarization via W/S (threshold) and E/D (smoothing).")

                except:
                    self.update_tool_tip(1, True)
                    logger.info("Hover and click on the corneal reflex, then press 3.")


            elif "z" == key:
                logger.info("Start tracking? (y/n)")
                self.inquiry = "track"

            elif "w" == key:
                self.current_cr_processor.binarythreshold += 1
                logger.info("Corneal reflex binarization threshold increased (to %s)." % self.current_cr_processor.binarythreshold)

            elif "s" == key:

                self.current_cr_processor.binarythreshold -= 1
                logger.info("Corneal reflex binarization threshold decreased (to %s)." % self.current_cr_processor.binarythreshold)

            elif "e" == key:
                self.current_cr_processor.blur = [x + 2 for x in self.current_cr_processor.blur]
                logger.info("Corneal reflex blurring increased (to %s)." % self.current_cr_processor.blur)

            elif "d" == key:
                if self.current_cr_processor.blur[0] > 1:
                    self.current_cr_processor.blur = [x - 2 for x in self.current_cr_processor.blur]
                logger.info("Corneal reflex blurring decreased (to %s)." % self.current_cr_processor.blur)

            elif "r" == key:
                self.pupil_processor.binarythreshold += 1
                logger.info("Pupil binarization threshold increased (to %s)." % self.pupil_processor.binarythreshold)
            elif "f" == key:

                self.pupil_processor.binarythreshold -= 1
                logger.info("Pupil binarization threshold decreased (to %s)." % self.pupil_processor.binarythreshold)

            elif "t" == key:

                self.pupil_processor.blur = [x + 2 for x in self.pupil_processor.blur]
                logger.info("Pupil blurring increased (to %s)." % self.pupil_processor.blur)

            elif "g" == key:
                if self.pupil_processor.blur[0] > 1:
                    self.pupil_processor.blur = [x - 2 for x in self.pupil_processor.blur]
                logger.info("Pupil blurring decreased (to %s)." % self.pupil_processor.blur)

        if "q" == key:
            # Terminate tracking
            config.engine.release()

    def arm(self, width: int, height: int) -> None:
        logger.info(f'Arming...')

        self.fps = np.round(1/config.arguments.fps, 2)
        self.pupil_processor = config.engine.pupil_processor

        self.cr_index = 0
        self.current_cr_processor = config.engine.cr_processor_1  # primary corneal reflection
        self.cr_processor_1 = config.engine.cr_processor_1
        self.cr_processor_2 = config.engine.cr_processor_2

        self.width, self.height = width, height
        self.binary_width = max(width, 300)
        self.binary_height = max(height, 200)

        def on_mouse_move(event):
            print("Mouse position: (%s %s)" % (event.x, event.y))
            return

        def on_click(event):
            print("Mouse position: (%s %s)" % (event.x, event.y))
            return

        # Initialize windows
        self.window = tk.Tk()
        self.window.title("Eyeloop")
        # self.window.rowconfigure(0, minsize=800, weight=1)
        # self.window.columnconfigure(1, minsize=1280, weight=1)

        window_tt = tk.Toplevel(self.window)
        window_tt.title("Eyeloop - Tooltips")
        window_tt.bind('<Button-1>', on_click)

        window_raw = tk.Toplevel(self.window)
        window_raw.title("Eyeloop - Raw image")
        window_raw.bind("<KeyRelease>", self.on_key)
        window_raw.bind('<Button-1>', self.on_click)

        window_bin = tk.Toplevel(self.window)
        window_bin.title("Eyeloop - Binarization")


        frm_raw = tk.Frame(self.window)
        frm_raw.configure(bg='red')
        frm_raw.grid(column=0, row=0)

        frm_binary = tk.Frame(self.window)
        frm_binary.configure(bg='blue')
        frm_binary.grid(column=1, row=0)


        self.img_raw = tk.Label(window_raw)
        self.img_raw.grid(column=0, row=0)
        self.img_binary = tk.Label(window_bin)
        self.img_binary.grid(column=0, row=0)
        self.img_tooltip = tk.Label(window_tt)
        self.img_tooltip.grid(column=0, row=0)

        self.images = {
            WINDOW_BINARY: self.img_binary,
            WINDOW_CONFIGURATION: self.img_raw,
            WINDOW_TOOLTIP: self.img_tooltip,
        }

        

        # -----

        # fourcc = cv2.VideoWriter_fourcc(*'MPEG')
        # output_vid = Path(config.file_manager.new_folderpath, "output.avi")
        # self.out = cv2.VideoWriter(str(output_vid), fourcc, 50.0, (self.width, self.height))

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

        # cv2.imshow(WINDOW_BINARY, np.vstack((self.bin_stock, self.bin_stock)))
        # cv2.imshow(WINDOW_CONFIGURATION, np.hstack((self.bin_stock, self.bin_stock)))
        # cv2.imshow(WINDOW_TOOLTIP, self.first_tool_tip)
        self.render(WINDOW_BINARY, np.vstack((self.bin_stock, self.bin_stock)))
        self.render(WINDOW_CONFIGURATION, np.hstack((self.bin_stock, self.bin_stock)))
        self.render(WINDOW_TOOLTIP, self.first_tool_tip)

        # cv2.moveWindow(WINDOW_BINARY, 105 + width * 2, 100)
        # cv2.moveWindow(WINDOW_CONFIGURATION, 100, 100)
        # cv2.moveWindow(WINDOW_TOOLTIP, 100, 1000 + height + 100)

    def render(self, widget_name, data):
        img_widget = self.images[widget_name]
        if (not img_widget):
            return

        img = Image.fromarray(data)
        img_tk = ImageTk.PhotoImage(img)
        img_widget.configure(image=img_tk)
        img_widget.image = img_tk

        self.window.update()


    def place_cross(self, source: np.ndarray, point: tuple, color: tuple) -> None:
        try:
            source[to_int(point[1] - 3):to_int(point[1] + 4), to_int(point[0])] = color
            source[to_int(point[1]), to_int(point[0] - 3):to_int(point[0] + 4)] = color
        except:
            pass


    def update_record(self, frame_preview) -> None:
        # cv2.imshow("Recording", frame_preview)
        # if cv2.waitKey(1) == ord('q'):
        #     config.engine.release()
        pass

    def skip_track(self):
        self.update = self.real_update


    def pupil(self, source_rgb):
        try:
            pupil_center, pupil_width, pupil_height, pupil_angle = self.pupil_processor.fit_model.params

            cv2.ellipse(source_rgb, tuple_int(pupil_center), tuple_int((pupil_width, pupil_height)), pupil_angle, 0, 360, red, 1)
            self.place_cross(source_rgb, pupil_center, red)
            return True
        except Exception as e:
            logger.info(f"pupil not found: {e}")
            return False

    def cr_1(self, source_rgb):
        try:
            #cr_center, cr_width, cr_height, cr_angle = params = self.cr_processor_1.fit_model.params

            #cv2.ellipse(source_rgb, tuple_int(cr_center), tuple_int((cr_width, cr_height)), cr_angle, 0, 360, green, 1)
            self.place_cross(source_rgb, self.cr_processor_1.center, green)
            return True
        except Exception as e:
            logger.info(f"cr1 func: {e}")
            return False

    def cr_2(self, source_rgb):
        try:
            #cr_center, cr_width, cr_height, cr_angle = params = self.cr_processor_2.fit_model.params

            #cv2.ellipse(source_rgb, tuple_int(cr_center), tuple_int((cr_width, cr_height)), cr_angle, 0, 360, green, 1)
            self.place_cross(source_rgb, self.cr_processor_2.center, green)
            return True
        except Exception as e:
            logger.info(f"cr2 func: {e}")
            return False

    def adj_update(self, img):
        source_rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        #if self.pupil_(source_rgb):
        self.bin_P = self.bin_stock.copy()

        if self.pupil_(source_rgb):
            self.bin_P[0:20, 0:self.binary_width] = self.bin_stock_txt_selected
        else:
            self.bin_P[0:20, 0:self.binary_width] = self.bin_stock_txt

        #self.bin_CR = self.bin_stock.copy()

        try:
            pupil_area = self.pupil_processor.source

            offset_y = int((self.binary_height - pupil_area.shape[0]) / 2)
            offset_x = int((self.binary_width - pupil_area.shape[1]) / 2)
            self.bin_P[offset_y:min(offset_y + pupil_area.shape[0], self.binary_height),
            offset_x:min(offset_x + pupil_area.shape[1], self.binary_width)] = pupil_area
        except:
            pass

        self.cr1_(source_rgb)
        self.cr2_(source_rgb)

        self.bin_CR = self.bin_stock.copy()

        try:
            cr_area = self.current_cr_processor.source
            offset_y = int((self.binary_height - cr_area.shape[0]) / 2)
            offset_x = int((self.binary_width - cr_area.shape[1]) / 2)
            self.bin_CR[offset_y:min(offset_y + cr_area.shape[0], self.binary_height),
            offset_x:min(offset_x + cr_area.shape[1], self.binary_width)] = cr_area
            self.bin_CR[0:20, 0:self.binary_width] = self.crstock_txt_selected
        except:
            self.bin_CR[0:20, 0:self.binary_width] = self.crstock_txt
            pass


        # #logger.info(cr_area)

        # cv2.imshow(WINDOW_BINARY, np.vstack((self.bin_P, self.bin_CR)))
        # cv2.imshow(WINDOW_CONFIGURATION, source_rgb)
        # #self.out.write(source_rgb)
        self.render(WINDOW_BINARY, np.vstack((self.bin_P, self.bin_CR)))
        self.render(WINDOW_CONFIGURATION, source_rgb)


        # key = cv2.waitKey(CV_IMAGE_PERIOD)
        # self.key_listener(key)
        if self.first_run:
            # cv2.destroyAllWindows()
            self.first_run = False


    def real_update(self, img) -> None:
        source_rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        self.pupil_(source_rgb)
        self.cr1_(source_rgb)
        self.cr2_(source_rgb)

        # cv2.imshow(WINDOW_TRACKING, source_rgb)
        self.render(WINDOW_TRACKING, source_rgb)

        threading.Timer(self.fps, self.skip_track).start() #run feed every n secs (n=1)
        self.update = lambda _: None

        # if cv2.waitKey(1) == ord("q"):
        #     config.engine.release()
