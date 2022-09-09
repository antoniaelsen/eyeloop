import argparse
from pathlib import Path

EYELOOP_DIR = Path(__file__).parent.parent
PROJECT_DIR = EYELOOP_DIR.parent
DEFAULT_FPS = 100


class Arguments:
    """
    Parses all command-line arguments and config.pupt parameters.
    """

    def __init__(self, args) -> None:
        self.config = None
        self.markers = None
        self.video = None
        self.output_dir = None
        self.source = None
        self.scale = None
        self.tracking = None
        self.model = None

        self.parsed_args = self.parse_args(args)
        self.build_config(parsed_args=self.parsed_args)

    @staticmethod
    def parse_args(args):
        parser = argparse.ArgumentParser(description='Help list')
        parser.add_argument("-b", "--blink", default="", type=str,
                            help="Load blink calibration file (.npy)")

        parser.add_argument("-c", "--config", default="0", type=str, help="Input a .pupt config file (preset).")

        parser.add_argument("-fps", "--framerate", default=DEFAULT_FPS, type=float,
                            help=f"How often to update preview window  (default = {DEFAULT_FPS} / second)")

        parser.add_argument("-d", "--device", default=0, type=str,
                            help="Camera device id, if streaming")

        parser.add_argument("-g", "--gui", default="minimal", type=str,
                            help="Run the application with the chosen gui (minimal)")

        parser.add_argument("-m", "--model", default="ellipsoid", type=str,
                            help="Set pupil model type (circular; ellipsoid = default).")

        parser.add_argument("-o", "--output_dir", default=str(PROJECT_DIR.joinpath("data").absolute()), type=str,
                            help="Specify output destination.")

        parser.add_argument("-p", "--params", default="", type=str,
                            help="Load pupil/cr parameter file (.npy)")

        parser.add_argument("-r", "--rotation", default=0, type=int,
                            help="Enable online rotation (yes/no, 1/0; default = 0)")

        parser.add_argument("-s", "--scale", default=1, type=float, help="Scale the stream (default: 1; 0-1)")

        parser.add_argument("-v", "--video", default="", type=str,
                            help="Input a video sequence for offline processing.")

        parser.add_argument("-x", "--extractors", default="", type=str,
                            help="Set file-path of extractor Python file. p = start file prompt.")

        parser.add_argument("--clear", default=0, type=float,
                            help="Clear parameters (yes/no, 1/0) - default = 0")

        parser.add_argument("--img_format", default="frame_$.jpg", type=str,
                            help="Set img format for import (default: frame_$.jpg where $ = 1, 2,...)")

        parser.add_argument("--markers", default=0, type=int,
                            help="Enable/disable artifact removing markers (0: disable/default; 1: enable)")

        parser.add_argument("--save", default=1, type=int,
                            help="Save video feed or not (yes/no, 1/0; default = 1)")

        parser.add_argument("--source", default="cv", type=str,
                            help="Set source stream (cv, pylon, vimba, ...)")

        parser.add_argument("--tracking", default=1, type=int,
                            help="Enable/disable tracking (1/enabled: default).")



        return parser.parse_args(args)

    def build_config(self, parsed_args):
        self.config = parsed_args.config

        if self.config != "0":  # config file was set.
            self.parse_config(self.config)

        self.blink_calibration_path = parsed_args.blink
        self.clear = parsed_args.clear
        self.device = parsed_args.device
        self.extractors = parsed_args.extractors
        self.fps = parsed_args.framerate
        self.gui = parsed_args.gui
        self.img_format = parsed_args.img_format
        self.markers = parsed_args.markers
        self.model = parsed_args.model.lower()
        self.output_dir = Path(parsed_args.output_dir.strip("\'\"")).absolute()
        self.params = parsed_args.params
        self.rotation = parsed_args.rotation
        self.save = parsed_args.save
        self.scale = parsed_args.scale
        self.source = parsed_args.source.lower()
        self.tracking = parsed_args.tracking
        self.video = "" if parsed_args.video == "" else Path(parsed_args.video.strip("\'\"")).absolute()  # Handle quotes used in argument


    def parse_config(self, config: str) -> None:
        with open(config, "r") as content:
            print("Loading config preset: ", config)
            for line in content:
                split = line.split("=")
                parameter = split[0]
                parameter = split[1].rstrip("\n").split("\"")

                if len(parameter) != 1:
                    parameter = parameter[1]
                else:
                    parameter = parameter[0]

                if parameter == "video":
                    print("Video preset: ", parameter)
                    self.video = parameter

                elif parameter == "dest":
                    print("Destination preset: ", parameter)
                    self.output_dir = Path(parameter).absolute()

                elif parameter == "import":
                    print("Source preset: ", parameter)
                    self.source = parameter

                elif parameter == "model":
                    print("Model preset: ", parameter)
                    self.model = parameter

                elif parameter == "markers":
                    print("Markers preset: ", parameter)
                    self.markers = parameter

                elif parameter == "extractors":
                    print("Extractors preset: ", parameter)
                    self.extractors = parameter

                elif parameter == "img_format":
                    print("img_format preset: ", parameter)
                    self.img_format = parameter

                elif parameter == "save":
                    print("save preset: ", parameter)
                    self.save = parameter

                elif parameter == "rotation":
                    print("rotation preset: ", parameter)
                    self.rotation = parameter

                elif parameter == "framerate":
                    print("framerate preset: ", parameter)
                    self.fps = parameter

            print("")
