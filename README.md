# Content Creator — PoC CrewAI

PoC de agencia de contenido multiagente con **CrewAI**, UI en **Chainlit** y trazabilidad opcional (**OpenLIT** / CrewAI Tracing).

## Flujo

1. **Analista** — Extrae puntos clave y el “gancho” del texto bruto (no redacta).
2. **Redactor** — Convierte la lista en borrador de hilo (tono edutainment, emojis, ≤1 por punto).
3. **Editor** — Corrige ortografía/gramática y asegura ≤280 caracteres por bloque (X/Twitter).

El orden se impone con **proceso secuencial** y **contexto** entre tareas.

## Requisitos

- Python 3.10+
- API key de OpenAI (por defecto CrewAI usa OpenAI para los agentes)

## Instalación

Con **uv** (entorno ya creado):

```powershell
cd content-creator   # o la ruta donde hayas clonado el repo
uv sync
```

O activar el venv y sincronizar:

```powershell
.\.venv\Scripts\Activate.ps1
uv sync
```

Copia las variables de entorno:

```powershell
copy .env.example .env
# Edita .env y añade OPENAI_API_KEY=sk-...
```

## Uso

### Interfaz chat (Chainlit)

```powershell
chainlit run app.py -w
```

Abre `http://localhost:8000`, pega un texto y obtendrás el hilo. En la UI verás los **pasos** (Analista, Redactor, Editor) como trazabilidad del flujo.

### Solo crew (CLI / script)

```python
from content_creator.crew import run_crew

result = run_crew("Tu texto largo aquí...")
print(result["output"])
# result["tasks_output"] tiene [salida_analista, salida_redactor, salida_editor]
```

## Trazabilidad (open-source)

### 1. Chainlit (incluido)

Cada ejecución muestra en la UI los tres pasos del crew (Analista → Redactor → Editor) con sus entradas/salidas.

### 2. OpenLIT (opcional)

[OpenLIT](https://github.com/openlit/openlit) usa OpenTelemetry para métricas y traces (coste, latencia, secuencia de tareas).

1. Clona y levanta OpenLIT (por ejemplo con Docker):
   ```powershell
   git clone https://github.com/openlit/openlit.git
   cd openlit
   docker compose up -d
   ```
2. En tu `.env`:
   ```env
   OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318
   ```
3. Vuelve a ejecutar `chainlit run app.py`. Las trazas se envían a OpenLIT (UI en `http://127.0.0.1:3000`).

### 3. CrewAI Tracing (opcional)

Traces integrados en [CrewAI AMP](https://app.crewai.com).

1. Cuenta en [app.crewai.com](https://app.crewai.com) y `crewai login`.
2. En `content_creator/crew.py`, en `Crew(...)` activa `tracing=True`.
3. O en `.env`: `CREWAI_TRACING_ENABLED=true`.

### Otras opciones documentadas por CrewAI

- [Langfuse](https://docs.crewai.com/en/observability/langfuse), [Langtrace](https://docs.crewai.com/en/observability/langtrace), [Arize Phoenix](https://docs.crewai.com/en/observability/arize-phoenix), etc. — ver [Observability](https://docs.crewai.com/en/observability/overview).

## Estructura del proyecto

No hay carpetas `backend/` y `frontend/` separadas: Chainlit sirve la UI y la lógica en el mismo proceso. La separación es lógica: `app.py` (entrada y capa de presentación) y `content_creator/` (lógica del crew, reutilizable sin UI).

```
content-creator/
├── app.py                 # Entrada Chainlit (presentación + orquestación)
├── content_creator/
│   ├── __init__.py
│   └── crew.py             # Agentes, tareas y crew CrewAI (lógica)
├── .env.example
├── pyproject.toml
└── README.md
```