/**
 * Author: Alexander Albers
 * Date:   04.12.2020
 */

/**
 * X-Axes for every test point, derived from the standard distributions.
 */
let standardDistributionAxes = standardDistributions[Object.keys(standardDistributions)[0]].map(d => d.x);

/**
 * Number of bins.
 */
let bins = standardDistributionAxes[0].length - 1;

/**
 * Re-layout all shown plots when switching tab.
 * If we don't do this, plots that are placed not inside the active tab
 * will have a default width of 700px.
 * @see https://stackoverflow.com/questions/35297628/plotly-chart-height-resize-when-using-tabs
 */
$(document).on('shown.bs.tab', 'a[data-toggle="tab"]', () => {
    $(".tab-pane.active .plot-parent.autosize").each(function () {
        if ($(this).children().length > 0) {
            Plotly.relayout($(this)[0], {autosize: true});
        }
    });
});


/**
 * Updates the plot using Plotl
 * @param {string} component
 * @param {string} selectedBatchId
 * @param {string} selectedKltId
 */
function showPlot(component, selectedBatchId, selectedKltId) {
    const characteristicValues = dataStore.getCharacteristicValues(component, selectedBatchId, selectedKltId);
    const characteristicValueNames = Object.keys(characteristicValues);
    const _data = characteristicValueNames.map(name => {
        return {
            name: name,
            x: characteristicValues[name],
            bins: bins
        };
    });
    // Show vertical lines for tolerances
    const shapes = characteristicValueNames.flatMap((characteristic, index) => {
        return [
            makeVerticalLineShape(index, tolerances[characteristic][0]),
            makeVerticalLineShape(index, tolerances[characteristic][1])
        ];
    });
    const ncols = 3;
    const nrows = Math.ceil(characteristicValueNames.length / ncols);
    const height = 180 + 160 * nrows + 60 * (nrows - 1);

    makePlot("plots-" + component.toLowerCase(), _data, height, 0, ncols, getCharacteristicsAxisRange(component), shapes);
}

/**
 * Updates the plot using Plotly
 * @param {string} id html-id of the plot
 * @param {string} component
 * @param {string} selectedBatchId
 * @param {string} selectedKltId
 * @param {number} height
 * @param {number} width
 * @param {number} ncols
 * @param {boolean} matchingData true, if the negative value for each data point should be used.
 * @param weighted
 */
function showFulfillmentPlot(id, component, selectedBatchId, selectedKltId, height, width, ncols, matchingData = false, weighted = false) {
    const filteredData = dataStore.getFulfillmentValues(component, selectedBatchId, selectedKltId, weighted);
    if (matchingData) {
        for (let testPoint = 0; testPoint < filteredData.length; testPoint++) {
            filteredData[testPoint] = filteredData[testPoint].map(n => -n);
        }
    }

    const _data = filteredData.map((values, index) => {
        return {
            name: index == n_testPoints ? "Gewichtet" : "F" + (index + 1),
            x: values,
            bins: bins
        }
    });

    makePlot(id, _data, height, width, ncols, getFulfillmentAxisRange().slice(0, _data.length), getFulfillmentShapes().slice(0, _data.length * 2));
}


function showStandardDistributionPlot(id, component, height, width, ncols, weighted = false) {
    const filteredData = standardDistributions[component];
    const plots = [...Array(weighted ? n_testPoints + 1 : n_testPoints).keys()];
    const _data = plots.map(index => {
        return {
            name: getSubplotName(index),
            x: filteredData[index].x,
            y: filteredData[index].y,
            type: "bar"
        }
    });

    makePlot(id, _data, height, width, ncols, getFulfillmentAxisRange().slice(0, _data.length), getFulfillmentShapes().slice(0, _data.length * 2));
}

/**
 * Updates the plot using Plotly
 * @param {string} id html-id of the plot
 * @param {*} data
 * @param {number} height
 * @param {number} width
 * @param {number} ncols
 * @param titleValue
 */
function showConvolutionPlot(id, data, height = n_testPoints * 200, width = 300, ncols = 1, titleValue = "") {
    const _data = data.map((entry, index) => {
        return {
            name: index == n_testPoints ? "Gewichtet" : "F" + (index + 1),
            x: histogramCenters(entry.x),
            y: entry.y,
            type: "bar"
        }
    });
    makePlot(id, _data, height, width, ncols, getFulfillmentAxisRange().slice(0, _data.length), getFulfillmentShapes().slice(0, _data.length * 2), titleValue);
}

/**
 * Updates the titles of the loss plots with the given loss values.
 * @param {string} id the HTML-div-id of the plot.
 * @param {{losses: number[], loss: number}} result quality loss dict.
 * @param {number} batch_size batch size.
 */
function updateQualityLossPlotTitle(id, result, batch_size) {
    const annotations = result["losses"].map((loss, index) => createTitleAnnotation(index, "L=" + formatFloat(loss) + "€ (" + formatFloat(loss / batch_size) + "€/Stk)"));
    const update = {annotations: annotations};
    Plotly.relayout(id, update);
    $("#" + id + "-avg").text("∅ Verlust=" + formatFloat(result["loss"]) + "€ (" + formatFloat(result["loss"] / batch_size) + "€/Stk)");
}

/**
 * Generates a multiplot using Plotly.js
 * @param {string} id the HTML-div-id of the plot.
 * @param {array} data array[{name, x}]
 * @param {number} height the total height of the plot.
 * @param {number} width the total width of the plot.
 * @param {number} ncols number of columns per row.
 * @param {array} xaxis_ranges for every subplot the range of the x axis.
 * @param {array} shapes additional shapes for each subplot (eg. vertical lines)
 * @param {string} title the title for the complete plot (above all subplots)
 */
function makePlot(id, data, height, width, ncols, xaxis_ranges = [], shapes = [], title = "") {
    // Histogram data
    const opt = data.map((entry, index) => {
        const defaults = {
            type: 'histogram',
            histnorm: 'probability',
            nbinsx: bins,
            xaxis: 'x' + (index + 1),
            yaxis: 'y' + (index + 1)
        };
        if (index < xaxis_ranges.length) {
            defaults["xbins"] = {
                start: xaxis_ranges[index][0],
                end: xaxis_ranges[index][1],
                size: (xaxis_ranges[index][1] - xaxis_ranges[index][0]) / bins
            };
        }
        return {
            ...defaults,
            ...entry
        };
    });

    // Title annotations
    let annotations = [];
    if (data.length > 1) {
        annotations = data.map((entry, index) => {
            return createTitleAnnotation(index, entry.name);
        });
    }

    // Layout and shapes
    const rows = Math.ceil(data.length / ncols);
    let layout = {
        shapes: shapes,
        grid: {rows: rows, columns: ncols, pattern: 'independent'},
        showlegend: false,
        annotations: annotations,
        margin: {
            l: 30,
            r: 30,
            b: 40,
            t: 60,
            pad: 0
        },
        bargap: 0
    };
    if (height !== 0) {
        layout.height = height;
    }
    if (width !== 0) {
        layout.width = width;
    }
    if (height !== 0 && width !== 0) {
        layout.autosize = false;
    }
    // X-Axis ranges
    for (let i = 0; i < xaxis_ranges.length; i++) {
        layout["xaxis" + (i + 1)] = {range: xaxis_ranges[i]};
    }
    // title for whole plot
    if (title !== "") {
        layout["title"] = {
            text: title
        };
    }

    // Make plot
    Plotly.newPlot(id, opt, layout, {responsive: true});
}

/**
 * Creates the vertical lines for every test point plot.
 * @returns {[]}
 */
function getFulfillmentShapes() {
    let result = [];
    for (const [i, testPointName] of testPointNames.entries()) {
        const tol = tolerances[testPointName];

        result.push(makeVerticalLineShape(i, tol[0]));
        result.push(makeVerticalLineShape(i, tol[1]));
    }
    return result;
}

/**
 * Creates the axis ranges for every characteristic value of the given component.
 * @param {string} component name of the component.
 * @returns {number[][]}
 */
function getCharacteristicsAxisRange(component) {
    let result = [];
    const characteristicValues = componentsCharacteristics.find(obj => obj["name"] === component)["characteristics"];
    for (const characteristicValue of characteristicValues) {
        const xAxis = tolerances[characteristicValue];
        const min = xAxis[0];
        const max = xAxis[1];
        const width = max - min;
        const binWidth = width / (bins - 2);

        result.push([min - binWidth, max + binWidth]);
    }
    return result;
}

/**
 * Creates the axis ranges for every test point plot.
 * @returns {number[][]}
 */
function getFulfillmentAxisRange() {
    let result = [];
    for (const xAxis of standardDistributionAxes) {
        const min = xAxis[0];
        const max = xAxis[xAxis.length - 1];
        result.push([min, max]);
    }
    return result;
}

/**
 * Returns the shape for a vertical line.
 * @param {int} plotIndex the index of the subplot.
 * @param {number} position the position on the x axis.
 * @param {string} color the color of the line.
 * @return {Object.<string, any>}
 */
function makeVerticalLineShape(plotIndex, position, color = 'rgb(255,0,0)') {
    return {
        type: 'line',
        xref: 'x' + (plotIndex + 1),
        yref: 'y' + (plotIndex + 1) + ' domain',
        x0: position,
        y0: 0,
        x1: position,
        y1: 1,
        line: {
            color: color,
            width: 2,
        }
    }
}

/**
 * @param index
 * @param name
 * @param font_size
 * @return {Object.<string, any>}
 */
function createTitleAnnotation(index, name, font_size = 16) {
    return {
        xref: 'x' + (index + 1) + ' domain',
        yref: 'y' + (index + 1) + ' domain',
        x: 0.5,
        y: 1.2,
        text: name,
        font: {
            size: font_size,
            color: 'black',
        },
        showarrow: false,
        align: 'center',
    }
}

/**
 *
 * @param {number} index
 * @return {string}
 */
function getSubplotName(index) {
    return index == n_testPoints ? "Gewichtet" : "F" + (index + 1)
}
