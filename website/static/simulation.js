
const WIDTH = 1000, HEIGHT = 700;
const app = new PIXI.Application({ width: WIDTH, height: HEIGHT, backgroundColor: 0x1099bb, resolution:
                                    1, antialias: true});


let container = document.querySelector(".simulation-container");
container.appendChild(app.view);
console.log("Connecting to Socket...");
let socket = io.connect("http://" + document.domain + ":" + location.port);
let sprites = {};

function lonLatToCanvas(lat, lon) {
    let x = WIDTH * ((lat - min_lat) / (max_lat - min_lat));
    let y = HEIGHT - HEIGHT * ((lon - min_lon) / (max_lon - min_lon));
    return [x, y];
}

function flatListOfCoordsToCanvasCoords(coords){
    var convertedArray = [];

    for (let i=0; i < coords.length; i+= 2){
        let lat = coords[i];
        let lon = coords[i + 1];
        let [x, y] = lonLatToCanvas(lat, lon);
        convertedArray = convertedArray.concat([x, y]);
    }
    return convertedArray;
}

function convertCoordsToCanvas(landmasses, bases){
    landmasses.forEach(landmass => {
        let new_coords = flatListOfCoordsToCanvasCoords(landmass.coords)
        landmass.coords = new_coords;
    })

    bases.forEach(base => {
        let new_coords = lonLatToCanvas(base.x, base.y)
        base.x = new_coords[0]
        base.y = new_coords[1]
    })
}

function placeLandmasses(app, landmasses) {

    landmasses.forEach(landmass => {
        let graphics = new PIXI.Graphics();
        graphics.beginFill(landmass.color);
        graphics.drawPolygon(landmass.coords);
        graphics.endFill();

        app.stage.addChild(graphics);
    })
}


simulation_started = false;

function startSimulation(){
    let start_button = document.getElementById("start-button");
    start_button.innerHTML = "Running Simulation...";
    start_button.style.backgroundColor = "red";
    start_button.disabled = true;

    if(simulation_started){
        var txt = document.getElementById('sim-logs');
        txt.value = "Continuing Simulation...\n" + txt.value
    }
    else{
        simulation_started = true;
        var txt = document.getElementById('sim-logs');
        txt.value += "Starting Simulation...\n" + txt.value
    }
    socket.emit("start");
}

sprite_dict = {"Merchant Manager": "static/assets/merchant_24x16.png",
               "China Navy Manager": "static/assets/hunter_24x16.png",
               "China Air Manager": "static/assets/cn_aircraft_24x16.png",
               "TW Escort Manager": "static/assets/escort_tw_24x16.png",
               "JP Escort Manager": "static/assets/escort_jp_24x16.png",
               "US Escort Manager": "static/assets/escort_us_24x16.png",
               "Harbour": "static/assets/anchor_grey_16x16.png",
               "AirportRed": "static/assets/airport_red_16x16.png"};

function placeBases(app, bases) {
    bases.forEach(base => {
        let sprite = PIXI.Sprite.from(sprite_dict[base.icon]);
        sprite.width = 16;
        sprite.height = 16;
        sprite.anchor.set(0.5);
        sprite.x = base.x;
        sprite.y = base.y;
        app.stage.addChild(sprite);
    })
}

function createSprite(type_of_agent){
    let sprite = PIXI.Sprite.from(sprite_dict[type_of_agent]);
    sprite.width = 24;
    sprite.height = 16;
    sprite.alpha = 0.8;
    sprite.anchor.set(0.5);
    sprite.interactive = true;
    return sprite;
}

function updatePlot(agents) {
    let agent_ids = agents.map(agent => agent.agent_id);
    Object.keys(sprites).forEach(key => {
        sprite = sprites[key];

        if (!(key in agents)){
            app.stage.removeChild(sprite);
            delete sprites[key];
        }
    })

    agents.forEach(agent => {
        if (!agent_data[agent.agent_id]){
            agent_data[agent.agent_id] = agent;
        }
        let [x, y] = lonLatToCanvas(agent.x, agent.y);
        agent.x = x;
        agent.y = y;
        if (!sprites[agent.agent_id] & agent.activated == true) {
            let sprite = createSprite(agent.type);
            sprite.x = agent.x;
            sprite.y = agent.y;

            app.stage.addChild(sprite);
            sprites[agent.agent_id] = sprite;

            var text = agent.service + ' - ' + agent.agent_id + '\non ' + agent.mission + '\nEndurance ' + agent.rem_endurance.toFixed(0);
            var message = new PIXI.Text(text, {fontSize: 16, fill: 0xff1010});
            sprite.message = message

            sprite.on('mouseover', function(event){
                    sprite.message.x = event.data.global.x + 10;
                    sprite.message.y = event.data.global.y;
                    app.stage.addChild(sprite.message)
                });

            sprite.on('mousemove',function (event) {
                if (!sprite.message) {
                    return;
                }

                sprite.message.x = event.data.global.x + 10;
                sprite.message.y = event.data.global.y;
            });

            sprite.on('mouseout', function(event){
                app.stage.removeChild(sprite.message);
            });

        } else {
            if (agent.activated == false & Object.hasOwn(sprites, agent.agent_id)){
                sprite = sprites[agent.agent_id];
                if (Object.hasOwn(sprite, 'message')){
                    app.stage.removeChild(sprite.message);
                }
                app.stage.removeChild(sprite);
                delete sprites[agent.agent_id];

            } else if(agent.activated == true) {
                sprite = sprites[agent.agent_id];
                sprite.x = agent.x;
                sprite.y = agent.y;
                sprite.message.x = sprite.x + 10;
                sprite.message.y = sprite.y;

                app.stage.removeChild(sprite.message);
                var text = agent.service + ' - ' + agent.agent_id + '\non ' + agent.mission + '\nEndurance ' + agent.rem_endurance.toFixed(0);
                var message = new PIXI.Text(text, {fontSize: 16, fill: 0xff1010});
                sprite.message = message

            }
        }
    });
}

function updateLogs(events) {
    events = JSON.parse(events);
    console.log(events)
    var new_logger_text = "";

    var selected_time = parseFloat(document.getElementById('world_time_select').value);

    var event_counts = {"Merchant Seized": 0,
                        "Merchant Destroyed": 0,
                        "Merchant CTL": 0,
                        "Merchant Arrived": 0,
                        "Escort Destroyed": 0,
                        "Submarine Destroyed": 0,
                        "Aircraft Destroyed": 0,
                        "Hunter Deterred": 0,
                        "Hunter Destroyed": 0,
    };

    for (let i=0; i<events.length; i++){
        let event = events[i];

        if (event.time > selected_time){
            break;
        }
        new_logger_text = event.time + " - " + event.text + "\n" + new_logger_text;
        event_counts[event.event_type] += 1;

    }

    document.getElementById('merchant-log-seized').innerHTML = event_counts["Merchant Seized"];
    document.getElementById('merchant-log-sunk').innerHTML = event_counts["Merchant Destroyed"];
    document.getElementById('merchant-log-damaged').innerHTML = event_counts["Merchant CTL"];
    document.getElementById('merchant-log-arrived').innerHTML = event_counts["Merchant Arrived"];

    document.getElementById('escorts-log-sunk').innerHTML = event_counts["Escort Destroyed"];
    document.getElementById('aircraft-log-sunk').innerHTML = event_counts["Aircraft Destroyed"];
    document.getElementById('submarines-log-sunk').innerHTML = event_counts["Submarine Destroyed"];

    document.getElementById('escorts-log-deterred').innerHTML = event_counts["Hunter Deterred"];
    document.getElementById('hunters-log-sunk').innerHTML = event_counts["Hunter Destroyed"];

    document.getElementById('sim-logs').value = new_logger_text;
}

function updateTime(time_stamp) {
    var world_time_select = document.getElementById('world_time_select')
    world_time_select.value = time_stamp;
}

function requestTimestampUpdate() {
    var world_time = parseFloat(document.getElementById('world_time_select').value);
    var max_time = parseFloat(document.getElementById('world_time_select').max);
    if (world_time > max_time){
        world_time = max_time;
        document.getElementById('world_time_select').value = max_time;
    }

    if (world_time > 0){
        socket.emit('request_timestamp_data', world_time);
    }
}

function completedSimulation(new_time) {
//  Update Top Scroll time
    var max_time = document.getElementById('world_time_select');
    max_time.max = new_time;
//  Re-enable button
    let start_button = document.getElementById("start-button");
    start_button.innerHTML = "Continue Simulation";
    start_button.style.backgroundColor = "green";
    start_button.disabled = false;
}


updatePlot(agent_data);

convertCoordsToCanvas(landmasses, bases);
placeLandmasses(app, landmasses);
placeBases(app, bases);

socket.on("update_plot", (data) => updatePlot(data));
socket.on("update_logs", (data) => updateLogs(data));
socket.on("update_time", (data) => updateTime(data));
socket.on("completed_simulation", (data) => completedSimulation(data));

