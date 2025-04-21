function createCoalitionTable() {
    let container = document.querySelector(".right-shifted-centered-container");
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

    let agentHeader = document.createElement("th");
    agentHeader.style.width = "200px";
    agentHeader.textContent = "Agent";
    headerRow.appendChild(agentHeader);

    Object.keys(coalition_info[Object.keys(coalition_info)[0]]).forEach(key => {
        let th = document.createElement("th");
        th.style.width = "20px";
        th.align = "center";
        th.textContent = key;
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    let tbody = document.createElement("tbody");
    Object.keys(coalition_info).forEach(agent => {
        let row = document.createElement("tr");
        row_info[agent] = row

        let agentCell = document.createElement("td");
        agentCell.textContent = agent;
        row.appendChild(agentCell);

        Object.values(Object.keys(coalition_info[agent])).forEach(zone => {
            let current_value = coalition_info[agent][zone];
            let cell = document.createElement("td");
            cell.style.width = "80px";
            cell.align = "center";

            var selector = document.createElement("input");
            selector.id = "select-".concat(agent, "-", zone);
            selector.name = "select-".concat(agent, "-", zone);

            selector.type = 'number';
            selector.min = 0;
            selector.max = 1;
            selector.step = 0.01;
            selector.value = current_value.toFixed(2);
            selector.style.width = "50px";
            selector.style.fontSize = "10px";
            selector.style.marginBottom = "3px";
            selector.setAttribute("onchange", "checkAssignmentConditions()");
            cell.appendChild(selector);
            row.appendChild(cell);
        });

        tbody.appendChild(row);
    });

    table.appendChild(tbody);

    let tableContainer = document.querySelector(".table-container:nth-of-type(2)");
    tableContainer.appendChild(table);
}

createCoalitionTable();
