import os
from typing import Optional, List

import pandas as pd
from flask import current_app as app


def get_standard_characteristic_values(config: str, component: str, sample_size: Optional[int],
                                       seed: Optional[int] = 42) -> pd.DataFrame:
    """
    Samples characteristic values for a given size.

    Parameters
    ----------
    config
        name of the config.
    component
        name of the component.
    sample_size
        size of the sample. Use None when the complete data set should be used.
    seed
        seed for random sampling. Use None for random seed.

    Returns
    -------
    pd.DataFrame
        a data frame with characteristic values as columns and samples in rows.
    """
    dir_name = os.path.join(app.instance_path, "data", config)
    with open(os.path.join(dir_name, f"{component}.csv"), "r") as f:
        df = pd.read_csv(f, sep=";", decimal=",")
        df = df.drop(df.columns[:2], axis=1)
        if sample_size:
            return df.sample(n=sample_size, random_state=seed)
        else:
            return df


def get_standard_characteristic_values_batches(config: str, component: str) -> List[List[pd.DataFrame]]:
    """
    Samples characteristic values for a given size.

    Parameters
    ----------
    config
        name of the config.
    component
        name of the component.

    Returns
    -------
    List[List[pd.DataFrame]]
        for every batch and every klt a data frame.
    """
    dir_name = os.path.join(app.instance_path, "data", config)
    with open(os.path.join(dir_name, f"{component}.csv"), "r") as f:
        df = pd.read_csv(f, sep=";", decimal=",")
        batches = []
        for _, batch in df.groupby("Batch_ID"):
            klts = []
            for _, klt in batch.groupby("KLT_ID"):
                klts.append(klt.drop(klt.columns[:2], axis=1).reset_index(drop=True))
            batches.append(klts)
        return batches
