"""Story generation and normalization for the animation pipeline."""
import asyncio, json, logging, os, re
from pathlib import Path
import requests

logger=logging.getLogger(__name__)
OLLAMA_URL=os.getenv("OLLAMA_URL","http://ollama:11434")
OLLAMA_MODEL=os.getenv("OLLAMA_MODEL","llama3.2:3b")

async def wait_for_ollama(max_retries=30,delay=1):
    for attempt in range(max_retries):
        try:
            if requests.get(f"{OLLAMA_URL}/api/tags",timeout=2).status_code==200:
                return True
        except Exception:
            pass
        if attempt<max_retries-1: await asyncio.sleep(delay)
    raise RuntimeError(f"Ollama not responding at {OLLAMA_URL}")

async def generate_story_with_llm(max_retries=3):
    await wait_for_ollama()
    prompt_paths=[Path("/app/prompts/story.txt"),Path("./prompts/story.txt"),Path("../prompts/story.txt")]
    prompt_file=next((p for p in prompt_paths if p.exists()),None)
    if not prompt_file: raise FileNotFoundError(f"Prompt file not found: {prompt_paths}")
    prompt=prompt_file.read_text(encoding="utf-8")
    for attempt in range(max_retries):
        try:
            response=requests.post(f"{OLLAMA_URL}/api/generate",
                json={"model":OLLAMA_MODEL,"prompt":prompt,"stream":False,"format":"json"},
                timeout=180)
            response.raise_for_status()
            text=response.json().get("response","").strip()
            if not text: raise ValueError("Ollama returned an empty response")
            return text
        except Exception:
            if attempt==max_retries-1: raise
            await asyncio.sleep(2**attempt)

def validate_story_json(raw_text):
    try:
        story=json.loads(raw_text)
    except json.JSONDecodeError:
        match=re.search(r"{.*}",raw_text,re.DOTALL)
        if not match: raise ValueError("Could not parse valid JSON from LLM output")
        story=json.loads(match.group(0))
    return repair_story_json(story)

def repair_story_json(story):
    if not isinstance(story,dict): raise ValueError("Story must be a JSON object")
    story.setdefault("title","Untitled Story")
    story.setdefault("description","A story for children")
    story.setdefault("lesson","Life is an adventure")
    story.setdefault("age_range","4-8")
    if not isinstance(story.get("scenes"),list) or not story["scenes"]:
        raise ValueError("Story must have a non-empty scenes array")
    story["duration_seconds"]=max(30,int(story.get("duration_seconds",180)))
    story.setdefault("characters",[])
    if not isinstance(story["characters"],list): story["characters"]=[]
    normalized=[]
    for i,scene in enumerate(story["scenes"],1):
        if not isinstance(scene,dict): scene={}
        scene["number"]=i
        scene.setdefault("title",f"Scene {i}")
        scene.setdefault("narration","Let's see what happens next.")
        scene.setdefault("visual_description","A cheerful cartoon scene with the main character outdoors.")
        scene.setdefault("action","The character looks around and smiles.")
        scene.setdefault("emotion","happy")
        scene.setdefault("camera","medium shot")
        scene.setdefault("motion","gentle camera push in")
        scene["duration_seconds"]=max(4,min(25,float(scene.get("duration_seconds",10))))
        normalized.append(scene)
    story["scenes"]=normalized
    return story
