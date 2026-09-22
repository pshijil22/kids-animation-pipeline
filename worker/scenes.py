"""
Scene generation - Create simple cartoon-style scenes as PNG images
Uses PIL (Pillow) to generate colorful, child-friendly visuals
"""
import os
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random

logger = logging.getLogger(__name__)

SCENES_DIR = Path("/data/scenes")

# Simple color palette for scenes
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
    Generate simple scene images for each scene in the story.
    
    Args:
        story: Story dict with scenes
        job_id: Unique job ID
    
    Returns:
        dict: Contains scene_images list with paths
    """
    
    # Create scenes directory on first use
    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating scene images for job {job_id}")
    
    for i, scene in enumerate(story.get('scenes', []), 1):
        scene_num = scene.get('number', i)
        description = scene.get('visual_description', '')
        narration = scene.get('narration', '')
        
        logger.info(f"Generating image for scene {scene_num}: {description[:50]}...")
        
        try:
            scene_file = SCENES_DIR / f"{job_id}_scene_{scene_num:02d}.png"
            
            # Generate a simple scene image
            image = create_simple_scene(description, narration, scene_num)
            
            # Save the image
            image.save(str(scene_file), 'PNG')
            logger.info(f"Scene image saved: {scene_file}")
            
            scene_images.append({
                'number': scene_num,
                'path': str(scene_file),
                'description': description
            })
            
        except Exception as e:
            logger.error(f"Failed to generate scene {scene_num}: {e}")
            raise
    
    logger.info(f"Generated {len(scene_images)} scene images")
    return {'scene_images': scene_images}


def create_simple_scene(description: str, narration: str, scene_num: int) -> Image.Image:
    """
    Create a simple cartoon-style scene image.
    
    Args:
        description: Visual description
        narration: Narration text
        scene_num: Scene number
    
    Returns:
        PIL Image object
    """
    
    # Create image (1280x720)
    img = Image.new('RGB', (1280, 720), color=COLORS['sky_blue'])
    draw = ImageDraw.Draw(img)
    
    # Try to use a bold font, fall back to default
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Draw grass (bottom half)
    draw.rectangle([(0, 360), (1280, 720)], fill=COLORS['grass_green'])
    
    # Draw sun
    draw.ellipse([(1100, 50), (1200, 150)], fill=COLORS['sun_yellow'])
    
    # Draw simple clouds
    for cx in [200, 400, 600]:
        draw.ellipse([(cx, 80), (cx + 80, 120)], fill=COLORS['cloud_white'])
        draw.ellipse([(cx + 40, 70), (cx + 120, 110)], fill=COLORS['cloud_white'])
    
    # Draw simple trees based on description
    if 'tree' in description.lower() or 'forest' in description.lower():
        # Left tree
        draw.rectangle([(100, 280), (140, 400)], fill=COLORS['tree_brown'])
        draw.polygon([(120, 200), (80, 280), (160, 280)], fill=COLORS['tree_green'])
        
        # Right tree
        draw.rectangle([(1100, 280), (1140, 400)], fill=COLORS['tree_brown'])
        draw.polygon([(1120, 200), (1080, 280), (1160, 280)], fill=COLORS['tree_green'])
    
    # Draw simple flowers if mentioned
    if 'flower' in description.lower():
        # Simple flower: circle with petals
        for angle in range(0, 360, 60):
            import math
            px = 640 + int(30 * math.cos(math.radians(angle)))
            py = 400 + int(30 * math.sin(math.radians(angle)))
            draw.ellipse([(px-15, py-15), (px+15, py+15)], fill=COLORS['flower_red'])
        draw.ellipse([(625, 385), (655, 415)], fill=COLORS['flower_yellow'])
    
    # Draw water if mentioned
    if 'water' in description.lower() or 'river' in description.lower() or 'lake' in description.lower():
        draw.rectangle([(0, 500), (1280, 720)], fill=COLORS['water_blue'])
    
    # Add scene title
    title = f"Scene {scene_num}"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = bbox[2] - bbox[0]
    title_x = (1280 - title_width) // 2
    draw.text((title_x, 20), title, fill='white', font=title_font)
    
    # Add wrapped narration text at bottom
    lines = wrap_text(narration, 60)
    y_pos = 650
    for line in lines[-2:]:  # Show last 2 lines
        bbox = draw.textbbox((0, 0), line, font=small_font)
        text_width = bbox[2] - bbox[0]
        text_x = (1280 - text_width) // 2
        draw.text((text_x, y_pos), line, fill='black', font=small_font)
        y_pos -= 25
    
    return img


def wrap_text(text: str, width: int) -> list:
    """
    Wrap text to specified character width.
    
    Args:
        text: Text to wrap
        width: Characters per line
    
    Returns:
        List of wrapped lines
    """
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        if len(' '.join(current_line)) > width:
            lines.append(' '.join(current_line[:-1]))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines
