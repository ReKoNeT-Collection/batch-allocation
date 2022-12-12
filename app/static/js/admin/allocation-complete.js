enableTabOnUploadCompleted("#allocation-complete");

tabDidLoad("#allocation-complete", () => {
    let base = dataStore.components[0];
    let comparison = dataStore.components[1];
    const parent = $("#allocation-complete");
    createOrReplaceMenu(parent, "allocation-complete-base", "1. Komponente", dataStore.components, 0, "", value => {
        base = value;
    }, "btn-info");
    createOrReplaceMenu(parent, "allocation-complete-comparison", "2. Komponente", dataStore.components, 1, "", value => {
        comparison = value;
    }, "btn-info");
});

async function onCalculateAllocationCompleteClicked() {
    const parent = $("#allocation-complete");
    const $spinner = parent.find("#allocation-calc-spinner")
    const $container = $("#allocation-complete-result");
    $spinner.show();
    $container.empty();

    const base = parent.find("#allocation-complete-base .dropdown-menu .active").data("value") || "";
    const comparison = parent.find("#allocation-complete-comparison .dropdown-menu .active").data("value") || "";
    const qc = parent.find("#allocation-qc-dropdown .dropdown-menu .active").data("value") || "";
    const method = parent.find("#allocation-method-dropdown .dropdown-menu .active").data("value") || "";
    const baseData = dataStore.getCharacteristicValuesNested(base, undefined, undefined);
    const comparisonData = dataStore.getCharacteristicValuesNested(comparison, undefined, undefined);
    const payload = [
        {
            name: base,
            batches: baseData
        },
        {
            name: comparison,
            batches: comparisonData
        }
    ];
    const params = new URLSearchParams({
        c: currentConfig,
        qc_strategy: qc,
        method: method,
        bins: bins
    });
    const allocation = await postRequest("/getAllocationComplete?" + params.toString(), payload);
    $spinner.hide();

    const $headerRow = $("<div>").addClass("row")
        .append($("<div>").addClass("col-sm-6").append($("<h4>").append(base)))
        .append($("<div>").addClass("col-sm-6").addClass("text-right").append($("<h4>").append(comparison)));
    $container.append($headerRow);

    for (let baseBatchIdx = 0; baseBatchIdx < allocation.length; baseBatchIdx++) {
        const allocated = allocation[baseBatchIdx];
        const comparisonBatchIdx = allocated["batch"];
        let $outerRow = $("<div>").addClass("row").addClass("row-outer");

        $outerRow.append($("<div>").addClass("col-sm-3").text("Batch " + dataStore.batches[base][baseBatchIdx].batchId));

        let $innerRowBase = $("<div>").addClass("col-sm-3");
        for (let baseKltIdx = 0; baseKltIdx < allocated["klts"].length; baseKltIdx++) {
            const kltName = dataStore.batches[base][baseBatchIdx].klts[baseKltIdx].kltId;
            $innerRowBase.append(
                $("<div>").addClass("row").addClass("row-inner")
                    .append($("<div>").addClass("col").text("KLT " + kltName))
            );
        }
        $outerRow.append($innerRowBase);

        let $innerRowComparison = $("<div>").addClass("col-sm-3");
        for (let index = 0; index < allocated["klts"].length; index++) {
            const kltName = dataStore.batches[comparison][comparisonBatchIdx].klts[allocated["klts"][index]].kltId;
            $innerRowComparison.append(
                $("<div>").addClass("row").addClass("row-inner")
                    .append($("<div>").addClass("col").addClass("text-right").text("KLT " + kltName))
            );
        }
        $outerRow.append($innerRowComparison);

        $outerRow.append($("<div>").addClass("col-sm-3").text("Batch " + dataStore.batches[comparison][comparisonBatchIdx].batchId));

        $container.append($outerRow).append($("<br>"));
    }
}
