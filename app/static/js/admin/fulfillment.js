/**
 * Author: Alexander Albers
 * Date:   22.05.2021
 */

enableTabOnUploadCompleted("#fulfillment");

tabDidLoad("#fulfillment", () => {
    // Create dropdowns and plots for fulfillment tab
    for (const component of dataStore.components) {
        createBatchKltDropdown($("#fulfillment-dropdown-" + component.toLowerCase()), dataStore.batches[component], (batchId, kltId) => {
            // Update called when dropdown has changed
            showFulfillmentPlot("plots-fulfillment-" + component.toLowerCase(), component, batchId, kltId, 300, 0, n_testPoints + 1, false, true);
        });
    }
});