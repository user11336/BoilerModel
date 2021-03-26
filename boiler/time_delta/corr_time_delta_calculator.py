import logging

import numpy as np
from scipy.signal import correlate


class CorrTimeDeltaCalculator:

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.debug("Creating instance")

    # noinspection PyMethodMayBeStatic
    def find_lag(self, x: np.ndarray, y: np.ndarray) -> int:
        self._logger.debug("Lag calculation is requested")

        x -= x.mean()
        x /= x.std()

        y -= y.mean()
        y /= y.std()

        corr = correlate(y, x)
        lag = corr.argmax() + 1 - len(y)

        return lag