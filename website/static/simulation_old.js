
const WIDTH = 1000, HEIGHT = 800;
const app = new PIXI.Application({ width: WIDTH, height: HEIGHT, backgroundColor: 0x1099bb, resolution:
                                   window.devicePixelRatio || 1, antialias: true});


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

    for (i=0; i < coords.length; i+= 2){
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

function placeBases(app, bases) {
    bases.forEach(base => {
        let graphics = new PIXI.Graphics();
        graphics.beginFill(base.color);
        graphics.drawRoundedRect(base.x, base.y, 5, 5, 0.5);
        graphics.endFill();
        graphics.interactive = true
        graphics.mouseover = function() { console.log("Moused over ", base.name); }
        app.stage.addChild(graphics)
    })
}

simulation_started = false;

function startSimulation(){
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

sprite_dict = {"Merchant Manager": "static/assets/merchant_12x8.png",
               "China Navy Manager": "static/assets/hunter_12x8.png",
               };

function createSprite(type_of_agent){
    let sprite = PIXI.Sprite.from(sprite_dict[type_of_agent]);
    sprite.width = 12;
    sprite.height = 8;
    sprite.anchor.set(0.5);
    return sprite;
}

function updatePlot(agents) {
    agents.forEach(agent => {
        if (!agent_data[agent.agent_id]){
            agent_data[agent.agent_id] = agent
        }
        let [x, y] = lonLatToCanvas(agent.x, agent.y)
        agent.x = x
        agent.y = y
        if (!sprites[agent.agent_id] & agent.activated == true) {
            let sprite = createSprite(agent.type)
            sprite.x = agent.x;
            sprite.y = agent.y;
            app.stage.addChild(sprite);
            sprites[agent.agent_id] = sprite;
        } else {
            if (agent.activated == false){
                sprite = sprites[agent.agent_id];
                app.stage.removeChild(sprite);
                delete sprites[agent.agent_id];
            } else{
                sprites[agent.agent_id].x = agent.x;
                sprites[agent.agent_id].y = agent.y;
            }
        }
    });
}

function updateLogs(event) {
    text = event.text
    var txt = document.getElementById('sim-logs');
    txt.value = text.concat("\n") + txt.value;

    event_type = event.event_type;
    switch(event_type){
        case "Merchant Seized":
            var txt = document.getElementById('merchant-log-seized');
            console.log(txt.innerHTML);
            txt.innerHTML = 1 + parseInt(txt.innerHTML);
            break;
        case "Merchant Arrived":
            var txt = document.getElementById('merchant-log-arrived');
            console.log(txt.innerHTML);
            txt.innerHTML = 1 + parseInt(txt.innerHTML);
        case "Merchant Sunk":
//            # TODO: work this out
            break;
        default:
            console.log("No log for event type ", event_type)
            break;
    }
}

function updateTime(time_stamp) {
    var txt = document.getElementById('world-time');
    txt.textContent = time_stamp;
}

updatePlot(agent_data);

convertCoordsToCanvas(landmasses, bases);
placeLandmasses(app, landmasses);
placeBases(app, bases);

socket.on("update_plot", (data) => updatePlot(data));
socket.on("update_logs", (data) => updateLogs(data));
socket.on("update_time", (data) => updateTime(data));

