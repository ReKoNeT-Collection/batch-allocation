# Specification of the JSON API

## Endpoints

### 1. Get functional fulfillment
* Description: Calculates the functional fulfillment of multiple functional characteristics. 
* Path: `/getFunction`
* Method: `POST`
* Params: `?c=<dummy>`
* Body: `application/json`
```
JSON dictionary with different functional characteristic values.
{
    "functional characteristic 1": [ Values for functional characteristic 1 ],
    "functional characteristic 2": [ Values for functional characteristic 2 ],
    ...
}
```
* Response: `application/json`
```
JSON array with one entry per test point and one weighted entry.
[
    [ Values for test point 1 ],
    ...
    [ Values for test point m ],
    [ Weighted values for all test points ]
]
```

### 2. Get convolution
* Description: Calculates the convolution of two or more distributions.
* Path: `/getConvolution`
* Method: `POST`
* Params: `?c=<dummy>`
* Body: `application/json`
```
JSON array of distributions.
{
    "distributions": [
        { distribution 1 },
        { distribution 2 },
        ...
    ],
    "result_histogram": <result_histogram>
}
```
* Response: `application/json`
```
Convolution of the functional fulfillment of all components, returned as histogram.
{
    x: [
        # Functional fulfillment axis
    ],
    y: [
        # Functional fulfillment values
    ]
}
```

### 3. Simulate assembly
* Description: Simulates a quality control strategy for the assembly of two or more components. 
Same as with `/getConvolution`, the functional values of the respective distributions are "convoluted", aka. summed up.
However, this does not happen with statistical methods, but by assuming a fixed order of the first component and then applying the selected quality control strategy to the other component(s). 
* Path: `/simulateAssembly`
* Method: `POST`
* Params:
```
c=<dummy>
qc_strategy=<conventional_assembly|selective_assembly|individual_assembly_greedy|ascending_descending>
bins=<nbins>
```

* Body: `application/json`
```
JSON array of characteristic values for every component.
[
    # Component 1
    {
        "name": "Name",
        "characteristics": [
            "functional characteristic 1": [ Values for functional characteristic 1 ],
            "functional characteristic 2": [ Values for functional characteristic 2 ],
            ...
        ]
    },
    # Component 2
    {
        "name": "Name",
        "characteristics": [
            ...
        ]
    },
    ...
]
```
* Response: `application/json`
```
Every element of the array represents one test point. For every test point the entry
represents the convolution of the functional fulfillment of all components.
[
    # Test Point 1
    [
        # Functional fulfillment values of test point 1 as histogram:
        {
            "x": [
                # Functional fulfillment axis
            ],
            "y": [
                # Functional fulfillment values
            ],
            "cpk": 0,
            "mean": 0,
            "mean_std": 0,
            "qualityloss": 0
        }
    ],
    # Test Point 2
    [
        ...
    ],
    ...
]
```

### 4. Get allocation
* Description: Calculates the best allocation of multiple batches of two components. 
* Path: `/getAllocation`
* Method: `POST`
* Params:
```
c=<dummy>
qc_strategy=<conventional_assembly|selective_assembly|individual_assembly_greedy|ascending_descending>
algorithm=<brute_force>
method=<mean|mean_std|cpk|qualityloss>
bins=<nbins>
```
* Body: `application/json`
```
JSON array of characteristic values for every component.

[
    {
        # Name of component 1
        "name": "Modul1",
        "batches": [
            # Batch 1
            [
                "functional characteristic 1": [ Values for functional characteristic 1 ],
                "functional characteristic 2": [ Values for functional characteristic 2 ],
                ...
            ]
            # Batch 2
            [
                ...
            ],
            ...
        ]
    },
    {
        # Name of component 2
        "name": "Modul2",
        "batches": [
            ...
        ]
    }
]
```
* Response: `application/json`
```
The optimal batch allocation of the second component.

Example:
{
    "permutation": [0, 1, 2],
    "values": [0.35, -0.3, 0] 
}

```


### 4. Get allocation complete
* Description: Calculates the best allocation of multiple batches and their of two components. 
* Path: `/getAllocationComplete`
* Method: `POST`
* Params:
```
c=<dummy>
qc_strategy=<conventional_assembly|selective_assembly|individual_assembly_greedy|ascending_descending>
algorithm=<brute_force>
method=<mean|mean_std|cpk|qualityloss>
bins=<nbins>
```
* Body: `application/json`
```
JSON array of characteristic values for every component.

JSON array of characteristic values for every component.
[
    # Component 1
    {
        "name": "Name",
        
        # The characteristic values of multiple batches, each one consisting of several klts
        "batches": [
            # KLTS for Batch 1
            [
                # Values for KLT 1
                [
                    "functional characteristic 1": [ Values for functional characteristic 1 ],
                    "functional characteristic 2": [ Values for functional characteristic 2 ],
                    ...
                ],
                # Values for KLT 2
                ...
            ],
            # KLTS for Batch 2
            [
            ...
            ]
        ]
    },
    # Component 2
    {
        "name": "Name",
        "batches": [
            ...
        ]
    },
    ...
]
```
* Response: `application/json`
```
The optimal batch allocation of the second component.
First component is assumed to have the initially supplied order.

Example:
[
    {
        "batch": 0,
        "klts": [0, 1, 2]
    },
    {
        "batch": 2,
        "klts": [1, 0, 2]
    },
    {
        "batch": 1,
        "klts": [2, 1, 0]
    }
]
```

### 5. Get quality loss
* Description: Calculates the quality loss of two given component batches.
* Path: `/getQualityLoss`
* Method: `POST`
* Params:
```
c=<dummy>
qc_strategy=<conventional_assembly|selective_assembly|individual_assembly_greedy|ascending_descending>
bins=<nbins>
```
* Body: `application/json`
```
JSON array of characteristic values for every component.
[
    # Component 1
    {
        "name": "Name",
        
        # The characteristic values of multiple batches, each one consisting
        # of several klts, with the server automatically performing an allocation.
        "batches": [
            # KLTS for Batch 1
            [
                # Values for KLT 1
                [
                    "functional characteristic 1": [ Values for functional characteristic 1 ],
                    "functional characteristic 2": [ Values for functional characteristic 2 ],
                    ...
                ],
                # Values for KLT 2
                ...
            ],
            # KLTS for Batch 2
            [
            ...
            ]
        ]
    },
    # Component 2
    {
        "name": "Name",
        "batches": [
            ...
        ]
    },
    ...
]
```
* Response: `application/json`
```
Quality loss values.

{
    "losses": [
        ...
    ],
    "loss": <weighted average of losses>,
    "convolutions": [
        # Functional fulfillment values of test point 1 as histogram:
        {
            x: [
                # Functional fulfillment axis
            ],
            y: [
                # Functional fulfillment values
            ]
        },
        # Functional fulfillment values of test point 2 as histogram:
        ...
    ]
}
```


## Models
The following structures are mostly related to the getConvolution request.
### Distributions
Distributions can be specified by the following means.
#### Empirical Distribution
```json5
{
    // type of the distribution
    "dist": "emp",
    // array of (float) values
    "values": [],
    // as what distribution should the distribution be parsed as?
    "fit": "norm|hist",
    // hist: number of bins in the histogram
    "bins": 30,
    // hist: range (min, max) of the histogram
    "range": [-5, 5]
}
```

#### Normal Distribution
```json5
{
    // type of the distribution
    "dist": "norm",
    // mean of the normal distribution
    "mean": 0,
    // standard deviation of the distribution
    "std": 1
}
```

#### Histogram Distribution
```json5
{
    // type of the distribution
    "dist": "hist",
    // list of x-values
    "x": [],
    // list of y-values
    "y": [],
}
```

### Result Histogram
Specifies how the result of a convolution should be returned.
```json5
{
    // number of bins in the histogram
    "bins": 30,
    // range (min, max) of the histogram
    "range": [-5, 5]
}
```