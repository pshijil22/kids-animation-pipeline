"""Procedural 2D scene renderer for kid-friendly animated videos.

The renderer deliberately stays CPU-only and deterministic.  It produces clean,
layered cartoon artwork that FFmpeg can animate with camera motion, so the
pipeline remains usable on small GitHub Actions runners.
"""
import hashlib
import logging
import math
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

logger = logging.getLogger(__name__)
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
SCENES_DIR = DATA_DIR / "scenes"
WIDTH = int(os.getenv("VIDEO_WIDTH", "1280"))
HEIGHT = int(os.getenv("VIDEO_HEIGHT", "720"))

PALETTES = [
    ("#8ED8FF", "#C9F7A8", "#FDE68A"),
    ("#B8A7FF", "#BDE7A5", "#FFD6A5"),
    ("#9EE7D7", "#D7F9B0", "#FFE7A8"),
]


def _font(size):
    from PIL import ImageFont
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _seed(scene):
    return int(hashlib.sha256(scene.get("visual_description", "").encode()).hexdigest()[:8], 16)


def _gradient(draw, top, bottom):
    import colorsys
    def rgb(value):
        value=value.lstrip("#")
        return tuple(int(value[i:i+2],16) for i in (0,2,4))
    a,b=rgb(top),rgb(bottom)
    for y in range(HEIGHT):
        t=y/max(1,HEIGHT-1)
        c=tuple(int(a[i]*(1-t)+b[i]*t) for i in range(3))
        draw.line((0,y,WIDTH,y), fill=c)


def _character(draw, cx, ground, kind, scale=1.0, bob=0):
    s=scale
    cy=ground - int(150*s) + int(bob)
    body="#F6A6B2" if kind=="rabbit" else "#F4B860" if kind=="fox" else "#9B8AFB" if kind=="owl" else "#8EC5FF" if kind=="bear" else "#F7C948"
    outline="#493B5A"
    # shadow
    draw.ellipse((cx-int(70*s),ground-int(10*s),cx+int(70*s),ground+int(15*s)), fill="#00000020")
    if kind=="owl":
        draw.ellipse((cx-int(58*s),cy-int(45*s),cx+int(58*s),cy+int(65*s)), fill=body, outline=outline, width=max(1,int(4*s)))
        draw.ellipse((cx-int(45*s),cy-int(65*s),cx-2,cy-int(5*s)), fill=body, outline=outline, width=max(1,int(4*s)))
        draw.ellipse((cx+2,cy-int(65*s),cx+int(45*s),cy-int(5*s)), fill=body, outline=outline, width=max(1,int(4*s)))
        for ex in (-24,24):
            draw.ellipse((cx+int((ex-15)*s),cy-int(42*s),cx+int((ex+15)*s),cy-int(12*s)), fill="white", outline=outline, width=max(1,int(3*s)))
            draw.ellipse((cx+int((ex-5)*s),cy-int(35*s),cx+int((ex+5)*s),cy-int(25*s)), fill=outline)
        draw.polygon([(cx-int(10*s),cy-int(3*s)),(cx+int(10*s),cy-int(3*s)),(cx,cy+int(12*s))],fill="#F7C948")
    else:
        draw.ellipse((cx-int(52*s),cy-int(35*s),cx+int(52*s),cy+int(70*s)), fill=body, outline=outline, width=max(1,int(4*s)))
        if kind=="rabbit":
            draw.ellipse((cx-int(40*s),cy-int(105*s),cx-int(10*s),cy-int(25*s)), fill=body, outline=outline, width=max(1,int(4*s)))
            draw.ellipse((cx+int(10*s),cy-int(105*s),cx+int(40*s),cy-int(25*s)), fill=body, outline=outline, width=max(1,int(4*s)))
        elif kind=="fox":
            draw.polygon([(cx-int(55*s),cy-int(25*s)),(cx-int(35*s),cy-int(90*s)),(cx,cy-int(55*s)),(cx+int(35*s),cy-int(90*s)),(cx+int(55*s),cy-int(25*s))],fill=body,outline=outline)
        else:
            draw.ellipse((cx-int(58*s),cy-int(75*s),cx+int(58*s),cy+int(25*s)), fill=body, outline=outline, width=max(1,int(4*s)))
        for ex in (-20,20):
            draw.ellipse((cx+int((ex-5)*s),cy-int(25*s),cx+int((ex+5)*s),cy-int(15*s)), fill=outline)
        draw.arc((cx-int(18*s),cy-int(10*s),cx+int(18*s),cy+int(18*s)),0,180,fill=outline,width=max(1,int(3*s)))
    # simple arms/legs create a readable pose
    draw.line((cx-int(45*s),cy+int(25*s),cx-int(75*s),cy+int(5*s)), fill=outline, width=max(2,int(6*s)))
    draw.line((cx+int(45*s),cy+int(25*s),cx+int(75*s),cy+int(5*s)), fill=outline, width=max(2,int(6*s)))


def _kind(text):
    t=text.lower()
    for word in ("owl","rabbit","bunny","fox","bear","cat","dog","bird"):
        if word in t:
            return "rabbit" if word=="bunny" else word
    return "bear"


def _create_scene_image(scene, scene_num):
    description=(scene.get("visual_description") or "").strip()
    seed=_seed(scene)
    sky,grass,sun=PALETTES[seed % len(PALETTES)]
    image=Image.new("RGB",(WIDTH,HEIGHT))
    draw=ImageDraw.Draw(image)
    _gradient(draw,sky,"#FFF4D6")
    # distant hills
    draw.polygon([(0,430),(220,300),(430,430),(650,280),(900,430),(1110,300),(WIDTH,430),(WIDTH,HEIGHT),(0,HEIGHT)],fill="#A8DFA8")
    draw.rectangle((0,430,WIDTH,HEIGHT),fill=grass)
    # sun + soft clouds
    draw.ellipse((WIDTH-190,55,WIDTH-70,175),fill=sun)
    for x in (120,470,820):
        y=90+(seed+x)%45
        for dx,dy,r in ((0,12,42),(45,0,52),(88,14,38)):
            draw.ellipse((x+dx-r,y+dy-r,x+dx+r,y+dy+r),fill="#FFFFFF")
    # trees from semantic cues, with a few background trees for depth
    has_tree="tree" in description.lower() or "forest" in description.lower()
    tree_x=[110,WIDTH-150] if has_tree else [90,WIDTH-110]
    for x in tree_x:
        trunk=draw.rectangle((x-18,300,x+18,445),fill="#8B5A3C")
        draw.ellipse((x-75,220,x+75,360),fill="#4FAF62",outline="#397B49",width=4)
        draw.ellipse((x-55,185,x+55,315),fill="#62BF6F",outline="#397B49",width=4)
    # flowers / path add visual rhythm
    if "flower" in description.lower() or "garden" in description.lower():
        for x in range(260,1050,110):
            draw.line((x,445,x,405),fill="#3F8C45",width=4)
            draw.ellipse((x-12,390,x+2,404),fill="#FF7BA5")
            draw.ellipse((x+1,390,x+15,404),fill="#FFD166")
    if "path" in description.lower() or "road" in description.lower():
        draw.polygon([(WIDTH//2-35,HEIGHT),(WIDTH//2+35,HEIGHT),(WIDTH//2+170,445),(WIDTH//2-170,445)],fill="#E7CFA3")
    # Main character is intentionally prominent and consistent across scenes.
    cx=WIDTH//2 + ((seed % 7)-3)*35
    _character(draw,cx,520,_kind(description),1.0,0)
    # Foreground leaves provide depth without external assets.
    for i in range(12):
        x=(seed*(i+3)*17)%WIDTH
        y=HEIGHT-((seed*(i+5)*11)%180)
        draw.ellipse((x,y,x+18,y+8),fill="#5BAE63")
    # No baked-in scene labels: the artwork remains reusable for animation.
    return image.filter(ImageFilter.SMOOTH)


async def generate_scenes(story: dict, job_id: str) -> dict:
    SCENES_DIR.mkdir(parents=True,exist_ok=True)
    scene_images=[]
    for i,scene in enumerate(story.get("scenes",[]),1):
        number=int(scene.get("number",i))
        path=SCENES_DIR/f"{job_id}_scene_{number:02d}.png"
        try:
            _create_scene_image(scene,number).save(path,"PNG",optimize=True)
        except Exception:
            logger.exception("Scene %s failed; creating fallback",number)
            Image.new("RGB",(WIDTH,HEIGHT),"#9DDCFF").save(path,"PNG")
        scene_images.append({"number":number,"path":str(path),"description":scene.get("visual_description",""),"type":"procedural_cartoon"})
    return {"scene_images":scene_images}
