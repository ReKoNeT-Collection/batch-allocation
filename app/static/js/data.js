class DataStore {
    /**
     * Dictionary of component and batch array pairs.
     * @type {Object.<string, Batch[]>}
     */
    batches = components.reduce((result, item) => {
        // default values to keep the original order of components
        result[item] = [];
        return result;
    }, {});

    /**
     * Sets the product data of a specific component.
     * @param {string} component name of the component.
     * @param {Object.<string, number>[]} data list of key-value pairs.
     * @param {boolean} calculateFulfillments true if the functional fulfillment should be calculated.
     */
    async setData(component, data, calculateFulfillments) {
        // load fulfillments
        let payload = {};
        const characteristicValues = componentsCharacteristics.find(obj => obj["name"] === component)["characteristics"];
        for (const column of characteristicValues) {
            payload[column] = data.map(d => +d[column]);
        }

        if (calculateFulfillments) {
            const result = await postRequest("/getFunction?c=" + currentConfig, payload);
            for (let i = 0; i < data.length; i++) {
                data[i].Fulfillment = result.slice(0, n_testPoints).map(col => col[i]);
                data[i].WeightedFulfillment = result[n_testPoints][i];
            }
        }

        // group by batch and klt
        const batchMap = groupBy(data, "Batch_ID");
        this.batches[component] = Object.keys(batchMap).map(batchId => {
            const kltMap = groupBy(batchMap[batchId], "KLT_ID");
            const klts = Object.keys(kltMap).map(kltId => {
                let characteristics = {};
                for (const characteristic of characteristicValues) {
                    characteristics[characteristic] = kltMap[kltId].map(d => +d[characteristic]);
                }
                let fulfillments = Array.from({length: n_testPoints}, _ => []);
                let weightedFulfillment = [];
                if (calculateFulfillments) {
                    for (let i = 0; i < n_testPoints; i++) {
                        fulfillments[i] = kltMap[kltId].map(d => +d.Fulfillment[i]);
                    }
                    weightedFulfillment = kltMap[kltId].map(d => +d.WeightedFulfillment);
                }

                return new KLT(kltId, batchId, characteristics, fulfillments, weightedFulfillment);
            });
            return new Batch(batchId, klts);
        });
    }

    /**
     * @return {boolean} true, if all components have been uploaded.
     */
    get isComplete() {
        return this.components.every(component => this.batches[component].length > 0);
    }

    /**
     * Gets all batches for the given component and batch id.
     * @param {string} component name of the component.
     * @param {?string} batchId name of the batch, or undefined.
     * @return {Batch[]} list of klts.
     */
    getBatches(component, batchId) {
        return this.batches[component]
            .filter(batch => !batchId || batch.batchId == batchId);
    }

    /**
     * Gets all klts for the given component, batch and klt id.
     * @param {string} component name of the component.
     * @param {?string} batchId name of the batch, or undefined.
     * @param {?string} kltId name of the klt, or undefined.
     * @return {KLT[]} list of klts.
     */
    getKLTs(component, batchId, kltId) {
        return this.batches[component]
            .filter(batch => !batchId || batch.batchId == batchId)
            .flatMap(batch => batch.klts)
            .filter(klt => !kltId || klt.kltId == kltId);
    }

    /**
     * Gets the characteristic values for the given component, batch and klt id.
     * @param {string} component name of the component.
     * @param {?string} batchId name of the batch, or undefined.
     * @param {?string} kltId name of the klt, or undefined.
     * @return {Object.<string, number[]>} characteristic values. 1st dim = characteristic value.
     */
    getCharacteristicValues(component, batchId, kltId) {
        return _reduceCharacteristics(this.getKLTs(component, batchId, kltId));
    }

    /**
     * Generates a nested array of characteristic values for the given component, batch and klt.
     * @param {string} componentName name of the component.
     * @param {?string} batchId name of the batch, or undefined.
     * @param {?string} kltId name of the klt, or undefined.
     * @return {Object.<string, number[]>[][]} request dictionary.
     */
    getCharacteristicValuesNested(componentName, batchId, kltId) {
        if (batchId && kltId) {
            return [[this.getCharacteristicValues(componentName, batchId, kltId)]];
        } else if (batchId) {
            return [this.getKLTs(componentName, batchId, kltId).map(klt => klt.getCharacteristicValues())];
        } else {
            return this.getBatches(componentName, batchId)
                .map(batch => batch.klts.map(klt => klt.getCharacteristicValues()));
        }
    }

    /**
     * Gets the functional fulfillment values for the given component, batch and klt id.
     * @param {string} component name of the component.
     * @param {?string} batchId name of the batch, or undefined.
     * @param {?string} kltId name of the klt, or undefined.
     * @param {boolean} weighted true if in addition the weighted test point should be returned.
     * @return {number[][]} functional fulfillment values. 1st dim = test points.
     */
    getFulfillmentValues(component, batchId, kltId, weighted = false) {
        return _reduceFulfillments(this.getKLTs(component, batchId, kltId), weighted);
    }

    /**
     * Calculates the total number of components contained in the given batches and klts.
     * @param {string} component name of the component.
     * @param {?string} batchId name of the batch, or undefined.
     * @param {?string} kltId name of the klt, or undefined.
     * @return {number} total number of components.
     */
    getNumberOfComponents(component, batchId, kltId) {
        return this.getKLTs(component, batchId, kltId).reduce((result, klt) => result + klt.getSize(), 0)
    }

    /**
     * @return {string[]} names of all uploaded components.
     */
    get components() {
        return Object.keys(this.batches);
    }

    /**
     * @return {string[][]} for every uploaded component, list of batch ids.
     */
    get componentBatchIds() {
        return this.components.map((component) => this.batches[component].map(elem => elem.batchId));
    }

    /**
     * @return {string[][][]} for every uploaded component and batch, list of klt ids.
     */
    get componentKLTIds() {
        return this.components.map((component) => this.batches[component].map(elem => elem.kltIds));
    }

}

class Batch {
    /**
     * @param {string} batchId name of the batch.
     * @param {KLT[]} klts list of klts.
     */
    constructor(batchId, klts) {
        this.id = batchId;
        this.batchId = batchId;
        this.klts = klts;
    }

    /**
     * @return {string[]} list of KLT IDs.
     */
    get kltIds() {
        return this.klts.map(klt => klt.kltId);
    }

    /**
     * Gets the functional fulfillment values for the klt id.
     * @return {number[][]} functional fulfillment values. 1st dim = test points.
     */
    getFulfillmentValues() {
        return _reduceFulfillments(this.klts);
    }

    /**
     * Gets the characteristic values for the klt id.
     * @return {Object.<string, number[]>} characteristic values.
     */
    getCharacteristicValues() {
        return _reduceCharacteristics(this.klts);
    }
}

class KLT {
    /**
     * @param {string} kltId name of the klt.
     * @param {string} batchId name of the batch.
     * @param {Object.<string, number[]>} characteristics characteristic values => all components.
     * @param {number[][]} fulfillments for every test point, the fulfillments of all components.
     * @param {number[]} weightedFulfillments weighted fulfillments of all components.
     */
    constructor(kltId, batchId, characteristics, fulfillments, weightedFulfillments) {
        this.id = kltId;
        this.kltId = kltId;
        this.batchId = batchId;
        this.characteristics = characteristics;
        this.fulfillments = fulfillments;
        this.weightedFulfillments = weightedFulfillments;
    }

    /**
     * Gets the functional fulfillment values for the klt id.
     * @return {number[][]} functional fulfillment values. 1st dim = test points.
     */
    getFulfillmentValues() {
        return _reduceFulfillments([this]);
    }

    /**
     * Gets the characteristic values for the klt id.
     * @return {Object.<string, number[]>} characteristic values.
     */
    getCharacteristicValues() {
        return _reduceCharacteristics([this]);
    }

    /**
     * Gets the number of components inside this klt.
     * @return {number} number of components.
     */
    getSize() {
        return this.characteristics[Object.keys(this.characteristics)[0]].length;
    }

}

/**
 * Combines the fulfillment values of several klts into one array.
 * @param {KLT[]} klts list of klts.
 * @param {boolean} weighted true if in addition the weighted test point should be returned.
 * @return {number[][]} functional fulfillment values. 1st dim = test points.
 */
function _reduceFulfillments(klts, weighted = false) {
    return klts.reduce((result, klt) => {
        for (let testPoint = 0; testPoint < n_testPoints; testPoint++) {
            result[testPoint] = result[testPoint].concat(klt.fulfillments[testPoint]);
        }
        if (weighted) {
            result[n_testPoints] = result[n_testPoints].concat(klt.weightedFulfillments);
        }
        return result;
    }, Array.from({length: weighted ? n_testPoints + 1 : n_testPoints}, _ => []));
}

/**
 * Combines the characteristic values of several klts into one array.
 * @param {KLT[]} klts list of klts.
 * @return {Object.<string, number[]>} characteristic values.
 */
function _reduceCharacteristics(klts) {
    return klts.reduce((result, klt) => {
        for (let characteristic of Object.keys(klt.characteristics)) {
            result[characteristic] = (result[characteristic] || []).concat(klt.characteristics[characteristic]);
        }
        return result;
    }, {});
}


const dataStore = new DataStore();