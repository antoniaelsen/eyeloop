# original script: https://github.com/AlliedToasters/circle-fit
# original script author: Michael Klear/AlliedToasters
# hyper-fit doi: https://doi.org/10.1016/j.csda.2010.12.012
# hyper-fit authors: Kenichi Kanatani & Prasanna Rangarajan

import numpy as np
import logging
np.seterr('raise')

from eyeloop.engine.models.model import Model
from eyeloop.utilities.general_operations import tuple_int
logger = logging.getLogger(__name__)


class Circle(Model):
    def __init__(self):
        super().__init__()

    def fit(self, r) -> tuple:
        return self.hyper_fit(r)

    def hyper_fit(self, r: float) -> tuple:
        """
        Fits coords to circle using hyperfit algorithm.
        Inputs:
            - coords, list or numpy array with len > 2 of the form:
            [
        [x_coord, y_coord],
        ...,
        [x_coord, y_coord]
        ]
            or numpy array of shape (n, 2)
        Outputs:
            - xc : x-coordinate of solution center (float)
            - yc : y-coordinate of solution center (float)
            - R : Radius of solution (float)
            - residu : s, sigma - variance of data wrt solution (float)
        """
        X, Y = r[:,0], r[:,1]
        n = X.shape[0]

        mean_X = np.mean(X)
        mean_Y = np.mean(Y)
        Xi = X - mean_X
        Yi = Y - mean_Y
        Xi_sq = Xi**2
        Yi_sq = Yi**2
        Zi = Xi_sq + Yi_sq

        # compute moments

        Mxy = np.sum(Xi * Yi) / n
        Mxx = np.sum(Xi_sq) / n
        Myy = np.sum(Yi_sq) / n
        Mxz = np.sum(Xi * Zi) / n
        Myz = np.sum(Yi * Zi) / n

        Mz = Mxx + Myy

        # finding the root of the characteristic polynomial
        det = (Mxx * Myy - Mxy**2) * 2
        try:
            Xcenter = (Mxz * Myy - Myz * Mxy) / det
            Ycenter = (Myz * Mxx - Mxz * Mxy) / det
        except:
            return False

        x = Xcenter + mean_X
        y = Ycenter + mean_Y
        center = (x, y)
        r = np.sqrt(Xcenter ** 2 + Ycenter ** 2 + Mz)
        self.params = (center, r, r, 0)

        return center
