import math
import time
import eyeloop.config as config
from eyeloop.extractors.extractor import Extractor

class FpsExtractor(Extractor):
    def __init__(self):
        self.last_frame = None
        self.last_time = None

    def activate(self):
        self.last_frame = 0
        self.last_time = time.time()

    def fetch(self, engine):
        delta = time.time() - self.last_time
        frames = engine.frame_i - self.last_frame
        fps = math.floor(frames / delta)
        self.last_time = time.time()
        self.last_frame = engine.frame_i
        print(f"Processing {fps} frames per second.")
        return fps

    def release(self, core):
        self.thread.cancel()
