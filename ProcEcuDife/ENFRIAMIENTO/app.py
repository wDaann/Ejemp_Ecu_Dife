import os
import json
import math
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# CRÍTICO - Gestión de Almacenamiento y Rutas
STORAGE_PATH = r"C:\Users\danie\ProcEcuDife\ENFRIAMIENTO"

# Verifica si el directorio existe; si no, lo crea automáticamente al iniciar el script
os.makedirs(STORAGE_PATH, exist_ok=True)

# Inicialización de la aplicación FastAPI
app = FastAPI(title="Simulador de Enfriamiento de Newton")

class SimulationRequest(BaseModel):
    """
    Esquema de datos esperado desde el frontend para la simulación.
    """
    t0: float  # Temperatura inicial del alimento
    tm: float  # Temperatura ambiente
    k: float   # Constante de proporcionalidad de enfriamiento
    t_max: int # Tiempo máximo de simulación en segundos

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """
    Sirve el archivo HTML (frontend) ubicado en el mismo directorio.
    """
    # Usamos rutas absolutas basadas en la ubicación de este archivo (app.py)
    # para evitar errores cuando se ejecuta desde un directorio de trabajo distinto.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "index.html")
    
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return html_content

@app.post("/api/simulate")
async def simulate_cooling(data: SimulationRequest):
    """
    Calcula el enfriamiento en base a la solución analítica de la EDO de Newton:
    dT/dt = -k(T - Tm)  =>  T(t) = Tm + (T0 - Tm) * exp(-k * t)
    
    Genera la serie temporal de temperaturas y la exporta a un archivo JSON.
    """
    # Generación de datos de simulación
    tiempos = list(range(0, data.t_max + 1))
    temperaturas = [
        data.tm + (data.t0 - data.tm) * math.exp(-data.k * t) 
        for t in tiempos
    ]
    
    # Estructuración de los resultados
    resultados = {
        "modelo": "Ley de Enfriamiento de Newton",
        "parametros": {
            "T0": data.t0,
            "Tm": data.tm,
            "k": data.k
        },
        "datos": [
            {"tiempo": t, "temperatura": round(temp, 3)} 
            for t, temp in zip(tiempos, temperaturas)
        ]
    }
    
    # Generación de un nombre único con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sim_enfriamiento_{timestamp}.json"
    filepath = os.path.join(STORAGE_PATH, filename)
    
    # Exportación automática de datos al PATH definido
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(resultados, file, indent=4)
        
    return {
        "status": "success",
        "filepath": filepath,
        "resultados": resultados
    }

if __name__ == "__main__":
    # Ejecuta el servidor de desarrollo en http://localhost:8000
    uvicorn.run(app, host="127.0.0.1", port=8000)
