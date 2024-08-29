from fastapi import FastAPI, Request, Depends,Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import json
import random

import asyncio

from .tools.dataTool import Sensors
from .tools.pred import linear_regresion,arima,random_forest,sarima
# from .tools.const import *
from .tools.tools import *

app = FastAPI(debug=True)

token = readtxtline("data/token.txt")
host = "influxdb.canair.io"
sensors = Sensors("canairio", host)
templates = Jinja2Templates(directory="core/templates")

algorithm_names = ["originalData","linearRegression", "Arima", "randomForest","Sarima"]
algorithm_map = {
    "linearRegression": linear_regresion,
    "Arima": arima,
    "randomForest": random_forest,
    "Sarima":sarima,

}

formatted_data = []

async def update_sensor_data():
    global formatted_data
    while True:
        # Update the formatted data every 30 minutes
        formatted_data = sensors.get_formatted_data()
        await asyncio.sleep(1800)  # 1800 seconds = 30 minutes

@app.on_event("startup")
async def startup_event():
    # Start the background task to update sensor data every 30 minutes
    asyncio.create_task(update_sensor_data())


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    data = [
        {
            'type': 'Feature',
            'properties': {'name': 'Jardins du Trocadéro', 'pm25': 16},
            'geometry': {'type': 'Point', 'coordinates': [2.289207, 48.861561]},
        },
        {
            'type': 'Feature',
            'properties': {'name': 'Jardin des Plantes', 'pm25': 5},
            'geometry': {'type': 'Point', 'coordinates': [2.359823, 48.843995]},
        },
        {
            'type': 'Feature',
            'properties': {'name': 'Jardins das Tulherias', 'pm25': 9999},
            'geometry': {'type': 'Point', 'coordinates': [2.327092, 48.863608]},
        },
        {
            'type': 'Feature',
            'properties': {'name': 'Parc de Bercy', 'pm25': 12},
            'geometry': {'type': 'Point', 'coordinates': [2.382094, 48.835962]},
        },
        {
            'type': 'Feature',
            'properties': {'name': 'Jardin du Luxemburg', 'pm25': 6},
            'geometry': {'type': 'Point', 'coordinates': [2.336975, 48.846421]},
        },
    ] + formatted_data

    return templates.TemplateResponse("index.html", {"request": request, "token": token, "data": data})

@app.get("/{sensor_name}", response_class=HTMLResponse)
async def sensor(request: Request, sensor_name: str):
    return templates.TemplateResponse("sensors.html", {"request": request, "sensor_name": sensor_name})

@app.get("/{sensor_name}/predictions", response_class=HTMLResponse)
async def get_mlalgorithm(request: Request, sensor_name: str):
    random_list = [random.randint(0, 55) for _ in range(200)]
    data = sensors.data(sensor_name)[10:]
    #data = list(map(int,data))
    data = [int(value) for value in data if value is not None]
    #print(data,random_list)    
    return templates.TemplateResponse("ml_algorithms.html", {
        "request": request,
        "algorithm_names": algorithm_names,
        "data": data,
        "result": None
    })

@app.post("/{sensor_name}/predictions", response_class=HTMLResponse)
async def post_mlalgorithm(
    request: Request,
    sensor_name: str,
    algorithm: str = Form(...),
):  
    random_list = [random.randint(0, 55) for _ in range(200)]
    data = sensors.data(sensor_name)
    data = [int(value) for value in data if value is not None]

    #print(data)
    
    # Apply the selected algorithm
    if algorithm in algorithm_map:
        result = algorithm_map[algorithm](data)
    elif algorithm=="originalData":
        result = [[int(value) for value in data if value is not None],"0"]

    else:
        result = [random_list,"THE ALGORITHM SELECTED NOT EXIST"]  # If no valid algorithm is selected, return the original data
    print(data[0:20],result[0:20])
    #print("\n\nalgorithm",algorithm)
    return templates.TemplateResponse("ml_algorithms.html", {
        "request": request,
        "algorithm_names": algorithm_names,
        "data": list(map(int,result[0])),
        "result": "Error of "+str(result[1])
    })
