/**
 * Author: Alexander Albers
 * Date:   04.12.2020
 */


/**
 * Select a dropdown entry on click.
 */
$(document).ready(() => {
    $(".dropdown-menu a").click(function () {
        selectDropdownValue($(this));
    });
    $(".dropdown-menu").each(function () {
        selectDropdownValue($(this).find(".active"));
    });
});

function selectDropdownValue(selected) {
    const parent = selected.parent();
    // remove active attribute from previously selected item
    parent.find(".active").removeClass("active");
    // set current item as active
    selected.addClass("active");
    // update title
    const toggle = parent.parent().find(".dropdown-toggle");
    const name = toggle.data("name");
    if (name === undefined || name === "") {
        toggle.text(selected.text());
    } else {
        toggle.text(name + ": " + selected.text());
    }
}

/**
 * Create a dropdown menu for selecting batches and klts.
 * @param {*} parent the html parent element
 * @param {Batch[]} batches a dictionary of batches and matching klt ids.
 * @param {*} updateCallback update callback with the currently selected batch and klt id.
 */
function createBatchKltDropdown(parent, batches, updateCallback) {
    let selectedBatch = "";
    let selectedKlt = "";
    const menuParentBatch = $("<div>").attr("id", "batch");
    const menuParentKLT = $("<div>").attr("id", "klt");
    parent.empty();
    parent.append(menuParentBatch).append(menuParentKLT);

    // update callback when selecting a new KLT
    const kltUpdate = klt => {
        selectedKlt = klt;
        updateCallback(selectedBatch, selectedKlt);
    };
    // update callback when selecting a new Batch
    const batchUpdate = batch => {
        // Update KLT menu
        if (batch == "") {
            selectedKlt = "";
        }
        parent.find("#klt").replaceWith(createMenu("klt", "KLT", batch == "" ? [] : batches.find(entry => entry.batchId == batch).kltIds, 0, "Alle", kltUpdate));

        selectedBatch = batch;
        updateCallback(selectedBatch, selectedKlt);
    };

    // create both dropdown menus
    menuParentBatch.replaceWith(createMenu("batch", "Batch", batches.map(entry => entry.batchId), 0, "Alle", batchUpdate));
    menuParentKLT.replaceWith(createMenu("klt", "KLT", [], 0, "Alle", kltUpdate));

    // call the update callback with initial values.
    updateCallback(selectedBatch, selectedKlt);
}

function createComparisonMenus(parent, components, items, selectedIndex, updateCallback) {
    let selectedValues = items.map(i => i[selectedIndex]);
    for (let i = 0; i < components.length; i++) {
        const menu = createMenu("component-" + i, components[i], items[i], selectedIndex, "", value => {
            selectedValues[i] = value;
            updateCallback(selectedValues);
        });
        const existing = parent.find("#component-" + i);
        if (existing.length) {
            existing.replaceWith(menu);
        } else {
            parent.append(menu);
        }
    }
    updateCallback(selectedValues);
}

/**
 * Create a new dropdown menu with the specified name.
 * @param {string} id the HTML id of the new component.
 * @param {string} prefix the display name of the dropdown menu.
 * @param {string[]} entries entries of the dropdown menu.
 * @param {number} selectedIndex the default selected index.
 * @param {string} defaultEntry the default entry
 * @param {*} updateCallback callback after selecting a single item.
 * @param {string} color dropdown color.
 * @return the HTML (jQuery) component.
 */
function createMenu(id, prefix, entries, selectedIndex, defaultEntry, updateCallback, color = "btn-primary") {
    const menuParent = createDropdownMenu(id, prefix, entries, selectedIndex, defaultEntry, color);

    menuParent.find(".dropdown-menu a").click(function () {
        const val = $(this).data("value");
        selectDropdownValue($(this));

        // call the update callback
        updateCallback("" + val);
    });
    return menuParent;
}

/**
 * Create a new dropdown menu with the specified name or replace an existing one.
 * @param {*} parent HTML parent.
 * @param {string} id the HTML id of the new component.
 * @param {string} prefix the display name of the dropdown menu.
 * @param {string[]} entries entries of the dropdown menu.
 * @param {number} selectedIndex the default selected index.
 * @param {string} defaultEntry the default entry
 * @param {*} updateCallback callback after selecting a single item.
 * @param {string} color dropdown color.
 */
function createOrReplaceMenu(parent, id, prefix, entries, selectedIndex, defaultEntry, updateCallback, color = "btn-primary") {
    parent.find("#" + id).replaceWith(createMenu(id, prefix, entries, selectedIndex, defaultEntry, updateCallback, color));
}

/**
 * Creates a dropdown menu from the given items.
 * @param {string} id the HTML id of the new component.
 * @param {string} prefix name of the dropdown menu.
 * @param {string[]} items the items inside the dropdown menu.
 * @param {number} selectedIndex the default selected index.
 * @param {string} defaultItem the default item (not included in the items list).
 * @param {string} color dropdown color.
 * @return the HTML (jQuery) component.
 */
function createDropdownMenu(id, prefix, items, selectedIndex, defaultItem, color) {
    const dropdownToggle = $("<a>")
        .addClass("btn")
        .addClass(color)
        .addClass("dropdown-toggle")
        .attr("href", "#")
        .attr("role", "button")
        .attr("data-toggle", "dropdown")
        .attr("data-name", prefix);
    $(document).ready(function () {
        dropdownToggle.dropdown();
    });

    const dropdownMenu = $("<div>")
        .addClass("dropdown-menu");
    if (defaultItem !== "") {
        dropdownMenu.append(
            $("<a>")
                .attr("class", "dropdown-item active")
                .attr("data-value", "")
                .text(defaultItem)
        );
        dropdownToggle.text(prefix + ": " + defaultItem);
    } else {
        dropdownToggle.text(prefix + ": " + items[selectedIndex]);
    }
    for (let i = 0; i < items.length; i++) {
        dropdownMenu.append(
            $("<a>")
                .attr("class", defaultItem === "" && selectedIndex == i ? "dropdown-item active" : "dropdown-item")
                .attr("data-value", items[i])
                .text(items[i])
        );
    }

    return $("<div>")
        .attr("id", id)
        .addClass("dropdown")
        .append(dropdownToggle)
        .append(dropdownMenu);
}
