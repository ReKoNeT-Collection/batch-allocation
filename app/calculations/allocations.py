from typing import List

from werkzeug.exceptions import BadRequest

from app.calculations.allocation.convolution_methods import *
from app.calculations.allocation.optimization_algorithms import *
from app.calculations.allocation.valuation_methods import *
from app.utils.qc_strategy import QcStrategy


def allocate(components: Tuple[List[pd.DataFrame], List[pd.DataFrame]],
             qc_strategy: Optional[QcStrategy] = None,
             valuation_method: str = "mean", algorithm: str = "brute_force",
             settings_dict: Dict[str, Any] = None) -> Tuple[List[int], List[float]]:
    """
    Allocates all batches of two or more component types.

    Parameters
    ----------
    components
        Component types that should be allocated to each other.
        Every component type consists of a list of batches,
        and each batch consists of a list distributions for each test point.
    qc_strategy
        Tells how two distributions should be convoluted.
    valuation_method
        Tells how two distributions are converted into a single scalar value,
        i.e. how a given allocation should be valuated.
        One of "mean", "mean_std", "cpk", "qualityloss".
    algorithm
        Optimization algorithm.
        Currently, only "brute_force" is supported.
    settings_dict
        config name etc.

    Returns
    -------
    List[int]
        optimal allocation sequence.
    List[float]
        the optimal scalar values.
    """
    ####################################################################
    # INPUT VALIDATION                                                 #
    ####################################################################
    if algorithm == "brute_force" and len(components) > 2:
        raise BadRequest("Brute force algorithm only supports two components")
    if algorithm not in supported_algorithms:
        raise BadRequest(
            "Only " + str(supported_algorithms.keys) + " algorithms supported"
        )
    if qc_strategy not in supported_convolution_methods:
        raise BadRequest(
            "Only " + str(supported_convolution_methods.keys) + " convolution methods supported"
        )
    if valuation_method not in supported_valuation_methods:
        raise BadRequest("Only " + str(supported_valuation_methods.keys) + " valuation methods supported")

    ####################################################################
    # APPLY SELECTED ALGORITHM WITH THE SELECTED METHOD                #
    ####################################################################

    # optimization algorithm could be to try out all possible combinations,
    # or something more sophisticated like genetic optimization
    optimization_algorithm = supported_algorithms[algorithm]
    # tells how two components are assembled and what the
    # resulting functional fulfillment will be
    convolution_method = supported_convolution_methods[qc_strategy]
    # evaluates a given combination using mean, std, or something else
    valuation_method = supported_valuation_methods[valuation_method]

    # call optimization algorithm
    optimal_permutation, scalar = optimization_algorithm(components, convolution_method, valuation_method,
                                                         settings_dict or {})
    return optimal_permutation, scalar


def allocate_complete(components_batches: List[List[List[pd.DataFrame]]], qc_strategy: Optional[QcStrategy] = None,
                      valuation_method: str = "mean", algorithm: str = "brute_force",
                      settings_dict: Dict[str, Any] = None) -> List[Tuple[int, List[int]]]:
    """
    Iteratively allocates all batches and then for every batch all klts.

    Parameters
    ----------
    components_batches
        For every component, a list of batches, which consists of a list of klts,
        which consists of characteristic values.
    qc_strategy
        Tells how two distributions should be convoluted.
    valuation_method
        Tells how two distributions are converted into a single scalar value,
        i.e. how a given allocation should be valuated.
        One of "mean", "mean_std", "cpk", "qualityloss".
    algorithm
        Optimization algorithm.
        Currently, only "brute_force" is supported.
    settings_dict
        config name etc.

    Returns
    -------
    List[Tuple[int, List[int]]]
        Every entry of this list represents a) the allocated batch and b) the allocated klts for the allocated batch.
    """
    # concat data frames on batch level:
    components_concat = [[pd.concat(batch).reset_index(drop=True) for batch in component] for component in
                         components_batches]
    # calculate optimal batch allocation
    # noinspection PyTypeChecker
    optimal_permutation, _ = allocate(components_concat, qc_strategy, valuation_method, algorithm, settings_dict)
    # reorder second component according to optimal allocation
    components_batches[1] = [components_batches[1][index] for index in optimal_permutation]

    result = []
    for base_batch_idx, allocated_batch_idx in zip(range(len(optimal_permutation)), optimal_permutation):
        base_klts = components_batches[0][base_batch_idx]
        comparison_klts = components_batches[1][allocated_batch_idx]
        # calculate optimal klt allocation
        # noinspection PyTypeChecker
        optimal_klt_permutation, _ = allocate([base_klts, comparison_klts], qc_strategy, valuation_method, algorithm,
                                              settings_dict)
        result.append((allocated_batch_idx, optimal_klt_permutation))

    return result
