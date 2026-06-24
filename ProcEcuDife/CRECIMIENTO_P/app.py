import csv
import math
import uuid
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# CRÍTICO - Gestión de Almacenamiento y Rutas con pathlib
# Se obtiene la ruta absoluta donde se encuentra este script
BASE_DIR = Path(__file__).resolve().parent

# Se define la constante para el directorio de datos (compatible con Win/Linux)
DATA_DIR = BASE_DIR / "data" / "poblacion"

# Aseguramos la existencia del directorio padre y del propio DATA_DIR
DATA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Simulador de Crecimiento Demográfico")

class SimulationRequest(BaseModel):
    """
    Estructura de datos para los parámetros del modelo logístico/malthusiano.
    """
    p0: float  # Población inicial
    r: float   # Tasa de crecimiento intrínseca (natalidad - mortalidad)
    k: float   # Capacidad de carga del entorno
    years: int # Años a simular

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """
    Sirve el archivo frontend asegurando la ruta correcta con pathlib.
    """
    index_path = BASE_DIR / "index.html"
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/simulate")
async def run_simulation(data: SimulationRequest):
    """
    Calcula el crecimiento poblacional año por año usando el Modelo Logístico.
    Ecuación Diferencial: dP/dt = r*P*(1 - P/K)
    Solución analítica: P(t) = K / (1 + A*e^(-rt)) donde A = (K - P0)/P0
    Guarda los resultados en un archivo CSV.
    """
    sim_id = f"SIM-{str(uuid.uuid4())[:6].upper()}"
    resultados = []
    
    # Cálculo paso a paso (año por año)
    for t in range(data.years + 1):
        if data.k > 0 and data.p0 > 0:
            # Modelo Logístico
            A = (data.k - data.p0) / data.p0
            p_t = data.k / (1 + A * math.exp(-data.r * t))
        else:
            # Modelo Malthusiano clásico (si K=0 como flag o error)
            p_t = data.p0 * math.exp(data.r * t)
            
        resultados.append({
            "year": t, 
            "population": round(p_t, 2)
        })
        
    # Exportación automática del registro histórico a CSV en la ruta segura
    csv_filename = f"registro_{sim_id}.csv"
    csv_filepath = DATA_DIR / csv_filename
    
    with open(csv_filepath, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # Cabeceras especificadas en los requisitos
        writer.writerow(["Sim_ID", "Año", "Población Calculada", "Población Inicial", "Tasa (r)", "Capacidad (K)"])
        
        for r in resultados:
            writer.writerow([
                sim_id, 
                r["year"], 
                r["population"], 
                data.p0, 
                data.r, 
                data.k
            ])
            
    return {
        "status": "success",
        "sim_id": sim_id,
        "csv_saved_at": str(csv_filepath),
        "data": resultados
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
