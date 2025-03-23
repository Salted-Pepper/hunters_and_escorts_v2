function createOOBTable() {
    let container = document.querySelector(".centered-container");
    if (!container) {
        console.error("Centered container not found.");
        return;
    }

    let table = document.createElement("table");
    table.border = "1";
    table.classList.add("standard-table");
    table.align = "center";


    let thead = document.createElement("thead");
    let headerRow = document.createElement("tr");

    let merchantHeader = document.createElement("th");
    merchantHeader.style.width = "80px";
    merchantHeader.textContent = "Code";
    headerRow.appendChild(merchantHeader);

    let th = document.createElement("th");
    th.style.width = "40px";
    th.align = "center";
    th.textContent = "# Arrivals";
    headerRow.appendChild(th);

    thead.appendChild(headerRow);
    table.appendChild(thead);

    let tbody = document.createElement("tbody");
    Object.keys(current_oob).forEach(merchantType => {
        let row = document.createElement("tr");

        let merchantCell = document.createElement("td");
        merchantCell.style.width = "80px";
        merchantCell.textContent = merchantType;
        row.appendChild(merchantCell);

        let current_value = current_oob[merchantType]["arrivals"];

        let cell = document.createElement("td");
        cell.style.width = "80px";
        cell.align = "center";

        var input = document.createElement("input");
        input.id = "oob-".concat(merchantType);
        input.name = "oob-".concat(merchantType);
        input.type = "number";
        input.min = 0;
        input.step = 1;
        input.value = current_value;
        input.style.width = "60px";
        input.style.align = "center";

        cell.appendChild(input);
        row.appendChild(cell);

        tbody.appendChild(row)
    });

    table.appendChild(tbody)

    let tableContainer = document.querySelector(".table-container")
    tableContainer.appendChild(table)
}

createOOBTable();
