/**
 * Registers an event listener that gets called when the tab has been opened for the first time.
 * @param {string} name href of the tab.
 * @param callback gets called when the tab has been loaded for the first time.
 */
function tabDidLoad(name, callback) {
    $(document).on('show.bs.tab', 'a[data-toggle="tab"][href="' + name + '"]:not([data-loaded])', e => {
        $(e.target).attr("data-loaded", true);
        callback()
    });
}

/**
 * Enables the given tab.
 * @param name href of the tab.
 */
function enableTab(name) {
    $('a[data-toggle="tab"][href="' + name + '"]').removeClass("disabled");
}

/**
 * Enables the given tab when all components have been uploaded.
 * @param name href of the tab.
 */
function enableTabOnUploadCompleted(name) {
    $(document).on("ReKoNet:allComponentsUploaded", function () {
        enableTab(name);
    });
}


/**
 * Create a histogram from the given data.
 * @param {array} data list of numbers, which should be turned into a histogram.
 * @param {*} min minimum x-value. All items below will be placed into the leftmost bin.
 * @param {*} max maximum x-value. All items above will be placed into the rightmost bin.
 * @param {*} bins the number of bins.
 */
function calculateHistogram(data, min, max, bins = 20) {
    const size = (max - min) / bins;
    const axis = new Array(bins).fill(0);
    for (let i = 0; i < bins; i++) {
        axis[i] = min + i * size + size / 2;
    }
    const histogram = new Array(bins).fill(0);

    for (const item of data) {
        let index = Math.floor((item - min) / size);
        if (index < 0) {
            index = 0;
        }
        if (index >= bins) {
            index = bins - 1;
        }
        histogram[index]++;
    }
    const sum = data.length;
    for (let i = 0; i < bins; i++) {
        histogram[i] /= sum;
    }

    return {x: axis, y: histogram};
}

/**
 * Calculates the mean value of a distribution.
 * @param {Object.<string, number>} data distribution
 * @returns {number} the mean value of the distribution.
 */
function calculateMean(data) {
    let mean = 0;
    // x are bin boundaries, so take the average to get the bin center
    for (let j = 0; j < data["x"].length - 1; j++) {
        mean += (data["x"][j] + data["x"][j + 1]) / 2 * data["y"][j];
    }
    return mean;
}

/**
 * Calculates the variance of a distribution.
 * @param {Object.<string, number>} data distribution
 * @returns {number} the variance of the distribution.
 */
function calculateVariance(data) {
    const mean = calculateMean(data);
    let sum_squares = 0;
    for (let j = 0; j < data["x"].length - 1; j++) {
        sum_squares += data["y"][j] * Math.pow((data["x"][j] + data["x"][j + 1]) / 2 - mean, 2)
    }
    return sum_squares;
}

/**
 * Calculates the Cpk value from the test point distributions.
 * @param {array[]} data array of distributions
 * @returns {number} the mean Cpk value of all test points.
 */
function calculateCpk(data) {
    let cpk = 0;
    for (let i = 0; i < data.length; i++) {
        const mean = calculateMean(data[i]);
        const std = Math.sqrt(calculateVariance(data[i])) || 0;

        const tol = tolerances[testPointNames[i]];
        const tol_width = (tol[1] - tol[0]) / 2;
        cpk += Math.min((tol_width - mean), (mean + tol_width)) / (3 * std);
    }

    return cpk / data.length;
}

function histogramCenters(data) {
    let result = [];
    for (let i = 0; i < data.length - 1; i++) {
        result.push((data[i] + data[i + 1]) / 2);
    }
    return result;
}

/**
 * Initiates a post request to the specified endpoint (url).
 * @param {string} endpoint the url or endpoint of the post request.
 * @param {object} payload the payload of the post request.
 */
function postRequest(endpoint, payload) {
    // noinspection JSUnusedGlobalSymbols
    return $.ajax({
        url: endpoint,
        dataType: "json",
        type: "post",
        contentType: "application/json",
        data: JSON.stringify(payload),
        error: function (jqXHR, _, errorThrown) {
            if (errorThrown === "abort") {
                return;
            }
            console.error(errorThrown, jqXHR.responseText);
        }
    });
}

/**
 * Filters only unique values of an array
 */
function onlyUnique(value, index, self) {
    return self.indexOf(value) === index;
}

/**
 * Formats a float to contain 2 digits and replaces the decimal separator.
 * @param {number} n the number that should be formatted.
 * @returns {string} the formatted string.
 */
function formatFloat(n) {
    return n.toFixed(2).replace(".", ",");
}

// Checks whether an object has no keys
function ObjectIsEmpty(obj) {
    for (const prop in obj) if (obj.hasOwnProperty(prop)) return false;
    return true;
}

/**
 * Groups an array of objects by the specified key.
 * @param {Object[]} xs
 * @param {string} key
 * @return {Object.<string, any>}
 */
function groupBy(xs, key) {
    return xs.reduce(function (rv, x) {
        (rv[x[key]] = rv[x[key]] || []).push(x);
        return rv;
    }, {});
}
