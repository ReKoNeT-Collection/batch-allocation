/**
 * Author: Alexander Albers
 * Date:   22.05.2021
 */

enableTabOnUploadCompleted("#price-calculation");
enableTabOnUploadCompleted("#price-calculation-conv");
enableTabOnUploadCompleted("#price-calculation-losses");

tabDidLoad("#price-calculation", () => {
    // Create price calculation dropdowns and plots
    createDropdowns("default", false, false);
});

tabDidLoad("#price-calculation-conv", () => {
    // Create price calculation dropdowns and *convoluted* plots
    createDropdowns("conv", true, false);
});

tabDidLoad("#price-calculation-losses", () => {
    // Create price calculation dropdowns and *loss* plots
    createDropdowns("losses", false, true);
});

function createDropdowns(_name, _showAllocation, _showLoss) {
    const name = _name;
    const showAllocation = _showAllocation;
    const showLoss = _showLoss;

    const parent = $("#price-calculation-base-" + name).parent();
    let base = dataStore.components[0];
    let comparison = dataStore.components[1];
    let baseSelected = {};
    let comparisonSelected = {};
    createOrReplaceMenu(parent, "price-calculation-base-" + name, "1. Komponente", dataStore.components, 0, "", value => {
        base = value;
        $(".price-calculation-name-base-" + name).text(value);
        createLossDropdowns(base, comparison, name, showAllocation, showLoss, baseSelected, comparisonSelected);
    }, "btn-info");
    createOrReplaceMenu(parent, "price-calculation-comparison-" + name, "2. Komponente", dataStore.components, 1, "", value => {
        comparison = value;
        $(".price-calculation-name-comparison-" + name).text(value);
        createLossDropdowns(base, comparison, name, showAllocation, showLoss, baseSelected, comparisonSelected);
    }, "btn-info");
    createLossDropdowns(base, comparison, name, showAllocation, showLoss, baseSelected, comparisonSelected);
    // qc strategy dropdown menu selection
    $("#price-calculation-qc-dropdown-" + name + " .dropdown-menu a").click(function () {
        updateOptimalQualityLosses(base, comparison, name, baseSelected.batchId, baseSelected.kltId, showAllocation, showLoss);
        updateStandardQualityLosses(base, comparison, name, baseSelected.batchId, baseSelected.kltId, showAllocation, showLoss);
        updateAllocatedQualityLoss(base, comparison, name, baseSelected.batchId, baseSelected.kltId, comparisonSelected.batchId, comparisonSelected.kltId, showAllocation, showLoss);
    });
}

function createLossDropdowns(_base, _comparison, _name, _showAllocation, _showLoss, _baseSelected, _comparisonSelected) {
    // copy parameter names into separate variables,
    // as calling this function for each tab overrides the stored parameter values.
    const name = _name;
    const showAllocation = _showAllocation;
    const showLoss = _showLoss;
    const base = _base;
    const comparison = _comparison;
    const baseSelected = _baseSelected;
    const comparisonSelected = _comparisonSelected;

    createBatchKltDropdown($("#price-calculation-dropdown-base-" + name), dataStore.batches[base], (batchId, kltId) => {
        // Update called when dropdown has changed
        if (baseSelected.batchId === batchId && baseSelected.kltId === kltId) {
            return;
        }
        const batchSelected = baseSelected.batchId != batchId;
        baseSelected.batchId = batchId;
        baseSelected.kltId = kltId;
        showFulfillmentPlot("plots-comparison-base-" + name, base, batchId, kltId, (n_testPoints + 1) * 200, 250, 1, false, true);
        updateOptimalQualityLosses(base, comparison, name, batchId, kltId, showAllocation, showLoss);
        updateStandardQualityLosses(base, comparison, name, batchId, kltId, showAllocation, showLoss);
        if ($("#price-calculation-autoallocate-" + name).prop("checked")) {
            autoAllocateQualityLoss("price-calculation-dropdown-comparison-" + name, base, comparison, baseSelected, comparisonSelected, batchSelected).then(() => {
                updateAllocatedQualityLoss(base, comparison, name, baseSelected.batchId, baseSelected.kltId, comparisonSelected.batchId, comparisonSelected.kltId, showAllocation, showLoss);
            });
        } else {
            updateAllocatedQualityLoss(base, comparison, name, baseSelected.batchId, baseSelected.kltId, comparisonSelected.batchId, comparisonSelected.kltId, showAllocation, showLoss);
        }
    });
    createBatchKltDropdown($("#price-calculation-dropdown-comparison-" + name), dataStore.batches[comparison], (batchId, kltId) => {
        // Update called when dropdown has changed
        if (comparisonSelected.batchId === batchId && comparisonSelected.kltId === kltId) {
            return;
        }
        const batchSelected = comparisonSelected.batchId != batchId;
        comparisonSelected.batchId = batchId;
        comparisonSelected.kltId = kltId;
        if ($("#price-calculation-autoallocate-" + name).prop("checked")) {
            autoAllocateQualityLoss("price-calculation-dropdown-base-" + name, comparison, base, comparisonSelected, baseSelected, batchSelected).then(() => {
                updateAllocatedQualityLoss(base, comparison, name, baseSelected.batchId, baseSelected.kltId, comparisonSelected.batchId, comparisonSelected.kltId, showAllocation, showLoss);
            });
        } else {
            updateAllocatedQualityLoss(base, comparison, name, baseSelected.batchId, baseSelected.kltId, comparisonSelected.batchId, comparisonSelected.kltId, showAllocation, showLoss);
        }
    });
    if (!showAllocation && !showLoss) {
        showStandardDistributionPlot("plots-comparison-standard-" + name, comparison, (n_testPoints + 1) * 200, 250, 1, true);
    }
}

async function updateOptimalQualityLosses(base, comparison, name, batchId, kltId, showAllocation, showLoss) {
    const baseData = dataStore.getCharacteristicValuesNested(base, batchId, kltId);
    const batchSize = dataStore.getNumberOfComponents(base, batchId, kltId);
    const qc = $("#price-calculation-qc-dropdown-" + name + " .dropdown-menu .active").data("value") || "";
    const distributions = [
        {
            name: base,
            batches: baseData
        },
        {
            name: comparison,
            batches: "optimal"
        }
    ];
    const resultOptimal = await calculateQualityLoss("optimal", distributions, batchSize, qc);
    if (showAllocation) {
        showConvolutionPlot("plots-comparison-optimal-" + name, resultOptimal["convolutions"], (n_testPoints + 1) * 200, 250, 1);
    } else if (showLoss) {
        showConvolutionPlot("plots-comparison-optimal-" + name, calculateLoss(resultOptimal["convolutions"]), (n_testPoints + 1) * 200, 250, 1);
    } else {
        showFulfillmentPlot("plots-comparison-optimal-" + name, base, batchId, kltId, (n_testPoints + 1) * 200, 250, 1, true, true);
    }
    updateQualityLossPlotTitle("plots-comparison-optimal-" + name, resultOptimal, batchSize);
}

async function updateStandardQualityLosses(base, comparison, name, batchId, kltId, showAllocation, showLoss) {
    const baseData = dataStore.getCharacteristicValuesNested(base, batchId, kltId);
    const batchSize = dataStore.getNumberOfComponents(base, batchId, kltId);
    const qc = $("#price-calculation-qc-dropdown-" + name + " .dropdown-menu .active").data("value") || "";
    const distributions = [
        {
            name: base,
            batches: baseData
        },
        {
            name: comparison,
            batches: "standard"
        }
    ];
    const resultStandard = await calculateQualityLoss("standard", distributions, batchSize, qc);
    if (showAllocation) {
        showConvolutionPlot("plots-comparison-standard-" + name, resultStandard["convolutions"], (n_testPoints + 1) * 200, 250, 1);
    } else if (showLoss) {
        showConvolutionPlot("plots-comparison-standard-" + name, calculateLoss(resultStandard["convolutions"]), (n_testPoints + 1) * 200, 250, 1);
    }
    updateQualityLossPlotTitle("plots-comparison-standard-" + name, resultStandard, batchSize);
}

async function updateAllocatedQualityLoss(base, comparison, name, batchId, kltId, otherBatchId, otherKltId, showAllocation, showLoss) {
    const baseData = dataStore.getCharacteristicValuesNested(base, batchId, kltId);
    const batchSize = dataStore.getNumberOfComponents(base, batchId, kltId);
    const comparisonData = dataStore.getCharacteristicValuesNested(comparison, otherBatchId, otherKltId);
    const qc = $("#price-calculation-qc-dropdown-" + name + " .dropdown-menu .active").data("value") || "";
    const distributions = [
        {
            name: base,
            batches: baseData
        },
        {
            name: comparison,
            batches: comparisonData
        }
    ];
    const lossAllocated = await calculateQualityLoss("allocated", distributions, batchSize, qc);
    if (showAllocation) {
        showConvolutionPlot("plots-comparison-allocated-" + name, lossAllocated["convolutions"], (n_testPoints + 1) * 200, 250, 1);
    } else if (showLoss) {
        showConvolutionPlot("plots-comparison-allocated-" + name, calculateLoss(lossAllocated["convolutions"]), (n_testPoints + 1) * 200, 250, 1);
    } else {
        showFulfillmentPlot("plots-comparison-allocated-" + name, comparison, otherBatchId, otherKltId, (n_testPoints + 1) * 200, 250, 1, false, true);
    }
    updateQualityLossPlotTitle("plots-comparison-allocated-" + name, lossAllocated, batchSize);
}

async function autoAllocateQualityLoss(otherDropdownName, baseName, otherName, baseSelected, otherSelected, batchSelected) {
    if (!baseSelected.batchId) {
        // reset both dropdowns of the other one
        otherSelected.batchId = "";
        $("#" + otherDropdownName + " div .dropdown-menu")
            .find("[data-value='']")
            // Will call the dropdown callback.
            .click();
        return;
    }

    if (batchSelected) {
        const batchesBase = dataStore.getBatches(baseName, undefined);
        const batchesComparison = dataStore.getBatches(otherName, undefined);
        const batchPermutations = (await calculateAllocation([batchesBase, batchesComparison], "cpk", ""))["permutation"];
        const index = batchesBase.findIndex(elem => elem.batchId == baseSelected.batchId);
        const other = batchesComparison[batchPermutations[index]].batchId;

        otherSelected.batchId = other;
        $("#" + otherDropdownName + " #batch .dropdown-menu")
            .find("[data-value='" + other + "']")
            // Will call the dropdown callback.
            .click();
    } else {
        if (!baseSelected.kltId) {
            // reset the klt dropdown of the other one
            otherSelected.kltId = "";
            $("#" + otherDropdownName + " #klt .dropdown-menu")
                .find("[data-value='']")
                // Will call the dropdown callback.
                .click();
        } else {
            // klt allocation
            const kltsBase = dataStore.getKLTs(baseName, baseSelected.batchId, undefined);
            const kltsComparison = dataStore.getKLTs(otherName, otherSelected.batchId, undefined);
            const kltPermutations = (await calculateAllocation([kltsBase, kltsComparison], "cpk", ""))["permutation"];
            const index = kltsBase.findIndex(elem => elem.kltId == baseSelected.kltId);
            const other = kltsComparison[kltPermutations[index]].kltId;

            otherSelected.kltId = other;
            $("#" + otherDropdownName + " #klt .dropdown-menu")
                .find("[data-value='" + other + "']")
                // Will call the dropdown callback.
                .click();
        }
    }
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

/**
 * Calculates the mirrored characteristic value.
 * @param {Object.<string, number[]>[][]} baseData base data.
 * @return {Object.<string, number[]>[][]} mirrored data.
 */
function getOptimalData(baseData) {
    return baseData.map(batches => batches.map(klt => {
        return Object.keys(klt).reduce((res, key) => {
        res[key] = klt[key].map(v => {
            //const tol_center = tolerances[key][0] + (tolerances[key][1] - tolerances[key][0]) / 2;
            const tol_center = means[key];
            return v + (tol_center - v) * 2;
        });
        return res;
    }, {});
    }))

}