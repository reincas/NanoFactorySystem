import numpy as np
import typing

class simple_DOE():
    def __init__(self, rows: int, columns: int, z_profile):
        self.rows = rows
        self.columns = columns
        self.z_profile = np.asarray(z_profile)

        try:(rows, columns) == self.z_profile.shape
        except: Exception("Initialisation-Data don't match!")
