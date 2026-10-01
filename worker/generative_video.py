"""Free, registration-free 3D animated-feature renderer.

Uses Blender's open-source Eevee renderer locally on the GitHub runner. The
story JSON drives character actions, props, locations and camera movement.
No paid video API, API key, cloud video provider, or external image assets are
required.
"""
import json
import logging
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
VIDEOS_DIR = DATA_DIR / "videos"
SHOTS_DIR = DATA_DIR / "generated_shots"
BLENDER_FPS = int(os.getenv("BLENDER_RENDER_FPS", "5"))
BLENDER_WIDTH = int(os.getenv("BLENDER_RENDER_WIDTH", "640"))
BLENDER_HEIGHT = int(os.getenv("BLENDER_RENDER_HEIGHT", "360"))
MIN_SECONDS = 1470
MAX_SECONDS = 1830


def _run_blender(story_file, output_file):
    """Render a long movie as frames, then encode it with FFmpeg."""
    blender = shutil.which("blender")
    ffmpeg = shutil.which("ffmpeg")
    if not blender or not ffmpeg:
        raise RuntimeError("Blender and FFmpeg must be installed on the runner.")

    frames_dir = output_file.with_name(output_file.stem + "_frames")
    frames_dir.mkdir(parents=True, exist_ok=True)
    frame_pattern = frames_dir / "frame_####"
    command = [
        blender, "--background", "--enable-autoexec", "--python", str(Path(__file__).resolve()),
        "--", "--free-blender-render", "--story", str(story_file.resolve()),
        "--output", str(frame_pattern.resolve()), "--fps", str(BLENDER_FPS),
        "--width", str(BLENDER_WIDTH), "--height", str(BLENDER_HEIGHT),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=5 * 60 * 60)
    if result.returncode != 0:
        logger.error(result.stdout[-6000:])
        logger.error(result.stderr[-6000:])
        raise RuntimeError("Free Blender frame render failed")

    frames = sorted(frames_dir.glob("frame_*.jpg"))
    if len(frames) < 100 or not (frames_dir / "frame_0001.jpg").exists():
        logger.error("Blender stdout: %s", result.stdout[-4000:])
        logger.error("Blender stderr: %s", result.stderr[-6000:])
        raise RuntimeError(f"Blender produced only {len(frames)} usable frames")

    encode = [
        ffmpeg, "-y", "-loglevel", "warning",
        "-framerate", str(BLENDER_FPS), "-start_number", "1",
        "-i", str(frames_dir / "frame_%04d.jpg"),
        "-c:v", "libx264", "-preset", os.getenv("VIDEO_PRESET", "slow"),
        "-b:v", os.getenv("VIDEO_BITRATE", "1400k"),
        "-maxrate", os.getenv("VIDEO_MAXRATE", "1600k"),
        "-bufsize", os.getenv("VIDEO_BUFSIZE", "3200k"),
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output_file),
    ]
    encoded = subprocess.run(encode, capture_output=True, text=True, timeout=2 * 60 * 60)
    if encoded.returncode != 0 or not output_file.exists():
        logger.error("FFmpeg stdout: %s", encoded.stdout[-4000:])
        logger.error("FFmpeg stderr: %s", encoded.stderr[-6000:])
        raise RuntimeError("FFmpeg could not assemble the Blender frame sequence")
    shutil.rmtree(frames_dir, ignore_errors=True)


def _concat_audio_video(video, narration, subtitles, output):
    subtitle_path = str(subtitles.resolve()).replace(chr(92), "/").replace(":", "\:")
    subtitle_filter = (
        f"subtitles='{subtitle_path}':force_style="
        "'FontName=DejaVu Sans,FontSize=22,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H001B1630,BorderStyle=3,Outline=2,Shadow=1,MarginV=34'"
    )
    cmd = [
        "ffmpeg", "-y", "-loglevel", "warning",
        "-i", str(video), "-i", str(narration),
        "-filter_complex",
        f"[0:v]fps=30,scale=1920:1080:force_original_aspect_ratio=increase,"
        f"crop=1920:1080,eq=contrast=1.04:saturation=1.08:gamma=1.01,"
        f"unsharp=5:5:0.2:5:5:0.0,{subtitle_filter}[v]",
        "-map", "[v]", "-map", "1:a:0", "-c:v", "libx264",
        "-preset", os.getenv("VIDEO_PRESET", "slow"),
        "-b:v", os.getenv("VIDEO_BITRATE", "1400k"), "-maxrate", os.getenv("VIDEO_MAXRATE", "1600k"), "-bufsize", os.getenv("VIDEO_BUFSIZE", "3200k"), "-c:a", "aac", "-b:a", "96k",
        "-ar", "48000", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-shortest", str(output),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    if result.returncode:
        logger.error(result.stderr[-5000:])
        raise RuntimeError("Final free 3D movie assembly failed")


async def generate_scenes(story, job_id):
    """Render the complete story as a locally generated 3D animated movie."""
    SHOTS_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    scenes = story.get("scenes", [])
    if len(scenes) != 100:
        raise ValueError(f"Expected 100 scenes, received {len(scenes)}")

    story_file = SHOTS_DIR / f"{job_id}_story.json"
    silent_movie = VIDEOS_DIR / f"{job_id}_free3d.mp4"
    story_file.write_text(json.dumps(story, ensure_ascii=False), encoding="utf-8")
    logger.info(
        "Rendering 100 story-driven 3D shots locally with Blender Eevee at %sx%s/%sfps",
        BLENDER_WIDTH, BLENDER_HEIGHT, BLENDER_FPS,
    )
    _run_blender(story_file, silent_movie)
    if not silent_movie.exists() or silent_movie.stat().st_size < 100_000:
        raise RuntimeError("Blender produced no usable movie")
    return {"clips": [silent_movie], "scene_images": []}


async def create_animated_video(story, audio_data, scene_data, job_id):
    """Add offline narration/subtitles and deliver a 1080p MP4."""
    clips = [Path(p) for p in scene_data.get("clips", [])]
    if not clips:
        raise ValueError("No free 3D movie was produced")
    narration = Path(audio_data["narration_file"])
    subtitles = Path(audio_data["subtitles_file"])
    output = VIDEOS_DIR / f"{job_id}.mp4"
    _concat_audio_video(clips[0], narration, subtitles, output)

    duration = float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(output),
    ], text=True).strip())
    if not MIN_SECONDS <= duration <= MAX_SECONDS:
        raise RuntimeError(f"Generated movie duration is {duration:.1f}s; expected 25-30 minutes")
    size = output.stat().st_size
    if size < 100_000:
        raise RuntimeError(f"Video output is suspiciously small: {size} bytes")
    return {
        "video_file": str(output),
        "title": story["title"],
        "description": story["description"],
        "size_bytes": size,
        "duration_seconds": duration,
        "job_id": job_id,
        "resolution": "1920x1080",
        "fps": 30,
    }


def _arg(name, default=None):
    args = sys.argv
    if name in args:
        i = args.index(name)
        return args[i + 1]
    return default


def _blender_render():
    import bpy
    from mathutils import Vector

    story = json.loads(Path(_arg("--story")).read_text(encoding="utf-8"))
    output = Path(_arg("--output"))
    fps = int(_arg("--fps", "5"))
    width = int(_arg("--width", "640"))
    height = int(_arg("--height", "360"))
    scenes = story["scenes"]
    scene_seconds = 16.5
    total_frames = int(len(scenes) * scene_seconds * fps)

    def mat(name, color, roughness=0.65):
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.diffuse_color = (*color, 1)
        m.roughness = roughness
        return m

    def cube(name, loc, scale, material, bevel=0.12):
        bpy.ops.mesh.primitive_cube_add(location=loc)
        o = bpy.context.object
        o.name = name
        o.scale = scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if bevel:
            mod = o.modifiers.new("soft edges", "BEVEL")
            mod.width = bevel
            mod.segments = 2
        o.data.materials.append(material)
        return o

    def sphere(name, loc, scale, material):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=loc)
        o = bpy.context.object
        o.name = name
        o.scale = scale
        o.data.materials.append(material)
        return o

    def key(obj, frame, loc=None, rot=None, scale=None):
        if loc is not None:
            obj.location = loc
            obj.keyframe_insert("location", frame=frame)
        if rot is not None:
            obj.rotation_euler = rot
            obj.keyframe_insert("rotation_euler", frame=frame)
        if scale is not None:
            obj.scale = scale
            obj.keyframe_insert("scale", frame=frame)

    # Clean default scene.
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    scene = bpy.context.scene
    # Support both Blender 4.0 and newer Eevee engine names.
    engine_items = scene.render.bl_rna.properties["engine"].enum_items
    available_engines = {item.identifier for item in engine_items}
    if "BLENDER_EEVEE_NEXT" in available_engines:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    elif "BLENDER_EEVEE" in available_engines:
        scene.render.engine = "BLENDER_EEVEE"
    else:
        raise RuntimeError(f"No Eevee engine available; found {sorted(available_engines)}")
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.fps = fps
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.quality = 85
    scene.render.filepath = str(output)
    scene.render.film_transparent = False
    scene.frame_start = 1
    scene.frame_end = total_frames
    scene.render.image_settings.color_mode = "RGB"

    world = bpy.data.worlds.new("Movie World") if not bpy.data.worlds else bpy.data.worlds[0]
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Strength"].default_value = 0.65

    ground = mat("Ground", (0.24, 0.55, 0.28))
    trunk = mat("Trunk", (0.30, 0.16, 0.08))
    leaf = mat("Leaf", (0.18, 0.48, 0.22))
    rock = mat("Rock", (0.34, 0.37, 0.40))
    prop_mat = mat("Props", (0.95, 0.55, 0.16))

    cube("Ground", (0, 0, -0.35), (12, 12, 0.3), ground, 0.18)
    for x, y in [(-7, 3), (7, 4), (-6, -1), (6, -2)]:
        cube("TreeTrunk", (x, y, 1.2), (0.35, 0.35, 1.6), trunk, 0.12)
        sphere("TreeTop", (x, y, 3.2), (1.35, 1.35, 1.6), leaf)
    for x, y, s in [(-4, 3, .8), (4, 2, 1.0), (0, 5, .7)]:
        sphere("Rock", (x, y, .25), (s, s * .75, .45), rock)

    sun_data = bpy.data.lights.new("Key", "AREA")
    sun_data.energy = 1000
    sun_data.shape = "DISK"
    sun_data.size = 8
    sun = bpy.data.objects.new("Key", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.location = (0, -4, 8)
    sun.rotation_euler = (math.radians(25), 0, 0)

    cam_data = bpy.data.cameras.new("Camera")
    camera = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    cam_data.lens = 48

    characters = story.get("characters", [])[:3]
    char_objs = []
    palettes = [(0.95, 0.55, 0.25), (0.30, 0.60, 0.95), (0.75, 0.38, 0.75)]
    for idx, ch in enumerate(characters):
        color = palettes[idx % len(palettes)]
        body_mat = mat(f"Character{idx}", color, 0.5)
        skin = mat(f"Character{idx}Face", (0.98, 0.82, 0.68), 0.45)
        root = bpy.data.objects.new(f"Character_{idx}", None)
        bpy.context.collection.objects.link(root)
        body = sphere(f"Body_{idx}", (0, 0, 1.1), (0.75, 0.55, 0.9), body_mat)
        head = sphere(f"Head_{idx}", (0, -0.02, 2.15), (0.72, 0.62, 0.65), body_mat)
        for eye_x in (-0.22, 0.22):
            eye = sphere(f"Eye_{idx}", (eye_x, -0.57, 2.22), (0.09, 0.06, 0.12), skin)
            eye.parent = root
        body.parent = root
        head.parent = root
        for side in (-1, 1):
            foot = sphere(f"Foot_{idx}", (side * .32, 0, .35), (.28, .35, .2), body_mat)
            foot.parent = root
            ear = sphere(f"Ear_{idx}", (side * .38, 0, 2.68), (.22, .18, .45), body_mat)
            ear.parent = root
        char_objs.append(root)

    props = []
    for idx in range(3):
        props.append(cube(f"Prop_{idx}", (0, 0, .35), (.45, .45, .45), prop_mat, .15))

    def palette_for(text):
        h = sum(ord(c) for c in text) % 6
        colors = [
            (0.38, 0.68, 0.95), (0.92, 0.68, 0.35), (0.55, 0.78, 0.48),
            (0.78, 0.55, 0.80), (0.95, 0.72, 0.45), (0.46, 0.75, 0.76)
        ]
        return colors[h]

    def action_target(text, idx):
        t = text.lower()
        x = (-1.6 + idx * 1.6)
        if any(w in t for w in ("run", "chase", "follow", "move")):
            x += 2.0
        if any(w in t for w in ("left",)):
            x -= 1.8
        if any(w in t for w in ("right",)):
            x += 1.8
        if any(w in t for w in ("jump", "leap")):
            return (x + .8, 0.0, 1.4), math.radians(-12)
        if any(w in t for w in ("sit", "rest", "comfort")):
            return (x, 0.3, .05), 0.0
        return (x, 0.0, 0.0), math.radians(-8 if x > 0 else 8)

    for i, sc in enumerate(scenes):
        start = 1 + int(i * scene_seconds * fps)
        end = min(total_frames, start + int(scene_seconds * fps) - 1)
        action = f"{sc.get('action','')} {sc.get('character_actions','')}"
        location = sc.get("location", "the story world")
        cam_text = sc.get("camera", "").lower()
        bg_color = palette_for(location + sc.get("time_of_day", ""))

        bg.inputs["Color"].default_value = (*bg_color, 1)
        bg.inputs["Color"].keyframe_insert("default_value", frame=start)
        bg.inputs["Color"].keyframe_insert("default_value", frame=end)

        for idx, root in enumerate(char_objs):
            start_loc = (-1.4 + idx * 1.4, 0.0, 0.0)
            end_loc, zrot = action_target(action, idx)
            key(root, start, start_loc, (0, 0, 0))
            key(root, end, end_loc, (0, 0, zrot))
            # Small performance-friendly bounce for lively movement.
            mid = start + max(1, (end - start) // 2)
            if "jump" in action.lower() or "leap" in action.lower():
                key(root, mid, (end_loc[0] - .4, end_loc[1], .8), (0, 0, zrot))

        prop_text = sc.get("props", "")
        for pidx, prop in enumerate(props):
            angle = (i + pidx) * 1.7
            radius = 1.0 + (pidx * .65)
            loc = (math.sin(angle) * radius, 0.8 + pidx * .6, .35)
            if prop_text:
                loc = (loc[0], loc[1], loc[2] + .1)
            key(prop, start, loc)
            key(prop, end, (loc[0] + .35, loc[1], loc[2]))

        distance = 10.5
        if "close" in cam_text:
            distance = 6.5
        elif "wide" in cam_text or "establish" in cam_text:
            distance = 13.5
        cam_start = (0, -distance, 5.2)
        cam_end = (1.2 if "pan" in cam_text or "track" in cam_text else 0,
                   -distance + (1.5 if "push" in cam_text else 0), 5.0)
        for frame, loc in ((start, cam_start), (end, cam_end)):
            camera.location = loc
            target = Vector((0, 0, 1.4))
            direction = target - Vector(loc)
            camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
            camera.keyframe_insert("location", frame=frame)
            camera.keyframe_insert("rotation_euler", frame=frame)

    # Linear interpolation prevents overshooting between story shots.
    for obj in list(bpy.data.objects):
        if obj.animation_data and obj.animation_data.action:
            for fc in obj.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "BEZIER"

    scene.frame_set(1)
    blend_file = output.parent / "scene.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_file))
    result = bpy.ops.render.render(animation=True)
    if "FINISHED" not in result:
        raise RuntimeError(f"Blender animation render did not finish: {result}")


if "--free-blender-render" in sys.argv:
    _blender_render()
