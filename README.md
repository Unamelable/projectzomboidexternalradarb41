PZ Radar — Feature List
=========================
**For pictures, scroll down.**
Created with workshop mod in mind: https://steamcommunity.com/sharedfiles/filedetails/?id=3724547671


External radar overlay for Project Zomboid. Reads game data from Zomboid save files and renders a live 2D map of the player's surroundings: zombie positions, building layouts, cleared areas, and a global heatmap.

**CORE DISPLAY**
- Live 2D radar view (1000×1000 default, resizable + fullscreen)
- Real-time player position tracking with movement direction arrow
- Zombie positions rendered as colored dots by AI state
- Smooth zoom (scroll wheel) and pan (right-click drag)
- Lock-to-player mode (left-click to re-lock after panning)
- Idle pulse rings around player when standing still

**BUILDING RENDERER**
- Parses *.lotheader binary files (PZ map format)
- Renders all building/room rectangles on the map
- Color-coded by status: cleared (green), visited/partial (red), untouched (dark blue), building-touched (dim outline)
- Multi-floor support (darker tints for higher floors)
- Level-of-detail cache: low-zoom thumbnail for overview
- Automatically loads all cell files from the map directory

**BUILDING CLEARING SYSTEM**
- Tracks which rooms the player has entered (checked rooms)
- When entering a building, checks if any zombies remain inside
- Building marked CLEARED when all zombies in it are gone
- Tracks "in-progress" buildings that still have zombies
- Stale room checks expire after 5 minutes
- F2 key: force re-check nearest building at player's position
- Persists cleared buildings to zombiemap_cleaningbuildings_{savename}.txt
- Progress displayed in HUD: "Buildings Clear: X/Y (Z%)"

**CHUNK CLEARING SYSTEM**
- Clears 10×10 chunks around player where no zombies are present
- Zombie presence in a chunk revokes its cleared status
- Visual mode: green overlay showing all cleared chunks
- Persists cleared chunks to zombiemap_cleaningall_{savename}.txt

**HEATMAP (GLOBAL)**
- Loads global zombie density data from zombiemap_global.txt
- Two render modes:
    Full: per-chunk colored dots (red → yellow intensity)
    LowRes: pre-baked surface for far-zoom performance
- Switches to LowRes automatically below zoom threshold
- Three display modes toggled with V key:
    0 = OFF, 1 = HEATMAP, 2 = CLEARED CHUNKS

**CELL COUNTS**
- Toggle with C key — shows zombie count per 300×300 cell
- Numbers rendered in large impact font with heat coloring

**CHUNK GRID**
- Toggle with G key — draws 300×300 cell grid lines
- Grid fades out at low zoom levels

**SAVE DETECTION**
- Auto-detects most recently played save from Zomboid/Saves/
- Writes detected save name to detected_save.txt
- Supports per-save cleared-buildings and cleared-chunks files

**SOUND SYSTEM**
- Procedurally generated sound effects (no external audio files):
    Clear chime (multi-tone with echo)
    Click (short noise burst)
    Keypress confirmation
    Disable/error tone
    Zoom-in (high tick) and zoom-out (low tick) loop sounds
- All synthesized at runtime via math + pygame.mixer

**BACKGROUND MUSIC (CHIPTUNE)**
- Plays tracker module files (.XM/.IT) encoded as base64 (.B64)
- 8 bundled tracks from various artists
- Random playlist with shuffle
- Next/previous track (LEFT/RIGHT arrows)
- Volume control (UP/DOWN arrows, 0–100%)
- Auto-advance when track ends
- Smooth random color cycling for track title display
- Parse module headers for accurate duration estimation

**CONFIGURATION**
- Auto-generated pz_radar.cfg on first launch
- Configurable paths for map data, save data, and game files
- Adjustable window size, zoom, refresh rate, colors, etc.
- Boolean, int, float, and string settings with type coercion
- LOCK_CONFIG mode: skip path prompts, hide console

**WINDOW MANAGEMENT**
- Resizable window (drag edges to resize)
- Fullscreen mode (double-click to toggle)
- Borderless toggle (N key)
- Always-on-top toggle (middle mouse button)
- Set initial size and position via SetWindowPos

**HELP OVERLAY (F1)**
- Full keyboard/mouse controls reference
- Zombie state color legend table
- Volume slider with percentage display
- Animated title with pulsing gold color
- Scrolling rainbow text at bottom (player tips / easter eggs)

**LOADING SCREEN**
- Framed window (820×460) with animated gradient background
- Faint animated grid overlay (radar aesthetic)
- Gold pulsing title, white subtitle
- Progress bar with percentage for each loading stage
- Processes QUIT events during load

**NATIVE DIALOGS**
- Native Windows MessageBox for errors and notices
- Native Tkinter input dialog for missing file paths
- Handles Ctrl+C/V/X/A, Shift+Insert, right-click menu
- Map directory prompt on first launch (if not LOCK_CONFIG)
- zombiemap.txt is optional — notice shown, continues without it

**DATA PIPELINE**
- Reads zombiemap.txt at DATA_REFRESH_MS interval (default 170 ms)
- File-change detection via mtime — only re-reads when modified
- Parses player position (P:), zombies (Z:), and cell counts (C:)
- Gracefully handles missing/corrupt data files (returns empty set)

**COMPILED DISTRIBUTION**
- PyInstaller --onefile --noconsole
- All 8 B64 music files bundled as data resources
- No Python runtime required on target machine
- Sub-20 MB standalone executable for Windows

ZOMBIE STATE COLORS
- Red (CHASE), White-Red (ATTACK), Orange (ROAMING)
- Gray (IDLE), Dark Gray (FAKE-DEAD), Brown (CRAWLER)
- Dark Blue (SITTING), Green (EATING), Magenta (THUMP)
- Cyan (HIT/STAGGER), Lt Cyan (CLIMBING)
- Yellow (SPAWN QUEUE), Green (VIRTUAL), Blue (ASLEEP)
- Gray/Indoor (NOT VISIBLE — zombie behind wall)

<img width="749" height="236" alt="image" src="https://github.com/user-attachments/assets/4e19b459-0da5-4b20-8f26-6b30d23734a0" />

<img width="1000" height="1000" alt="image" src="https://github.com/user-attachments/assets/1da3db35-642c-45d8-b0ad-266a70de42b4" />

<img width="1000" height="1000" alt="image" src="https://github.com/user-attachments/assets/1b623a8f-af0d-413f-96c5-fad7fb2c9190" />

<img width="1000" height="1000" alt="image" src="https://github.com/user-attachments/assets/ffd66cdc-839f-4f3e-820e-78ff440d85e0" />

<img width="1000" height="1000" alt="image" src="https://github.com/user-attachments/assets/4ec27bbb-7c0d-4f8c-9da7-2c63a09e759b" />
