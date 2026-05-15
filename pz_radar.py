import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import sys
import struct
import glob as glob_mod
import math
import random
import base64
import io

def _set_topmost(state):
    """Set window always-on-top. Property setter first (safe), then fallbacks."""
    try:
        import pygame._sdl2.video as v
        w = v.Window.from_display_module()
        w.always_on_top = state
        return True
    except Exception:
        pass
    try:
        import ctypes
        sdl2 = ctypes.CDLL("SDL2.dll")
        sdl2.SDL_SetWindowAlwaysOnTop.argtypes = [ctypes.c_void_p, ctypes.c_int]
        sdl2.SDL_SetWindowAlwaysOnTop.restype = None
        import pygame._sdl2.video as v
        w = v.Window.from_display_module()
        sdl2.SDL_SetWindowAlwaysOnTop(ctypes.c_void_p(w.window), 1 if state else 0)
        return True
    except Exception:
        pass
    try:
        import ctypes
        hwnd = pygame.display.get_wm_info().get('window')
        if hwnd:
            flag = -1 if state else -2
            ctypes.windll.user32.SetWindowPos(hwnd, flag, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)
            return True
    except Exception:
        pass
    try:
        import ctypes
        hwnd = pygame.display.get_wm_info().get('window')
        if hwnd:
            GWL_EXSTYLE = -20
            WS_EX_TOPMOST = 0x00000008
            ex = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ex = (ex | WS_EX_TOPMOST) if state else (ex & ~WS_EX_TOPMOST)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex)
            ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0004 | 0x0020)
            return True
    except Exception:
        pass
    return False

VERSION = ""

LOCK_CONFIG = False
DEBUG = False
CLEAR_SOUND_VOLUME = 0.4
ACTION_SOUND_VOLUME = 0.2
MUSIC_VOLUME = 0.2
ZOMBIE_CHECK = True

ZOMBIEMAP_TXT_PATH = os.path.join(os.path.expanduser('~'), 'Zomboid', 'Lua', 'ZombieMapWritter', 'zombiemap.txt')
GLOBAL_TXT_PATH    = os.path.join(os.path.expanduser('~'), 'Zomboid', 'Lua', 'ZombieMapWritter', 'zombiemap_global.txt')

LOTHEADER_PATH   = r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid\media\maps\Muldraugh, KY"
DETECTED_SAVE_PATH = os.path.join(os.path.expanduser('~'), 'Zomboid', 'Lua', 'ZombieMapWritter', 'detected_save.txt')
CLEARED_CHUNKS_PATH = os.path.join(os.path.expanduser('~'), 'Zomboid', 'Lua', 'ZombieMapWritter', 'zombiemap_cleaningall_{savename}.txt')

ZOMBID_SAVES_DIR = os.path.join(os.path.expanduser('~'), 'Zomboid', 'Saves')
ZOMBID_LUA_DIR = os.path.join(os.path.expanduser('~'), 'Zomboid', 'Lua')

WINDOW_W = 1000
WINDOW_H = 1000
DEFAULT_ZOOM = 4.63
DATA_REFRESH_MS = 170
PULSE_RING_RADIUS = 20

COLOR_BACKGROUND = (10,10,10)
COLOR_PLAYER = (255,255,255)
COLOR_CHUNK_GRID = (255,255,255)
CHUNK_SIZE = 10
CELL_SIZE = 300

SHOW_BUILDINGS = True
SHOW_CHUNK_GRID = True
SHOW_PLAYER_ARROW = True
CLEAR_RADIUS = 9

LOD_CONFIG = [
    {"name": "Full",   "type": "full"},
    {"name": "LowRes", "type": "lowres"},
]
LOD_ZOOM_THRESHOLD = 0.37

SCROLL_TEXTS = ["Don't forget to wash your hands!", "Vibe-coded by OpenCode!", "Implementation by Unamelable", "It ain't much, but it's honest work", "Puppies!", "Are you dead yet?", "JUST DO IT!", "THIS IS HOW YOU DIED"]
SCROLL_TEXTS_CFG = ""

def debug_print(msg):
    if DEBUG:
        try:
            print(f"[PZ Radar {VERSION}] {msg}")
        except:
            pass

CFG_KEYS = {
    'LOCK_CONFIG': bool, 'DEBUG': bool, 'CLEAR_SOUND_VOLUME': float,
    'ACTION_SOUND_VOLUME': float, 'MUSIC_VOLUME': float, 'ZOMBIE_CHECK': bool,
    'ZOMBIEMAP_TXT_PATH': str, 'GLOBAL_TXT_PATH': str,
    'LOTHEADER_PATH': str,     'DETECTED_SAVE_PATH': str, 'CLEARED_CHUNKS_PATH': str,
    'ZOMBID_SAVES_DIR': str, 'ZOMBID_LUA_DIR': str,
    'WINDOW_W': int, 'WINDOW_H': int, 'DEFAULT_ZOOM': float,
    'DATA_REFRESH_MS': int, 'PULSE_RING_RADIUS': int,
    'SCROLL_TEXTS_CFG': str,
    'CHUNK_SIZE': int, 'CELL_SIZE': int,
    'SHOW_BUILDINGS': bool, 'SHOW_CHUNK_GRID': bool, 'SHOW_PLAYER_ARROW': bool,
    'CLEAR_RADIUS': int,
    'LOD_ZOOM_THRESHOLD': float, 'LOW_RES_TILES_PER_PX': int,
}

def _parse_cfg_value(s, t):
    s = s.strip()
    if t is str:
        return s.strip('"').strip("'")
    if t is bool:
        return s.lower() in ('true', '1', 'yes')
    if t is int:
        return int(s)
    if t is float:
        return float(s)
    return s

def _write_default_cfg(path):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('# PZ Radar Configuration\n')
        f.write('# Delete this file to regenerate defaults.\n\n')
        for k, t in CFG_KEYS.items():
            if k == 'SCROLL_TEXTS_CFG':
                f.write('# Scrolling texts at help panel bottom. Pipe-separated, e.g.:\n')
                f.write('# SCROLL_TEXTS_CFG = "hello world|foo bar|baz qux"\n')
            if k == 'MUSIC_VOLUME':
                f.write('# Background music volume (0.0 - 1.0). Adjust with UP/DOWN arrows.\n')
            v = globals().get(k, '')
            if t is str:
                f.write(f'{k} = "{v}"\n')
            elif t is bool:
                f.write(f'{k} = {"true" if v else "false"}\n')
            else:
                f.write(f'{k} = {v}\n')

def load_config():
    base = os.path.dirname(os.path.abspath(sys.argv[0]))
    path = os.path.join(base, "pz_radar.cfg")
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' not in line:
                        continue
                    k, _, v = line.partition('=')
                    k = k.strip()
                    if k not in CFG_KEYS:
                        continue
                    globals()[k] = _parse_cfg_value(v, CFG_KEYS[k])
            debug_print(f"Loaded config: {path}")
        else:
            debug_print(f"No config file, writing defaults: {path}")
            _write_default_cfg(path)
    except Exception as e:
        debug_print(f"Config error: {e}")

def ask_path(label, default):
    exists = os.path.isdir(default) or os.path.isfile(default)
    if exists:
        return default
    print(f"Missing {label}: {default}")
    path = input(f"Enter path for {label}: ").strip()
    if not (os.path.isdir(path) or os.path.isfile(path)):
        sys.exit(1)
    return path

# -------- BUILDINGS (from .lotheader binary files) --------

CHECKED_ROOMS = {}       # global_room_id -> last_check_time_ms
ROOM_RECTS = {}        # global_room_id -> list of (rx, ry, rw, rh)
ROOM_LEVEL = {}        # global_room_id -> floor level (z)
ROOM_TO_BUILDING = {}  # global_room_id -> building_global_id
BUILDING_ROOMS = {}    # building_global_id -> set of global_room_ids
RECT_TO_ROOM = {}

# State
CURRENT_SAVE = None
CLEANED_BUILDINGS = set()
CLEARED_CHUNKS = set()
TRACKED_BUILDINGS = set()
BUILDING_RECTS = {}
_room_spatial_chunks = {}  # (chx, chy) -> list of (rx, ry, rw, rh, level)
_flat_rects = []  # list of (bx, by, bw, bh, room_id, level, building_id) for fast rendering
_buildings_cache = None
_cache_world_x = 0
_cache_world_y = 0
_cache_world_w = 0
_cache_world_h = 0
_buildings_cache_dirty = True

_last_read_mtime = 0

# Sound
_clear_sound = None
_click_sound = None
_keypress_sound = None
_disable_sound = None
_zoom_in_sound = None
_zoom_out_sound = None
_zoom_channel = None
_zoom_direction = None
_last_zoom_time = 0

def _make_clear_sound():
    global _clear_sound
    sample_rate = 22050
    duration = 1.2
    frames = int(sample_rate * duration)
    buf = bytearray()

    # Pre-compute main chime
    main = [0.0] * frames
    for i in range(frames):
        t = i / sample_rate
        val = (math.sin(2 * math.pi * 1000 * t)
             + 0.5 * math.sin(2 * math.pi * 2000 * t)
             + 0.3 * math.sin(2 * math.pi * 1500 * t))
        env = math.exp(-t * 4.5) * min(1.0, t * 200)
        main[i] = val * env

    # Build final signal with prolonged echo
    for i in range(frames):
        t = i / sample_rate
        val = main[i]

        for delay, gain in [(0.15, 0.30), (0.30, 0.15), (0.45, 0.08), (0.60, 0.04)]:
            dt = t - delay
            if dt > 0:
                idx = int(delay * sample_rate)
                if idx < i:
                    e = math.exp(-dt * 3.5)
                    fade = min(1.0, dt * 80)
                    val += gain * e * fade * main[idx]

        val *= 0.35
        s = max(-32767, min(32767, int(val * 32767)))
        buf.extend(struct.pack('<h', s))

    try:
        _clear_sound = pygame.mixer.Sound(buffer=bytes(buf))
        _clear_sound.set_volume(CLEAR_SOUND_VOLUME)
    except:
        _clear_sound = None

def _make_click_sound():
    global _click_sound
    sample_rate = 22050
    duration = 0.15
    frames = int(sample_rate * duration)
    buf = bytearray()

    for i in range(frames):
        t = i / sample_rate
        noise = (random.random() * 2 - 1)
        env = math.exp(-t * 25)
        tone = math.sin(2 * math.pi * 800 * t) * env * 0.3
        sample = (noise * 0.7 + tone) * env
        s = max(-32767, min(32767, int(sample * 32767)))
        buf.extend(struct.pack('<h', s))

    try:
        _click_sound = pygame.mixer.Sound(buffer=bytes(buf))
        _click_sound.set_volume(ACTION_SOUND_VOLUME)
    except Exception as e:
        debug_print(f"Click sound init failed: {e}")
        _click_sound = None

def _make_keypress_sound():
    global _keypress_sound
    sample_rate = 22050
    duration = 0.3
    frames = int(sample_rate * duration)
    fade_frames = int(sample_rate * 0.02)
    buf = bytearray()

    for i in range(frames):
        t = i / sample_rate
        val = (0.5 * math.sin(2 * math.pi * 880 * t) +
               0.3 * math.sin(2 * math.pi * 1320 * t) +
               0.15 * math.sin(2 * math.pi * 1760 * t))
        env = math.exp(-t * 6) * min(1.0, t * 400)
        if i >= frames - fade_frames:
            env *= (frames - i) / fade_frames
        sample = val * env * 0.4
        s = max(-32767, min(32767, int(sample * 32767)))
        buf.extend(struct.pack('<h', s))

    try:
        _keypress_sound = pygame.mixer.Sound(buffer=bytes(buf))
        _keypress_sound.set_volume(ACTION_SOUND_VOLUME)
    except Exception as e:
        debug_print(f"Keypress sound init failed: {e}")
        _keypress_sound = None

def _make_disable_sound():
    global _disable_sound
    sample_rate = 22050
    duration = 0.3
    frames = int(sample_rate * duration)
    fade_frames = int(sample_rate * 0.02)
    buf = bytearray()

    for i in range(frames):
        t = i / sample_rate
        freq = 660 - t * 1200
        val = (0.5 * math.sin(2 * math.pi * freq * t) +
               0.25 * math.sin(2 * math.pi * freq * 0.5 * t))
        env = math.exp(-t * 5) * min(1.0, t * 400)
        if i >= frames - fade_frames:
            env *= (frames - i) / fade_frames
        sample = val * env * 0.35
        s = max(-32767, min(32767, int(sample * 32767)))
        buf.extend(struct.pack('<h', s))

    try:
        _disable_sound = pygame.mixer.Sound(buffer=bytes(buf))
        _disable_sound.set_volume(ACTION_SOUND_VOLUME)
    except Exception as e:
        debug_print(f"Disable sound init failed: {e}")
        _disable_sound = None

def _make_zoom_in_sound():
    global _zoom_in_sound
    sample_rate = 22050
    duration = 0.5
    frames = int(sample_rate * duration)
    fade = int(sample_rate * 0.02)
    buf = bytearray()

    tap_rate = 65
    tap_duty = 0.25

    for i in range(frames):
        t = i / sample_rate
        phase = (t * tap_rate) % 1.0
        if phase < tap_duty:
            local_t = phase / tap_duty
            env = math.sin(math.pi * local_t)
            val = math.sin(2 * math.pi * 3500 * t) * env
        else:
            val = 0.0
        if i < fade:
            val *= i / fade
        if i >= frames - fade:
            val *= (frames - i) / fade
        sample = val * 0.25
        s = max(-32767, min(32767, int(sample * 32767)))
        buf.extend(struct.pack('<h', s))

    try:
        _zoom_in_sound = pygame.mixer.Sound(buffer=bytes(buf))
        _zoom_in_sound.set_volume(ACTION_SOUND_VOLUME)
    except Exception as e:
        debug_print(f"Zoom-in sound init failed: {e}")
        _zoom_in_sound = None

def _make_zoom_out_sound():
    global _zoom_out_sound
    sample_rate = 22050
    duration = 0.5
    frames = int(sample_rate * duration)
    fade = int(sample_rate * 0.02)
    buf = bytearray()

    tap_rate = 50
    tap_duty = 0.2

    for i in range(frames):
        t = i / sample_rate
        phase = (t * tap_rate) % 1.0
        if phase < tap_duty:
            local_t = phase / tap_duty
            env = math.sin(math.pi * local_t)
            val = math.sin(2 * math.pi * 3400 * t) * env
        else:
            val = 0.0
        if i < fade:
            val *= i / fade
        if i >= frames - fade:
            val *= (frames - i) / fade
        sample = val * 0.2
        s = max(-32767, min(32767, int(sample * 32767)))
        buf.extend(struct.pack('<h', s))

    try:
        _zoom_out_sound = pygame.mixer.Sound(buffer=bytes(buf))
        _zoom_out_sound.set_volume(ACTION_SOUND_VOLUME)
    except Exception as e:
        debug_print(f"Zoom-out sound init failed: {e}")
        _zoom_out_sound = None

import time

# -- Chiptune Playlist System (hardcoded from TrackNames.txt) ------------
# Tracks are .B64 base64-encoded module files stored alongside this script.
# pygame.mixer.music loads them via io.BytesIO � no raw .XM / .IT support needed.
# When compiled to exe, they sit next to the .exe � still found automatically.

def _app_dir():
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.executable)))
    return os.path.dirname(os.path.abspath(__file__))

_MUSIC_DIR = _app_dir()

_TRACK_DB = [
    ("sickonmonday.B64",     "Sick on Monday - ELWOOD (Jussi Salmela) [20.04.1998]"),
    ("chipnight.B64",        "chipnight . YTK - yattak (BMR)"),
    ("youarenotalone.B64",   "You are not alone - Debi of GFA [December 2002]"),
    ("lonelysail.B64",       "Lonely sail - V.Kup"),
    ("butterflyflewaway.B64", "Butterfly Flew Away - Damac & Swallow"),
    ("undertheopensky.B64",  "Under the open sky - Falcon/Substance and Screw!Bolt [13.07.1996]"),
    ("tooold.B64",           "too old (final) - tj technoiZ [05.12.2004]"),
    ("allnightalone.B64",    "all night alone - argh [2000]"),
    ("daysofold.B64",        "Days of Old - darkwold (Phill Torreele) [1995]"),
    ("alongthehighway.B64",  "Along The Highway - Cooth [19/05/2002]"),
]

_SONG_LIST = []               # list of (filepath, display_name) tuples
_current_track_index = -1
_SONG_NAME = "No music"
_music_start_time = 0.0
_track_duration = 0.0
_TRACK_DURATION_EST_BYTES_PER_SEC = 3000

def _parse_xm_duration(data):
    try:
        headersize = struct.unpack_from('<I', data, 0x3C)[0]
        songlength = struct.unpack_from('<H', data, 0x40)[0]
        numpatterns = struct.unpack_from('<H', data, 0x46)[0]
        speed = struct.unpack_from('<H', data, 0x4C)[0]
        bpm = struct.unpack_from('<H', data, 0x4E)[0]
        if bpm == 0: bpm = 125
        if speed == 0: speed = 6
        order = list(data[0x50:0x50 + songlength])
        pat_off = 0x3C + headersize
        rows = {}
        for pi in range(numpatterns):
            if pat_off + 9 > len(data): break
            phl = struct.unpack_from('<I', data, pat_off)[0]
            if phl < 4: break
            rows[pi] = struct.unpack_from('<H', data, pat_off + 5)[0]
            pat_off += phl + struct.unpack_from('<H', data, pat_off + 7)[0]
        total = sum(rows.get(p, 64) for p in order if p < 254)
        return max(30.0, total * speed * 2.5 / bpm) if total else None
    except:
        return None

def _parse_it_duration(data):
    try:
        ordnum = struct.unpack_from('<H', data, 0x1E)[0]
        speed = struct.unpack_from('<H', data, 0x2E)[0]
        bpm = struct.unpack_from('<H', data, 0x30)[0]
        if bpm == 0: bpm = 125
        if speed == 0: speed = 6
        total = sum(64 for p in data[0x32:0x32 + ordnum] if p < 255)
        return max(30.0, total * speed * 2.5 / bpm) if total else None
    except:
        return None

def _calculate_module_duration(raw_data):
    if raw_data[:17] in (b"Extended Module: ", b"Extended Module:"):
        return _parse_xm_duration(raw_data)
    if raw_data[:4] == b"IMPM":
        return _parse_it_duration(raw_data)
    if len(raw_data) > 1084:
        mod = raw_data[1080:1084]
        if mod in (b"M.K.", b"M!K.", b"FLT4", b"4CHN", b"6CHN", b"8CHN"):
            try:
                order = list(raw_data[0x3E:0x3E + raw_data[0x3C]])
                total = sum(64 for p in order if p < 128)
                return max(30.0, total * 6 * 2.5 / 125) if total else None
            except:
                return None
    return None

def _build_playlist():
    """Build playlist from _TRACK_DB, keeping only .B64 files that exist."""
    global _SONG_LIST
    _SONG_LIST = []
    # Search script directory and one level of subdirectories
    search_dirs = [_MUSIC_DIR] + [os.path.join(_MUSIC_DIR, d) for d in os.listdir(_MUSIC_DIR)
                    if os.path.isdir(os.path.join(_MUSIC_DIR, d))]
    found_any = False
    for filename, display_name in _TRACK_DB:
        for search_dir in search_dirs:
            fpath = os.path.join(search_dir, filename)
            if os.path.isfile(fpath):
                _SONG_LIST.append((fpath, display_name))
                found_any = True
                break
            else:
                debug_print(f"Track not found: {fpath}")
    if found_any:
        debug_print(f"Playlist built: {len(_SONG_LIST)}/{len(_TRACK_DB)} tracks available")
    else:
        debug_print(f"No B64 tracks found in script directory or subfolders")

def _pick_random_track():
    """Select a random track index, avoiding the currently playing one."""
    global _current_track_index
    if not _SONG_LIST:
        _current_track_index = -1
        return
    if len(_SONG_LIST) <= 1:
        _current_track_index = 0
        return
    idx = random.randint(0, len(_SONG_LIST) - 1)
    if idx == _current_track_index:
        idx = (idx + 1) % len(_SONG_LIST)
    _current_track_index = idx

def _load_track(index):
    """Decode .B64 file and start playing the track at the given index."""
    global _SONG_NAME, _music_start_time, _track_duration
    if not (0 <= index < len(_SONG_LIST)):
        _SONG_NAME = "No music"
        try:
            pygame.mixer.music.stop()
        except:
            pass
        return

    fpath, display_name = _SONG_LIST[index]
    _SONG_NAME = display_name
    try:
        with open(fpath, "r", encoding="ascii") as f:
            b64_data = f.read().strip()
        raw_data = base64.b64decode(b64_data)
        pygame.mixer.music.load(io.BytesIO(raw_data))
        pygame.mixer.music.set_volume(MUSIC_VOLUME)
        if MUSIC_VOLUME > 0.01:
            pygame.mixer.music.play(0)
        _music_start_time = time.time()
        calc = _calculate_module_duration(raw_data)
        _track_duration = calc if calc else max(30.0, len(raw_data) / _TRACK_DURATION_EST_BYTES_PER_SEC)
        debug_print(f"Now playing [{index+1}/{len(_SONG_LIST)}]: {_SONG_NAME}")
    except Exception as e:
        debug_print(f"Failed to load track {fpath}: {e}")
        _SONG_NAME = "Error"
        _track_duration = 5.0

def _next_track_sequential():
    global _current_track_index
    if not _SONG_LIST:
        _current_track_index = -1
        return
    _current_track_index = (_current_track_index + 1) % len(_SONG_LIST)
    _load_track(_current_track_index)

def _next_track_random():
    _pick_random_track()
    _load_track(_current_track_index)

def _prev_track():
    global _current_track_index
    if not _SONG_LIST:
        _current_track_index = -1
        return
    _current_track_index = (_current_track_index - 1) % len(_SONG_LIST)
    _load_track(_current_track_index)

def _check_track_ended():
    """Auto-advance when the current track finishes (random next)."""
    if not _SONG_LIST or _current_track_index < 0:
        return
    # Don't auto-advance if muted � user explicitly stopped playback
    if MUSIC_VOLUME <= 0.01:
        return
    try:
        if pygame.mixer.music.get_busy():
            # Safety fallback: only force-advance if track runs vastly past estimate
            if time.time() - _music_start_time > _track_duration + 60.0:
                _next_track_random()
            return
    except:
        pass
    _next_track_random()


# -- Title color (smooth random) ----------------------------------------

_title_color_t = 0.0
_title_color_src = (255, 255, 255)
_title_color_dst = (255, 255, 255)

def _get_title_color():
    """Return a smoothly changing random color for SONG_NAME."""
    global _title_color_t, _title_color_src, _title_color_dst

    _title_color_t += 1.0 / 60.0
    if _title_color_t >= 1.0:
        _title_color_t = 0.0
        _title_color_src = _title_color_dst
        _title_color_dst = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

    # Smoothstep interpolation
    t = _title_color_t
    t = t * t * (3.0 - 2.0 * t)

    r = int(_title_color_src[0] + (_title_color_dst[0] - _title_color_src[0]) * t)
    g = int(_title_color_src[1] + (_title_color_dst[1] - _title_color_src[1]) * t)
    b = int(_title_color_src[2] + (_title_color_dst[2] - _title_color_src[2]) * t)
    return (r, g, b)


_MUSIC_AVAILABLE = True


def _init_background_music():
    """Initialize the playlist and start playing the first random track."""
    global _MUSIC_AVAILABLE
    _build_playlist()
    if _SONG_LIST:
        _pick_random_track()
        _load_track(_current_track_index)
        return
    # No B64 tracks found � still mark music as available but play nothing
    debug_print("No B64 tracks found in toconvert/. Music disabled.")
    _MUSIC_AVAILABLE = False

def _start_music():
    _init_background_music()

def _stop_music():
    try:
        pygame.mixer.music.stop()
    except:
        pass

def _read_int(f):
    data = f.read(4)
    return struct.unpack('<I', data)[0]

def _read_string(f):
    buf = bytearray()
    while True:
        c = f.read(1)
        if not c or c == b'\n':
            break
        buf.extend(c)
    return buf.decode('utf-8', errors='replace').strip()

def _parse_one_lotheader(filepath, cellX, cellY):
    rooms = []
    buildings = []
    with open(filepath, 'rb') as f:
        _read_int(f)
        tiles_count = _read_int(f)
        for _ in range(tiles_count):
            _read_string(f)

        f.read(1)
        _read_int(f)
        _read_int(f)
        _read_int(f)

        room_count = _read_int(f)
        for _ in range(room_count):
            name = _read_string(f)
            level = _read_int(f)
            rect_count = _read_int(f)
            rects = []
            for _ in range(rect_count):
                rx = _read_int(f) + cellX * CELL_SIZE
                ry = _read_int(f) + cellY * CELL_SIZE
                rw = _read_int(f)
                rh = _read_int(f)
                rects.append((rx, ry, rw, rh))

            obj_count = _read_int(f)
            for _ in range(obj_count):
                _read_int(f)
                _read_int(f)
                _read_int(f)

            rooms.append({"name": name, "level": level, "rects": rects})

        building_count = _read_int(f)
        for _ in range(building_count):
            room_count_b = _read_int(f)
            room_ids = []
            for _ in range(room_count_b):
                room_ids.append(_read_int(f))
            buildings.append({"room_ids": room_ids})

    return {"rooms": rooms, "buildings": buildings}

def load_buildings(map_dir):
    global ROOM_RECTS, RECT_TO_ROOM, ROOM_LEVEL, ROOM_TO_BUILDING, BUILDING_ROOMS

    if not os.path.isdir(map_dir):
        debug_print(f"Map directory not found: {map_dir}")
        return {}

    pattern = os.path.join(map_dir, '*_*.lotheader')
    files = sorted(glob_mod.glob(pattern))
    debug_print(f"Scanning {len(files)} lotheader files...")

    all_rects = []
    loaded = 0
    next_room_id = 0

    for fp in files:
        base = os.path.basename(fp)
        name = base[:-10]
        parts = name.split('_')
        if len(parts) != 2:
            continue
        try:
            cellX, cellY = int(parts[0]), int(parts[1])
        except ValueError:
            continue

        try:
            data = _parse_one_lotheader(fp, cellX, cellY)
            
            # Assign global IDs to rooms in the order they appear
            # room_index_in_file -> global_room_id
            room_index_to_global = {}
            for room_idx, room in enumerate(data["rooms"]):
                room_id = next_room_id
                next_room_id += 1
                ROOM_RECTS[room_id] = room["rects"]
                ROOM_LEVEL[room_id] = room["level"]
                for rect in room["rects"]:
                    RECT_TO_ROOM[rect] = room_id
                    all_rects.append(rect)
                room_index_to_global[room_idx] = room_id

            # Build building data using global room IDs
            building_global_id = len(BUILDING_ROOMS)
            for b in data["buildings"]:
                global_room_ids = set()
                for orig_room_idx in b["room_ids"]:
                    if orig_room_idx in room_index_to_global:
                        global_room_ids.add(room_index_to_global[orig_room_idx])
                
                if global_room_ids:
                    BUILDING_ROOMS[building_global_id] = global_room_ids
                    for rid in global_room_ids:
                        ROOM_TO_BUILDING[rid] = building_global_id
                    building_global_id += 1

            loaded += 1
        except Exception as e:
            debug_print(f"Parse error {base}: {e}")

    debug_print(f"Loaded buildings from {loaded} cells")
    debug_print(f"  {len(ROOM_RECTS)} rooms, {len(BUILDING_ROOMS)} buildings")
    return {"": all_rects}

def get_building_clean_file():
    if not CURRENT_SAVE:
        return None
    return os.path.join(ZOMBID_LUA_DIR, f"ZombieMapWritter/zombiemap_cleaningbuildings_{CURRENT_SAVE}.txt")

def load_cleaned_buildings():
    global CLEANED_BUILDINGS
    path = get_building_clean_file()
    if not path or not os.path.isfile(path):
        debug_print("No cleaned buildings file to load")
        return
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    CLEANED_BUILDINGS.add(int(line))
                except:
                    pass
        debug_print(f"Loaded {len(CLEANED_BUILDINGS)} cleaned buildings for save {CURRENT_SAVE}")
    except Exception as e:
        debug_print(f"Error loading cleaned buildings: {e}")

def save_cleaned_buildings():
    path = get_building_clean_file()
    if not path:
        return
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for bid in sorted(CLEANED_BUILDINGS):
                f.write(f"{bid}\n")
        debug_print(f"Saved {len(CLEANED_BUILDINGS)} cleaned buildings")
    except Exception as e:
        debug_print(f"Error saving cleaned buildings: {e}")

def get_cleared_chunks_path():
    if not CURRENT_SAVE:
        return None
    return CLEARED_CHUNKS_PATH.format(savename=CURRENT_SAVE)

def load_cleared_chunks():
    path = get_cleared_chunks_path()
    if not path or not os.path.isfile(path):
        return
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(",")
                if len(parts) >= 2:
                    try:
                        CLEARED_CHUNKS.add((int(parts[0]), int(parts[1])))
                    except:
                        pass
        debug_print(f"Loaded {len(CLEARED_CHUNKS)} cleared chunks")
    except Exception as e:
        debug_print(f"Error loading cleared chunks: {e}")

def save_cleared_chunks():
    path = get_cleared_chunks_path()
    if not path:
        return
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for chx, chy in sorted(CLEARED_CHUNKS):
                f.write(f"{chx},{chy}\n")
        debug_print(f"Saved {len(CLEARED_CHUNKS)} cleared chunks")
    except Exception as e:
        debug_print(f"Error saving cleared chunks: {e}")

def build_building_rects():
    """Pre-compute all room rects per building for zombie-hit testing."""
    for bid, room_ids in BUILDING_ROOMS.items():
        rects = []
        for rid in room_ids:
            rects.extend(ROOM_RECTS.get(rid, []))
        BUILDING_RECTS[bid] = rects

def build_room_spatial():
    """Index room rects by chunk (10x10) for fast is_inside_room lookup."""
    _room_spatial_chunks.clear()
    for room_id, rects in ROOM_RECTS.items():
        zz = ROOM_LEVEL.get(room_id, 0)
        for rx, ry, rw, rh in rects:
            min_chx = int(rx // 10)
            max_chx = int((rx + rw - 1) // 10)
            min_chy = int(ry // 10)
            max_chy = int((ry + rh - 1) // 10)
            for chx in range(min_chx, max_chx + 1):
                for chy in range(min_chy, max_chy + 1):
                    key = (chx, chy)
                    if key not in _room_spatial_chunks:
                        _room_spatial_chunks[key] = []
                    _room_spatial_chunks[key].append((rx, ry, rw, rh, zz))
    debug_print(f"Room spatial index: {len(_room_spatial_chunks)} chunks indexed")

def build_flat_rects(buildings_by_type):
    """Pre-compute flat rect list with metadata to eliminate dict lookups per frame."""
    global _flat_rects
    _flat_rects = []
    for rects in buildings_by_type.values():
        for (bx, by, bw, bh) in rects:
            room_id = RECT_TO_ROOM.get((bx, by, bw, bh))
            if room_id is None:
                continue
            level = ROOM_LEVEL.get(room_id, 0)
            bid = ROOM_TO_BUILDING.get(room_id)
            _flat_rects.append((bx, by, bw, bh, room_id, level, bid))
    debug_print(f"Flat rects built: {len(_flat_rects)} total")

def _build_buildings_cache():
    global _buildings_cache
    global _cache_world_x, _cache_world_y, _cache_world_w, _cache_world_h, _buildings_cache_dirty
    if not _flat_rects:
        return
    min_x = min(bx for bx, _, _, _, _, _, _ in _flat_rects)
    min_y = min(by for _, by, _, _, _, _, _ in _flat_rects)
    max_x = max(bx + bw for bx, _, bw, _, _, _, _ in _flat_rects)
    max_y = max(by + bh for _, by, _, bh, _, _, _ in _flat_rects)
    pad = 20
    min_x -= pad
    min_y -= pad
    max_x += pad
    max_y += pad
    extent_w = max_x - min_x
    extent_h = max_y - min_y
    s = min(2000 / extent_w, 2000 / extent_h, 0.1)
    _cache_world_x = min_x
    _cache_world_y = min_y
    _cache_world_w = extent_w
    _cache_world_h = extent_h
    cw = max(1, int(extent_w * s))
    ch = max(1, int(extent_h * s))
    cache = pygame.Surface((cw, ch))
    cleaned_room_ids = set()
    for bid in CLEANED_BUILDINGS:
        cleaned_room_ids.update(BUILDING_ROOMS.get(bid, set()))
    partially_room_ids = set(CHECKED_ROOMS) - cleaned_room_ids

    buildings_touched = set()
    for rid in CHECKED_ROOMS:
        bid = ROOM_TO_BUILDING.get(rid)
        if bid is not None:
            buildings_touched.add(bid)
    for (bx, by, bw, bh, room_id, level, bid) in _flat_rects:
        cx = int((bx - min_x) * s)
        cy = int((by - min_y) * s)
        cw_r = max(1, int(bw * s))
        ch_r = max(1, int(bh * s))
        color, outline = _building_colors(room_id, level, bid, cleaned_room_ids, partially_room_ids, buildings_touched)
        if color is not None:
            pygame.draw.rect(cache, color, (cx, cy, cw_r, ch_r))
        if cw_r > 1 and ch_r > 1:
            pygame.draw.rect(cache, outline, (cx, cy, cw_r, ch_r), 1)
    _buildings_cache = cache
    _buildings_cache_dirty = False

def _building_colors(room_id, level, bid, cleaned_ids, partial_ids, touched_ids):
    """Return (fill_color, outline_color) for a building rect. fill_color=None means skip fill."""
    if room_id in cleaned_ids:
        return ((60, 110, 60), (80, 150, 80))
    if room_id in partial_ids:
        if level == 0:
            return ((200, 50, 50), (240, 80, 80))
        dark = min((level - 1) * 40, 120)
        return ((max(30, 200 - dark), max(20, 110 - dark), max(30, 160 - dark)),
                (max(50, 240 - dark), max(40, 140 - dark), max(50, 200 - dark)))
    if bid is not None and bid in touched_ids:
        return (None, (40, 40, 50))
    dark = level * 12
    return ((max(10, 50 - dark), max(10, 60 - dark), max(10, 90 - dark)),
            (max(15, 80 - dark), max(15, 90 - dark), max(15, 130 - dark)))

def has_zombies_in_building(building_id, zombies):
    """Check if any zombie position falls inside any room rect of this building."""
    rects = BUILDING_RECTS.get(building_id, [])
    if not rects:
        return False
    for zx, zy, _, _ in zombies:
        for rx, ry, rw, rh in rects:
            if rx <= zx < rx + rw and ry <= zy < ry + rh:
                return True
    return False

def is_inside_room(zx, zy, zz):
    chx = int(zx // 10)
    chy = int(zy // 10)
    for (rx, ry, rw, rh, level) in _room_spatial_chunks.get((chx, chy), []):
        if level != zz:
            continue
        if rx <= zx < rx + rw and ry <= zy < ry + rh:
            return True
    return False

def update_cleared_chunks(px, py, zombies):
    global CLEAR_RADIUS
    center_chx = int(px // 10)
    center_chy = int(py // 10)
    for chx in range(center_chx - CLEAR_RADIUS, center_chx + CLEAR_RADIUS + 1):
        for chy in range(center_chy - CLEAR_RADIUS, center_chy + CLEAR_RADIUS + 1):
            key = (chx, chy)
            has_zombie = any(int(zx // 10) == chx and int(zy // 10) == chy for zx, zy, _, _ in zombies)
            if has_zombie:
                CLEARED_CHUNKS.discard(key)
            else:
                CLEARED_CHUNKS.add(key)

def revalidate_tracked_buildings(zombies, newly_cleared):
    """Re-check buildings that had zombies. Clear any that are now zombie-free."""
    if not zombies:
        return
    global TRACKED_BUILDINGS
    for bid in list(TRACKED_BUILDINGS):
        if not has_zombies_in_building(bid, zombies):
            if bid not in CLEANED_BUILDINGS:
                CLEANED_BUILDINGS.add(bid)
                newly_cleared.append(bid)
                debug_print(f"Building {bid} CLEARED! (zombies cleared)")
            TRACKED_BUILDINGS.discard(bid)

def invalidate_zombie_touched_buildings(zombies):
    """Remove buildings from CLEANED_BUILDINGS if zombies are inside them."""
    for bid in list(CLEANED_BUILDINGS):
        if has_zombies_in_building(bid, zombies):
            CLEANED_BUILDINGS.discard(bid)
            TRACKED_BUILDINGS.add(bid)
            debug_print(f"Building {bid} re-contaminated by zombies!")

def check_player_in_buildings(px, py, pz, zombies, now, force=False):
    """Check if player is in a room. Mark buildings clean per zombie presence."""
    global TRACKED_BUILDINGS
    if px is None or py is None:
        return []

    newly_cleared = []

    for room_id, rects in ROOM_RECTS.items():
        if not force and room_id in CHECKED_ROOMS:
            continue
        if ROOM_LEVEL.get(room_id, 0) != pz:
            continue

        player_in_room = False
        for rect in rects:
            rx, ry, rw, rh = rect
            if rx <= px < rx + rw and ry <= py < ry + rh:
                player_in_room = True
                break

        if player_in_room:
            debug_print(f"Player entered room {room_id} at ({px:.0f},{py:.0f}) level {pz}")
            CHECKED_ROOMS[room_id] = now
            building_id = ROOM_TO_BUILDING.get(room_id)
            if building_id is not None and building_id not in CLEANED_BUILDINGS:
                if ZOMBIE_CHECK:
                    if has_zombies_in_building(building_id, zombies):
                        if building_id not in TRACKED_BUILDINGS:
                            TRACKED_BUILDINGS.add(building_id)
                            debug_print(f"Building {building_id} tracking (zombies inside)")
                    else:
                        CLEANED_BUILDINGS.add(building_id)
                        newly_cleared.append(building_id)
                        debug_print(f"Building {building_id} CLEARED! (no zombies, {len(BUILDING_ROOMS[building_id])} rooms)")
                else:
                    building_rooms = BUILDING_ROOMS.get(building_id, set())
                    if building_rooms and building_rooms.issubset(CHECKED_ROOMS.keys()):
                        CLEANED_BUILDINGS.add(building_id)
                        newly_cleared.append(building_id)
                        debug_print(f"Building {building_id} CLEARED! (all rooms visited, {len(building_rooms)} rooms)")

    return newly_cleared


def force_clear_building_at(px, py, pz, zombies):
    """Find nearest building to player position and clear it if no zombies. Checks all floors."""
    debug_print(f"force_clear: scanning {len(ROOM_RECTS)} rooms near ({px:.0f},{py:.0f}) z={pz}")
    best_dist = 10.0
    best_bid = None
    for room_id, rects in ROOM_RECTS.items():
        for rx, ry, rw, rh in rects:
            if rx <= px < rx + rw and ry <= py < ry + rh:
                bid = ROOM_TO_BUILDING.get(room_id)
                if bid is not None:
                    best_bid = bid
                    best_dist = -1
                break
            cx = max(rx, min(px, rx + rw - 1))
            cy = max(ry, min(py, ry + rh - 1))
            dx = px - cx
            dy = py - cy
            dist = dx * dx + dy * dy
            if dist < best_dist:
                other = ROOM_TO_BUILDING.get(room_id)
                if other is not None:
                    best_dist = dist
                    best_bid = other
    if best_bid is None:
        debug_print("  no building found near player")
        return False
    debug_print(f"  nearest building {best_bid} dist={best_dist:.0f}")
    if best_bid in CLEANED_BUILDINGS:
        debug_print(f"  building {best_bid} already cleared")
        return False
    has_zombies = has_zombies_in_building(best_bid, zombies)
    debug_print(f"  has_zombies={has_zombies} zombies_count={len(zombies)}")
    if has_zombies:
        TRACKED_BUILDINGS.add(best_bid)
        debug_print(f"  tracking building {best_bid}")
        return False
    CLEANED_BUILDINGS.add(best_bid)
    TRACKED_BUILDINGS.discard(best_bid)
    debug_print(f"  CLEARED building {best_bid}")
    for rid in BUILDING_ROOMS.get(best_bid, set()):
        CHECKED_ROOMS[rid] = pygame.time.get_ticks()
    save_cleaned_buildings()
    return True


STALE_ROOM_TIMEOUT = 300000  # 5 minutes in ms

def purge_stale_checked_rooms(now):
    global _buildings_cache_dirty
    stale = [rid for rid, t in CHECKED_ROOMS.items() if now - t > STALE_ROOM_TIMEOUT]
    for rid in stale:
        del CHECKED_ROOMS[rid]
    if stale:
        debug_print(f"Purged {len(stale)} stale checked rooms")
        _buildings_cache_dirty = True

# -------- Detect current save --------

def detect_current_save():
    if not os.path.isdir(ZOMBID_SAVES_DIR):
        debug_print(f"Saves dir not found: {ZOMBID_SAVES_DIR}")
        return None

    newest_save = None
    newest_time = 0

    try:
        for mode in os.listdir(ZOMBID_SAVES_DIR):
            mode_path = os.path.join(ZOMBID_SAVES_DIR, mode)
            if not os.path.isdir(mode_path):
                continue
            for name in os.listdir(mode_path):
                save_path = os.path.join(mode_path, name)
                if not os.path.isdir(save_path):
                    continue
                try:
                    mtime = os.path.getmtime(save_path)
                    if mtime > newest_time:
                        newest_time = mtime
                        newest_save = name
                except:
                    pass
    except:
        pass

    if newest_save:
        debug_print(f"Detected save: {newest_save}")
    return newest_save

def write_detected_save(save_name):
    if not save_name:
        return
    try:
        os.makedirs(os.path.dirname(DETECTED_SAVE_PATH), exist_ok=True)
        with open(DETECTED_SAVE_PATH, 'w') as f:
            f.write(save_name)
        debug_print(f"Wrote detected save: {save_name}")
    except Exception as e:
        debug_print(f"Failed to write detected_save.txt: {e}")

def setup_save():
    global CURRENT_SAVE
    save_name = detect_current_save()
    if save_name:
        write_detected_save(save_name)
        CURRENT_SAVE = save_name
        debug_print(f"Save set to: {CURRENT_SAVE}")
        load_cleaned_buildings()
        load_cleared_chunks()

# -------- Drawing --------

def world_to_screen(wx, wy, cam_x, cam_y, zoom, sw, sh):
    return (
        int((wx - cam_x) * zoom + sw / 2),
        int((wy - cam_y) * zoom + sh / 2),
    )

def draw_buildings(surface, cam_x, cam_y, zoom, sw, sh):
    global _buildings_cache_dirty

    if zoom < 0.04:
        if _buildings_cache is None or _buildings_cache_dirty:
            _build_buildings_cache()
        if _buildings_cache is not None:
            sx = (_cache_world_x - cam_x) * zoom + sw / 2
            sy = (_cache_world_y - cam_y) * zoom + sh / 2
            sw2 = _cache_world_w * zoom
            sh2 = _cache_world_h * zoom
            if sw2 > 0 and sh2 > 0:
                scaled = pygame.transform.scale(_buildings_cache, (int(sw2), int(sh2)))
                surface.blit(scaled, (int(sx), int(sy)))
            return

    margin = 30
    vis_left = cam_x - sw / 2 / zoom - margin
    vis_right = cam_x + sw / 2 / zoom + margin
    vis_top = cam_y - sh / 2 / zoom - margin
    vis_bottom = cam_y + sh / 2 / zoom + margin

    cleaned_room_ids = set()
    for bid in CLEANED_BUILDINGS:
        cleaned_room_ids.update(BUILDING_ROOMS.get(bid, set()))

    partially_room_ids = set(CHECKED_ROOMS) - cleaned_room_ids

    buildings_touched = set()
    for rid in CHECKED_ROOMS:
        bid = ROOM_TO_BUILDING.get(rid)
        if bid is not None:
            buildings_touched.add(bid)

    for (bx, by, bw, bh, room_id, level, bid) in _flat_rects:
        if bx + bw < vis_left or bx > vis_right or by + bh < vis_top or by > vis_bottom:
            continue

        color, outline = _building_colors(room_id, level, bid, cleaned_room_ids, partially_room_ids, buildings_touched)

        sx = int((bx - cam_x) * zoom + sw / 2)
        sy = int((by - cam_y) * zoom + sh / 2)
        pw = max(1, int(bw * zoom))
        ph = max(1, int(bh * zoom))

        if color is not None:
            pygame.draw.rect(surface, color, (sx, sy, pw, ph))
        if pw > 1 and ph > 1:
            pygame.draw.rect(surface, outline, (sx, sy, pw, ph), 1)

def draw_chunk_grid(surface, cam_x, cam_y, zoom, sw, sh):
    t = max(0.0, min(1.0, (zoom - 0.12) / (1.0 - 0.12)))
    alpha = int(t * 229)
    if alpha <= 0:
        return

    line_surface = pygame.Surface((sw, sh), pygame.SRCALPHA)
    cell_size = 300.0

    left = int((cam_x - sw / 2 / zoom) / cell_size) - 1
    right = int((cam_x + sw / 2 / zoom) / cell_size) + 2
    top = int((cam_y - sh / 2 / zoom) / cell_size) - 1
    bottom = int((cam_y + sh / 2 / zoom) / cell_size) + 2

    for gx in range(left, right):
        for gy in range(top, bottom):
            wx = gx * cell_size
            wy = gy * cell_size

            sx = int((wx - cam_x) * zoom + sw / 2)
            sy = int((wy - cam_y) * zoom + sh / 2)

            if 0 <= sx <= sw:
                pygame.draw.line(line_surface, (255,255,255,255), (sx, 0), (sx, sh), 1)
            if 0 <= sy <= sh:
                pygame.draw.line(line_surface, (255,255,255,255), (0, sy), (sw, sy), 1)

    line_surface.set_alpha(alpha)
    surface.blit(line_surface, (0, 0))

def draw_cleared_chunks(surface, cam_x, cam_y, zoom, sw, sh):
    chunk_w = 10.0
    margin = 2
    left = int((cam_x - sw / 2 / zoom) // chunk_w) - margin
    right = int((cam_x + sw / 2 / zoom) // chunk_w) + 1 + margin
    top = int((cam_y - sh / 2 / zoom) // chunk_w) - margin
    bottom = int((cam_y + sh / 2 / zoom) // chunk_w) + 1 + margin
    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    for chx in range(left, right):
        for chy in range(top, bottom):
            if (chx, chy) in CLEARED_CHUNKS:
                wx = chx * chunk_w
                wy = chy * chunk_w
                sx = int((wx - cam_x) * zoom + sw / 2)
                sy = int((wy - cam_y) * zoom + sh / 2)
                pw = max(1, int(chunk_w * zoom + 1))
                ph = max(1, int(chunk_w * zoom + 1))
                pygame.draw.rect(overlay, (0, 255, 0, 64), (sx, sy, pw, ph))
    surface.blit(overlay, (0, 0))

SHOW_CELL_COUNTS = False

def draw_cell_counts(surface, cell_counts, cam_x, cam_y, zoom, sw, sh, font):
    CELL_SIZE = 300.0
    for (cx, cy), count in cell_counts.items():
        wx = cx * CELL_SIZE + CELL_SIZE / 2
        wy = cy * CELL_SIZE + CELL_SIZE / 2
        sx = int((wx - cam_x) * zoom + sw / 2)
        sy = int((wy - cam_y) * zoom + sh / 2)
        if sx < -50 or sx > sw + 50 or sy < -50 or sy > sh + 50:
            continue
        intensity = min(count / 20.0, 1.0)
        r = 255
        g = int(255 * (1.0 - intensity * 0.5))
        label = str(count)
        text = font.render(label, True, (r, g, 0))
        text.set_alpha(200)
        surface.blit(text, (sx - text.get_width() // 2, sy - text.get_height() // 2))



# -------- GLOBAL HEATMAP --------

_global_chunks = []
_global_spatial = {}
GRID_SIZE = 1000

def preload_global_data():
    _global_chunks.clear()
    debug_print(f"Pre-loading global data from {GLOBAL_TXT_PATH}...")

    try:
        with open(GLOBAL_TXT_PATH, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                parts = line.split(",")

                if len(parts) < 3:
                    continue

                try:
                    chx_i = int(parts[0])
                    chy_i = int(parts[1])
                    raw = int(parts[2])

                    cx = chx_i * 10
                    cy = chy_i * 10
                    if raw > 0:
                        _global_chunks.append((cx, cy, raw))
                except:
                    pass

        debug_print(f"Loaded {len(_global_chunks)} global chunks")
    except Exception as e:
        debug_print(f"Global preload error: {e}")

def build_spatial_index():
    _global_spatial.clear()

    for (cx, cy, raw) in _global_chunks:
        gx = int(cx // GRID_SIZE)
        gy = int(cy // GRID_SIZE)

        _global_spatial.setdefault((gx, gy), []).append((cx, cy, raw))

# -------- LOW RES --------

_low_res_surface = None
_low_res_data = None
_low_res_min_cx = 0
_low_res_min_cy = 0
_low_res_w = 0
_low_res_h = 0
LOW_RES_TILES_PER_PX = 50

def build_low_res_data():
    global _low_res_data, _low_res_min_cx, _low_res_min_cy
    global _low_res_w, _low_res_h

    if not _global_chunks:
        return

    min_cx = min(c[0] for c in _global_chunks)
    max_cx = max(c[0] for c in _global_chunks)
    min_cy = min(c[1] for c in _global_chunks)
    max_cy = max(c[1] for c in _global_chunks)

    _low_res_min_cx = min_cx
    _low_res_min_cy = min_cy

    _low_res_w = min(int((max_cx - min_cx) / LOW_RES_TILES_PER_PX) + 1, 2048)
    _low_res_h = min(int((max_cy - min_cy) / LOW_RES_TILES_PER_PX) + 1, 2048)

    _low_res_data = [[[0,0] for _ in range(_low_res_h)] for _ in range(_low_res_w)]

    for (cx, cy, raw) in _global_chunks:
        px = int((cx - min_cx) / LOW_RES_TILES_PER_PX)
        py = int((cy - min_cy) / LOW_RES_TILES_PER_PX)

        px = max(0, min(px, _low_res_w - 1))
        py = max(0, min(py, _low_res_h - 1))

        _low_res_data[px][py][0] += raw
        _low_res_data[px][py][1] += 1

def build_low_res_surface():
    global _low_res_surface, _low_res_data

    if _low_res_data is None:
        return

    _low_res_surface = pygame.Surface((_low_res_w, _low_res_h), pygame.SRCALPHA)

    for px in range(_low_res_w):
        for py in range(_low_res_h):
            total, count = _low_res_data[px][py]

            if count == 0:
                continue

            avg = total / count
            t = min(avg / 255.0, 1.0)

            color = (
                255,
                int(255 * (1.0 - t * 0.7)),
                0,
                max(30, int(200 * t))
            )

            _low_res_surface.set_at((px, py), color)

    _low_res_data = None



# -------- DATA READERS --------

def read_dynamic_data(path):
    player_pos = None
    player_z = 0
    zombies = []
    cell_counts = {}

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()

                if line.startswith("P:"):
                    parts = line[2:].split(",")
                    if len(parts) >= 2:
                        try:
                            player_pos = (float(parts[0]), float(parts[1]))
                            player_z = int(float(parts[2])) if len(parts) >= 3 else 0
                        except:
                            pass

                elif line.startswith("Z:"):
                    parts = line[2:].split(",")
                    if len(parts) >= 4:
                        try:
                            zx = float(parts[0])
                            zy = float(parts[1])
                            zz = int(float(parts[2])) if len(parts) >= 4 else 0
                            tag = parts[3].strip()
                            zombies.append((zx, zy, zz, tag))
                        except:
                            pass

                elif line.startswith("C:"):
                    parts = line[2:].split(",")
                    if len(parts) >= 3:
                        try:
                            cx = int(parts[0])
                            cy = int(parts[1])
                            count = int(parts[2])
                            cell_counts[(cx, cy)] = count
                        except:
                            pass
    except:
        pass

    return player_pos, player_z, zombies, cell_counts

# -------- DRAW --------

def draw_global_chunks(surface, cam_x, cam_y, zoom, sw, sh, lod):
    if lod == 1 and _low_res_surface is not None:
        px = int((cam_x - _low_res_min_cx) / LOW_RES_TILES_PER_PX - sw / 2 / zoom / LOW_RES_TILES_PER_PX)
        py = int((cam_y - _low_res_min_cy) / LOW_RES_TILES_PER_PX - sh / 2 / zoom / LOW_RES_TILES_PER_PX)
        pw = max(1, int(sw / zoom / LOW_RES_TILES_PER_PX) + 2)
        ph = max(1, int(sh / zoom / LOW_RES_TILES_PER_PX) + 2)
        clip_px = max(0, px)
        clip_py = max(0, py)
        clip_pw = min(pw, _low_res_w - clip_px)
        clip_ph = min(ph, _low_res_h - clip_py)
        if clip_pw > 0 and clip_ph > 0:
            sx = int((_low_res_min_cx + clip_px * LOW_RES_TILES_PER_PX - cam_x) * zoom + sw / 2)
            sy = int((_low_res_min_cy + clip_py * LOW_RES_TILES_PER_PX - cam_y) * zoom + sh / 2)
            sub = _low_res_surface.subsurface(clip_px, clip_py, clip_pw, clip_ph)
            scaled = pygame.transform.smoothscale(sub, (int(clip_pw * LOW_RES_TILES_PER_PX * zoom), int(clip_ph * LOW_RES_TILES_PER_PX * zoom)))
            surface.blit(scaled, (sx, sy))
        return
    if not _global_spatial:
        return
    chunk_w = 10.0
    margin = 2
    left = int((cam_x - sw / 2 / zoom) // chunk_w) - margin
    right = int((cam_x + sw / 2 / zoom) // chunk_w) + 1 + margin
    top = int((cam_y - sh / 2 / zoom) // chunk_w) - margin
    bottom = int((cam_y + sh / 2 / zoom) // chunk_w) + 1 + margin
    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    gx_left = int(left * chunk_w // GRID_SIZE) - 1
    gx_right = int(right * chunk_w // GRID_SIZE) + 1
    gy_top = int(top * chunk_w // GRID_SIZE) - 1
    gy_bottom = int(bottom * chunk_w // GRID_SIZE) + 1
    for gx in range(gx_left, gx_right):
        for gy in range(gy_top, gy_bottom):
            for (cx, cy, raw) in _global_spatial.get((gx, gy), ()):
                chx = int(cx // 10)
                chy = int(cy // 10)
                if chx < left or chx >= right or chy < top or chy >= bottom:
                    continue
                t = min(raw / 255.0, 1.0)
                color = (255, int(255 * (1 - t * 0.7)), 0, max(30, int(200 * t)))
                sx = int((cx - cam_x) * zoom + sw / 2)
                sy = int((cy - cam_y) * zoom + sh / 2)
                pw = max(1, int(chunk_w * zoom + 1))
                ph = max(1, int(chunk_w * zoom + 1))
                pygame.draw.rect(overlay, color, (sx, sy, pw, ph))
    surface.blit(overlay, (0, 0))


# -------- MAIN --------

def _zombie_color_for_state(state, inside_room=False):
    if inside_room:
        return (140, 140, 140)
    if state == "C":
        return (255, 50, 50)
    if state == "A":
        return (255, 120, 120)
    if state == "M":
        return (255, 200, 60)
    if state == "I":
        return (140, 140, 140)
    if state == "F":
        return (60, 60, 60)
    if state == "W":
        return (160, 100, 60)
    if state == "S":
        return (60, 60, 200)
    if state == "E":
        return (80, 220, 80)
    if state == "T":
        return (220, 60, 220)
    if state == "H":
        return (80, 220, 220)
    if state == "U":
        return (100, 255, 255)
    if state in ("SQ",):
        return (255, 255, 100)
    if state in ("MQ",):
        return (255, 200, 100)
    if state == "V":
        return (100, 220, 100)
    if state == "R":
        return (255, 140, 0)
    return (220, 60, 60)

# -------- GUI DIALOGS & LOADING SCREEN --------

def gui_message_box(screen, title, message, buttons=None):
    try:
        import ctypes
        hwnd = pygame.display.get_wm_info().get('window')
        if buttons is None or len(buttons) <= 1:
            ctypes.windll.user32.MessageBoxW(hwnd, message, title, 0x00000040)
        elif len(buttons) == 2:
            flags = 0x00000020
            if "Yes" in buttons:
                flags = 0x00000004 | 0x00000020
            elif "Cancel" in buttons:
                flags = 0x00000001 | 0x00000040
            else:
                flags = 0x00000000
            ctypes.windll.user32.MessageBoxW(hwnd, message, title, flags)
    except:
        pass

def gui_input_dialog(screen, title, message, default=""):
    try:
        import tkinter as tk
        from tkinter import simpledialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        result = simpledialog.askstring(title, message, initialvalue=default)
        root.destroy()
        return result
    except:
        return None


def _draw_loading(screen, stage, progress):
    sw, sh = screen.get_size()
    cx, cy = sw // 2, sh // 2

    t = pygame.time.get_ticks()

    for x in range(sw):
        p = x / sw
        r = int(8 + p * 12)
        g = int(8 + p * 10)
        b = int(18 + p * 15)
        pygame.draw.line(screen, (r, g, b), (x, 0), (x, sh))

    for i in range(0, sw, 40):
        a = int(6 + 4 * math.sin((t * 0.001) + i * 0.01))
        pygame.draw.line(screen, (a, a, a + 4), (i, 0), (i, sh), 1)
    for i in range(0, sh, 40):
        a = int(6 + 4 * math.sin((t * 0.001) + i * 0.01))
        pygame.draw.line(screen, (a, a, a + 4), (0, i), (sw, i), 1)

    pulse = 0.6 + 0.4 * math.sin(t * 0.002)
    gold = (255, int(180 * pulse), 0)

    try:
        t_font = pygame.font.SysFont("impact", 36)
        s_font = pygame.font.SysFont("bahnschrift", 18)
        v_font = pygame.font.SysFont("bahnschrift", 14)
    except:
        t_font = pygame.font.Font(None, 48)
        s_font = pygame.font.Font(None, 26)
        v_font = pygame.font.Font(None, 20)

    tt = t_font.render("PROJECT ZOMBOID", True, gold)
    tt2 = t_font.render("EXTERNAL RADAR", True, (220, 220, 220))
    screen.blit(tt, (cx - tt.get_width() // 2, cy - 130))
    screen.blit(tt2, (cx - tt2.get_width() // 2, cy - 86))

    s = s_font.render(stage, True, (180, 180, 190))
    screen.blit(s, (cx - s.get_width() // 2, cy - 28))

    bw, bh = min(560, sw - 60), 16
    bx, by = cx - bw // 2, cy + 18
    pygame.draw.rect(screen, (25, 25, 30), (bx, by, bw, bh))
    pygame.draw.rect(screen, (50, 50, 55), (bx, by, bw, bh), 1)
    if progress > 0:
        fw = max(1, int(bw * min(progress, 1.0)))
        gr = int(80 + 100 * min(progress, 1.0))
        pygame.draw.rect(screen, (40, gr, 40), (bx, by, fw, bh))
        if fw > 4:
            pygame.draw.rect(screen, (60, min(255, gr + 40), 60), (bx, by, fw, bh), 1)

    pct = s_font.render(f"{int(min(progress, 1.0) * 100)}%", True, (120, 120, 130))
    screen.blit(pct, (cx - pct.get_width() // 2, by + bh + 10))

    if VERSION:
        v = v_font.render(VERSION, True, (55, 55, 60))
        screen.blit(v, (cx - v.get_width() // 2, sh - 28))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit(1)

    pygame.display.flip()


def _apply_fullscreen(screen):
    """Set fullscreen mode on the current monitor (no border, fills whole screen)."""
    try:
        import ctypes
        from ctypes import wintypes
        class RECT(ctypes.Structure):
            _fields_ = [('left', ctypes.c_long), ('top', ctypes.c_long),
                       ('right', ctypes.c_long), ('bottom', ctypes.c_long)]
        class MONITORINFO(ctypes.Structure):
            _fields_ = [('cbSize', ctypes.c_ulong), ('rcMonitor', RECT),
                       ('rcWork', RECT), ('dwFlags', ctypes.c_ulong)]
        hwnd = pygame.display.get_wm_info()['window']
        style = ctypes.windll.user32.GetWindowLongW(hwnd, -16)
        style &= ~0x00C00000 & ~0x00800000 & ~0x00040000
        ctypes.windll.user32.SetWindowLongW(hwnd, -16, style)
        monitor = ctypes.windll.user32.MonitorFromWindow(hwnd, 2)
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        ctypes.windll.user32.GetMonitorInfoW(monitor, ctypes.byref(mi))
        w = mi.rcMonitor.right - mi.rcMonitor.left
        h = mi.rcMonitor.bottom - mi.rcMonitor.top
        x = mi.rcMonitor.left
        y = mi.rcMonitor.top
        ctypes.windll.user32.SetWindowPos(hwnd, 0, x, y, w, h, 0x0020 | 0x0040)
    except:
        pass

def main():
    global LOTHEADER_PATH, ZOMBIEMAP_TXT_PATH, CURRENT_SAVE
    global _last_read_mtime
    global _zoom_channel, _zoom_direction, _last_zoom_time, _buildings_cache_dirty
    global MUSIC_VOLUME

    load_config()
    _scroll_pool = list(SCROLL_TEXTS)
    if SCROLL_TEXTS_CFG:
        _scroll_pool += [t.strip() for t in SCROLL_TEXTS_CFG.split("|") if t.strip()]

    debug_print("PZ Radar starting...")

    # Initialize pygame early for loading screen & GUI dialogs
    pygame.init()

    if not DEBUG:
        try:
            import ctypes
            ctypes.windll.kernel32.FreeConsole()
        except:
            pass

    L_W, L_H = 820, 460
    screen = pygame.display.set_mode((L_W, L_H))
    pygame.display.set_caption("PZ Radar - Loading...")

    def _ls(stage, progress):
        _draw_loading(screen, stage, progress)

    _ls("Loading configuration...", 0.02)

    if not LOCK_CONFIG:
        _ls("Checking paths...", 0.05)
        if not os.path.isdir(LOTHEADER_PATH):
            LOTHEADER_PATH = gui_input_dialog(screen, "Missing Map Directory",
                "Project Zomboid map directory not found.\nEnter the correct path:",
                LOTHEADER_PATH)
            if LOTHEADER_PATH is None:
                gui_message_box(screen, "Error", "Map directory is required. Exiting.")
                pygame.quit()
                sys.exit(1)
        if not os.path.isfile(ZOMBIEMAP_TXT_PATH):
            path_input = gui_input_dialog(screen, "Missing zombiemap.txt",
                "zombiemap.txt not found.\nEnter the correct path, or Cancel to skip:",
                ZOMBIEMAP_TXT_PATH)
            if path_input is None or not os.path.isfile(path_input):
                ZOMBIEMAP_TXT_PATH = ""
                gui_message_box(screen, "Notice",
                    "Radar works best with zombiemap.txt for zombie heatmap data."
                    " Continuing with preview on available data (buildings, cleared areas).")
            else:
                ZOMBIEMAP_TXT_PATH = path_input
    _ls("Detecting save...", 0.12)
    setup_save()

    _ls("Loading global heatmap data...", 0.22)
    preload_global_data()

    _ls("Building spatial index...", 0.32)
    build_spatial_index()

    _ls("Building low-res data...", 0.38)
    build_low_res_data()

    _ls("Loading buildings...", 0.48)
    buildings_by_type = load_buildings(LOTHEADER_PATH)
    build_building_rects()
    build_room_spatial()
    build_flat_rects(buildings_by_type)
    debug_print(f"Rooms loaded: {len(ROOM_RECTS)}, Buildings: {len(BUILDING_ROOMS)}")
    if ROOM_RECTS:
        sample = next(iter(ROOM_RECTS.items()))
        debug_print(f"Sample room {sample[0]}: {sample[1][:3]}")

    _ls("Initializing audio...", 0.68)
    try:
        pygame.mixer.init(frequency=22050)
        _make_clear_sound()
        _make_click_sound()
        _make_keypress_sound()
        _make_disable_sound()
        _make_zoom_in_sound()
        _make_zoom_out_sound()
        debug_print(f"Sound init: clear={_clear_sound is not None}, click={_click_sound is not None}, disable={_disable_sound is not None}, zoomin={_zoom_in_sound is not None}, zoomout={_zoom_out_sound is not None}")
    except Exception as e:
        debug_print(f"Sound init failed: {e}")

    _ls("Starting music...", 0.78)
    _init_background_music()

    _ls("Building surface data...", 0.88)
    build_low_res_surface()

    _ls("Ready!", 1.0)
    pygame.time.wait(250)

    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
    pygame.display.set_caption("Project Zomboid External Radar " + VERSION)

    clock = pygame.time.Clock()
    font_hud = pygame.font.SysFont("bahnschrift", 14, bold=True)
    font_help = pygame.font.SysFont("arialblack", 14)
    font_cells = pygame.font.SysFont("impact", 48)

    # HUD text cache
    _hud_text = ""
    _hud_surf = None
    _status_text = ""
    _status_surf = None

    zoom = DEFAULT_ZOOM
    zoom_target = DEFAULT_ZOOM
    cam_x, cam_y = 7500.0, 7500.0

    locked_to_player = True
    player_pos = None
    _player_prev_pos = None
    _player_angle = 0.0
    _player_moving = False
    _pulse_enabled = True
    _pulse_list = []
    _last_pulse_time = 0
    zombies = []
    cell_counts = {}

    show_heatmap = False
    show_local_heatmap = False

    panning = False
    pan_start_mouse = (0,0)
    pan_start_cam = (0,0)

    is_fullscreen = False
    _always_on_top = False
    _no_border = False
    last_click_time = 0
    last_refresh = 0
    show_help = False
    _scroll_items = []
    _scroll_queue = []

    running = True

    while running:
        sw, sh = screen.get_size()
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_v:
                    show_heatmap = not show_heatmap
                    sound = _disable_sound if not show_heatmap else _keypress_sound
                    if sound:
                        sound.play()

                elif event.key == pygame.K_h:
                    show_local_heatmap = not show_local_heatmap
                    sound = _disable_sound if not show_local_heatmap else _keypress_sound
                    if sound:
                        sound.play()

                elif event.key == pygame.K_b:
                    global SHOW_BUILDINGS
                    sound = _disable_sound if SHOW_BUILDINGS else _keypress_sound
                    if sound:
                        sound.play()
                    SHOW_BUILDINGS = not SHOW_BUILDINGS
                    debug_print(f"Buildings: {SHOW_BUILDINGS}")

                elif event.key == pygame.K_g:
                    global SHOW_CHUNK_GRID
                    sound = _disable_sound if SHOW_CHUNK_GRID else _keypress_sound
                    if sound:
                        sound.play()
                    SHOW_CHUNK_GRID = not SHOW_CHUNK_GRID

                elif event.key == pygame.K_c:
                    global SHOW_CELL_COUNTS
                    sound = _disable_sound if SHOW_CELL_COUNTS else _keypress_sound
                    if sound:
                        sound.play()
                    SHOW_CELL_COUNTS = not SHOW_CELL_COUNTS
                    debug_print(f"Cell counts: {SHOW_CELL_COUNTS}")

                elif event.key == pygame.K_F1:
                    sound = _disable_sound if show_help else _keypress_sound
                    if sound:
                        sound.play()
                    show_help = not show_help

                elif event.key == pygame.K_F2:
                    sound = _keypress_sound
                    if sound:
                        sound.play()
                    if player_pos:
                        debug_print(f"F2 at ({player_pos[0]:.0f},{player_pos[1]:.0f}) z={player_z} rooms={len(ROOM_RECTS)}")
                        px, py = player_pos
                        cleared = force_clear_building_at(px, py, player_z, zombies)
                        _buildings_cache_dirty = True
                        if cleared:
                            if _clear_sound:
                                _clear_sound.play()

                elif event.key == pygame.K_p:
                    _pulse_enabled = not _pulse_enabled
                    sound = _keypress_sound if _pulse_enabled else _disable_sound
                    if sound:
                        sound.play()

                elif event.key == pygame.K_UP:
                    was_zero = MUSIC_VOLUME == 0.0
                    MUSIC_VOLUME = round(min(1.0, MUSIC_VOLUME + 0.05), 2)
                    try:
                        pygame.mixer.music.set_volume(MUSIC_VOLUME)
                    except:
                        pass
                    if was_zero and MUSIC_VOLUME > 0:
                        try:
                            pygame.mixer.music.play(0)
                        except:
                            _start_music()
                    if _keypress_sound:
                        _keypress_sound.play()

                elif event.key == pygame.K_DOWN:
                    MUSIC_VOLUME = round(max(0.0, MUSIC_VOLUME - 0.05), 2)
                    try:
                        pygame.mixer.music.set_volume(MUSIC_VOLUME)
                    except:
                        pass
                    if MUSIC_VOLUME == 0.0:
                        try:
                            pygame.mixer.music.stop()
                        except:
                            pass
                    if _keypress_sound:
                        _keypress_sound.play()

                elif event.key == pygame.K_LEFT:
                    _prev_track()
                    if _keypress_sound:
                        _keypress_sound.play()

                elif event.key == pygame.K_RIGHT:
                    _next_track_sequential()
                    if _keypress_sound:
                        _keypress_sound.play()

                elif event.key == pygame.K_n:
                    if not is_fullscreen:
                        _no_border = not _no_border
                        sound = _keypress_sound if _no_border else _disable_sound
                        if sound:
                            sound.play()
                        try:
                            import ctypes
                            hwnd = pygame.display.get_wm_info()['window']
                            sw, sh = screen.get_size()
                            if _no_border:
                                screen = pygame.display.set_mode((sw, sh), pygame.NOFRAME)
                                style = ctypes.windll.user32.GetWindowLongW(hwnd, -16)
                                style &= ~0x00C00000 & ~0x00800000 & ~0x00040000
                                ctypes.windll.user32.SetWindowLongW(hwnd, -16, style)
                                ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0004 | 0x0020)
                            else:
                                screen = pygame.display.set_mode((sw, sh), pygame.RESIZABLE)
                        except:
                            pass
                        debug_print(f"No border: {_no_border}")

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if now - last_click_time < 400:
                        is_fullscreen = not is_fullscreen
                        if _click_sound:
                            _click_sound.play()

                        try:
                            import ctypes
                            if is_fullscreen:
                                screen = pygame.display.set_mode((0, 0), pygame.NOFRAME)
                                _apply_fullscreen(screen)
                            else:
                                flags = pygame.NOFRAME if _no_border else pygame.RESIZABLE
                                screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), flags)
                                hwnd = pygame.display.get_wm_info()['window']
                                monitor = ctypes.windll.user32.MonitorFromWindow(hwnd, 2)
                                from ctypes import wintypes
                                class RECT(ctypes.Structure):
                                    _fields_ = [('left', ctypes.c_long), ('top', ctypes.c_long),
                                               ('right', ctypes.c_long), ('bottom', ctypes.c_long)]
                                class MONITORINFO(ctypes.Structure):
                                    _fields_ = [('cbSize', ctypes.c_ulong), ('rcMonitor', RECT),
                                               ('rcWork', RECT), ('dwFlags', ctypes.c_ulong)]
                                mi = MONITORINFO()
                                mi.cbSize = ctypes.sizeof(MONITORINFO)
                                ctypes.windll.user32.GetMonitorInfoW(monitor, ctypes.byref(mi))
                                cx = (mi.rcWork.left + mi.rcWork.right) // 2
                                cy = (mi.rcWork.top + mi.rcWork.bottom) // 2
                                x = cx - WINDOW_W // 2
                                y = cy - WINDOW_H // 2
                                ctypes.windll.user32.SetWindowPos(hwnd, 0, x, y, 0, 0, 0x0001 | 0x0004 | 0x0040)
                        except:
                            if is_fullscreen:
                                screen = pygame.display.set_mode((0, 0), pygame.NOFRAME)
                            else:
                                flags = pygame.NOFRAME if _no_border else pygame.RESIZABLE
                                screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), flags)
                    else:
                        if not locked_to_player:
                            locked_to_player = True
                            if _click_sound:
                                _click_sound.play()

                    last_click_time = now

                elif event.button == 3:
                    panning = True
                    if locked_to_player:
                        locked_to_player = False
                        if _disable_sound:
                            _disable_sound.play()
                    pan_start_mouse = event.pos
                    pan_start_cam = (cam_x, cam_y)

                elif event.button == 4:
                    zoom_target = min(zoom_target * 1.15, 512.0)
                    _last_zoom_time = pygame.time.get_ticks()
                    if _zoom_direction != 'in':
                        if _zoom_channel:
                            _zoom_channel.fadeout(50)
                        if _zoom_in_sound:
                            ch = _zoom_in_sound.play(loops=-1)
                            if ch:
                                _zoom_channel = ch
                                _zoom_channel.set_volume(ACTION_SOUND_VOLUME)
                        _zoom_direction = 'in'

                elif event.button == 5:
                    zoom_target = max(zoom_target / 1.15, 0.01)
                    _last_zoom_time = pygame.time.get_ticks()
                    if _zoom_direction != 'out':
                        if _zoom_channel:
                            _zoom_channel.fadeout(50)
                        if _zoom_out_sound:
                            ch = _zoom_out_sound.play(loops=-1)
                            if ch:
                                _zoom_channel = ch
                                _zoom_channel.set_volume(ACTION_SOUND_VOLUME)
                        _zoom_direction = 'out'

                elif event.button == 2:
                    _always_on_top = not _always_on_top
                    sound = _keypress_sound if _always_on_top else _disable_sound
                    if sound:
                        sound.play()
                    _set_topmost(_always_on_top)
                    debug_print(f"Always on top: {_always_on_top}")

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3:
                    panning = False

            elif event.type == pygame.MOUSEMOTION:
                if panning:
                    dx = event.pos[0] - pan_start_mouse[0]
                    dy = event.pos[1] - pan_start_mouse[1]

                    cam_x = pan_start_cam[0] - dx / zoom
                    cam_y = pan_start_cam[1] - dy / zoom

            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            elif event.type == pygame.WINDOWRESTORED:
                if is_fullscreen:
                    _apply_fullscreen(screen)

        if now - last_refresh > DATA_REFRESH_MS:
            last_refresh = now

            try:
                current_mtime = os.path.getmtime(ZOMBIEMAP_TXT_PATH)
            except:
                current_mtime = 0

            if current_mtime > _last_read_mtime:
                _last_read_mtime = current_mtime
                player_pos, player_z, zombies, cell_counts = read_dynamic_data(ZOMBIEMAP_TXT_PATH)

                if player_pos:
                    if _player_prev_pos:
                        dx = player_pos[0] - _player_prev_pos[0]
                        dy = player_pos[1] - _player_prev_pos[1]
                        dist = math.sqrt(dx*dx + dy*dy)
                        _player_moving = dist > 0.1
                        if _player_moving:
                            _player_angle = math.atan2(dy, dx)
                    else:
                        _player_moving = False
                    _player_prev_pos = player_pos
                    px, py = player_pos
                    zombies_for_buildings = list(zombies)
                    invalidate_zombie_touched_buildings(zombies_for_buildings)
                    newly_cleared = check_player_in_buildings(px, py, player_z, zombies_for_buildings, now)
                    tracked_before = set(TRACKED_BUILDINGS)
                    revalidate_tracked_buildings(zombies_for_buildings, newly_cleared)
                    combat_cleared = [bid for bid in newly_cleared if bid in tracked_before]
                    prev_count = len(CLEARED_CHUNKS)
                    update_cleared_chunks(px, py, zombies_for_buildings)
                    if len(CLEARED_CHUNKS) != prev_count:
                        save_cleared_chunks()
                    _buildings_cache_dirty = True
                    if newly_cleared:
                        debug_print(f"Buildings cleared: {newly_cleared}")
                        save_cleaned_buildings()
                        if _clear_sound and combat_cleared:
                            _clear_sound.play()

            purge_stale_checked_rooms(now)

        # Auto-advance to next track when current one ends
        _check_track_ended()

        if locked_to_player and player_pos:
            cam_x, cam_y = player_pos

        zoom += (zoom_target - zoom) * 0.18

        if _zoom_channel and pygame.time.get_ticks() - _last_zoom_time > 350:
            _zoom_channel.fadeout(100)
            _zoom_channel = None
            _zoom_direction = None

        screen.fill(COLOR_BACKGROUND)

        if SHOW_BUILDINGS:
            draw_buildings(screen, cam_x, cam_y, zoom, sw, sh)

        if SHOW_CHUNK_GRID:
            draw_chunk_grid(screen, cam_x, cam_y, zoom, sw, sh)

        heatmap_lod = 1 if zoom <= LOD_ZOOM_THRESHOLD else 0

        if show_heatmap:
            draw_global_chunks(screen, cam_x, cam_y, zoom, sw, sh, heatmap_lod)

        if show_local_heatmap:
            draw_cleared_chunks(screen, cam_x, cam_y, zoom, sw, sh)

        if SHOW_CELL_COUNTS and cell_counts:
            draw_cell_counts(screen, cell_counts, cam_x, cam_y, zoom, sw, sh, font_cells)

        visible_margin = 20
        cam_left = cam_x - sw / 2 / zoom - visible_margin
        cam_right = cam_x + sw / 2 / zoom + visible_margin
        cam_top = cam_y - sh / 2 / zoom - visible_margin
        cam_bottom = cam_y + sh / 2 / zoom + visible_margin

        for (zx, zy, zz, state) in zombies:
                if not (cam_left <= zx <= cam_right and cam_top <= zy <= cam_bottom):
                    continue
                sx, sy = world_to_screen(zx, zy, cam_x, cam_y, zoom, sw, sh)

                color = _zombie_color_for_state(state, inside_room=is_inside_room(zx, zy, zz))

                pygame.draw.circle(screen, color, (sx, sy), 3)

        if player_pos:
            sx, sy = world_to_screen(player_pos[0], player_pos[1], cam_x, cam_y, zoom, sw, sh)

            # Idle pulse rings
            if _pulse_enabled and not _player_moving:
                if now - _last_pulse_time > 2000:
                    _pulse_list.append(now)
                    _last_pulse_time = now
                if _pulse_list:
                    ps = pygame.Surface((sw, sh), pygame.SRCALPHA)
                    new_list = []
                    for start in _pulse_list:
                        elapsed = now - start
                        if elapsed >= 4000:
                            continue
                        p = elapsed / 4000.0
                        radius = max(1, int(p * PULSE_RING_RADIUS * zoom))
                        a = int(178 * (1.0 - p))
                        pygame.draw.circle(ps, (0, 255, 255, a), (sx, sy), radius)
                        new_list.append(start)
                    _pulse_list = new_list
                    screen.blit(ps, (0, 0))
            else:
                _pulse_list.clear()

            if _player_moving and SHOW_PLAYER_ARROW:
                cos_a = math.cos(_player_angle)
                sin_a = math.sin(_player_angle)
                pts = [(10, 0), (-5, -7), (1, 0), (-5, 7)]
                rot = [(sx + x * cos_a - y * sin_a, sy + x * sin_a + y * cos_a) for x, y in pts]
                pygame.draw.polygon(screen, (255, 255, 255), rot)
                pygame.draw.polygon(screen, (255, 255, 255), rot, 2)
            else:
                pygame.draw.circle(screen, (255, 255, 255), (sx, sy), 4)
                pygame.draw.circle(screen, (0, 100, 100), (sx, sy), 4, 1)

        current_lod = LOD_CONFIG[heatmap_lod]
        lod_display = current_lod["name"]
        hm_indicator = f"H: {'ON' if show_heatmap else 'OFF'}"
        lm_indicator = f"L: {'ON' if show_local_heatmap else 'OFF'}"

        hud = (
            f"{hm_indicator} {lm_indicator} | "
            f"LOD: {lod_display} | "
            f"Zoom: {zoom:.2f}x | "
            f"Z: {len(zombies)} | "
            f"Cells: {len(cell_counts)}"
        )
        if hud != _hud_text:
            _hud_text = hud
            _hud_surf = font_hud.render(hud, True, (255,255,255))
        screen.blit(_hud_surf, ((sw - _hud_surf.get_width()) // 2, 6))

        # Music info (below HUD, hidden when volume < 10%)
        try:
            _music_busy = pygame.mixer.music.get_busy()
        except:
            _music_busy = False
        if MUSIC_VOLUME >= 0.05 and _MUSIC_AVAILABLE and _music_busy:
            title_color = _get_title_color()
            now_text = "Now Playing: "
            suffix_text = " | CHIPTUNE as digital freedom of speech"
            if _SONG_LIST:
                track_text = f"  [{_current_track_index + 1}/{len(_SONG_LIST)}]"
            else:
                track_text = "  [0/0]"
            now_surf = font_hud.render(now_text, True, (255, 255, 255))
            title_surf = font_hud.render(_SONG_NAME, True, title_color)
            suffix_surf = font_hud.render(suffix_text, True, (255, 255, 255))
            track_surf = font_hud.render(track_text, True, (150, 220, 150))
            total_w = now_surf.get_width() + title_surf.get_width() + suffix_surf.get_width() + track_surf.get_width()
            music_surf = pygame.Surface((total_w, now_surf.get_height()), pygame.SRCALPHA)
            music_surf.fill((0, 0, 0, 0))
            x = 0
            music_surf.blit(now_surf, (x, 0)); x += now_surf.get_width()
            music_surf.blit(title_surf, (x, 0)); x += title_surf.get_width()
            music_surf.blit(suffix_surf, (x, 0)); x += suffix_surf.get_width()
            music_surf.blit(track_surf, (x, 0))
            screen.blit(music_surf, ((sw - total_w) // 2, 24))

        # Show building progress in HUD (bottom-left)
        save_label = CURRENT_SAVE or "unknown"
        bldg_total = len(BUILDING_ROOMS)
        bldg_cleared = len(CLEANED_BUILDINGS)
        bldg_pct = int(bldg_cleared / max(bldg_total, 1) * 100)
        bldg_tracked = len(TRACKED_BUILDINGS)
        status_line = f"Save: {save_label} | Buildings Clear: {bldg_cleared}/{bldg_total} ({bldg_pct}%) | Tracked: {bldg_tracked}"
        if status_line != _status_text:
            _status_text = status_line
            _status_surf = font_hud.render(status_line, True, (150, 220, 150))
        screen.blit(_status_surf, (6, sh - 20))

        # Help hint (bottom-right, hidden if overlapping status text)
        help_hint = font_hud.render("F1=Help", True, (255,255,255))
        if 6 + _status_surf.get_width() < sw - 60:
            screen.blit(help_hint, (sw - 60, sh - 20))

        # Toggleable help panel
        if show_help:
            panel_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            panel_surf.fill((0, 0, 0, 200))
            screen.blit(panel_surf, (0, 0))

            t = pygame.time.get_ticks()
            pulse = 0.6 + 0.4 * math.sin(t * 0.003)
            gold = (255, int(180 * pulse), 0)
            title_scale = 1.0 + 0.08 * math.sin(t * 0.003)

            title_font = pygame.font.SysFont("impact", 44)
            section_font = pygame.font.SysFont("impact", 26)
            key_font = pygame.font.SysFont("impact", 20)
            desc_font = font_help

            controls = [
                ("F1",     "Toggle help",                              lambda: 3),
                ("F2",     "Force-clear building at your feet",         lambda: 3),
                ("V",     "Toggle static heatmap",                      lambda: 1 if show_heatmap else 0),
                ("H",     "Toggle local heatmap",                      lambda: 1 if show_local_heatmap else 0),
                ("B",     "Toggle building render",                    lambda: 1 if SHOW_BUILDINGS else 0),
                ("G",     "Toggle chunk grid",                         lambda: 1 if SHOW_CHUNK_GRID else 0),
                ("C",     "Toggle cell counts",                        lambda: 1 if SHOW_CELL_COUNTS else 0),
                ("P",     "Toggle idle pulse",                         lambda: 1 if _pulse_enabled else 0),
                ("ESC",   "Exit",                                      lambda: 3),
                ("LMB",   "Lock / fullscreen",                         lambda: 3),
                ("RMB",   "Pan",                                       lambda: 3),
                ("Wheel", "Zoom",                                      lambda: 3),
                ("MMB",   "Toggle always-on-top",                     lambda: 1 if _always_on_top else 0),
                ("N",     "Toggle window border",                     lambda: 1 if _no_border else 0),
                ("UP",    "Volume +",                                   lambda: 3),
                ("DOWN",  "Volume -",                                   lambda: 3),
                ("LEFT",  "Previous track",                             lambda: 3),
                ("RIGHT", "Next track",                                 lambda: 3),
            ]

            state_rows = [
                ("Red",          "CHASE"),
                ("White-Red",    "ATTACK"),
                ("Orange",       "ROAMING"),
                ("Gray",         "IDLE"),
                ("Dark Gray",    "FAKE-DEAD"),
                ("Brown",        "CRAWLER"),
                ("Dark Blue",    "SITTING"),
                ("Green",        "EATING"),
                ("Magenta",      "THUMP"),
                ("Cyan",         "HIT / STAGGER"),
                ("Lt Cyan",      "CLIMB"),
                ("Yellow",       "SPAWN QUEUE"),
                ("Green",        "VIRTUAL"),
                ("Blue",         "ASLEEP"),
                ("Gray (Indoor)","NOT VISIBLE"),
            ]

            state_colors = [
                (240, 80, 80), (240, 140, 140), (240, 180, 60),
                (160, 160, 160), (110, 110, 110), (170, 120, 70),
                (70, 70, 200), (80, 200, 80), (200, 60, 200),
                (60, 200, 200), (140, 220, 220), (220, 220, 60),
                (100, 220, 100), (100, 150, 220), (140, 140, 140),
            ]

            col1_w = max(desc_font.size(r[0])[0] for r in state_rows) + 20
            col2_w = max(desc_font.size(r[1])[0] for r in state_rows) + 20
            mid_x = col1_w + 2
            table_w = col1_w + col2_w + 3
            row_h = 18
            bot_pad = 4

            max_key_w = max(key_font.size(c[0])[0] for c in controls)
            max_desc_w = max(desc_font.size(c[1])[0] for c in controls)
            controls_w = max_key_w + 20 + max_desc_w

            title_h = 44
            section_h = 26
            ctrl_rows_h = len(controls) * 26
            table_rows_h = len(state_rows) * row_h
            total_h = (20 + title_h + 12 + section_h + 10 + ctrl_rows_h + 10 +
                       section_h + 10 + 1 + table_rows_h + 1)
            y = max(20, (sh - total_h) // 2)

            title_base = title_font.render("PROJECT ZOMBOID EXTERNAL RADAR", True, gold)
            tw, th = title_base.get_size()
            sw2, sh2 = int(tw * title_scale), int(th * title_scale)
            title = pygame.transform.scale(title_base, (sw2, sh2))
            screen.blit(title, (sw // 2 - sw2 // 2, y))
            y += title_h + 12

            s = section_font.render("CONTROLS", True, (200, 200, 200))
            screen.blit(s, (sw // 2 - s.get_width() // 2, y))
            y += section_h + 10

            controls_cx = sw // 2 - controls_w // 2
            for key, desc, state_fn in controls:
                state = state_fn()
                if state == 3 or state == 0:
                    color = (255, 255, 255)
                elif state == 1:
                    color = (255, 255, 0)
                elif state == 2:
                    color = (180, 60, 255)

                ks = key_font.render(key, True, color)
                ds = desc_font.render(desc, True, (200, 200, 200))
                screen.blit(ks, (controls_cx, y + 2))
                screen.blit(ds, (controls_cx + max_key_w + 20, y + 5))
                y += 26

            y += 10
            bar_w = 200
            bar_h = 8
            bar_x = sw // 2 - bar_w // 2
            fill_w = int(bar_w * MUSIC_VOLUME)
            pygame.draw.rect(screen, (60, 60, 60), (bar_x, y, bar_w, bar_h))
            if fill_w > 0:
                pygame.draw.rect(screen, (80, 200, 80), (bar_x, y, fill_w, bar_h))
            vol_label = desc_font.render("VOLUME", True, (180, 180, 180))
            screen.blit(vol_label, (bar_x - vol_label.get_width() - 8, y - 2))
            pct_label = desc_font.render("%d%%" % (MUSIC_VOLUME * 100), True, (200, 200, 200))
            screen.blit(pct_label, (bar_x + bar_w + 8, y - 2))
            y += 18
            s = section_font.render("ZOMBIE STATES", True, (200, 200, 200))
            screen.blit(s, (sw // 2 - s.get_width() // 2, y))
            y += section_h + 10

            table_lx = sw // 2 - table_w // 2
            bc = (100, 100, 100)
            pygame.draw.line(screen, bc, (table_lx, y), (table_lx + table_w, y))
            for i, (col1, col2) in enumerate(state_rows):
                ry = y + 1 + i * row_h
                washed = tuple(min(c + 70, 255) for c in state_colors[i])
                c1 = desc_font.render(col1, True, washed)
                c2 = desc_font.render(col2, True, (200, 200, 200))
                screen.blit(c1, (table_lx + (col1_w - c1.get_width()) // 2, ry))
                screen.blit(c2, (table_lx + mid_x + (col2_w - c2.get_width()) // 2, ry))
            bot_y = y + 1 + len(state_rows) * row_h + bot_pad
            pygame.draw.line(screen, bc, (table_lx, bot_y), (table_lx + table_w, bot_y))
            pygame.draw.line(screen, bc, (table_lx, y), (table_lx, bot_y))
            pygame.draw.line(screen, bc, (table_lx + mid_x, y), (table_lx + mid_x, bot_y))
            pygame.draw.line(screen, bc, (table_lx + table_w, y), (table_lx + table_w, bot_y))

            # Scrolling rainbow text at the bottom of help panel
            if _scroll_pool:
                scroll_font = font_hud

                for item in _scroll_items:
                    item[1] -= item[2] * (1.0 / 60.0)

                _scroll_items = [it for it in _scroll_items if it[1] + scroll_font.size(it[0])[0] > -20]

                if not _scroll_items:
                    if not _scroll_queue:
                        _scroll_queue = list(_scroll_pool)
                        random.shuffle(_scroll_queue)
                    text = _scroll_queue.pop(0)
                    _scroll_items.append([text, sw, random.randint(180, 800)])

                hue = (now * 0.0005) % 1.0
                r = int(127 + 127 * math.sin(hue * math.tau))
                g = int(127 + 127 * math.sin((hue + 0.333) * math.tau))
                b = int(127 + 127 * math.sin((hue + 0.667) * math.tau))
                for text, x, _ in _scroll_items:
                    surf = scroll_font.render(text, True, (r, g, b))
                    screen.blit(surf, (int(x), bot_y + 10))

        pygame.display.flip()
        clock.tick(60)

    save_cleaned_buildings()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()