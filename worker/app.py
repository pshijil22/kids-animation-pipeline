"""
FastAPI application for Kids Animation Pipeline - Phase 1
Exposes /create endpoint to generate stories via Ollama
"""
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import pipeline modules
try:
    from pipeline import generate_story
except ImportError as e:
    logger.error(f"Failed to import pipeline: {e}")
    sys.exit(1)

app = FastAPI(
    title="Kids Animation Pipeline - Phase 1",
    description="Story generation via local LLM",
    version="0.1.0"
)

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

@app.post("/create")
async def create_story():
    """
    Generate a new children's story.
    
    Returns:
        dict: Generated story with scenes
    """
    try:
        logger.info("Story creation request received")
        story = await generate_story()
        logger.info(f"Story '{story.get('title')}' generated successfully")
        return JSONResponse(status_code=200, content=story)
    except Exception as e:
        logger.error(f"Story generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "Kids Animation Pipeline",
        "phase": 1,
        "endpoints": {
            "health": "GET /health",
            "create_story": "POST /create"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('WORKER_PORT', 8000))
    logger.info(f"Starting worker on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
