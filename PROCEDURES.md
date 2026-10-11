# Manual de procedimientos — Integración y corrección de NotebookLM MCP

Documento de referencia del trabajo de integración: qué estaba roto, qué se cambió
y por qué, para que el proyecto cohesione y se pueda registrar como servidor MCP en
Claude Desktop / Claude Code.

## 1. Estado inicial

El proyecto arrancó desde un template de `uv init`, por lo que convivían dos capas que
no cohesionaban:

- `server.py` — servidor MCP real (FastMCP) con 15 herramientas sobre `notebooklm-py`.
- `main.py` — placeholder `print("Hello from notebooklm-assistant!")` que no arrancaba nada.
- `pyproject.toml` — nombre `notebooklm-assistant` y descripción por defecto.

## 2. Errores corregidos (runtime)

Las herramientas usaban campos que no existen en la API de `notebooklm-py` v0.3.1.
Verificado por introspección del paquete instalado (no por suposición):

| Herramienta            | Antes (rompía)                          | Ahora (campo real)                       |
|------------------------|-----------------------------------------|------------------------------------------|
| `list_notebooks`       | `nb.source_count`                       | `nb.sources_count`                       |
| `ask_notebook`         | `result.text`, `result.sources[].title` | `result.answer`, `result.references[]`   |
| `get_notebook_summary` | `result.text`                           | `result.answer`                          |

`AskResult` expone `answer` y `references` (cada `ChatReference` tiene `source_id`,
`citation_number`, `cited_text`). Por eso `ask_notebook` ahora devuelve
`{answer, references:[{source_id, citation, text}]}`.

Firmas confirmadas de `artifacts`: `generate_report` usa `custom_prompt=`; el resto
(`generate_video`, `generate_audio`, `generate_slide_deck`, `generate_infographic`,
`generate_quiz`, `generate_flashcards`, `generate_data_table`) usa `instructions=`.
Los llamados de `server.py` ya coincidían con esas firmas.

## 3. Cohesión de archivos

- `server.py`: se envolvió `mcp.run()` en `def main()` como punto de entrada nombrado.
- `main.py`: ahora `from server import main` — un único arranque, sin lógica duplicada.
- `pyproject.toml`: `name = "notebooklm-mcp"` y descripción real del servidor.

## 4. Punto de entrada y registro en Claude

El entry point oficial (documentado en `README.md`) es ejecutar `server.py` por stdio:

```bash
uv run python server.py
```

Registro en Claude Code:

```bash
claude mcp add notebooklm -- uv --directory <PROJECT_PATH> run python server.py
```

Antes del primer uso hay que autenticar una vez (abre el navegador):

```bash
uv run notebooklm login
```

El `lifespan` del servidor crea el cliente con `NotebookLMClient.from_storage()`; si no
hay sesión guardada, falla al arrancar con un mensaje que pide correr el login. Es el
comportamiento esperado, no un error del proyecto.

## 5. Verificación realizada

```bash
uv run python -m py_compile server.py main.py   # compila
uv run python -c "import asyncio, server; print(len(asyncio.run(server.mcp.get_tools())))"  # 15
```

Resultado: compila, importa, 15 herramientas registradas, `main.py` delega en
`server.main`. No se invocó la API real de NotebookLM (requiere login de navegador).
