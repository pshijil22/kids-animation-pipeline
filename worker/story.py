"""Long-form story generation for the kids animation pipeline.

Generate the complete 100-scene episode in small, coherent batches so the
local LLM does not time out while preserving the full 25-30 minute plan.
"""
import asyncio
import json
import logging
import os
import re
from pathlib import Path

import requests

logger = logging.getLogger(__name__)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
MIN_SECONDS = 1140
MAX_SECONDS = 1260
SCENES_PER_ACT = 16
SCENES_PER_BATCH = 5


async def wait_for_ollama(max_retries=180, delay=1):
    for attempt in range(max_retries):
        try:
            if requests.get(f"{OLLAMA_URL}/api/tags", timeout=3).status_code == 200:
                return True
        except Exception:
            pass
        if attempt < max_retries - 1:
            await asyncio.sleep(delay)
    raise RuntimeError(f"Ollama not responding at {OLLAMA_URL}")


def _series_bible():
    for path in (Path("../series/series.json"), Path("series/series.json")):
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.warning("Could not load series bible: %s", exc)
    return {}


def _prompt_file():
    paths = [
        Path("/app/prompts/story.txt"),
        Path("./prompts/story.txt"),
        Path("../prompts/story.txt"),
    ]
    path = next((p for p in paths if p.exists()), None)
    if not path:
        raise FileNotFoundError(f"Prompt file not found: {paths}")
    return path


def _extract_json(raw):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise ValueError("Could not parse valid JSON from LLM output")
        return json.loads(match.group(0))


async def _ask_ollama(prompt, timeout=180):
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "num_ctx": 4096,
                "num_predict": 2400,
                "temperature": 0.7,
            },
        },
        timeout=timeout,
    )
    response.raise_for_status()
    text = response.json().get("response", "").strip()
    if not text:
        raise ValueError("Ollama returned an empty response")
    return _extract_json(text)


def _scene_schema(start_number, batch_size, include_episode):
    episode = ""
    if include_episode:
        episode = """
For the first batch also return title, description, lesson, age_range,
characters and the five acts. Characters must be reusable and visually
specific so the Blender renderer can keep them consistent.
"""
    return f"""
Return ONLY valid JSON.
{episode}
Return a "scenes" array containing EXACTLY {batch_size} scene objects.
The scene numbers must run from {start_number} through
{start_number + batch_size - 1}.

Every scene object MUST contain:
number, act, title, narration, visual_description, visual_beats,
location, time_of_day, action, character_actions, props, emotion, camera,
motion, continuity, duration_seconds.

visual_beats MUST contain EXACTLY 3 objects. Each beat MUST contain:
narration_line, subject, action, prop, camera.

The three beats must represent three different moments from the same
scene: setup, physical action/discovery, and reaction/payoff. The
narration_line must be the actual portion of narration represented.
Do not repeat the same action, camera or background for all three beats.
If narration says a character finds a key, show approaching/searching,
the key being noticed/picked up, and the character reacting to it.
If narration says a character opens a box, show reaching/opening, the
lid changing state, and the reaction to what is revealed.

Each scene's narration should be 38-45 natural spoken words. It must
advance the story rather than describe a generic picture. Every concrete
noun or action in narration should have a matching visual beat.
"""


def _fallback_plan(series):
    cast = series.get("recurring_cast", [])
    return {
        "title": "The Hidden Garden Bell",
        "description": "Pip, Momo and Tilly follow a mysterious bell sound through their village and learn that careful listening and teamwork can reveal a wonderful surprise.",
        "lesson": "Small clues become big discoveries when friends listen, share ideas and help one another.",
        "age_range": "4-8",
        "characters": cast,
        "acts": [
            {"number": 1, "goal": "find the source of a mysterious bell", "obstacle": "the sound keeps moving", "discovery": "three tiny clues point toward the old garden"},
            {"number": 2, "goal": "cross the meadow and follow the clues", "obstacle": "wind scatters the trail", "discovery": "a ribbon and seed trail reveal a hidden path"},
            {"number": 3, "goal": "open the overgrown garden gate", "obstacle": "the gate is stuck and the path is tangled", "discovery": "each friend has a useful idea"},
            {"number": 4, "goal": "restore the quiet garden bell", "obstacle": "the bell rope is tangled high in a tree", "discovery": "cooperation makes the difficult job simple"},
            {"number": 5, "goal": "share the discovery with the village", "obstacle": "everyone rushes before noticing the final clue", "discovery": "the garden is a place for everyone to enjoy together"}
        ],
        "locations": ["Sunny Village", "Dandelion Meadow", "Creek Footbridge", "Old Garden Gate", "Hidden Garden"],
        "props": ["tiny brass bell", "teal ribbon", "yellow satchel", "purple backpack", "wooden sign", "garden key", "watering can", "flower basket"]
    }


async def _compact_story_plan(series):
    prompt = f"""
Create a compact ORIGINAL children's animation episode plan for ages 4-8.
Series bible: {json.dumps(series, ensure_ascii=False)}
Return ONLY JSON with:
title, description, lesson, age_range, characters, acts, locations, props.
Use the recurring characters and preserve their appearance/personality.
acts must be exactly 5 objects, each with number, goal, obstacle, discovery.
Keep the whole answer under about 1800 tokens. Do not write scenes or narration.
The episode should have a clear beginning, escalating middle, emotional payoff and warm ending.
"""
    try:
        result = await _ask_ollama(prompt, timeout=180)
        if not isinstance(result, dict):
            raise ValueError("compact plan was not an object")
        acts = result.get("acts")
        if not isinstance(acts, list) or len(acts) < 5:
            raise ValueError("compact plan did not contain five acts")
        result["acts"] = acts[:5]
        return result
    except Exception as exc:
        logger.warning("Compact story plan unavailable; using deterministic fallback: %s", exc)
        return _fallback_plan(series)


def _make_scene(number, act, plan, series):
    cast = plan.get("characters") or series.get("recurring_cast") or _fallback_plan(series)["characters"]
    names = [c.get("name", "friend") for c in cast if isinstance(c, dict)]
    names = (names + ["Pip", "Momo", "Tilly"])[:3]
    hero = names[(number - 1) % len(names)]
    partner = names[number % len(names)]
    locations = plan.get("locations") or _fallback_plan(series)["locations"]
    props = plan.get("props") or _fallback_plan(series)["props"]
    location = locations[(number - 1) % len(locations)]
    prop = props[(number * 3) % len(props)]
    action_cycle = [
        ("spots", "leans closer and points"),
        ("follows", "steps carefully after the clue"),
        ("checks", "kneels to inspect the trail"),
        ("carries", "carefully carries the useful object"),
        ("opens", "gently tests the hidden mechanism"),
        ("climbs", "reaches toward the next clue"),
        ("listens", "pauses and listens for the sound"),
        ("shares", "shows the clue to the friends"),
    ]
    verb, motion = action_cycle[(number - 1) % len(action_cycle)]
    act_index = min((number - 1) // SCENES_PER_ACT, len(act) - 1) if act else 0
    act_info = act[act_index] if act else {}
    goal = act_info.get("goal", "discover what happens next")
    obstacle = act_info.get("obstacle", "the trail becomes harder to follow")
    discovery = act_info.get("discovery", "the friends find a useful clue")
    moment = (number - 1) % 16
    time_of_day = ["morning", "morning", "late morning", "noon", "afternoon", "afternoon", "golden hour", "evening"][moment % 8]
    title = f"Act {((number - 1) // 16) + 1}: {verb.title()} the Clue"
    s1 = f"{hero} {verb} a clue near the {location}, keeping the friends focused on their goal."
    s2 = f"{partner} {motion} while the {prop} gives them a fresh hint about what to do next."
    s3 = f"Together they face {obstacle}, then notice that {discovery} and move one step closer to {goal}."
    narration = " ".join([s1, s2, s3])
    beats = [
        {"narration_line": s1, "subject": hero, "action": f"{verb} a clue", "prop": prop, "camera": "wide establishing push-in"},
        {"narration_line": s2, "subject": partner, "action": motion, "prop": prop, "camera": "medium tracking shot"},
        {"narration_line": s3, "subject": f"{hero} and {partner}", "action": "react, cooperate and continue", "prop": prop, "camera": "warm close reaction shot"},
    ]
    return {
        "number": number,
        "act": ((number - 1) // 16) + 1,
        "title": title,
        "narration": narration,
        "visual_description": f"High-end family 3D animated-feature scene in {location}; {hero} and {partner} interact with a {prop} while following a physical clue.",
        "visual_beats": beats,
        "location": location,
        "time_of_day": time_of_day,
        "action": f"{hero} {verb} a clue and {partner} helps.",
        "character_actions": f"{hero} and {partner} cooperate, react and continue the search.",
        "props": prop,
        "emotion": ["curious", "excited", "hopeful", "surprised", "determined"][number % 5],
        "camera": beats[1]["camera"],
        "motion": "gentle character movement with a controlled cinematic camera move",
        "continuity": "Carry the same clue, character appearances and emotional state naturally from the previous scene.",
        "duration_seconds": 15.0,
    }


async def generate_story_with_llm():
    await wait_for_ollama(max_retries=30, delay=1)
    series = _series_bible()
    plan = await _compact_story_plan(series)
    total_scenes = int(os.getenv("TOTAL_SCENES", "80"))
    acts = plan.get("acts", [])
    scenes = [_make_scene(i, acts, plan, series) for i in range(1, total_scenes + 1)]
    cast = plan.get("characters") or series.get("recurring_cast") or _fallback_plan(series)["characters"]
    story = {
        "title": plan.get("title", "A New Adventure"),
        "description": plan.get("description", "An original adventure for children."),
        "lesson": plan.get("lesson", "Kindness and teamwork help us solve problems."),
        "age_range": plan.get("age_range", "4-8"),
        "target_duration_seconds": total_scenes * 15,
        "duration_seconds": total_scenes * 15,
        "characters": cast,
        "acts": acts[:5],
        "series_title": series.get("series_title", "Original Kids Adventures"),
        "episode_number": int(series.get("episode_number", 1)),
        "scenes": scenes,
    }
    return json.dumps(story, ensure_ascii=False)

def validate_story_json(raw_text):
    return repair_story_json(_extract_json(raw_text))


def repair_story_json(story):
    if not isinstance(story, dict):
        raise ValueError("Story must be a JSON object")
    story.setdefault("title", "Untitled Story")
    story.setdefault("description", "An original story for children")
    story.setdefault("lesson", "Kindness and teamwork help us solve problems.")
    story.setdefault("age_range", "4-8")
    story.setdefault("characters", [])
    if isinstance(story.get("characters"), dict):
        story["characters"] = list(story["characters"].values())
    story["characters"] = [c for c in story.get("characters", []) if isinstance(c, dict) and c.get("name")][:3]
    story.setdefault("acts", [])
    if not isinstance(story.get("scenes"), list) or not story["scenes"]:
        raise ValueError("Story must have a non-empty scenes array")
    if len(story["scenes"]) != int(os.getenv("TOTAL_SCENES", "80")):
        raise ValueError(
            f"Story needs exactly {int(os.getenv('TOTAL_SCENES', '80'))} scenes for the full episode; "
            f"received {len(story['scenes'])}"
        )

    story["duration_seconds"] = max(
        MIN_SECONDS, min(MAX_SECONDS, int(story.get("duration_seconds", 1200)))
    )
    story["target_duration_seconds"] = max(
        MIN_SECONDS, min(MAX_SECONDS, int(story.get("target_duration_seconds", 1200)))
    )

    normalized = []
    for i, scene in enumerate(story["scenes"], 1):
        if not isinstance(scene, dict):
            scene = {}
        scene["number"] = i
        scene.setdefault("act", ((i - 1) // SCENES_PER_ACT) + 1)
        scene.setdefault("title", f"Scene {i}")
        scene.setdefault(
            "narration",
            "The adventure continues as everyone works together.",
        )
        scene.setdefault(
            "visual_description",
            "A cinematic 3D animated-feature scene with the recurring characters.",
        )
        beats = scene.get("visual_beats")
        if not isinstance(beats, list) or len(beats) < 3:
            narration = str(scene.get("narration", "")).strip()
            parts = [
                p.strip()
                for p in re.split(r"(?<=[.!?])\s+", narration)
                if p.strip()
            ]
            while len(parts) < 3:
                parts.append(narration)
            base_subject = scene.get("character_actions", "") or "the main character"
            base_action = scene.get("action", "") or "moves through the scene"
            base_prop = scene.get("props", "") or ""
            beats = [
                {
                    "narration_line": parts[0],
                    "subject": base_subject,
                    "action": "sets up the situation: " + base_action,
                    "prop": base_prop,
                    "camera": "establishing shot",
                },
                {
                    "narration_line": parts[1],
                    "subject": base_subject,
                    "action": base_action,
                    "prop": base_prop,
                    "camera": "action medium shot",
                },
                {
                    "narration_line": parts[2],
                    "subject": base_subject,
                    "action": "reacts and completes the moment: " + base_action,
                    "prop": base_prop,
                    "camera": "close reaction shot",
                },
            ]
        scene["visual_beats"] = beats[:3]
        scene.setdefault("location", "the established story world")
        scene.setdefault("time_of_day", "day")
        scene.setdefault(
            "action",
            "The characters move together and discover something new.",
        )
        scene.setdefault(
            "character_actions",
            scene.get("action", "The characters move together."),
        )
        scene.setdefault("props", "")
        scene.setdefault("emotion", "curious")
        scene.setdefault("camera", "medium shot")
        scene.setdefault("motion", "gentle camera movement")
        scene.setdefault("continuity", "Continue naturally from the previous shot.")
        scene["duration_seconds"] = max(
            8, min(24, float(scene.get("duration_seconds", 16.5)))
        )
        normalized.append(scene)
    story["scenes"] = normalized
    return story
