function createChinaTable() {
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
    agentHeader.style.width = "500px";
    agentHeader.textContent = "Agent";
    headerRow.appendChild(agentHeader);

    Object.keys(china_info[Object.keys(china_info)[0]]).forEach(key => {
        let th = document.createElement("th");
        th.style.width = "20px";
        th.align = "center";
        th.textContent = key;
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    let tbody = document.createElement("tbody");
    Object.keys(china_info).forEach(agent => {
        let row = document.createElement("tr");

        let agentCell = document.createElement("td");
        agentCell.style.width = "350px";
        agentCell.textContent = agent;
        row.appendChild(agentCell);

        Object.values(Object.keys(china_info[agent])).forEach(zone => {
            let current_value = china_info[agent][zone]
            let cell = document.createElement("td");
            cell.style.width = "40px";
            cell.align = "center";

            var slider = document.createElement("input");
            slider.id = "select-".concat(agent, "-", zone);
            slider.name = "select-".concat(agent, "-", zone);
            console.log("Option name is: ", slider.name, " with value ", current_value);

            slider.type = 'range';
            slider.min = 0;
            slider.max = 1;
            slider.step = 0.01;
            slider.value = current_value;
            slider.style.width = "40px";

            cell.appendChild(slider);
            row.appendChild(cell);
        });

        tbody.appendChild(row);
    });

    table.appendChild(tbody);

    let tableContainer = document.querySelector(".table-container:nth-of-type(1)");
    tableContainer.appendChild(table);
}

createChinaTable();
