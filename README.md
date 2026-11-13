# 🌟 Poko: The Paper Universe
### A 3D Adventure Game

A paper-themed 3D adventure game developed using **Python and OpenGL (PyOpenGL)** as a Computer Graphics Lab project.

Guide **Poko**, a little paper character, through floating islands to reach the golden star. Fold paper walls into bridges, unfold stairs, flatten yourself to pass beneath low arches, and transform into a paper boat to cross rivers.

The environment features pastel-colored islands, flying paper cranes, animated water, collectible paper scraps, and moving scissors.

## 🎥 Project Demo

*Demo video link will be added here.*

## ✨ Features

- **3D Paper World:** Floating islands, paper trees, rivers, arches, and elevated platforms.
- **Character Movement:** Move Poko across a tile-based environment using arrow keys.
- **Folding Bridges:** Fold nearby paper walls into temporary bridges that close after three seconds.
- **Unfolding Stairs:** Open nearby stairs to reach elevated areas.
- **Flatten Transformation:** Flatten Poko to travel beneath low arches.
- **Paper Boat Transformation:** Transform into a boat before entering water and return to walking upon reaching land.
- **Moving Obstacles:** Avoid scissors that patrol predefined paths.
- **Crumbling Tiles:** Cracked paper tiles tear after being stepped on.
- **Collectible Scraps:** Collect optional paper scraps along the way.
- **Four Levels:** Explore different islands with increasingly varied obstacles.
- **Lives System:** Start with three lives; collisions and falls cost a life.
- **Camera Controls:** Rotate the camera with mouse dragging and adjust zoom.
- **Sound Effects:** Generated sound effects for movement, folding, scissors, falling, collecting scraps, and reaching the goal.
- **Progress Display:** View lives, collected scraps, step count, and gameplay hints.

## 🛠️ Technologies Used

- **Python 3** — Game logic and level management.
- **PyOpenGL** — Rendering and geometric transformations.
- **GLUT / FreeGLUT** — Window creation, input handling, and timer callbacks.
- **GLU** — Perspective projection and camera positioning.
- **Pygame Mixer** — Sound playback.
- **math** — Trigonometry, animation, and distance calculations.
- **wave and struct** — Generating WAV sound files.

## 📦 Requirements

- Python 3.x
- PyOpenGL
- GLUT / FreeGLUT
- Pygame for sound playback
- PyOpenGL_accelerate — optional

The `math`, `wave`, and `struct` modules are included with Python.

## 🚀 Installation and Execution

### 1. Download the Project

Open this repository, select **Code → Download ZIP**, and extract the downloaded folder.

Alternatively, copy the repository’s HTTPS URL and clone it:

```bash
git clone YOUR_REPOSITORY_URL
```

Replace `YOUR_REPOSITORY_URL` with the actual URL.

### 2. Open the Project Folder

Open the extracted or cloned folder in your code editor, then open a terminal inside that folder.

### 3. Install the Python Packages

```bash
python -m pip install PyOpenGL pygame
```

Optional acceleration package:

```bash
python -m pip install PyOpenGL_accelerate
```

**Windows:** If your Python launcher uses `py`, replace `python` with `py` in these commands.

**Note:** GLUT / FreeGLUT must also be available on your system. Installing PyOpenGL alone may not provide the required native GLUT library.

### 4. Run the Game

```bash
python poko.py
```

The game generates its sound files in the current working directory at startup. Run it from a folder where you have write permission.

If Pygame is unavailable or audio initialization fails, the game is designed to continue without sound.

## 🎮 Controls

| Key / Input | Action |
|---|---|
| `↑` | Move in the negative Z direction |
| `↓` | Move in the positive Z direction |
| `←` | Move in the negative X direction |
| `→` | Move in the positive X direction |
| `F` | Fold a nearby paper wall into a temporary bridge |
| `U` | Unfold nearby stairs |
| `SPACE` | Toggle between flattened and standing form when allowed |
| `T` | Toggle paper boat form while on land |
| Left Mouse Drag | Rotate the camera |
| `+` / `=` | Zoom in |
| `-` | Zoom out |
| `R` | Restart the current level; restart the whole game from the final or game-over screen |
| `N` | Continue after completing a level |

**Note:** Movement follows the world axes, so its on-screen direction changes when the camera rotates.

## 🗺️ Levels

| Level | Name | Main Challenge |
|---|---|---|
| 1 | **Broken Bridge** | Fold a temporary bridge and cross while avoiding scissors |
| 2 | **Low Cave** | Flatten beneath arches and navigate cracked paper tiles |
| 3 | **Paper River** | Cross water as a boat, avoid scissors, and unfold stairs |
| 4 | **Last Island** | Combine the movement and transformation mechanics to reach the final star |

## 🕹️ How to Play

1. Use the arrow keys to explore the island.
2. Follow the hints displayed on the screen.
3. Press `F` near a folding wall and cross before the bridge closes.
4. Press `SPACE` before moving beneath low arches.
5. Press `T` on land before entering a river.
6. Press `U` near stairs to open the route to higher ground.
7. Avoid moving scissors and collapsing tiles.
8. Collect paper scraps and reach the golden star.
9. Press `N` after completing a level to continue.

The step counter records your moves, while the **par** value provides a target for comparison.

## 🎨 Computer Graphics Concepts

### 1. Geometric Primitives

- `GL_QUADS` — Background, water surfaces, interface panels, and paper boat surfaces.
- `GL_TRIANGLES` — Paper crane body and wings, boat sail, and hearts.
- `GL_TRIANGLE_FAN` — Golden star faces and curved portions of hearts.
- `GL_LINE_STRIP` — Cracked paper markings and animated water waves.
- `GL_POINTS` — Golden ring beneath the goal star.

### 2. Circle Drawing Algorithm

- **Bresenham Circle Algorithm:** Generates the goal ring using the decision parameter `d = 3 - 2r` and eight-way symmetry.
- **Point Rendering:** Draws the generated circle points using `GL_POINTS`.
- **Trigonometric Geometry:** Uses sine and cosine to calculate star vertices and curved heart shapes.

### 3. Geometric Transformations

- **Translation:** `glTranslatef()` positions objects and moves Poko.
- **Rotation:** `glRotatef()` animates stars, scissors, character limbs, and character orientation.
- **Pivot Rotation:** Folds bridges by translating to the hinge and rotating around it.
- **Scaling:** `glScalef()` flattens Poko and animates the paper boat transformation.
- **Reflection:** Negative X scaling mirrors paper-crane wings.
- **Matrix Stack:** `glPushMatrix()` and `glPopMatrix()` isolate transformations for individual objects.

### 4. Projection and Camera

- `gluPerspective()` creates the 3D perspective view.
- `gluLookAt()` positions and orients the camera.
- Camera yaw, pitch, and distance support rotation and zoom.
- `gluOrtho2D()` renders the background and on-screen interface.

### 5. Animation

- Lissajous-style paths animate flying paper cranes.
- Sine and cosine animate water waves, floating collectibles, and character motion.
- `glutTimerFunc()` schedules animation updates.
- `glutPostRedisplay()` requests screen redraws.
- `GLUT_DOUBLE` and `glutSwapBuffers()` provide double-buffered rendering.

### 6. Lighting and Depth

- `GL_DEPTH_TEST` handles visibility between overlapping 3D objects.
- OpenGL lighting and color materials illuminate the scene.
- `glShadeModel(GL_FLAT)` creates a faceted paper appearance.
- `glPolygonOffset()` helps prevent depth conflicts between surfaces and outlines.

### 7. Transparency and Text

- Alpha blending creates translucent water and interface panels.
- `glRasterPos2f()` and `glutBitmapCharacter()` display instructions, lives, steps, and progress.

### 8. User Interaction

- Arrow-key input controls character movement.
- Keyboard commands trigger folding, unfolding, transformations, restart, and level progression.
- Mouse dragging rotates the camera.
- Keyboard zoom controls adjust the viewing distance.

### 9. Game Logic and Collision Detection

- Tile-based checks determine valid movement.
- Height checks control access to elevated platforms.
- Distance-based collision detection identifies contact with scissors.
- Timers control temporary bridges and crumbling tiles.
- Game states manage gameplay, falling, level completion, and game over.
## 📁 Project Files

| File | Purpose |
|---|---|
| `poko.py` | Main game code |
| `README.md` | Project documentation |
| `step.wav` | Generated movement sound |
| `fold.wav` | Generated folding sound |
| `snip.wav` | Generated scissors sound |
| `fall.wav` | Generated falling sound |
| `scrap.wav` | Generated collectible sound |
| `star.wav` | Generated goal sound |

The WAV files are created automatically when the program starts and do not need to be downloaded separately.

## 🖼️ Visual Design

The paper universe includes:

- Pastel floating islands with angular rock formations.
- A small geometric paper character.
- Folding yellow bridges and unfolding stairs.
- Paper trees and low arches.
- Animated rivers and a paper boat.
- Moving scissors and cracked floor tiles.
- Flying paper cranes.
- Rotating golden stars and collectible scraps.

The visuals are constructed programmatically using OpenGL primitives, without external image textures or imported 3D models.

## 🎓 Project Purpose

This project was developed for a **Computer Graphics Lab** to demonstrate how geometric modeling, transformations, projection, lighting, animation, and user interaction can be combined into a playable 3D adventure game.

The folding and transformation mechanics connect graphics concepts directly to gameplay: rotation creates a bridge, scaling flattens the character, and translation moves Poko through the environment.

## 👩‍💻 Author

**Nusrat Hossain**  
Department of Computer Science and Engineering  
Bangladesh Army University of Science and Technology (BAUST)
