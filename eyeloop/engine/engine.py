from enum import Enum
import logging
import time
from os.path import dirname, abspath
import glob, os

import eyeloop.config as config
from eyeloop.constants.engine_constants import *
from eyeloop.engine.processor import CornealReflection, Pupil
from eyeloop.sources.source import Source


logger = logging.getLogger(__name__)
PARAMS_DIR = f"{dirname(dirname(abspath(__file__)))}/engine/params"


class State(Enum):
    TRACK = 0
    RECORD = 1

class Engine:
    def __init__(self, source: Source, gui = None):
        self.source = source(on_frame=self.on_frame)
        self.gui = None
        if (gui is not None):
            self.gui = gui(on_angle=self.update_angle, on_quit=self.release)

        self.active = True
        self.extractors = []
        self.extractor_data = []
        self.state = State.RECORD if config.arguments.tracking == 0 else State.TRACK
        self.blink_calibrated = False
        self.blink_active = False
        self.blink = np.zeros(300, dtype=np.float64)
        self.blink_i = 0

        self.frame_i = 0
        self.angle = 0
        self.pupil_processor = Pupil()
        self.cr_processors = [CornealReflection(n = x) for x in range(2)]

    def activate(self) -> None:
        """
        Activates all extractors.
        The extractor activate() function is optional.
        """
        for key, extractor in self.extractors.items():
            try:
                extractor.activate()
            except AttributeError:
                logger.warning(f"Extractor {key} has no activate() method")


        self.arm()

    def release(self) -> None:
        """
        Releases/deactivates all running process, i.e., importers, extractors.
        """

        self.active = False
        param_dict = {
            "pupil" : [self.pupil_processor.binarythreshold, self.pupil_processor.blur],
        }
        for i in range(len(self.cr_processors)):
            param_dict[f'cr_{i}'] = [self.cr_processors[i].binarythreshold, self.cr_processors[i].blur]

        path = f"{config.file_manager.new_folderpath}/params_{self.dataout['time']}.npy"
        np.save(path, param_dict)
        print("Parameters saved")

        self.source.release()
        if (self.gui is not None):
            self.gui.release()

        for extractor in self.extractors:
            try:
                extractor.release(self)
            except AttributeError:
                logger.warning(f"Extractor {extractor} has no release() method")
            else:
                pass

    def load_extractors(self, extractors: dict = None) -> None:
        if extractors is None:
            extractors = {}
            return
        logger.info(f"loading extractors: {extractors}")
        self.extractors = extractors
        self.extractor_data = {}
        for key in self.extractors.keys():
            self.extractor_data[key] = None

    def run_extractors(self) -> None:
        """
        Calls all extractors at the end of each time-step.
        Assign additional extractors to core engine via eyeloop.py.
        """

        for key, value in self.extractors.items():
            try:
                self.extractor_data[key] = value.fetch(self)
            except Exception as e:
                print("Error in module class: {}".format(key))
                print("Error message: ", e)

    def construct_param_dict(self):
        param_dict = { "pupil" : [self.pupil_processor.binarythreshold, self.pupil_processor.blur] }
        for i in range(len(self.cr_processors)):
            param_dict[f'cr_{i}'] = [self.cr_processors[i].binarythreshold, self.cr_processors[i].blur]
        return param_dict

    def update_angle(self, inc):
        self.angle += inc
        self.source.angle = self.angle # TODO(aelsen) not great

    def arm(self) -> None:
        (width, height), image = self.source.init()
        self.source.arm(width, height, image)
        if (self.gui is not None):
            self.gui.arm(
                (width, height),
                self.pupil_processor,
                self.cr_processors
            )
        self.center = (width//2, height//2)
        self.width, self.height = width, height

        self.on_frame(image)

        if config.arguments.blink_calibration_path != "":
            self.blink = np.load(config.arguments.blink_calibration_path)
            self.blink_calibrated = True
            logger.info("(success) blink calibration loaded")

        if config.arguments.clear == False or config.arguments.params != "":
            try:
                if config.arguments.params != "":
                    latest_params = max(glob.glob(config.arguments.params), key=os.path.getctime)
                    print(config.arguments.params + " loaded")

                else:
                    latest_params = max(glob.glob(PARAMS_DIR + "/*.npy"), key=os.path.getctime)

                params_ = np.load(latest_params, allow_pickle=True).tolist()

                self.pupil_processor.binarythreshold, self.pupil_processor.blur = params_["pupil"][0], params_["pupil"][1]
                for i in range(len(self.cr_processors)):
                    self.cr_processors[i].binarythreshold, self.cr_processors[i].blur = params_[f'cr_{i}'][0], params_[f'cr_{i}'][1]

                logger.warn("(!) Parameters reloaded. Run --clear 1 to prevent this.")
                param_dict = self.construct_param_dict()
                logger.info(f"loaded parameters:\n{param_dict}")

            except:
                pass

        filtered_image = image[np.logical_and((image < 220), (image > 30))]

        self.pupil_processor.set_dimensions((width, height))
        self.pupil_processor.binarythreshold = np.min(filtered_image) * 1 + np.median(filtered_image) * .1 # + 50
        for i in range(len(self.cr_processors)):
            self.cr_processors[i].set_dimensions((width, height))
            self.cr_processors[i].binarythreshold = float(np.min(filtered_image)) * .7 + 150

        param_dict = self.construct_param_dict()
        logger.info(f"loaded parameters:\n{param_dict}")

    def blink_sampled(self, mean):
        if self.blink_i % 20 == 0:
            print(f"Calibrating blink detector - {round(self.blink_i / self.blink.shape[0] * 100, 1)}%")

        if (self.blink_i == self.blink.shape[0]):
            logger.info("Blink detection calibrated")
            path = f"{config.file_manager.new_folderpath}/blink_calibration_path_{self.dataout['time']}.npy"
            np.save(path, self.blink)
            print(f" - calibration file saved to {path}")
            self.blink_calibrated = True
            return

        self.blink[self.blink_i] = mean
        self.blink_i += 1

    def on_frame(self, frame) -> None:
        self.frame_i += 1

        if (self.active is False):
            return

        if (self.state == State.RECORD):
            self.record(frame)
        else:
            self.track(frame)

        self.run_extractors()
        if (self.gui is not None):
            self.gui.update(frame, self.extractor_data)

    def run(self) -> None:
        self.source.route()

    def record(self, frame) -> None:
        """
        Runs Core engine in record mode. Timestamps all frames in data output log.
        """
        self.dataout = { "time": time.time() }

    def track(self, frame) -> None:
        """
        Executes the tracking algorithm on the pupil and corneal reflections.
        First, blinking is analyzed.
        Second, corneal reflections are detected.
        Third, corneal reflections are inverted at pupillary overlap.
        Fourth, pupil is detected.
        Finally, data is logged and extractors are run.
        """
        self.dataout = {
            "time": time.time()
        }
        mean_img = np.mean(frame)

        if (not self.blink_calibrated):
            self.blink_sampled(mean_img)
            return

        # if np.abs(mean_img - np.mean(self.blink[np.nonzero(self.blink)])) > 10:
        mean_blink = np.mean(self.blink)
        is_blinking = np.abs(mean_img - mean_blink) > 10
        # blinks_nonzero = self.blink[np.nonzero(self.blink)]
        # if np.abs(mean_img - np.mean(blinks_nonzero)) > 10:
        if is_blinking:
            self.dataout["blink"] = 1
            self.pupil_processor.fit_model.params = None
            if (not self.blink_active):
                self.blink_active = True
                logger.info("Blink started.")
        else:
            if (self.blink_active):
                self.blink_active = False
                logger.info("Blink over.")

            self.dataout["pupil"] = self.pupil_processor.track(frame)
            for i in range(len(self.cr_processors)):
                self.dataout[f"cr_{i}"] = self.cr_processors[i].track(frame)
