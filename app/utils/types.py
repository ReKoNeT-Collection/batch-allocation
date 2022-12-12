from typing import Dict, Tuple

import numpy as np

# Characteristic values of a single component 
Component = Dict[str, float]

# Y-axis values and X-axis edges of a histogram
Histogram = Tuple[np.ndarray, np.ndarray]
