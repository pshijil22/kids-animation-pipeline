"""
Scene generation - Create colorful scene images
Production-ready with comprehensive error handling
"""
import os
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.getenv('DATA_DIR', './data'))
SCENES_DIR = DATA_DIR / 'scenes'

COLORS = {
    'sky_blue': '#87CEEB',
    'grass_green': '#90EE90',
    'sun_yellow': '#FFD700',
    'cloud_white': '#FFFFFF',
    'tree_brown': '#8B4513',
    'tree_green': '#228B22',
    'flower_red': '#FF69B4',
    'flower_yellow': '#FFD700',
    'water_blue': '#4169E1',
}


async def generate_scenes(story: dict, job_id: str) -> dict:
    """
    Generate colorful scene images with error handling.
    """
    
    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Generating scene images for job {job_id}")
    
    scene_images = []
    
    for i, scene in enumerate(story.get('scenes', []), 1):
        scene_num = scene.get('number', i)
        description = scene.get('visual_description', f'Scene {i}')
        
        scene_file = SCENES_DIR / f"{job_id}_scene_{scene_num:02d}.png"
        
        try:
            image = _create_scene_image(description, scene_num)
            image.save(str(scene_file), 'PNG')
            logger.info(f"Scene {i} saved")
            
            scene_images.append({
                'number': scene_num,
                'path': str(scene_file),
                'description': description
            })
            
        except Exception as e:
            logger.error(f"Scene {i} failed: {e}")
            # Create fallback image
            image = _create_fallback_image(scene_num)
            image.save(str(scene_file), 'PNG')
            scene_images.append({
                'number': scene_num,
                'path': str(scene_file),
                'description': description
            })
    
    logger.info(f"Generated {len(scene_images)} scenes")
    return {'scene_images': scene_images}


def _create_scene_image(description: str, scene_num: int) -> Image.Image:
    """Create a colorful scene image."""
    try:
        # 1280x720 HD
        img = Image.new('RGB', (1280, 720), color=COLORS['sky_blue'])
        draw = ImageDraw.Draw(img)
        
        # Grass
        draw.rectangle([(0, 400), (1280, 720)], fill=COLORS['grass_green'])
        
        # Sun
        draw.ellipse([(1100, 50), (1200, 150)], fill=COLORS['sun_yellow'])
        
        # Clouds
        for cx in [200, 500, 800]:
            draw.ellipse([(cx, 80), (cx + 100, 130)], fill=COLORS['cloud_white'])
        
        # Trees if mentioned
        if 'tree' in description.lower():
            draw.rectangle([(100, 300), (150, 400)], fill=COLORS['tree_brown'])
            draw.polygon([(125, 250), (80, 300), (170, 300)], fill=COLORS['tree_green'])
            draw.rectangle([(1100, 300), (1150, 400)], fill=COLORS['tree_brown'])
            draw.polygon([(1125, 250), (1080, 300), (1170, 300)], fill=COLORS['tree_green'])
        
        # Flowers if mentioned
        if 'flower' in description.lower():
            for x in [300, 600, 900]:
                draw.ellipse([(x-20, 350), (x+20, 390)], fill=COLORS['flower_red'])
                draw.ellipse([(x-10, 360), (x+10, 380)], fill=COLORS['flower_yellow'])
        
        # Title
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        title = f"Scene {scene_num}"
        bbox = draw.textbbox((0, 0), title, font=font)
        title_width = bbox[2] - bbox[0]
        draw.text(((1280 - title_width) // 2, 20), title, fill='white', font=font)
        
        # Description (truncated)
        try:
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            small_font = font
        
        desc_text = description[:100] if description else "A scene in the story"
        draw.text((40, 650), desc_text, fill='black', font=small_font)
        
        return img
        
    except Exception as e:
        logger.error(f"Scene creation failed: {e}")
        return _create_fallback_image(scene_num)


def _create_fallback_image(scene_num: int) -> Image.Image:
    """Create a minimal fallback image."""
    img = Image.new('RGB', (1280, 720), color=(100, 150, 200))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
    except:
        font = ImageFont.load_default()
    
    text = f"Scene {scene_num}"
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (1280 - (bbox[2] - bbox[0])) // 2
    y = (720 - (bbox[3] - bbox[1])) // 2
    draw.text((x, y), text, fill='white', font=font)
    
    return img
