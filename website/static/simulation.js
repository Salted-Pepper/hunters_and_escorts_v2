
const WIDTH = 800, HEIGHT = 800;
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

function startSimulation(){
    console.log("Starting Simulation...")
    socket.emit("start")
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
//        TODO: MAKE THIS ACTUAL SPRITES INSTEAD OF GRAPHICS https://github.com/pixijs/pixijs/wiki/v4-Performance-Tips
//              https://pixijs.com/8.x/examples/sprite/basic
            let sprite = new PIXI.Graphics();
            sprite.beginFill(agent.color).drawCircle(0, 0, 2).endFill();
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

function updateLog(text) {
    var txt = document.getElementById('sim-logs');
    txt.value += text.concat("\n")
}

updatePlot(agent_data)

convertCoordsToCanvas(landmasses, bases);
placeLandmasses(app, landmasses);
placeBases(app, bases);

socket.on("update_plot", (data) => updatePlot(data));
socket.on("update_logs", (data) => updateLog(data));

