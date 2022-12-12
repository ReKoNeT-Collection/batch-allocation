from typing import List

import numpy as np
from scipy.optimize import linprog
from werkzeug.exceptions import InternalServerError


def solve_allocation(main_fulfillments: np.ndarray, mating_fulfillments: np.ndarray) -> List[int]:
    """
    Solves the allocation problem using the simplex algorithm.

    Parameters
    ----------
    main_fulfillments
        list of main fulfillment values (averaged and as a row-vector with dim=2).
    mating_fulfillments
        list of mating fulfillment values (averaged and as a row-vector with dim=2).

    Returns
    -------
    List[int]
        index order for mating component.
    """
    n = main_fulfillments.shape[1]
    ones = np.ones((n, 1))
    # Cost matrix
    F = main_fulfillments.T * ones + mating_fulfillments * ones.T

    # Simplex Parameters
    c = abs(F.flatten())
    A_eq = []
    for i in range(n):
        A_eq.append([0] * i * n + [1] * n + [0] * (n - i - 1) * n)
        A_eq.append(([0] * i + [1] + [0] * (n - i - 1)) * n)
    b_eq = np.ones(n * 2)

    # Apply Simplex
    res = linprog(c, None, None, A_eq, b_eq, method="simplex")

    # Raise exception if simplex failed
    if not res.success:
        raise InternalServerError(res.message)
    # Transform result variables (x_ij=1) into a list of indices
    return np.array(res.x).reshape((n, n)).nonzero()[1].tolist()
