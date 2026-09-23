"""
AI Scene Generation using Stable Diffusion
Generates high-quality scene images from story descriptions
"""
import logging
import os
from pathlib import Path
from typing import Dict, List
import asyncio

logger = logging.getLogger(__name__)

try:
    import torch
    from diffusers import StableDiffusionPipeline
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False
    logger.warning("Diffusers not available, falling back to placeholder")

# Use environment variable for data directory or default to ./data
DATA_DIR = Path(os.getenv('DATA_DIR', './data'))
SCENES_DIR = DATA_DIR / 'scenes'

# Stable Diffusion model ID
SD_MODEL_ID = os.getenv('SD_MODEL_ID', 'runwayml/stable-diffusion-v1-5')
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'


async def generate_ai_scenes(story: dict, job_id: str) -> dict:
    """
    Generate AI-powered scene images using Stable Diffusion.
    
    Args:
        story: Story dict with scenes containing 'visual_description'
        job_id: Unique job ID for file naming
    
    Returns:
        dict: Contains scene_images list with paths and metadata
    """
    
    # Create scenes directory on first use
    SCENES_DIR.mkdir(parents=True, exist_ok=True)
    
    if not DIFFUSERS_AVAILABLE:
        logger.warning("Diffusers not installed, using placeholder scenes")
        return await _generate_placeholder_scenes(story, job_id)
    
    logger.info(f"Generating AI scenes for job {job_id} using Stable Diffusion")
    logger.info(f"Device: {DEVICE}")
    
    scene_images = []
    
    try:
        # Load Stable Diffusion pipeline
        logger.info(f"Loading model: {SD_MODEL_ID}")
        pipe = StableDiffusionPipeline.from_pretrained(
            SD_MODEL_ID,
            torch_dtype=torch.float16 if DEVICE == 'cuda' else torch.float32,
            safety_checker=None  # For faster generation
        )
        pipe = pipe.to(DEVICE)
        pipe.enable_attention_slicing()  # For memory efficiency
        
        # Generate image for each scene
        for i, scene in enumerate(story.get('scenes', []), 1):
            scene_num = scene.get('number', i)
            description = scene.get('visual_description', '')
            
            logger.info(f"Generating image for scene {scene_num}...")
            
            try:
                # Create detailed prompt
                prompt = f"{description}. High quality, professional, detailed, cinematic lighting, 4K, beautiful composition"
                negative_prompt = "blurry, low quality, distorted, ugly, bad, worst"
                
                # Generate image
                with torch.no_grad():
                    image = pipe(
                        prompt=prompt,
                        negative_prompt=negative_prompt,
                        height=1080,
                        width=1920,
                        num_inference_steps=50,
                        guidance_scale=7.5
                    ).images[0]
                
                # Save image
                scene_file = SCENES_DIR / f"{job_id}_scene_{scene_num:02d}.png"
                image.save(str(scene_file), 'PNG')
                logger.info(f"AI scene saved: {scene_file}")
                
                scene_images.append({
                    'number': scene_num,
                    'path': str(scene_file),
                    'description': description,
                    'type': 'ai_generated'
                })
                
            except Exception as e:
                logger.error(f"Failed to generate AI scene {scene_num}: {e}")
                raise
        
        logger.info(f"Generated {len(scene_images)} AI scenes")
        return {'scene_images': scene_images}
        
    except Exception as e:
        logger.error(f"AI scene generation failed: {e}")
        raise


async def _generate_placeholder_scenes(story: dict, job_id: str) -> dict:
    """
    Fallback: generate simple placeholder scenes when Stable Diffusion unavailable.
    Uses Pillow for basic images.
    """
    from PIL import Image, ImageDraw, ImageFont
    
    logger.warning("Generating placeholder scenes (low quality)")
    scene_images = []
    
    for i, scene in enumerate(story.get('scenes', []), 1):
        scene_num = scene.get('number', i)
        description = scene.get('visual_description', '')
        
        try:
            # Create basic image
            img = Image.new('RGB', (1920, 1080), color=(135, 206, 235))  # Sky blue
            draw = ImageDraw.Draw(img)
            
            # Add text
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            except:
                font = ImageFont.load_default()
            
            draw.text((100, 100), f"Scene {scene_num}", fill='white', font=font)
            draw.text((100, 200), description[:100], fill='white', font=font)
            
            # Save
            scene_file = SCENES_DIR / f"{job_id}_scene_{scene_num:02d}.png"
            img.save(str(scene_file), 'PNG')
            
            scene_images.append({
                'number': scene_num,
                'path': str(scene_file),
                'description': description,
                'type': 'placeholder'
            })
            
        except Exception as e:
            logger.error(f"Failed to generate placeholder scene {scene_num}: {e}")
            raise
    
    return {'scene_images': scene_images}
