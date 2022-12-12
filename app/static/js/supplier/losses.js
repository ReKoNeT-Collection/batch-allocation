/**
 * Author: Alexander Albers
 * Date:   29.09.2021
 * Modified from admin/losses1.js
 */

enableTabOnUploadCompleted("#price-calculation");

tabDidLoad("#price-calculation", () => {
    // Create price calculation dropdowns and plots
    createDropdowns("default", false, false);
});

function createDropdowns(_name, _showAllocation, _showLoss) {
    const name = _name;
    const showAllocation = _showAllocation;
    const showLoss = _showLoss;

    let base = dataStore.components[0];
    let comparison = Object.keys(standardDistributions).find(item => item != base);

    createLossDropdowns(base, comparison, name, showAllocation, showLoss);
}

function createLossDropdowns(_base, _comparison, _name, _showAllocation, _showLoss) {
    const name = _name;
    const comparison = _comparison;
    const showAllocation = _showAllocation;
    const showLoss = _showLoss;
    const base = _base;
    let baseSelected = {};

    createBatchKltDropdown($("#price-calculation-dropdown-base"), dataStore.batches[base], (batchId, kltId) => {
        // Update called when dropdown has changed
        if (baseSelected.batchId === batchId && baseSelected.kltId === kltId) {
            return;
        }
        baseSelected.batchId = batchId;
        baseSelected.kltId = kltId;
        showFulfillmentPlot("plots-comparison-allocated-" + name, base, baseSelected.batchId, baseSelected.kltId, (n_testPoints + 1) * 200, 250, 1, false, true);
        updateAllocatedQualityLoss(base, name, batchId, kltId, undefined, undefined, showAllocation, showLoss);
    });
    if (!showAllocation && !showLoss) {
        showStandardDistributionPlot("plots-comparison-standard-" + name, base, (n_testPoints + 1) * 200, 250, 1, true);

        let optimal = [];
        for (let testPoint = 0; testPoint < standardDistributions[comparison].length; testPoint++) {
            const x = standardDistributions[comparison][testPoint].x;
            const y = standardDistributions[comparison][testPoint].y.slice().reverse();  // mirror for optimal data
            optimal.push({x: x, y: y});
        }
        standardDistributions[comparison + "_optimal"] = optimal;

        showStandardDistributionPlot("plots-comparison-optimal-" + name, comparison + "_optimal", (n_testPoints + 1) * 200, 250, 1, true);
        showFulfillmentPlot("plots-comparison-allocated-" + name, base, baseSelected.batchId, baseSelected.kltId, (n_testPoints + 1) * 200, 250, 1, false, true);
    }

    updateOptimalQualityLosses(base, name, baseSelected.batchId, baseSelected.kltId, showAllocation, showLoss);
    updateStandardQualityLosses(base, name, baseSelected.batchId, baseSelected.kltId, showAllocation, showLoss);
    updateAllocatedQualityLoss(base, name, baseSelected.batchId, baseSelected.kltId, undefined, undefined, showAllocation, showLoss);
}

async function updateOptimalQualityLosses(base, name, batchId, kltId, showAllocation, showLoss) {
    const batchSize = dataStore.getNumberOfComponents(base, batchId, kltId);
    const distributions = [
        {
            name: base,
            batches: "optimal"
        }
    ];
    const resultOptimal = await calculateQualityLoss("optimal", distributions, batchSize, undefined);
    if (showAllocation) {
        showConvolutionPlot("plots-comparison-optimal-" + name, resultOptimal["convolutions"], (n_testPoints + 1) * 200, 250, 1);
    } else if (showLoss) {
        showConvolutionPlot("plots-comparison-optimal-" + name, calculateLoss(resultOptimal["convolutions"]), (n_testPoints + 1) * 200, 250, 1);
    }
    updateQualityLossPlotTitle("plots-comparison-optimal-" + name, resultOptimal, batchSize);
}

async function updateStandardQualityLosses(base, name, batchId, kltId, showAllocation, showLoss) {
    const batchSize = dataStore.getNumberOfComponents(base, batchId, kltId);
    const distributions = [
        {
            name: base,
            batches: "standard"
        }
    ];
    const resultStandard = await calculateQualityLoss("standard", distributions, batchSize, undefined);
    if (showAllocation) {
        showConvolutionPlot("plots-comparison-standard-" + name, resultStandard["convolutions"], (n_testPoints + 1) * 200, 250, 1);
    } else if (showLoss) {
        showConvolutionPlot("plots-comparison-standard-" + name, calculateLoss(resultStandard["convolutions"]), (n_testPoints + 1) * 200, 250, 1);
    }
    updateQualityLossPlotTitle("plots-comparison-standard-" + name, resultStandard, batchSize);
}

async function updateAllocatedQualityLoss(base, name, batchId, kltId, otherBatchId, otherKltId, showAllocation, showLoss) {
    const baseData = dataStore.getCharacteristicValuesNested(base, batchId, kltId);
    const batchSize = dataStore.getNumberOfComponents(base, batchId, kltId);
    const distributions = [
        {
            name: base,
            batches: baseData
        }
    ];
    const lossAllocated = await calculateQualityLoss("allocated", distributions, batchSize, undefined);
    if (showAllocation) {
        showConvolutionPlot("plots-comparison-allocated-" + name, lossAllocated["convolutions"], (n_testPoints + 1) * 200, 250, 1);
    } else if (showLoss) {
        showConvolutionPlot("plots-comparison-allocated-" + name, calculateLoss(lossAllocated["convolutions"]), (n_testPoints + 1) * 200, 250, 1);
    }
    updateQualityLossPlotTitle("plots-comparison-allocated-" + name, lossAllocated, batchSize);
}

function calculateLoss(lossAllocated) {
    let multData = [];
    for (let i = 0; i < qualityLossClasses.length; i++) {
        const loss = qualityLossClasses[i];
        const conv = lossAllocated[i];
        let mult = {x: loss.x, y: loss.y.slice()};
        for (let j = 0; j < loss.y.length; j++) {
            mult.y[j] *= conv.y[j];
        }
        multData.push(mult);
    }
    return multData;
}
