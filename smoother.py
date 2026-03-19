# smoother.py

class PositionSmoother:
    def __init__(self, alpha=0.2):
        """
        alpha : smoothing factor (0 < alpha <= 1)
        lower value = more smoothing, less jitter
        """
        self.alpha = alpha
        self.prev_x = None
        self.prev_y = None

    def smooth(self, x, y):
        """
        Apply exponential smoothing to (x, y) position
        """

        # First frame: no previous value
        if self.prev_x is None or self.prev_y is None:
            self.prev_x, self.prev_y = x, y
            return x, y

        sx = int(self.prev_x + self.alpha * (x - self.prev_x))
        sy = int(self.prev_y + self.alpha * (y - self.prev_y))

        self.prev_x, self.prev_y = sx, sy
        return sx, sy

    def reset(self):
        """
        Reset smoother (useful when hand disappears)
        """
        self.prev_x = None
        self.prev_y = None
