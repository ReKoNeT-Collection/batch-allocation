/**
 * Author: Alexander Albers
 * Date:   22.05.2021
 */

enableTabOnUploadCompleted("#batch-allocation");
enableTabOnUploadCompleted("#klt-allocation");


tabDidLoad("#batch-allocation", () => {
    // Create dropdowns and plots for batch allocation tab
    const componentBatchIds = dataStore.componentBatchIds;
    createBatchAllocationTab("batch", componentBatchIds);
});

tabDidLoad("#klt-allocation", () => {
    // Create dropdowns and plots for klt allocation tab
    const componentBatchIds = dataStore.componentBatchIds;
    const componentKLTIds = dataStore.componentKLTIds;
    createBatchAllocationTab("klt", componentKLTIds.map(comp => comp[0]));

    // Update handler when selecting different batch ids in the KLT allocation tab.
    let kltParent = $("#klt-allocation-plots");
    createComparisonMenus($("#klt-allocation-selected-batches"), dataStore.components, componentBatchIds, 0, values => {
        if (getSelectedBatchIdsForKLTAllocation().length === 0) {
            // no batch ids yet selected, abort.
            // this case occurs when the plots have been created before the
            // batch selection dropdown has been added to the page.
            return;
        }
        const kltIds = componentKLTIds.map((comp, compIndex) => comp[componentBatchIds[compIndex].indexOf(values[compIndex])]);
        createBatchAllocationTab("klt", kltIds);
    });
});

function getSelectedBatchIdsForKLTAllocation() {
    return $("#klt-allocation-selected-batches .dropdown-menu .active").map(function () {
        return this.text;
    }).get();
}

/**
 * @param {string} type either "batch" or "klt"
 * @param {string[][]} dropdownItems all dropdown items.
 */
function createBatchAllocationTab(type, dropdownItems) {
    let parent = $("#" + type + "-allocation-plots");
    let items = dropdownItems;
    for (let i = 0; i < items[0].length; i++) {
        createBatchAllocationPlots(i, parent, type);

        createComparisonMenus(parent.find("#batch-allocation-dropdown-" + i), dataStore.components, items, i, _ => {
            // Update called when dropdown has changed
            updateBatchAllocationDropdowns(i, parent, type, items);
        });
    }
}

/**
 * Called when a new batch has been selected from one of the batch allocation tab dropdowns.
 *
 * This method tries to figure out by itself what batch has been selected from the dropdowns
 * so that the program does not have to maintain any state.
 *
 * @param allocationIndex for every batch id several plots and dropdown menus are generated.
 * This index tells which of those dropdown menus has been selected.
 * @param parent the parent div.
 * @param type {string} either "batch" or "klt".
 * @param dropdownItems all dropdown items.
 */
function updateBatchAllocationDropdowns(allocationIndex, parent, type, dropdownItems) {
    /*
     * 1. Find out what dropdowns are currently selected for the allocationIndex-th plot.
     */
    const selectedComponents = parent.find("#batch-allocation-dropdown-" + allocationIndex + " .active")
        .map(function () {
            return this.text;
        })
        .get();

    /*
     * 2. Calculate the convolution of the selected batches.
     */
    let characteristicValues;
    if (type === "batch") {
        characteristicValues = dataStore.components.map((componentName, index) => {
            return {
                name: componentName,
                characteristics: dataStore.getCharacteristicValues(componentName, selectedComponents[index], undefined)
            };
        });
    } else {
        characteristicValues = dataStore.components.map((componentName, index) => {
            const batchId = $("#klt-allocation-selected-batches #component-" + index + " .dropdown-menu .active").data("value");
            return {
                name: componentName,
                characteristics: dataStore.getCharacteristicValues(componentName, batchId, selectedComponents[index])
            };
        });
    }
    const qc = parent.parent().find("#allocation-qc-dropdown .dropdown-menu .active").data("value") || "";
    const method = parent.parent().find("#allocation-method-dropdown .dropdown-menu .active").data("value") || "";
    const methodName = parent.parent().find("#allocation-method-dropdown .dropdown-menu .active").text() || "";
    calculateConvolution(characteristicValues, qc).then((result) => {
        // Update the convolution plots
        let value = 0;
        for (let i = 0; i < result.length; i++) {
            value += result[i][method];
        }
        const title = methodName + ": " + formatFloat(Math.abs(value / result.length));
        showConvolutionPlot(type + "-allocation-plots-" + allocationIndex, result, 350, 0, Math.ceil(Math.sqrt(n_testPoints)), title);
    });

    /*
     * 3. (Convenience feature) Find out what other plot has currently selected the same batch id for the changed
     *    component dropdown and update this value to the previous value of the changed dropdown.
     */
    for (let i = 0; i < dataStore.components.length; i++) {
        // 3a. Find the dropdown which has the same batch id currently selected
        const value = selectedComponents[i];
        const other = parent.find(
            // make sure that we don't select the currently changed dropdown
            ".batch-allocation-dropdown:not(#batch-allocation-dropdown-" + allocationIndex + ") " +
            // only look for the same component
            "#component-" + i + " " +
            // find the dropdown which has the same batch id active
            ".dropdown-menu .active[data-value='" + value + "']"
        );
        // 3b. Find out *all* currently selected batch ids for the current component.
        const currentBatchIds = parent.find("#component-" + i + " .dropdown-menu .active")
            .map(function () {
                return this.text;
            })
            .get();
        // 3c. Find out what batch id is currently *not* selected.
        //     This will be the new value for the other dropdown.
        const missingBatchId = dropdownItems[i].filter((el) => !currentBatchIds.includes(el))[0];
        // 3d. Select the other component with the missing batch id.
        other.parent()
            .find("[data-value='" + missingBatchId + "']")
            // Will call the dropdown callback.
            .click();
    }
}

/**
 * Dynamically generates the plots for the batch allocation tabs.
 * @param allocationIndex {int} for every batch id several plots and dropdown menus are generated.
 * This index tells which of those dropdown menus has been selected.
 * @param parent the parent div.
 * @param type {string} either "batch" or "klt"
 */
function createBatchAllocationPlots(allocationIndex, parent, type) {
    let child = $("<div>")
        .addClass("allocation-matrix");
    let dropdownParent = $("<div>")
        .attr("id", "batch-allocation-dropdown-" + allocationIndex)
        .addClass("batch-allocation-dropdown");
    child
        .append(dropdownParent)
        .append($("<br>")).append($("<br>"));
    let plotDiv = $("<div>")
        .addClass("plot-parent")
        .addClass("autosize")
        .attr("id", type + "-allocation-plots-" + allocationIndex);
    child.append(plotDiv);
    parent.append(child);
}

/**
 * Called when user clicked on the "Calculate best allocation" button.
 * @param type either "batch" or "klt".
 */
async function onCalculateAllocationClicked(type) {
    if (!dataStore.isComplete) {
        return;
    }

    /**
     * @type {Batch[][]|KLT[][]}
     */
    let componentBatches;
    if (type === "batch") {
        componentBatches = dataStore.components.map(component => dataStore.getBatches(component, undefined));
    } else {
        componentBatches = dataStore.components.map((component, i) => {
            const batchId = $("#klt-allocation-selected-batches #component-" + i + " .dropdown-menu .active").data("value");
            return dataStore.getKLTs(component, batchId, undefined);
        });
    }

    const parent = $("#" + type + "-allocation-plots").parent();
    parent.find("#allocation-calc-spinner").show();
    const method = parent.find("#allocation-method-dropdown .dropdown-menu .active").data("value") || "";
    const methodName = parent.find("#allocation-method-dropdown .dropdown-menu .active").text() || "";
    const qc = parent.find("#allocation-qc-dropdown .dropdown-menu .active").data("value") || "";

    const result = await calculateAllocation(componentBatches, method, qc);
    const permutation = result["permutation"];
    const values = result["values"];

    parent.find("#allocation-calc-spinner").hide();
    for (let i = 0; i < permutation.length; i++) {
        const dropdownMenus = parent.find("#batch-allocation-dropdown-" + i);

        // TODO: more than 2 components
        const dropdown0 = dropdownMenus.find("#component-0");
        selectDropdownValue(dropdown0.find("[data-value='" + componentBatches[0][i].id + "']"));

        const dropdown1 = dropdownMenus.find("#component-1");
        selectDropdownValue(dropdown1.find("[data-value='" + componentBatches[1][permutation[i]].id + "']"));

        const components = [
            {
                name: dataStore.components[0],
                characteristics: componentBatches[0][i].getCharacteristicValues()
            },
            {
                name: dataStore.components[1],
                characteristics: componentBatches[1][permutation[i]].getCharacteristicValues()
            }
        ];
        components.push();
        components.push();

        const value = formatFloat(Math.abs(values[i]));
        calculateConvolution(components, qc).then((result) => {
            showConvolutionPlot(type + "-allocation-plots-" + i, result, 350, 0, Math.ceil(Math.sqrt(n_testPoints)), methodName + ": " + value);
        });
    }
}