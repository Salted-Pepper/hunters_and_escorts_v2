function createROETable() {
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
    agentHeader.style.width = "100px";
    agentHeader.textContent = "Agent";
    headerRow.appendChild(agentHeader);

    Object.keys(current_roe[Object.keys(current_roe)[0]]).forEach(key => {
        let th = document.createElement("th");
        th.style.width = "30px";
        th.align = "center";
        th.textContent = key;
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    let tbody = document.createElement("tbody");
    Object.keys(current_roe).forEach(agent => {
        let row = document.createElement("tr");

        let agentCell = document.createElement("td");
        agentCell.style.width = "30px";
        agentCell.textContent = agent;
        row.appendChild(agentCell);

        Object.values(Object.keys(current_roe[agent])).forEach(zone => {
            let current_value = current_roe[agent][zone]
            let cell = document.createElement("td");
            cell.style.width = "30px";
            cell.align = "center";

            var selectList = document.createElement("select");
            selectList.id = "select-".concat(agent, "-", zone);
            selectList.name = "select-".concat(agent, "-", zone);

            min_val = min_roe[agent][zone]

            for (var i = min_val; i < 5; i++){
                var option = document.createElement("option");
                option.value = i;
                option.text = i;
                selectList.appendChild(option);
            }
            selectList.value = current_value;
            cell.appendChild(selectList);
            row.appendChild(cell);
        });

        tbody.appendChild(row);
    });

    table.appendChild(tbody);

    let tableContainer = document.querySelector(".table-container");
    tableContainer.appendChild(table);

}

createROETable();
