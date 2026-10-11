import logging
import sys
from contextlib import asynccontextmanager
from fastmcp import FastMCP
from notebooklm import NotebookLMClient

# Configure logging to stderr (stdout is used for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Client instance (singleton for the session)
_client = None
_client_context = None

@asynccontextmanager
async def lifespan(_app):
    """Initialize NotebookLM client on server startup."""
    global _client, _client_context
    logger.info("Starting NotebookLM MCP server...")
    try:
        _client = await NotebookLMClient.from_storage()
        _client_context = await _client.__aenter__()
        logger.info("NotebookLM client initialized successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize NotebookLM client: {e}")
        logger.error("Please run 'uv run notebooklm login' to authenticate.")
        raise
    finally:
        if _client:
            try:
                await _client.__aexit__(None, None, None)
                logger.info("NotebookLM client closed")
            except Exception as e:
                logger.error(f"Error closing client: {e}")

# Initialize FastMCP server with lifespan
mcp = FastMCP("NotebookLM", lifespan=lifespan)

async def get_client():
    global _client
    if _client is None:
        raise RuntimeError("NotebookLM client not initialized. Please restart the server.")
    return _client

@mcp.tool()
async def list_notebooks():
    """List all notebooks in your NotebookLM account."""
    client = await get_client()
    notebooks = await client.notebooks.list()
    return [{"id": nb.id, "title": nb.title, "source_count": nb.sources_count} for nb in notebooks]

@mcp.tool()
async def create_notebook(title: str):
    """Create a new notebook with the given title."""
    client = await get_client()
    notebook = await client.notebooks.create(title)
    return {"id": notebook.id, "title": notebook.title}

@mcp.tool()
async def add_source_url(notebook_id: str, url: str):
    """Add a website URL as a source to a notebook."""
    client = await get_client()
    source = await client.sources.add_url(notebook_id, url)
    return {"id": source.id, "title": source.title}

@mcp.tool()
async def add_source_text(notebook_id: str, title: str, text: str):
    """Add raw text as a source to a notebook."""
    client = await get_client()
    source = await client.sources.add_text(notebook_id, title, text)
    return {"id": source.id, "title": source.title}

@mcp.tool()
async def ask_notebook(notebook_id: str, question: str):
    """Ask a question based on the sources in a specific notebook."""
    client = await get_client()
    result = await client.chat.ask(notebook_id, question)
    return {
        "answer": result.answer,
        "references": [
            {"source_id": ref.source_id, "citation": ref.citation_number, "text": ref.cited_text}
            for ref in result.references
        ],
    }

@mcp.tool()
async def get_notebook_summary(notebook_id: str):
    """Get the summary and key insights of a notebook."""
    client = await get_client()
    # Using chat to get summary if there's no direct summary API
    result = await client.chat.ask(notebook_id, "Please provide a comprehensive summary and key insights of this notebook.")
    return {"summary": result.answer}

@mcp.tool()
async def generate_video_overview(notebook_id: str, instructions: str = "Create an engaging video overview of these sources."):
    """
    Generate a Video Overview artifact in NotebookLM.
    """
    client = await get_client()
    status = await client.artifacts.generate_video(notebook_id, instructions=instructions)
    return {"task_id": status.task_id, "status": "Task started. Check NotebookLM studio."}

@mcp.tool()
async def generate_audio_overview(notebook_id: str, instructions: str = "Create a deep dive podcast-style overview."):
    """
    Generate an Audio Overview (Deep Dive podcast) in NotebookLM.
    """
    client = await get_client()
    status = await client.artifacts.generate_audio(notebook_id, instructions=instructions)
    return {"task_id": status.task_id, "status": "Task started. Check NotebookLM studio."}

@mcp.tool()
async def generate_slide_deck(notebook_id: str, instructions: str = "Create a comprehensive slide deck."):
    """
    Generate a Slide Deck (PowerPoint style) in NotebookLM.
    """
    client = await get_client()
    status = await client.artifacts.generate_slide_deck(notebook_id, instructions=instructions)
    return {"task_id": status.task_id, "status": "Task started. Check NotebookLM studio."}

@mcp.tool()
async def generate_mind_map(notebook_id: str):
    """
    Generate an interactive Mind Map in NotebookLM.
    This creates a mind map and saves it as a note.
    """
    client = await get_client()
    result = await client.artifacts.generate_mind_map(notebook_id)
    return {"note_id": result.get("note_id"), "status": "Mind map generated and saved to notes."}

@mcp.tool()
async def generate_infographic(notebook_id: str, instructions: str = "Create an informative infographic."):
    """
    Generate an Infographic in NotebookLM.
    """
    client = await get_client()
    status = await client.artifacts.generate_infographic(notebook_id, instructions=instructions)
    return {"task_id": status.task_id, "status": "Task started. Check NotebookLM studio."}

@mcp.tool()
async def generate_quiz(notebook_id: str, instructions: str = "Create a quiz based on these sources."):
    """
    Generate a Quiz in NotebookLM.
    """
    client = await get_client()
    status = await client.artifacts.generate_quiz(notebook_id, instructions=instructions)
    return {"task_id": status.task_id, "status": "Task started. Check NotebookLM studio."}

@mcp.tool()
async def generate_flashcards(notebook_id: str, instructions: str = "Create study flashcards."):
    """
    Generate Flashcards in NotebookLM.
    """
    client = await get_client()
    status = await client.artifacts.generate_flashcards(notebook_id, instructions=instructions)
    return {"task_id": status.task_id, "status": "Task started. Check NotebookLM studio."}

@mcp.tool()
async def generate_summary_report(notebook_id: str, instructions: str = "Create a briefing document."):
    """
    Generate a Summary Report (Briefing Doc) in NotebookLM.
    """
    client = await get_client()
    status = await client.artifacts.generate_report(notebook_id, custom_prompt=instructions)
    return {"task_id": status.task_id, "status": "Task started. Check NotebookLM studio."}

@mcp.tool()
async def generate_data_table(notebook_id: str, instructions: str = "Extract key data into a table."):
    """
    Generate a Data Table artifact in NotebookLM.
    """
    client = await get_client()
    status = await client.artifacts.generate_data_table(notebook_id, instructions=instructions)
    return {"task_id": status.task_id, "status": "Task started. Check NotebookLM studio."}

def main():
    """Entry point for running the NotebookLM MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
