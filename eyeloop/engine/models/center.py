import numpy as np


# TODO(aelsen) this was never fully implemented
class Center():
    def fit(self, r):
        self.params = tuple(np.mean(r, axis = 0))
        return self.params