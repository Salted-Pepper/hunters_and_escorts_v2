function createTargetTable() {
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

    let agentHeader = document.createElement("th");
    agentHeader.style.width = "200px";
    agentHeader.textContent = "Agent";
    headerRow.appendChild(agentHeader);

    Object.keys(target_rules[Object.keys(target_rules)[0]]).forEach(key => {
        let th = document.createElement("th");
        th.style.width = "20px";
        th.align = "center";
        th.textContent = key;
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    let tbody = document.createElement("tbody");
    Object.keys(target_rules).forEach(h_agent => {
        let row = document.createElement("tr");

        let agentCell = document.createElement("td");
        agentCell.style.width = "30px";
        agentCell.textContent = h_agent;
        row.appendChild(agentCell);

        Object.values(Object.keys(target_rules[h_agent])).forEach(c_agent => {
            let current_value = target_rules[h_agent][c_agent];
            let cell = document.createElement("td");
            cell.style.width = "20px";
            cell.align = "center";

            var checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.checked = current_value;
            checkbox.id = "check-".concat(h_agent, "-", c_agent);
            checkbox.name = "check-".concat(h_agent, "-", c_agent);
            cell.appendChild(checkbox);
            row.appendChild(cell);
        });

        tbody.appendChild(row);
    });

    table.appendChild(tbody);

    let tableContainer = document.querySelector(".table-container");
    tableContainer.appendChild(table);
}

createTargetTable();
