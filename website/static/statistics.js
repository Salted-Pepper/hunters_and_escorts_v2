let checkboxes_attackers = {};
let checkboxes_targets = {};

function requestUpdate(){
    socket.emit("request-update-statistics",
                getCheckedCheckboxes(checkboxes_attackers),
                getCheckedCheckboxes(checkboxes_targets))
}

function getCheckedCheckboxes(checkboxes) {
  const checked = [];

  for (const [name, checkbox] of Object.entries(checkboxes)) {
    if (checkbox.checked) {
        agent_type = checkbox.id
        checked.push(agent_type);
    }
  }

  return checked;
}

function generate_selection_options(){
    let attacker_list = document.querySelector(".attacker-selector");
    let target_list = document.querySelector(".target-selector");

    agent_types.forEach(agent_type => {
        if (!agent_type.includes("Merchant")){
            var attacker_checkbox = document.createElement("input");
            attacker_checkbox.type = 'checkbox';
            attacker_checkbox.id = agent_type;
            attacker_checkbox.addEventListener('change', requestUpdate)
            attacker_checkbox.checked = true;
            attacker_label = document.createElement("Label");
            attacker_label.setAttribute("for", attacker_checkbox.id);
            attacker_label.innerHTML = agent_type;
            attacker_label.style.marginLeft = "6px";

            attacker_list.appendChild(attacker_checkbox);
            attacker_list.appendChild(attacker_label);
            attacker_list.appendChild(document.createElement("br"));
            checkboxes_attackers[agent_type] = attacker_checkbox;
        }

        var target_checkbox = document.createElement("input");
        target_checkbox.type = 'checkbox';
        target_checkbox.id = agent_type;
        target_checkbox.addEventListener('change', requestUpdate)
        target_checkbox.checked = true;
        target_label = document.createElement("Label");
        target_label.setAttribute("for", target_checkbox.id);
        target_label.innerHTML = agent_type;
        target_label.style.marginLeft = "6px";

        target_list.appendChild(target_checkbox);
        target_list.appendChild(target_label);
        target_list.appendChild(document.createElement("br"));

        checkboxes_targets[agent_type] = target_checkbox;
    })
}
generate_selection_options();

let socket = io.connect("http://" + document.domain + ":" + location.port);
socket.emit("request-update-statistics",
             getCheckedCheckboxes(checkboxes_attackers),
             getCheckedCheckboxes(checkboxes_targets));

function checkImage(imageSrc, success, fail) {
        var img = new Image();
        img.onload = success;
        img.onerror = fail;
        img.src = imageSrc;
}

function tryToUpdateImage(path, image_id){
    default_path = "static/assets/graph_placeholder.png";
    checkImage(path, function(){document.getElementById(image_id).src=path;},
                     function(){document.getElementById(image_id).src=default_path;});
}

function updateStatistics(){
    tryToUpdateImage("static/assets/turn-losses.png?random="+new Date().getTime(), "turn-losses-fig")
    tryToUpdateImage("static/assets/country-losses.png?random="+new Date().getTime(), "country-losses-fig")
    tryToUpdateImage("static/assets/losses-cause.png?random="+new Date().getTime(), "losses-cause-fig")
}


function updateLogs(events) {
    events = JSON.parse(events);
    console.log(events)
    var new_logger_text = "";

    for (let i=0; i<events.length; i++){
        let event = events[i];

        new_logger_text = event.time + " - " + event.text + "\n" + new_logger_text;
    }
    document.getElementById('filtered-sim-logs').value = new_logger_text;
}

socket.on("updated_statistics", (data) => updateStatistics(data));
socket.on('filtered_logs', (data) => updateLogs(data));
