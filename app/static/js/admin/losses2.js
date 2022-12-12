/**
 * Author: Alexander Albers
 * Date:   22.05.2021
 */

enableTabOnUploadCompleted("#losses");

tabDidLoad("#losses", () => {
    showConvolutionPlot("plots-losses", qualityLossClasses, 300, 0, 5);

    const base = dataStore.components[0];
    const comparison = dataStore.components[1];
    let baseSelected = {};
    let comparisonSelected = {};
    createBatchKltDropdown($("#losses-dropdown-base"), dataStore.batches[base], async (batchId, kltId) => {
        if (baseSelected.batchId === batchId && baseSelected.kltId === kltId) {
            return;
        }
        const batchSelected = baseSelected.batchId != batchId;
        baseSelected.batchId = batchId;
        baseSelected.kltId = kltId;
        if ($("#losses-autoallocate").prop("checked")) {
            await autoAllocateQualityLoss("losses-dropdown-comparison", base, comparison, baseSelected, comparisonSelected, batchSelected);
        }
        await updateLossPlots(baseSelected.batchId, baseSelected.kltId, comparisonSelected.batchId, comparisonSelected.kltId);
    });
    createBatchKltDropdown($("#losses-dropdown-comparison"), dataStore.batches[comparison], async (batchId, kltId) => {
        if (comparisonSelected.batchId === batchId && comparisonSelected.kltId === kltId) {
            return;
        }
        const batchSelected = comparisonSelected.batchId != batchId;
        comparisonSelected.batchId = batchId;
        comparisonSelected.kltId = kltId;
        if ($("#losses-autoallocate").prop("checked")) {
            await autoAllocateQualityLoss("losses-dropdown-base", comparison, base, comparisonSelected, baseSelected, batchSelected);
        }
        await updateLossPlots(baseSelected.batchId, baseSelected.kltId, comparisonSelected.batchId, comparisonSelected.kltId);
    });

    // qc strategy dropdown menu selection
    $("#losses-qc-dropdown .dropdown-menu a").click(function () {
        updateLossPlots(baseSelected.batchId, baseSelected.kltId, comparisonSelected.batchId, comparisonSelected.kltId);
    });
});

async function updateLossPlots(batchId, kltId, otherBatchId, otherKltId) {
    const baseData = dataStore.getCharacteristicValuesNested(dataStore.components[0], batchId, kltId);
    const batchSize = dataStore.getNumberOfComponents(dataStore.components[0], batchId, kltId);
    const comparisonData = dataStore.getCharacteristicValuesNested(dataStore.components[1], otherBatchId, otherKltId);
    const qc = $("#losses-qc-dropdown .dropdown-menu .active").data("value") || "";
    const distributions = [
        {
            name: dataStore.components[0],
            batches: baseData
        },
        {
            name: dataStore.components[1],
            batches: comparisonData
        }
    ];
    const lossAllocated = await calculateQualityLoss("loss", distributions, batchSize, qc);
    showConvolutionPlot("plots-losses-conv", lossAllocated["convolutions"], 300, 0, 5);
    updateQualityLossPlotTitle("plots-losses-conv", lossAllocated, batchSize);

    // multiply y values
    let multData = calculateLoss(lossAllocated["convolutions"]);
    showConvolutionPlot("plots-losses-mult", multData, 300, 0, 5);
    updateQualityLossPlotTitle("plots-losses-mult", lossAllocated, batchSize);
}