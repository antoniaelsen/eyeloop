import importlib
import logging
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
import os
import numpy as np

import eyeloop.config as config
from eyeloop.engine.engine import Engine
from eyeloop.extractors.log import LogExtractor
from eyeloop.extractors.fps import FpsExtractor
from eyeloop.guis.minimum.minimum_gui import GUI
from eyeloop.sources.cv_offline import CvOfflineSource
from eyeloop.sources.cv_stream import CvStreamSource
from eyeloop.sources.pylon import PylonSource
from eyeloop.utilities.argument_parser import Arguments
from eyeloop.utilities.file_manager import File_Manager
from eyeloop.utilities.format_print import welcome
from eyeloop.utilities.shared_logging import setup_logging

EYELOOP_DIR = Path(__file__).parent
PROJECT_DIR = EYELOOP_DIR.parent

logger = logging.getLogger(__name__)


class EyeLoop:
    """
    EyeLoop is a Python 3-based eye-tracker tailored specifically to dynamic, closed-loop experiments on consumer-grade hardware.
    Lead developer: Simon Arvin
    Git: https://github.com/simonarvin/eyeloop
    """

    def __init__(self, args, logger=None):
        welcome()

        self.engine = None
        self.gui = None
        self.source = None

        config.arguments = Arguments(args)
        config.file_manager = File_Manager(output_root=config.arguments.output_dir, img_format = config.arguments.img_format)
        if logger is None:
            logger, logger_filename = setup_logging(log_dir=config.file_manager.new_folderpath, module_name="run_eyeloop")

        self.init()

    def load_extractors(self, file_path):
        fps_counter = FpsExtractor()
        log = LogExtractor(config.file_manager.new_folderpath)
        extractors = { "FpsExtractor": fps_counter, "LogExtractor": log }

        if file_path == "p":
            root = tk.Tk()
            root.withdraw()
            file_path = filedialog.askopenfilename()

        if file_path != "":
            try:
                logger.info(f"including {file_path}")
                sys.path.append(os.path.dirname(file_path))
                extractor_module_name = os.path.basename(file_path).split(".")[0]

                logger.info(f'importing extractor {extractor_module_name}')
                extractor_module = importlib.import_module()
                extractors[extractor_module_name] = extractor_module

            except Exception as e:
                logger.info(f"extractors not included, {e}")

        return extractors

    def init(self):
        gui = None
        if (config.arguments.gui == "minimal"):
            gui = GUI

        source = None
        if (config.arguments.video != ""):
            source = CvOfflineSource
        else:
            source = PylonSource if config.arguments.source == "pylon" else CvStreamSource

        self.engine = Engine(source=source, gui=gui)
        self.engine.load_extractors(self.load_extractors(config.arguments.extractors))
        self.engine.activate()
        self.engine.run()


def main():
    EyeLoop(sys.argv[1:], logger=None)


if __name__ == '__main__':
    main()
