/**
 * Author: Alexander Albers
 * Date:   04.12.2020
 */

/**
 * Called, when a new file has been selected in the file chooser.
 */
function onFileSelected(fileChooser) {
    // Get the file that has been selected
    const file = fileChooser.files[0];
    if (file === undefined) {
        return;
    }
    const component = fileChooser.getAttribute('data-value');

    // Set new placeholder text
    $("#file-text-" + component.toLowerCase()).text(file.name);

    // Read the contents of the file using a File-Reader
    const reader = new FileReader();
    reader.addEventListener('load', e => {
        // Parse the csv file
        const text = e.target.result;
        const data = Plotly.d3.dsv(";").parse(text.replaceAll(",", "."));

        onComponentDataUploaded(data, component);
    });

    reader.readAsText(file);
}

/**
 * Called when the read CSV file has been processed.
 * @param data
 * @param component the component which data has been uploaded.
 */
async function onComponentDataUploaded(data, component) {
    await dataStore.setData(component, data, true);

    // Create dropdowns for the main input view
    createBatchKltDropdown($("#input-dropdown-" + component.toLowerCase()), dataStore.batches[component], (batchId, kltId) => {
        // update the plots in the first tab whenever a new item from the dropdown has been selected
        showPlot(component, batchId, kltId);
    });

    // Fire event when all data has been uploaded.
    if (dataStore.isComplete) {
        $(document).trigger("ReKoNet:allComponentsUploaded");
    }
}

$(document).on("ReKoNet:allComponentsUploaded", function () {
    $("#data-upload-button").removeAttr("disabled");
});
$(document).ready(function () {
    $("#qc-dropdown .dropdown-menu a").click(function () {
        const qc = $(this).data("value");
        postRequest("/uploadCustomerData/qcStrategy?c=" + currentConfig, qc);
    });
});

async function uploadData() {
    if (!dataStore.isComplete) {
        return;
    }
    const $spinner = $("#data-upload-button-spinner");
    $spinner.show();

    const payload = dataStore.components
        .reduce((result, component) => {
            result[component] = dataStore.getCharacteristicValuesNested(component, undefined, undefined);
            return result;
        }, {});
    const response = await postRequest("/uploadCustomerData/componentData?c=" + currentConfig, payload);
    const $upload = $("#upload-alert");
    $upload.text(response["status"]);
    $upload.fadeIn().delay(2000).fadeOut();

    $spinner.hide();
}
