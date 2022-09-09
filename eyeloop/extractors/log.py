import json
from pathlib import Path

from eyeloop.extractors.extractor import Extractor


class LogExtractor(Extractor):
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.filepath = Path(output_dir, f"output.json")
        self.file = open(self.filepath, "a")

    def activate(self):
        return

    def fetch(self, core):
        try:
            self.file.write(json.dumps(core.dataout) + "\n")

        except ValueError:
            pass

    def release(self, core):
        try:
            self.file.write(json.dumps(core.dataout) + "\n")
            self.file.close()
        except ValueError:
            pass

        self.fetch(core)
