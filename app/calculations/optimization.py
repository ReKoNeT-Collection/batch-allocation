from itertools import permutations
from typing import List, Callable, Any, Tuple

import numpy as np
from tqdm import tqdm


def brute_force(arrays: Tuple[List[any], List[any]], scalar_function: Callable[[Any, Any], float]) -> Tuple[
    List[int], List[float]]:
    """
    Uses brute-force optimization to find the best allocation with a minimal scalar value.

    Parameters
    ----------
    arrays
        two different lists, whose elements should be evaluated against each other.
    scalar_function
        function which evaluates two given values and returns a scalar.

    Returns
    -------
    List[int]
        optimal allocation sequence.
    List[float]
        optimal scalar value.
    """
    n_batches_a = len(arrays[0])
    n_batches_b = len(arrays[1])
    # Keep track of the best value and best permutation
    best_val = [np.inf]
    best_perm = list(range(n_batches_b))
    # Iterate over all possible permutations

    for perm_b in tqdm(list(permutations(best_perm))):
        current_val = []
        # Iterate over all allocations of the current permutation
        for index_a, index_b in enumerate(perm_b):
            if index_a >= n_batches_a:
                break
            val_a = arrays[0][index_a]
            val_b = arrays[1][index_b]
            scalar = scalar_function(val_a, val_b)
            current_val.append(scalar)

        # Check if current permutation is better then the previous ones
        if sum(current_val) < sum(best_val):
            best_val = current_val
            best_perm = list(perm_b)[:n_batches_a]
    return best_perm, best_val
