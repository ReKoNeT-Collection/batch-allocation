from collections import defaultdict
from typing import List, Tuple, Dict

import numpy as np
import pandas as pd
from flask import current_app as app

from app.calculations import simplex
from app.calculations.functionalmodel import get_function, get_batch_function
from app.calculations.math import histedges_equalN
from app.utils.qc_strategy import QcStrategy
from app.utils.requests import get_tolerances
from app.utils.types import Component


def simulate_assembly(qc_strategy: QcStrategy,
                      main_components_df: pd.DataFrame,
                      mating_components_df: pd.DataFrame,
                      config: str
                      ) -> Tuple[pd.DataFrame, Dict[str, any]]:
    """
    Simulates the assembly of two component batches.

    Assembly is assumed to be FIFO for the main components.
    Depending on the quality control strategy, the mating component will be selected differently.

    Parameters
    ----------
    qc_strategy
        quality control strategy.
    main_components_df
        a pandas data frame where the columns represent the characteristic values and each row is a single entry.
    mating_components_df
        a pandas data frame where the columns represent the characteristic values and each row is a single entry.
    config
        name of the configuration that should be used for the functional model.

    Returns
    -------
    pd.DataFrame
        functional fulfillments of resulting (convoluted) assembled components.
    Dict[str, any]
        statistics about the simulated assembly.
    """
    assert len(main_components_df) == len(
        mating_components_df), f"{len(main_components_df)} != {len(mating_components_df)}"

    # various statistics, depending on the selected quality strategy
    stats = {}
    # number of bins for selective assembly
    nbin = 2

    ##########################################
    # PREPARATION FOR SOME QUALITY STRATEGIES
    ##########################################

    def get_avg_fulfillment(fulfillments: List[float]) -> float:
        """
        Calculates the weighted average of the given functional fulfillments.

        Parameters
        ----------
        fulfillments
            functional fulfillments of one component.

        Returns
        -------
        float
            weighted average
        """
        weights = app.config[config]["TestPointWeights"]
        return np.average(fulfillments, weights=weights)

    # calculate the fulfillments for all components
    main_fulfillments = get_batch_function(main_components_df, config, True)
    mating_fulfillments = get_batch_function(mating_components_df, config, True)

    # sort main components by their fulfillments in ascending order, mating in descending order
    if qc_strategy == QcStrategy.ascending_descending:
        main_fulfillments = main_fulfillments.sort_values("weighted")
        mating_fulfillments = mating_fulfillments.sort_values("weighted", ascending=False)
        main_components_df = main_components_df.reindex(main_fulfillments.index)
        mating_components_df = mating_components_df.reindex(mating_fulfillments.index)
    # only regard a fixed group at once when sorting -> sort subsets
    if qc_strategy == QcStrategy.ascending_descending_grouped:
        GROUP_COUNT = 12
        main_index = []
        mating_index = []
        for i in range(0, len(main_components_df), GROUP_COUNT):
            main_index.extend(main_fulfillments[i:i + GROUP_COUNT].sort_values("weighted").index.tolist())
            mating_index.extend(
                mating_fulfillments[i:i + GROUP_COUNT].sort_values("weighted", ascending=False).index.tolist())
        main_components_df = main_components_df.reindex(main_index)
        mating_components_df = mating_components_df.reindex(mating_index)

    #
    main_components: List[Component] = list(main_components_df.to_dict(orient="index").values())
    mating_components: List[Component] = list(mating_components_df.to_dict(orient="index").values())

    # run the Simplex algorithm
    if qc_strategy == QcStrategy.individual_assembly_simplex:
        main_fulfillments = np.expand_dims(main_fulfillments["weighted"], axis=0)
        mating_fulfillments = np.expand_dims(mating_fulfillments["weighted"], axis=0)
        allocation_order = simplex.solve_allocation(main_fulfillments, mating_fulfillments)
        print(allocation_order)

    # create equal-numbered classes for selective assembly
    if qc_strategy == QcStrategy.selective_assembly:
        # create classes of equal width
        main_class_edges = histedges_equalN(main_fulfillments["weighted"], nbin)[:-1]
        mating_class_edges = histedges_equalN(mating_fulfillments["weighted"], nbin)[:-1]
        # map fulfillment values to classes
        classes = defaultdict(list)
        for cl, value in zip(np.digitize(mating_fulfillments["weighted"], mating_class_edges) - 1, mating_components):
            classes[cl].append(value)

    ##########################################
    # SIMULATION METHODS
    ##########################################

    def assemble(main_component: Component, mating_component: Component, weighted: bool) -> List[float]:
        """
        "Assembles" two components by taking the sum of both functional fulfillments of each test point.

        Parameters
        ----------
        main_component
            list of functional fulfillments of main component.
        mating_component
            list of functional fulfillments of mating component.
        weighted
            true if another column should be returned with a weighted fulfillment over all test points.

        Returns
        -------
        List[float]
            functional fulfillments of resulting assembled component.
        """
        return get_function(dict(main_component, **mating_component), config, weighted)

    def in_tol(functional_fulfillments: List[float]) -> bool:
        """
        Checks whether the supplied functional fulfillments are inside the specified tolerances.

        Parameters
        ----------
        functional_fulfillments
            fulfillments to check.

        Returns
        -------
        bool
            true, if the tolerances of all test points are satisfied.
        """
        tolerances = get_tolerances(config)
        return all(lt <= fulfillment <= ut for fulfillment, (lt, ut) in zip(functional_fulfillments, tolerances))

    def find_mating_component(index: int, main_component: Component) -> Component:
        """
        Finds a mating component according to the current quality control strategy.

        Parameters
        ----------
        index
            index of main component.
        main_component
            list of functional fulfillments of main component.
        Returns
        -------
        Component
            mating component.
        """
        if qc_strategy == QcStrategy.conventional_assembly or qc_strategy == QcStrategy.ascending_descending \
                or qc_strategy == QcStrategy.ascending_descending_grouped:
            # just take the first available mating component
            return mating_components.pop(0)
        elif qc_strategy == QcStrategy.individual_assembly or qc_strategy == QcStrategy.individual_assembly_greedy:
            # either select the first in-tol-component (first fit)
            # or check for all mating components the best match (best fit)
            min_index, min_fulfillment = 0, np.inf
            for index, mating_component in enumerate(mating_components):
                resulting_fulfillments = assemble(main_component, mating_component, False)
                if in_tol(resulting_fulfillments):
                    if qc_strategy == QcStrategy.individual_assembly:
                        return mating_components.pop(index)
                    else:
                        avg = abs(get_avg_fulfillment(resulting_fulfillments))
                        if avg < min_fulfillment:
                            min_index = index
                            min_fulfillment = avg

            # mating component inside tolerance not found
            if qc_strategy == QcStrategy.individual_assembly:
                stats.setdefault("individual_assembly", defaultdict(int))["not_in_tol"] += 1
            stats.setdefault("individual_assembly_greedy", []).append(min_index)
            return mating_components.pop(min_index)
        elif qc_strategy == QcStrategy.individual_assembly_simplex:
            # we already pre-calculated the allocation order using simplex
            return mating_components[allocation_order[index]]
        elif qc_strategy == QcStrategy.selective_assembly:
            # we already pre-calculated the classes,
            # here we just select the first component from the opposite class
            avg = main_fulfillments.loc[main_fulfillments.index[index], "weighted"]
            cl = np.digitize(avg, main_class_edges) - 1
            opposite_class = nbin - 1 - cl
            return classes[opposite_class].pop(0)
        else:
            raise NotImplementedError(f"qc strategy {qc_strategy} has not been implemented yet")

    ##########################################
    # SIMULATION START
    ##########################################

    selected_mating_components = []
    for index, main_component in enumerate(main_components):
        mating_component = find_mating_component(index, main_component)
        selected_mating_components.append(mating_component)

    main_component_df_final = pd.DataFrame(main_components)
    mating_component_df_final = pd.DataFrame(selected_mating_components)
    assembled_values = pd.concat([main_component_df_final, mating_component_df_final], axis=1)
    result = get_batch_function(assembled_values, config)

    return result, stats
