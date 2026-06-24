import json
import uuid
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# CRÍTICO - Gestión de Almacenamiento y Rutas
# Determinamos el directorio base del script para evitar problemas de rutas relativas
BASE_DIR = Path(__file__).resolve().parent

# Definimos el PATH estructural para los logs de la simulación
OUTPUT_PATH = BASE_DIR / "logs" / "simulaciones_virus"

# Validación por código: si el PATH no existe, se crea recursivamente
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Simulador Epidemiológico de Redes - WannaCry")

class SimulationConfig(BaseModel):
    """
    Parámetros de entrada para configurar el modelo SIR.
    Basado libremente en la propagación real del ransomware WannaCry (2017).
    """
    total_nodes: int      # N: Total de computadoras en la red vulnerable
    initial_infected: int # I(0): Computadoras inicialmente infectadas
    beta: float           # Tasa de contagio (infección por hora)
    gamma: float          # Tasa de recuperación (parcheado por hora)
    duration_hours: int   # Tiempo total de la simulación en horas

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """
    Despliega el archivo HTML del frontend.
    """
    index_file = BASE_DIR / "index.html"
    with open(index_file, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/simulate_attack")
async def execute_simulation(config: SimulationConfig):
    """
    Ejecuta el modelo matemático SIR (Susceptible, Infectado, Recuperado).
    Las métricas horarias generadas se empaquetan y se escriben en el OUTPUT_PATH.
    """
    sim_id = f"WCRY-{str(uuid.uuid4())[:6].upper()}"
    
    # Condiciones iniciales
    S = config.total_nodes - config.initial_infected
    I = config.initial_infected
    R = 0
    N = config.total_nodes
    
    timeline_metrics = []
    
    # Integración numérica simple por el método de Euler (paso dt = 1 hora)
    dt = 1.0
    for hour in range(config.duration_hours + 1):
        # Registro del estado actual
        timeline_metrics.append({
            "hour": hour,
            "susceptible": int(S),
            "infected": int(I),
            "recovered": int(R)
        })
        
        # Sistema de Ecuaciones Diferenciales Ordinarias (EDO)
        # dS/dt = -(beta * S * I) / N
        # dI/dt = (beta * S * I) / N - gamma * I
        # dR/dt = gamma * I
        dS = - (config.beta * S * I) / N
        dI = (config.beta * S * I) / N - config.gamma * I
        dR = config.gamma * I
        
        # Aplicación del cambio (Euler)
        S += dS * dt
        I += dI * dt
        R += dR * dt
        
        # Evitar números negativos por errores de precisión
        S = max(0, S)
        I = max(0, I)
        R = max(0, R)
        
    # Empaquetado y almacenamiento de auditoría
    audit_log = {
        "simulation_id": sim_id,
        "malware_profile": "WannaCry Ransomware",
        "parameters": config.model_dump(),
        "telemetry": timeline_metrics
    }
    
    log_filename = f"audit_log_{sim_id}.json"
    log_filepath = OUTPUT_PATH / log_filename
    
    # Escritura en el PATH crítico definido
    with open(log_filepath, "w", encoding="utf-8") as file:
        json.dump(audit_log, file, indent=4)
        
    return {
        "status": "success",
        "audit_file": str(log_filepath),
        "metrics": timeline_metrics
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
