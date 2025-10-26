# FiscAI MCP — FiscMCP

README profesional (en español) para el proyecto FiscMCP. Este documento explica qué hace el proyecto, cómo instalarlo y ejecutarlo, cómo configurarlo y pasos de desarrollo y despliegue.

## Descripción

FiscAI MCP (FiscMCP) es un servidor de herramientas (MCP) orientado a ofrecer asesoría fiscal y financiera para micro y pequeñas empresas en México. Combina:

- Un motor de inteligencia artificial (Google Gemini) para generación de lenguaje y embeddings.
- Un backend de búsqueda semántica y almacenamiento (Supabase) para RAG (Retrieval-Augmented Generation).
- Herramientas para: recomendaciones fiscales, chat asistido, análisis de riesgo, búsqueda de documentos, roadmap de formalización, predicción de crecimiento (modelo ML) y apertura de mapas (deep links).

El núcleo está implementado con `fastmcp` (instancia `mcp` en `src/main.py`) y ofrece además un servidor HTTP opcional (`src/http_server.py`) para probar endpoints REST.

## Características principales

- Recomendaciones fiscales personalizadas gracias a RAG (embeddings + documentos relevantes).
- Chat asistido con detección automática de intención (por ejemplo, abrir mapa para bancos o SAT).
- Búsqueda semántica de documentos fiscales en Supabase.
- Análisis de riesgo fiscal y generación de roadmap de formalización.
- Predicción de crecimiento del negocio con un modelo entrenado (en `src/modelDemo`).

## Estructura del repositorio (resumen)

- `run_server.py` — Entrypoint para ejecutar el servidor MCP (modo FastMCP).
- `run_http_server.py` — Script para ejecutar el servidor HTTP (FastAPI + Uvicorn).
- `server.py` — Archivo preparado para deployment (exporta `mcp` para detectores automáticos).
- `requirements.txt` — Dependencias del proyecto.
- `src/` — Código fuente principal:
  - `main.py` — Registro de herramientas MCP (`@mcp.tool()` y prompts `@mcp.prompt()`).
  - `http_server.py` — API REST para probar herramientas.
  - `gemini.py` — Cliente e integración con Google Gemini (LLM & embeddings).
  - `supabase_client.py` — Cliente para Supabase (búsqueda semántica, historial de chat, etc.).
  - `places.py` — Integración con Google Places para búsqueda de ubicaciones.
  - `config.py` — Carga de variables de entorno y validaciones.
  - `modelDemo/` — Datos y scripts de ejemplo para el modelo ML (entrenamiento y demo).
- `test_*.py` — Suites de tests unitarios y de integración (varios archivos `test_*.py`).

## Requisitos

- Python 3.10+ (preferible).
- Pip.
- Acceso a las APIs externas usadas:
  - Google Gemini (clave `GEMINI_API_KEY`)
  - Supabase (URL y service role key)
  - Google Places API (para búsqueda de lugares)

Dependencias listadas en `requirements.txt`. Adicionalmente para el servidor HTTP se recomienda instalar `fastapi` y `uvicorn[standard]`.

## Variables de entorno (principales)

Configurar en un archivo `.env` en la raíz del proyecto o en el entorno del sistema:

- SUPABASE_URL — URL del proyecto Supabase.
- SUPABASE_SERVICE_ROLE_KEY — Service role key para Supabase (se usa para RPCs/privilegios).
- GEMINI_API_KEY — API key para Google Gemini.
- EXPO_PUBLIC_GOOGLE_MAPS_API_KEY o GOOGLE_MAPS_API_KEY — para `places`.
- PORT — Puerto para el servidor HTTP (por defecto `8000`).
- NODE_ENV — `development` o `production`.
- Opcionales:
  - GEMINI_MODEL — Nombre del modelo Gemini (por defecto `gemini-2.0-flash`).
  - GEMINI_EMBED_MODEL — Modelo de embeddings (por defecto `gemini-embedding-001`).
  - EMBED_DIM — Dimensionalidad del embedding (por defecto `768`).
  - SIMILARITY_THRESHOLD — Umbral de similitud (por defecto `0.6`).
  - TOPK_DOCUMENTS — Número de documentos a recuperar (por defecto `6`).

Importante: No publiques claves secretas en repositorios públicos. Usa secretos en tu plataforma de despliegue.

## Instalación (local)

1. Clona el repositorio y navega a la carpeta:

```powershell
cd C:\Users\Owner\Downloads\FiscMCP
```

2. (Opcional) Crea y activa un entorno virtual:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

3. Instala las dependencias:

```powershell
pip install -r requirements.txt
# Recomendado para la API HTTP (si vas a usarla):
pip install fastapi uvicorn[standard]
```

4. Crea un archivo `.env` siguiendo la sección "Variables de entorno" y añade las claves necesarias.

## Ejecución

Hay dos modos principales para ejecutar el proyecto:

1) Servidor MCP (modo FastMCP)

- Uso (desde la raíz del repo):

```powershell
python run_server.py
```

Este script añade `src` al `PYTHONPATH` y ejecuta `main()` en `src/main.py`, que registra las herramientas y ejecuta `mcp.run()`.

2) Servidor HTTP (FastAPI) — para probar endpoints REST

- Uso (desde la raíz del repo):

```powershell
python run_http_server.py
```

- El script usa `uvicorn` internamente y expondrá:
  - Health: http://localhost:8000/health
  - Documentación interactiva (Swagger/OpenAPI): http://localhost:8000/docs
  - Endpoints principales: `/api/fiscal-advice`, `/api/chat`, `/api/risk-analysis`, `/api/search`, `/api/user-context`.

Si cambias el puerto, define `PORT` en `.env`.

## Endpoints (ejemplos)

1) Health check

```powershell
# Obtener estado
Invoke-RestMethod -Method Get -Uri http://localhost:8000/health
```

2) Solicitar recomendación fiscal (ejemplo)

```powershell
$body = @{ actividad = 'Ventas en línea'; ingresos_anuales = 300000; estado = 'CDMX' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/fiscal-advice -Body $body -ContentType 'application/json'
```

3) Chat con el asistente

```powershell
$body = @{ message = '¿Dónde está un Banorte cerca de Reforma?'; user_id = 'guest' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/chat -Body $body -ContentType 'application/json'
```

4) Búsqueda semántica de documentos

```powershell
$body = @{ query = 'beneficios régimen RESICO'; limit = 5 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/search -Body $body -ContentType 'application/json'
```

## Cómo funciona (alto nivel)

- `src/main.py` registra múltiples herramientas como `@mcp.tool()` y prompts con `@mcp.prompt()` que implementan la lógica de negocio (RAG, chat, análisis de riesgo, roadmap, etc.).
- `src/gemini.py` encapsula la integración con Google Gemini: generación de embeddings, prompts, y lógica para el chat y RAG.
- `src/supabase_client.py` encapsula acceso a Supabase — incluye RPCs para búsqueda semántica (`match_fiscai_documents`) y tablas para historial de chat y usuarios.
- `src/places.py` usa Google Places APIs para búsquedas de establecimientos y genera `deepLink` para la app móvil (fiscai://...).
- `src/config.py` centraliza la configuración y valida variables de entorno críticas.

## Desarrollo y pruebas

- El repo contiene tests `test_*.py` para pruebas unitarias básicas. Puedes ejecutar los tests con `pytest`.

```powershell
pip install pytest
pytest -q
```

- Para desarrollo iterativo recomendamos usar un entorno virtual y reiniciar el servidor cuando cambies código.

## Depuración y problemas comunes

- Error: "Faltan variables de entorno..." — Asegúrate de crear `.env` con `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY` y `EXPO_PUBLIC_GOOGLE_MAPS_API_KEY` si usas `places`.
- Error de Gemini: Verifica que `GEMINI_API_KEY` sea válida y que el modelo configurado exista en tu cuenta.
- Supabase: Si las funciones RPC fallan, verifica que los nombres (`match_fiscai_documents`, `match_documents`) existan en tu proyecto Supabase.

## Seguridad

- Nunca subas `SUPABASE_SERVICE_ROLE_KEY` ni `GEMINI_API_KEY` a repositorios públicos.
- Para producción, utiliza secretos gestionados por la plataforma de hosting (Vercel, Railway, Fly, AWS, etc.) en lugar de `.env` en disco.

## Despliegue (sugerencias rápidas)

- Plataformas recomendadas: Railway, Fly.io, Azure App Service, DigitalOcean App Platform.
- Recomendación: desplegar el servidor HTTP (`run_http_server.py`) detrás de un proxy y gestionar secretos con el proveedor.
- Considerar usar contenedor Docker para portabilidad (Dockerfile no incluido — puede añadirse fácilmente).

## Contribuir

- Abre issues para sugerencias o bugs.
- Fork + PR: agrega tests para cambios funcionales.
- Sigue el estilo de codificación existente y documenta cambios en `README.md` cuando alteres el comportamiento público.

## Siguientes pasos recomendados

- Añadir un `Dockerfile` y `docker-compose` para facilitar despliegue local.
- Añadir CI (GitHub Actions) que valide linting y tests.
- Añadir un ejemplo de `.env.example` con variables no sensibles (nombres de variables y descripciones).
- Mejorar la cobertura de tests para `src/gemini.py` (simular responses) y `src/supabase_client.py` (mock de RPCs).

---

Resumen: he analizado la estructura y el código principal del proyecto (`src/main.py`, `src/http_server.py`, `src/gemini.py`, `src/supabase_client.py`, `src/places.py`, `src/config.py`) y he preparado este README en español con guías de instalación, configuración y uso. Si quieres, puedo:

- Añadir un archivo `.env.example` al repo con las variables de entorno listadas.
- Crear un `Dockerfile` y `docker-compose.yml` de ejemplo.
- Añadir un script de comprobación (makefile / ps1) para desarrollo local.

Dime qué prefieres y lo implemento a continuación.