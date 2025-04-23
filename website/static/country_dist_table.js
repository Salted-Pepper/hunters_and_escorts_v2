function createCountryDistTable() {
    let container = document.querySelector(".centered-container");

    let table = document.createElement("table");
    table.border = "1";
    table.classList.add("standard-table");
    table.align = "center";

    let thead = document.createElement("thead");
    let headerRow = document.createElement("tr");

    Object.keys(country_info[Object.keys(country_info)[0]]).forEach(key => {
        let th = document.createElement("th");
        th.style.width = "60px";
        th.align = "center";
        th.textContent = key;
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    let tbody = document.createElement("tbody");

    let row = document.createElement("tr");

    Object.keys(country_info).forEach(country => {
        let current_value = country_info[country]
        let countryCell = document.createElement("td");
        countryCell.style.width = "60px";
        countryCell.textContent = country;

        var slider = document.createElement("input");
        slider.id = "select-".concat(country);
        slider.name = "select-".concat(country);

        slider.type = 'range';
        slider.min = 0;
        slider.max = 1;
        slider.step = 0.01;
        slider.value = current_value;
        slider.style.width = "60px";

        countryCell.appendChild(slider);
        row.appendChild(countryCell);

        tbody.appendChild(row);
    });

    table.appendChild(tbody);

    let tableContainer = document.querySelector(".table-container:nth-of-type(3)");
    tableContainer.appendChild(table);
}

createCountryDistTable();