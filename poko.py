from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math

# POKO: THE PAPER UNIVERSE (3D puzzle game) - get Poko to the golden star.
# Dangers: scissors, cracked paper, bridges that fold back after 3 s. 3 lives.
# Arrows: move  F: fold bridge  U: unfold stairs  SPACE: flatten  T: paper boat
# Mouse drag: camera   +/-: zoom   R: restart   N: next level

W, H, DT = 1100, 750, 0.016

# . ground  x cracked paper  c paper scrap  T tree  L low arch  W water
# # high ground  P start  G/g star  S folded stairs (opens to +x)  (space) sky
LEVELS = [
    {"name": "Broken Bridge", "map": ["c..  ......", ".P.  ....G.", "...  ..c..."], "par": 8,
     "flaps": [(2, 1, 1, 0, 2)], "scissors": [([(6, 0), (6, 1), (6, 2)], 1.2)],
     "tip": "F folds the bridge, but it springs back in 3 s. Mind the scissors!"},
    {"name": "Low Cave", "map": ["TTTTTTTTTTTT", "P.LLLL.xx.cT", "TT.TTT.TTx.T", "TT......xxGT", "TTTTTTTTTTTT"],
     "par": 12, "flaps": [], "scissors": [([(6, 1), (6, 2), (6, 3)], 1.6)],
     "tip": "SPACE to flatten under arches. Cracked paper tears! Scissors guard the cave exit!"},
    {"name": "Paper River", "map": ["TTc.WWW..T###", "P..xWWW..S #g", "TT..WWW..T###"], "par": 12,
     "flaps": [], "scissors": [([(8, 0), (8, 1), (8, 2)], 1.4)],
     "tip": "T makes a paper boat. U opens the stairs. Scissors guard the shore!"},
    {"name": "Last Island", "map": ["TTTTTT  TTc.WW..T###", "P.LLx.  .x..WW..S g#", "TTTTTT  TT..WWc.T###"],
     "par": 18, "flaps": [(5, 1, 1, 0, 2)],
     "scissors": [([(10, 0), (10, 1), (10, 2)], 2.0), ([(15, 2), (15, 1), (15, 0)], 2.0)],
     "tip": "Everything at once. Good luck, Poko!"},
]
PINK, LAVENDER, MINT = (1.0, 0.72, 0.80), (0.75, 0.68, 0.95), (0.70, 0.92, 0.80)
CREAM, YELLOW, RED = (1.0, 0.97, 0.90), (1.0, 0.88, 0.45), (0.95, 0.30, 0.30)
GOLD, PAPER, GREEN, INK = (1.0, 0.80, 0.20), (0.98, 0.98, 0.96), (0.45, 0.80, 0.55), (0.35, 0.25, 0.4)

level, lives, scrapsTotal = 0, 3, 0
MAP, flaps, stairs, scissors, scraps = [], [], [], [], []
crumble, rocks, got = {}, {}, set()    
px = pz = fromX = fromZ = 0
moveT, facing = 1.0, 90
flat = flatTarget = boat = boatTarget = steps = deadT = t = 0
state = 'play'                          
message, msgTime = "", 0
camYaw, camPitch, camDist = 25, 50, 12
drag, RING = None, []

# ---------------- helpers ----------------
def box(x, y, z, w, h, d, col, outline=True):
    glPushMatrix(); glTranslatef(x, y, z); glScalef(w, h, d)
    glColor3f(*col); glutSolidCube(1)
    if outline:                         
        glDisable(GL_LIGHTING)
        glColor3f(col[0] * 0.6, col[1] * 0.6, col[2] * 0.6); glutWireCube(1.002)
        glEnable(GL_LIGHTING)
    glPopMatrix()

def cone(x, y, z, r, h, col, slices=5, down=False):    
    glPushMatrix(); glTranslatef(x, y, z); glRotatef(90 if down else -90, 1, 0, 0)
    glColor3f(*col); glutSolidCone(r, h, slices, 1)
    glPopMatrix()

def text(x, y, s, font=GLUT_BITMAP_HELVETICA_18):
    glRasterPos2f(x, y)
    for c in s:
        glutBitmapCharacter(font, ord(c))

def quad2(x1, y1, x2, y2):
    glBegin(GL_QUADS); glVertex2f(x1, y1); glVertex2f(x2, y1); glVertex2f(x2, y2); glVertex2f(x1, y2); glEnd()

def bresenhamRing(r):                   
    pts, x, y, d = [], 0, r, 3 - 2 * r
    while x <= y:
        pts += [(x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)]
        if d < 0:
            d = d + 4 * x + 6
        else:
            d, y = d + 4 * (x - y) + 10, y - 1
        x = x + 1
    return pts

def say(s, frames=120):
    global message, msgTime
    message, msgTime = s, frames

import wave, struct
try:
    import pygame
    pygame.mixer.init()
except Exception:
    pygame = None                       
SOUNDS = {}

def makeSound(name, notes):            
    with wave.open(name + ".wav", "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050)
        for f, sec in notes:
            n = int(22050 * sec)
            for i in range(n):          # sine wave that fades out
                w.writeframes(struct.pack('<h', int(9000 * (1 - i / n) * math.sin(2 * math.pi * f * i / 22050))))
    if pygame:
        SOUNDS[name] = pygame.mixer.Sound(name + ".wav")

def play(name):
    if name in SOUNDS:
        SOUNDS[name].play()

# ---------------- level data ----------------
def tile(gx, gz):
    return MAP[gz][gx] if 0 <= gz < len(MAP) and 0 <= gx < len(MAP[gz]) else ' '

def world(gx, gz):                     
    return gx - (len(MAP[0]) - 1) / 2, gz - (len(MAP) - 1) / 2

def standHeight(gx, gz):                
    if (gx, gz) in crumble and crumble[(gx, gz)][1] > 0.3:
        return None
    for s in stairs:
        if (gx, gz) == (s['x'], s['z']):
            return 0.33
        if s['open'] >= 1 and (gx, gz) == (s['x'] + 1, s['z']):
            return 0.66
    for f in flaps:
        if f['p'] >= 1 and any((gx, gz) == (f['x'] + f['dx'] * k, f['z'] + f['dz'] * k) for k in range(1, f['len'] + 1)):
            return 0.0
    c = tile(gx, gz)
    return 0.0 if c in '.PGLcxW' else (1.0 if c in '#g' else None)

def startLevel(n):
    global level, MAP, flaps, stairs, scissors, scraps, got, px, pz, fromX, fromZ
    global moveT, facing, flat, flatTarget, boat, boatTarget, steps, state, camDist
    level, L = n, LEVELS[n]
    width = max(len(r) for r in L["map"])
    MAP = [r.ljust(width) for r in L["map"]]
    flaps = [{'x': x, 'z': z, 'dx': dx, 'dz': dz, 'len': ln, 'p': 0.0, 'target': 0, 'timer': 0}
             for (x, z, dx, dz, ln) in L["flaps"]]
    scissors = [{'path': p, 'speed': sp, 'u': 0.0, 'dir': 1, 'x': 0, 'z': 0, 'h': 0, 'rest': 0}
                for (p, sp) in L["scissors"]]
    stairs, scraps, got = [], [], set()
    crumble.clear(); rocks.clear()
    for gz, row in enumerate(MAP):
        for gx, c in enumerate(row):
            if c == 'P':
                px, pz = gx, gz
            elif c == 'S':
                stairs.append({'x': gx, 'z': gz, 'open': 0.0, 'target': 0})
            elif c == 'x':
                crumble[(gx, gz)] = [0.0, 0.0]
            elif c == 'c':
                scraps.append((gx, gz))
            if c != ' ':               
                rocks[(gx, gz)] = (0.8 + ((gx * 7 + gz * 13) % 10) * 0.14, (gx + gz) % 2 == 0)
    fromX, fromZ, moveT, facing = px, pz, 1.0, 90
    flat = flatTarget = boat = boatTarget = steps = 0
    state, camDist = 'play', 6 + width * 0.75
    say(L["tip"], 300)

def newGame():
    global lives, scrapsTotal
    lives, scrapsTotal = 3, 0
    startLevel(0)

# ---------------- drawing: world ----------------
def background():                      
    glDisable(GL_DEPTH_TEST); glDisable(GL_LIGHTING)
    glMatrixMode(GL_PROJECTION); glLoadIdentity(); gluOrtho2D(0, 1, 0, 1)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    glShadeModel(GL_SMOOTH)
    glBegin(GL_QUADS)
    glColor3f(0.98, 0.80, 0.88); glVertex2f(0, 1); glVertex2f(1, 1)
    glColor3f(0.70, 0.86, 0.99); glVertex2f(1, 0); glVertex2f(0, 0)
    glEnd()
    glShadeModel(GL_FLAT); glEnable(GL_DEPTH_TEST); glEnable(GL_LIGHTING)

def island():
    for (gx, gz), (hgt, pink) in rocks.items():
        c = tile(gx, gz)
        x, z = world(gx, gz)
        drop = crumble[(gx, gz)][1] * 4 if c == 'x' else 0      
        if drop > 6:
            continue
        cone(x, -0.1 - drop, z, 0.68, hgt, PINK if pink else LAVENDER, 4, True)
        if c in '#g':
            box(x, 0.45, z, 0.98, 1.1, 0.98, LAVENDER); box(x, 1.0, z, 0.98, 0.04, 0.98, CREAM)
        elif c == 'W':
            box(x, -0.12, z, 0.98, 0.16, 0.98, (0.55, 0.65, 0.85), False)
        elif c == 'x':
            shake = 0.03 * math.sin(t * 60) if crumble[(gx, gz)][0] > 0.7 else 0
            box(x + shake, -0.08 - drop, z, 0.98, 0.18, 0.98, (0.93, 0.85, 0.75))
            glDisable(GL_LIGHTING); glColor3f(0.45, 0.3, 0.25)
            glBegin(GL_LINE_STRIP)      # crack
            for a, b in [(-0.4, -0.3), (-0.1, -0.05), (0.05, -0.25), (0.25, 0.1), (0.4, 0.3)]:
                glVertex3f(x + a + shake, 0.02 - drop, z + b)
            glEnd(); glEnable(GL_LIGHTING)
        else:
            box(x, -0.08, z, 0.98, 0.18, 0.98, MINT if (gx + gz) % 2 == 0 else CREAM)
        if c == 'T':
            box(x, 0.15, z, 0.12, 0.3, 0.12, (0.6, 0.4, 0.3), False)
            cone(x, 0.25, z, 0.38, 0.5, GREEN); cone(x, 0.55, z, 0.28, 0.45, MINT)
        elif c == 'L':
            box(x - 0.42, 0.2, z, 0.1, 0.4, 0.9, PINK); box(x + 0.42, 0.2, z, 0.1, 0.4, 0.9, PINK)
            box(x, 0.45, z, 0.95, 0.1, 0.95, LAVENDER)

def water():                           
    glDisable(GL_LIGHTING); glEnable(GL_BLEND); glDepthMask(GL_FALSE)
    for (gx, gz) in rocks:
        if tile(gx, gz) == 'W':
            x, z = world(gx, gz)
            y = 0.02 + 0.03 * math.sin(t * 2 + gx)
            glColor4f(0.45, 0.70, 1.0, 0.65)
            glBegin(GL_QUADS)
            for a, b in ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)):
                glVertex3f(x + a, y, z + b)
            glEnd()
            glColor4f(1, 1, 1, 0.8)
            glBegin(GL_LINE_STRIP)      
            for k in range(9):
                glVertex3f(x - 0.4 + k * 0.1, y + 0.01, z + 0.1 * math.sin(k + t * 3))
            glEnd()
    glDepthMask(GL_TRUE); glDisable(GL_BLEND); glEnable(GL_LIGHTING)

def drawFlap(f):                       
    bx, bz = world(f['x'], f['z'])
    warn = max(0, 1 - f['timer'] / 1.5) if f['target'] else 0    
    glPushMatrix()
    glTranslatef(bx + 0.5 * f['dx'], 0, bz + 0.5 * f['dz'])          
    glRotatef(math.degrees(math.atan2(-f['dz'], f['dx'])), 0, 1, 0)  
    glRotatef(-90 * f['p'], 0, 0, 1)                                 
    box(0, f['len'] / 2, 0, 0.06, f['len'], 0.96, [YELLOW[i] + (RED[i] - YELLOW[i]) * warn for i in range(3)])
    glPopMatrix()

def drawStairs(s):                      
    x, z = world(s['x'], s['z'])
    box(x, 0.165, z, 0.96, 0.33, 0.96, YELLOW)
    box(x + s['open'], 0.33 * (1 + s['open']) / 2, z, 0.96, 0.33 * (1 + s['open']), 0.96, PINK)

def goal():
    for (gx, gz) in rocks:
        if tile(gx, gz) not in 'Gg':
            continue
        x, z = world(gx, gz)
        y = 1.0 if tile(gx, gz) == 'g' else 0.0
        glDisable(GL_LIGHTING); glPointSize(3); glColor3f(*GOLD)
        glBegin(GL_POINTS)             
        for a, b in RING:
            glVertex3f(x + a * 0.012, y + 0.03, z + b * 0.012)
        glEnd()
        glPushMatrix(); glTranslatef(x, y + 0.7 + 0.1 * math.sin(t * 3), z); glRotatef(t * 90, 0, 1, 0)
        r = [0.32 if i % 2 == 0 else 0.13 for i in range(10)]
        pts = [(r[i] * math.cos(math.pi / 2 + i * math.pi / 5), r[i] * math.sin(math.pi / 2 + i * math.pi / 5)) for i in range(10)]
        for side in (1, -1):            
            glColor3f(*(GOLD if side == 1 else (0.95, 0.65, 0.15)))
            glBegin(GL_TRIANGLE_FAN); glVertex3f(0, 0, 0.1 * side)
            for p in pts + [pts[0]]:
                glVertex3f(p[0], p[1], 0)
            glEnd()
        glPopMatrix(); glEnable(GL_LIGHTING)

def drawScraps():                      
    for (gx, gz) in scraps:
        if (gx, gz) not in got:
            x, z = world(gx, gz)
            glPushMatrix(); glTranslatef(x, 0.35 + 0.08 * math.sin(t * 4 + gx), z)
            glRotatef(t * 120, 0, 1, 0); glRotatef(45, 1, 0, 1)
            box(0, 0, 0, 0.2, 0.2, 0.02, LAVENDER)
            glPopMatrix()

def drawScissors(sc):
    snip = 12 + 14 * math.sin(t * 14)   
    glPushMatrix(); glTranslatef(sc['x'], 0.35 + 0.05 * math.sin(t * 5), sc['z'])
    glRotatef(sc['h'], 0, 1, 0); glScalef(1.5, 1.5, 1.5)
    for side in (1, -1):
        glPushMatrix(); glRotatef(side * snip, 0, 1, 0)
        box(0, side * 0.02, 0.25, 0.06, 0.03, 0.5, (0.82, 0.84, 0.88))
        glTranslatef(side * 0.07, 0, -0.18); glRotatef(90, 1, 0, 0)
        glColor3f(*RED); glutSolidTorus(0.03, 0.08, 6, 12)   
        glPopMatrix()
    glPopMatrix()

def crane(i):                          
    glPushMatrix()
    glTranslatef(len(MAP[0]) * 0.6 * math.sin(0.3 * t + i * 2), 3.6 + i * 0.7, 3.5 * math.cos(0.6 * t + i))
    glRotatef(math.degrees(math.atan2(math.cos(0.3 * t + i * 2), -2 * math.sin(0.6 * t + i))), 0, 1, 0)
    glScalef(0.7, 0.7, 0.7); glDisable(GL_LIGHTING)
    glColor3f(*[PINK, PAPER, LAVENDER][i % 3])
    glBegin(GL_TRIANGLES)
    glVertex3f(0, 0, 0.35); glVertex3f(0, 0.08, -0.3); glVertex3f(0, -0.06, -0.05)
    glVertex3f(0, 0, 0.2); glVertex3f(0, 0.3, 0.45); glVertex3f(0, 0.02, 0.3)
    glEnd()
    for side in (1, -1):                
        glPushMatrix(); glScalef(side, 1, 1)
        glBegin(GL_TRIANGLES)
        glVertex3f(0, 0, 0.12); glVertex3f(0, 0, -0.15); glVertex3f(0.55, 0.3 * math.sin(t * 6 + i), 0)
        glEnd(); glPopMatrix()
    glEnable(GL_LIGHTING); glPopMatrix()

# ---------------- drawing: Poko ----------------
def pokoBody():
    swing = 30 * math.sin(moveT * math.pi * 2) if moveT < 1 else 0
    for side in (-1, 1):
        glPushMatrix(); glTranslatef(side * 0.1, 0.15, 0); glRotatef(side * swing, 1, 0, 0)   
        box(0, -0.07, 0, 0.08, 0.15, 0.08, CREAM); glPopMatrix()
        glPushMatrix(); glTranslatef(side * 0.17, 0.86, 0); glRotatef(-side * 20, 0, 0, 1)    
        cone(0, 0, 0, 0.09, 0.18, PINK, 3); glPopMatrix()
    box(0, 0.32, 0, 0.36, 0.34, 0.28, PAPER)
    box(0, 0.67, 0, 0.44, 0.38, 0.4, PAPER)
    glDisable(GL_LIGHTING)
    for side in (-1, 1):
        for (col, x, y, sy, sz) in (((0.15, 0.1, 0.15), 0.1, 0.7, 1, 1), ((1.0, 0.6, 0.7), 0.15, 0.62, 0.6, 0.2)):
            glColor3f(*col)             
            glPushMatrix(); glTranslatef(side * x, y, 0.205); glScalef(1, sy, sz)
            glutSolidSphere(0.04, 8, 8); glPopMatrix()
    glEnable(GL_LIGHTING)

def paperBoat():
    glColor3f(*PAPER)
    glBegin(GL_QUADS)
    for s in (-1, 1):
        glNormal3f(s, 0.4, 0)           
        glVertex3f(s * 0.24, 0.2, -0.45); glVertex3f(s * 0.24, 0.2, 0.45); glVertex3f(s * 0.06, 0, 0.27); glVertex3f(s * 0.06, 0, -0.27)
        glNormal3f(0, 0.3, s)           
        glVertex3f(-0.24, 0.2, s * 0.45); glVertex3f(0.24, 0.2, s * 0.45); glVertex3f(0.06, 0, s * 0.27); glVertex3f(-0.06, 0, s * 0.27)
    glEnd()
    glColor3f(*YELLOW)
    glBegin(GL_TRIANGLES); glVertex3f(0, 0.2, -0.28); glVertex3f(0, 0.2, 0.28); glVertex3f(0, 0.55, 0); glEnd()   
    box(0, 0.28, -0.33, 0.2, 0.18, 0.16, PAPER)        # Poko peeking out

def pokoPos():                          
    k = min(1, moveT)
    (ax, az), (bx, bz) = world(fromX, fromZ), world(px, pz)
    h0, h1 = standHeight(fromX, fromZ) or 0, standHeight(px, pz) or 0
    return ax + (bx - ax) * k, h0 + (h1 - h0) * k, az + (bz - az) * k

def poko():
    x, y, z = pokoPos()
    if state == 'dead':
        y = y - deadT * deadT * 6                       
    elif state in ('done', 'end'):
        y = y + abs(math.sin(t * 6)) * 0.3              
    elif boat > 0.5:
        y = y + 0.04 * math.sin(t * 3)
    elif moveT < 1:
        y = y + 0.25 * math.sin(moveT * math.pi)        
    glPushMatrix(); glTranslatef(x, y, z)
    glRotatef(facing + (deadT * 720 if state == 'dead' else 0), 0, 1, 0)
    glScalef(1.25, 1.25, 1.25)
    if boat < 1:                                       
        glPushMatrix(); glScalef(1 - boat, (1 - boat) * (1 - 0.82 * flat), 1 - boat); pokoBody(); glPopMatrix()
    if boat > 0:                                        
        glPushMatrix(); glScalef(boat, boat, boat); paperBoat(); glPopMatrix()
    glPopMatrix()


def heart(x, y):
    glColor3f(*RED)
    for cx in (x - 6, x + 6):
        glBegin(GL_TRIANGLE_FAN); glVertex2f(cx, y)
        for i in range(13):
            glVertex2f(cx + 6 * math.cos(math.pi * i / 12), y + 6 * math.sin(math.pi * i / 12))
        glEnd()
    glBegin(GL_TRIANGLES); glVertex2f(x - 12, y); glVertex2f(x + 12, y); glVertex2f(x, y - 14); glEnd()

def hud():
    glDisable(GL_LIGHTING); glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION); glLoadIdentity(); gluOrtho2D(0, W, 0, H)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    glEnable(GL_BLEND)
    glColor4f(1, 1, 1, 0.82); quad2(0, H - 60, W, H)
    glColor3f(0.55, 0.3, 0.55); text(20, H - 35, "POKO: THE PAPER UNIVERSE", GLUT_BITMAP_TIMES_ROMAN_24)
    for i in range(lives):
        heart(470 + i * 32, H - 25)
    glColor3f(*INK)
    text(20, H - 55, "Level %d: %s" % (level + 1, LEVELS[level]["name"]), GLUT_BITMAP_HELVETICA_12)
    text(600, H - 32, "Scraps: %d/%d" % (len(got), len(scraps)))
    text(800, H - 32, "Steps: %d (par %d)" % (steps, LEVELS[level]["par"]))
    text(15, 15, "Arrows: move   F: fold   U: unfold   SPACE: flatten   T: boat   Mouse drag: camera   R: restart",
         GLUT_BITMAP_HELVETICA_12)
    for f in flaps:
        if f['target'] and f['p'] >= 1:
            glColor3f(*RED); text(800, H - 54, "Bridge closes in %.1f s" % f['timer'], GLUT_BITMAP_HELVETICA_12)
    if msgTime > 0 and state in ('play', 'dead'):
        glColor4f(1, 1, 1, 0.82); quad2(W / 2 - 320, 70, W / 2 + 320, 105)
        glColor3f(0.45, 0.2, 0.45); text(W / 2 - len(message) * 4.6, 82, message)
    lines = {'done': ["Island restored!", "Scraps %d/%d   Steps %d (par %d)" % (len(got), len(scraps), steps,
                      LEVELS[level]["par"]), "Press N for the next island"],
             'end': ["The paper universe is whole!", "Paper scraps found: %d" % scrapsTotal, "Press R to play again"],
             'over': ["Poko is out of lives...", "", "Press R to start again"]}.get(state)
    if lines:
        glColor4f(1, 1, 1, 0.82); quad2(W / 2 - 260, H / 2 - 60, W / 2 + 260, H / 2 + 70)
        glColor3f(0.55, 0.3, 0.55)
        text(W / 2 - len(lines[0]) * 6, H / 2 + 35, lines[0], GLUT_BITMAP_TIMES_ROMAN_24)
        for i, s in enumerate(lines[1:]):
            text(W / 2 - len(s) * 4.6, H / 2 - i * 35, s)
    glDisable(GL_BLEND); glEnable(GL_DEPTH_TEST); glEnable(GL_LIGHTING)

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    background()
    glMatrixMode(GL_PROJECTION); glLoadIdentity(); gluPerspective(40, W / H, 0.1, 100)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    yaw, pitch = math.radians(camYaw), math.radians(camPitch)
    gluLookAt(camDist * math.cos(pitch) * math.sin(yaw), camDist * math.sin(pitch),
              camDist * math.cos(pitch) * math.cos(yaw), 0, 0, 0, 0, 1, 0)
    glLightfv(GL_LIGHT0, GL_POSITION, [0.4, 1.0, 0.6, 0])
    island()
    for f in flaps:
        drawFlap(f)
    for s in stairs:
        drawStairs(s)
    for sc in scissors:
        drawScissors(sc)
    for i in range(3):
        crane(i)
    goal(); drawScraps(); poko(); water(); hud()
    glutSwapBuffers()

# ---------------- game logic ----------------
def die(reason):
    global state, deadT
    if state == 'play':
        state, deadT = 'dead', 0
        say(reason)
        play("snip" if "Snip" in reason else "fall")

def tryMove(dx, dz):
    global px, pz, fromX, fromZ, moveT, facing, steps, boatTarget
    if state != 'play' or moveT < 1:
        return
    facing = math.degrees(math.atan2(dx, dz))
    nx, nz = px + dx, pz + dz
    hNew, hNow, c, here = standHeight(nx, nz), standHeight(px, pz), tile(nx, nz), tile(px, pz)
    if hNew is None:
        return say("Poko can't go there")
    if c == 'W' and not boatTarget:
        return say("Water! Press T to become a paper boat")
    if c != 'W' and boatTarget and here != 'W':
        return say("A boat can't walk on land. Press T")
    if c == 'L' and not flatTarget:
        return say("Too low! Press SPACE to flatten")
    if abs(hNew - hNow) > 0.5:
        return say("Too high to climb")
    if c != 'W' and here == 'W':
        boatTarget = 0                  
    if (px, pz) in crumble and crumble[(px, pz)][1] == 0:
        crumble[(px, pz)][1] = 0.001   
    fromX, fromZ, px, pz = px, pz, nx, nz
    moveT, steps = 0, steps + 1
    play("step")

def useNearby(items, act, msg):         
    for it in items:
        if abs(it['x'] - px) + abs(it['z'] - pz) <= 1:
            act(it)
            play("fold")
            return say(msg, 60)
    say("Nothing to use here")

def updateScissors():
    x, y, z = pokoPos()
    for sc in scissors:
        n = len(sc['path']) - 1
        if sc['rest'] > 0:
            sc['rest'] = sc['rest'] - DT                     
        else:
            sc['u'] = sc['u'] + sc['dir'] * sc['speed'] * DT 
            if sc['u'] >= n:
                sc['u'], sc['dir'], sc['rest'] = n, -1, 0.5
            elif sc['u'] <= 0:
                sc['u'], sc['dir'], sc['rest'] = 0, 1, 0.5
        i = min(int(sc['u']), n - 1)
        k = sc['u'] - i
        (ax, az), (bx, bz) = world(*sc['path'][i]), world(*sc['path'][i + 1])
        sc['x'], sc['z'] = ax + (bx - ax) * k, az + (bz - az) * k
        sc['h'] = math.degrees(math.atan2((bx - ax) * sc['dir'], (bz - az) * sc['dir']))
        if math.hypot(sc['x'] - x, sc['z'] - z) < 0.55:
            die("Snip! The scissors cut Poko")

def Update(v):
    global t, moveT, flat, boat, msgTime, state, camYaw, deadT, lives, scrapsTotal
    t, msgTime = t + DT, max(0, msgTime - 1)
    if state == 'play':
        moveT = min(1, moveT + DT / 0.22)
        flat, boat = flat + (flatTarget - flat) * 0.2, boat + (boatTarget - boat) * 0.15
        for f in flaps:                
            f['p'] = max(0, min(1, f['p'] + (0.03 if f['target'] else -0.03)))
            if f['target'] and f['p'] >= 1:
                f['timer'] = f['timer'] - DT
                if f['timer'] <= 0:
                    f['target'] = 0
                    say("The bridge folded back up!")
        for s in stairs:
            s['open'] = min(1, s['open'] + (0.03 if s['target'] else 0))
        for key, c in crumble.items(): 
            if c[1] > 0:
                c[1] = c[1] + DT
            elif key == (px, pz) and moveT >= 1:
                c[0] = c[0] + DT
                if c[0] > 1.2:
                    c[1] = 0.001
        updateScissors()
        if moveT >= 1:
            if standHeight(px, pz) is None:
                die("Poko fell off the paper world!")
            if (px, pz) in scraps and (px, pz) not in got:
                got.add((px, pz))
                say("Paper scrap +1", 50)
                play("scrap")
            if state == 'play' and tile(px, pz) in 'Gg':
                state, scrapsTotal = 'done', scrapsTotal + len(got)
                play("star")
    elif state == 'dead':
        deadT = deadT + DT
        if deadT > 1.2:
            lives = lives - 1
            if lives <= 0:
                state = 'over'
            else:
                startLevel(level)
                say("Try again! Lives left: %d" % lives)
    else:
        camYaw = camYaw + 0.2           
    glutPostRedisplay()
    glutTimerFunc(16, Update, 0)


def arrowkey(key, x, y):
    moves = {GLUT_KEY_RIGHT: (1, 0), GLUT_KEY_LEFT: (-1, 0), GLUT_KEY_UP: (0, -1), GLUT_KEY_DOWN: (0, 1)}
    if key in moves:
        tryMove(*moves[key])

def normalkey(key, x, y):
    global flatTarget, boatTarget, camDist, state
    key = key.lower()
    if state == 'play' and key == b'f':
        useNearby(flaps, lambda f: f.update(target=1, timer=3.0), "Fold! Hurry across")
    elif state == 'play' and key == b'u':
        useNearby(stairs, lambda s: s.update(target=1), "Unfold!")
    elif state == 'play' and key == b' ' and not boatTarget:
        if flatTarget and tile(px, pz) == 'L':
            say("No room to stand up here!")
        else:
            flatTarget = 1 - flatTarget
    elif state == 'play' and key == b't':
        if tile(px, pz) == 'W':
            say("Can't change in the middle of the water!")
        else:
            boatTarget, flatTarget = 1 - boatTarget, 0
    elif key in (b'+', b'='):
        camDist = max(5, camDist - 1)
    elif key == b'-':
        camDist = min(30, camDist + 1)
    elif key == b'r':
        newGame() if state in ('end', 'over') else startLevel(level)
    elif key == b'n' and state == 'done':
        if level + 1 < len(LEVELS):
            startLevel(level + 1)
        else:
            state = 'end'

def mouseclick(button, st, x, y):
    global drag
    if button == GLUT_LEFT_BUTTON:
        drag = (x, y, camYaw, camPitch) if st == GLUT_DOWN else None

def mousedrag(x, y):
    global camYaw, camPitch
    if drag:
        camYaw = drag[2] - (x - drag[0]) * 0.3
        camPitch = max(15, min(85, drag[3] + (y - drag[1]) * 0.3))

glutInit()
glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
glutInitWindowSize(W, H)
glutInitWindowPosition(120, 40)
glutCreateWindow(b"Poko: The Paper Universe")
for cap in (GL_DEPTH_TEST, GL_NORMALIZE, GL_LIGHTING, GL_LIGHT0, GL_COLOR_MATERIAL, GL_POLYGON_OFFSET_FILL):
    glEnable(cap)
glShadeModel(GL_FLAT)                   
glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.85, 0.85, 0.85, 1])
glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.5, 0.48, 0.52, 1])
glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)
glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
glPolygonOffset(1, 1)                   
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
RING.extend(bresenhamRing(30))
makeSound("step", [(660, 0.05)])
makeSound("fold", [(400, 0.08), (600, 0.12)])
makeSound("snip", [(1200, 0.05), (900, 0.05), (1200, 0.05)])
makeSound("fall", [(500, 0.15), (350, 0.15), (200, 0.3)])
makeSound("scrap", [(880, 0.08), (1320, 0.12)])
makeSound("star", [(523, 0.12), (659, 0.12), (784, 0.12), (1047, 0.3)])
newGame()
glutDisplayFunc(showScreen)
glutSpecialFunc(arrowkey)
glutKeyboardFunc(normalkey)
glutMouseFunc(mouseclick)
glutMotionFunc(mousedrag)
glutTimerFunc(16, Update, 0)
glutMainLoop()
