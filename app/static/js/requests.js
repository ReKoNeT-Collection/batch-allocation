/**
 * Author: Alexander Albers
 * Date:   26.01.2021
 */


/**
 * Calculates the convolution of the functional fulfillment of all specified components.
 * @param {Object.<string, *>[]} components dictionary with components.
 * @param {string} qc quality control strategy.
 */
async function calculateConvolution(components, qc = "") {
    const params = new URLSearchParams({
        c: currentConfig,
        qc_strategy: qc,
        bins: bins
    });
    return postRequest("/simulateAssembly?" + params.toString(), components);
}

/**
 * Calculates the best allocation.
 * @param {Batch[][]|KLT[][]} componentBatches fulfillment values.
 * @param {string} method method how a given allocation should be evaluated.
 * @param {string} qc quality control strategy which should be simulated.
 */
async function calculateAllocation(componentBatches, method, qc) {
    let distributions = [];
    const components = dataStore.components;
    for (let componentIdx = 0; componentIdx < components.length; componentIdx++) {
        const batches = componentBatches[componentIdx].map(batch => batch.getCharacteristicValues());
        distributions.push(
            {
                name: components[componentIdx],
                batches: batches
            }
        );
    }

    const params = new URLSearchParams({
        c: currentConfig,
        qc_strategy: qc,
        method: method,
        bins: bins
    });

    return postRequest("/getAllocation?" + params.toString(), distributions);
}

var qualityLossRequests = {};
/**
 * Calculates the quality loss of the given allocation.
 * @param {string} id identifier for this type of quality loss request. Only one request with this id can exist at the same time.
 * @param {Object.<string, *>[]} distributions distribution of the base component.
 * @param {number} batchSize size of the batch, used as a factor for calculating the loss.
 * @param {string?} qc quality control strategy.
 */
async function calculateQualityLoss(id, distributions, batchSize, qc) {
    const _id = id;
    if (id in qualityLossRequests) {
        qualityLossRequests[id].abort();
    }

    let p = {
        c: currentConfig,
        bins: bins
    };
    if (qc !== undefined) {
        p["qc_strategy"] = qc;
    }
    const params = new URLSearchParams(p);

    const xhr = postRequest("/getQualityLoss?" + params.toString(), distributions);
    qualityLossRequests[id] = xhr;
    const response = await xhr.catch(function (e) {
        if (e.statusText === "abort") {
            throw Error("aborted");
        }
        console.error(e);
    });
    delete qualityLossRequests[_id];
    return response;
}

/**
 * Creates a distribution for each of the given fulfillment values.
 * @param {number[][]} array fulfillment values for every test point.
 * @return {EmpDistribution[]} empirical distribution for every test point.
 */
function createDist(array) {
    const ranges = getFulfillmentAxisRange();
    return array.map((arr, index) => new EmpDistribution(arr, ranges[index]));
}

// noinspection JSUnusedGlobalSymbols
class EmpDistribution {
    /**
     * Empirical distribution that will be fitted to a histogram.
     * @param {number[]} values list of values.
     * @param {number[]} range lower and upper limit for the histogram.
     */
    constructor(values, range) {
        this.dist = "emp";
        this.values = values;
        this.fit = "hist";
        this.bins = bins;
        this.range = range;
    }
}

// noinspection JSUnusedGlobalSymbols
class HistDistribution {
    /**
     * Histogram distribution.
     * @param {{x: number[], y: number[]}} values x and y values of the histogram.
     */
    constructor(values) {
        this.dist = "hist";
        this.x = values.x;
        this.y = values.y;
    }
}
