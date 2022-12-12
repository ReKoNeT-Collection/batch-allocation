/**
 * Author: Alexander Albers
 * Date:   22.05.2021
 */

enableTabOnUploadCompleted("#allocation");

tabDidLoad("#allocation", () => {
    // Create dropdowns and plots for allocation tab
    let selectedComponents = {};
    for (const component of dataStore.components) {
        createBatchKltDropdown($("#allocation-dropdown-" + component.toLowerCase()), dataStore.batches[component], (batchId, kltId) => {
            // Update called when dropdown has changed
            showFulfillmentPlot("plots-allocation-" + component.toLowerCase(), component, batchId, kltId, n_testPoints * 200, 300, 1);
            selectedComponents[component] = {batchId: batchId, kltId: kltId};

            // if selected components == all components, then calculate the convolution of all components
            if (dataStore.isComplete && Object.keys(selectedComponents).length == dataStore.components.length) {
                const qc = $("#overview-allocation-qc-dropdown .dropdown-menu .active").data("value");
                const characteristicValues = Object.entries(selectedComponents).map(([component, selected]) => {
                    return {
                        name: component,
                        characteristics: dataStore.getCharacteristicValues(component, selected.batchId, selected.kltId)
                    };
                });
                calculateConvolution(characteristicValues, qc).then(result => showConvolutionPlot("convoluted-plots-allocation", result));
            }
        });
    }

    $("#overview-allocation-qc-dropdown .dropdown-menu a").click(function () {
        const qc = $(this).data("value");
        const characteristicValues = Object.entries(selectedComponents).map(([component, selected]) => {
            return {
                name: component,
                characteristics: dataStore.getCharacteristicValues(component, selected.batchId, selected.kltId)
            };
        });
        calculateConvolution(characteristicValues, qc).then(result => showConvolutionPlot("convoluted-plots-allocation", result));
    });
});