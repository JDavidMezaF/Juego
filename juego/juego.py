import pygame
import random
import sys
import os
import math

# ---------------- Configuración base ----------------
ANCHO, ALTO = 800, 600
SUELO_Y = 300
FPS = 60

# Preferencias de presentación
PIXEL_ART = True        # True = escalado nítido (pixel-perfect)
SHOW_SUELO = True       # mostrar suelo verde del motor
BG_SPEED = 0         # velocidad de parallax del fondo (0 = estático)

COLOR_CIELO = (135, 206, 235)   # skyblue
COLOR_SUELO = (0, 128, 0)       # green
COLOR_ENEMIGO = (139, 0, 0)     # darkred
COLOR_TEXTO = (0, 0, 0)         # black
COLOR_BROWN = (165, 42, 42)
COLOR_SADDLE = (139, 69, 19)
BLANCO = (255, 255, 255)
ROJO = (220, 20, 60)
GRIS = (200, 200, 200)
AMARILLO = (255, 215, 0)
AZUL = (70, 130, 180)

# --- Rutas de assets (opcionales) ---
ASSETS = os.path.join(os.path.dirname(__file__), "assets")
# player
BEAR_FRAMES = [os.path.join(ASSETS, f"bear_{i}.png") for i in range(8)]
BEAR_FALLBACK = os.path.join(ASSETS, "bear.png")
# enemigos
ELEPHANT_PNG = os.path.join(ASSETS, "elephant.png")
UNICORN_PNG  = os.path.join(ASSETS, "unicorn.png")
BEE_PNG      = os.path.join(ASSETS, "bee.png")
# proyectiles
SHEET_PNG    = os.path.join(ASSETS, "sheet.png")
BUILDING_PNG = os.path.join(ASSETS, "building.png")
# sonidos
SND_JUMP  = os.path.join(ASSETS, "jump.wav")
SND_COIN  = os.path.join(ASSETS, "coin.wav")
SND_HIT   = os.path.join(ASSETS, "hit.wav")
SND_PWR   = os.path.join(ASSETS, "powerup.wav")
SND_SHOOT = os.path.join(ASSETS, "shoot.wav")
SND_BUZZ  = os.path.join(ASSETS, "buzz.wav")
BGM_OGG   = os.path.join(ASSETS, "bgm.ogg")
# high score
HIGHSCORE_FILE = os.path.join(os.path.dirname(__file__), "highscore.txt")

pygame.init()
pygame.display.set_caption("Runner del Oso — Sprites + Proyectiles + Fondo")
LOGICO = (ANCHO, ALTO)
pantalla = pygame.display.set_mode(LOGICO)
superficie = pygame.Surface(LOGICO)
fullscreen = False

clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 22, bold=True)
font_big = pygame.font.SysFont("arial", 40, bold=True)

# -------- helpers de assets --------
def load_img(path):
    if os.path.exists(path):
        try:
            return pygame.image.load(path).convert_alpha()
        except Exception:
            return None
    return None

def load_sound(path):
    if os.path.exists(path):
        try:
            return pygame.mixer.Sound(path)
        except Exception:
            return None
    return None

def sfx(s):
    try:
        if s: s.play()
    except Exception:
        pass

def scale_img(img, size):
    """Escala nítido si PIXEL_ART=True; suave si False."""
    return pygame.transform.scale(img, size) if PIXEL_ART else pygame.transform.smoothscale(img, size)

# Detectar todos los backgrounds: background*.png
def load_backgrounds():
    files = [f for f in os.listdir(ASSETS)
             if f.lower().startswith("background") and f.lower().endswith(".png")]
    files.sort()
    items = []
    for name in files:
        img = load_img(os.path.join(ASSETS, name))
        if img:
            items.append((name, img))
    return items

# sprites
bear_frames = []
for p in BEAR_FRAMES:
    img = load_img(p)
    if img: bear_frames.append(img)
if not bear_frames:
    img = load_img(BEAR_FALLBACK)
    if img: bear_frames = [img]

sprite_elephant = load_img(ELEPHANT_PNG)
sprite_unicorn  = load_img(UNICORN_PNG)
sprite_bee      = load_img(BEE_PNG)
sprite_sheet    = load_img(SHEET_PNG)
sprite_building = load_img(BUILDING_PNG)
backgrounds = load_backgrounds()   # lista de (nombre, imagen)

# sonidos
jump_snd  = load_sound(SND_JUMP)
coin_snd  = load_sound(SND_COIN)
hit_snd   = load_sound(SND_HIT)
pwr_snd   = load_sound(SND_PWR)
shoot_snd = load_sound(SND_SHOOT)
buzz_snd  = load_sound(SND_BUZZ)
# música de fondo opcional
try:
    if os.path.exists(BGM_OGG):
        pygame.mixer.music.load(BGM_OGG)
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1)
except Exception:
    pass

def toggle_fullscreen():
    global pantalla, fullscreen
    fullscreen = not fullscreen
    if fullscreen:
        pantalla = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        pantalla = pygame.display.set_mode(LOGICO)

# ---------------- Utilidades HUD ----------------
def dibujar_corazon(surface, x, y, t=6, color=ROJO):
    pts = [
        (x, y),
        (x - t, y - t),
        (x - 2*t, y),
        (x - t, y + 2*t),
        (x, y + 3*t),
        (x + t, y + 2*t),
        (x + 2*t, y),
        (x + t, y - t),
    ]
    pygame.draw.polygon(surface, color, pts)

# ---------------- Fondo parallax ----------------
class Fondo:
    def __init__(self, img, speed=0.25):
        self.img = img
        self.speed = speed
        self.x = 0
    def set_img(self, img):
        self.img = img
        self.x = 0
    def update(self, vel_scroll):
        if self.img:
            self.x -= vel_scroll * self.speed
            w = self.img.get_width()
            if self.x <= -w:
                self.x += w
    def draw(self, surf):
        if not self.img:
            surf.fill(COLOR_CIELO)  # fallback: cielo plano
            return
        w = self.img.get_width()
        x1 = int(self.x)
        surf.blit(self.img, (x1, 0))
        surf.blit(self.img, (x1 + w, 0))

# ---------------- Nubes y suelo ----------------
class Nube:
    def __init__(self, x, y, escala=1.0):
        self.partes = []
        r = int(20 * escala)
        offsets = [(-30,0), (-15,-15), (0,0), (15,-10), (30,0), (-10,10), (10,10)]
        for dx, dy in offsets:
            self.partes.append(pygame.Rect(x+dx, y+dy, 2*r, 2*r))
    def mover(self, dx):
        for rect in self.partes:
            rect.x += dx
            if rect.right < 0:
                rect.x += ANCHO + 200
    def dibujar(self, surf):
        for rect in self.partes:
            pygame.draw.ellipse(surf, BLANCO, rect)

BLOQUE_W = 100
def crear_suelo():
    return [pygame.Rect(x, SUELO_Y, BLOQUE_W, ALTO - SUELO_Y)
            for x in range(-BLOQUE_W, ANCHO + BLOQUE_W, BLOQUE_W)]
def mover_suelo(bloques, dx):
    for b in bloques: b.x += dx
    for b in bloques:
        if b.right <= 0:
            max_x = max(bb.right for bb in bloques)
            b.x = max_x
def dibujar_suelo(surf, bloques):
    for b in bloques:
        pygame.draw.rect(surf, COLOR_SUELO, b)

# ---------------- Jugador (osito) ----------------
class Oso:
    patron = [
        ["", "D", "D", "D", "D", ""],
        ["D", "B", "B", "B", "B", "D"],
        ["D", "B", "B", "B", "B", "D"],
        ["", "B", "B", "B", "B", ""],
        ["", "B", "B", "B", "B", ""]
    ]
    def __init__(self, x, y, pixel=10):
        self.pixel = pixel
        self.partes = []
        self.vel_y = 0
        self.saltando = False
        self.agachado = False
        self.invencible_hasta = 0
        # sprite
        self.frames = bear_frames[:] if bear_frames else []
        self.frame_i = 0
        self.frame_timer = 0
        self.sprite_size = (60, 50)
        for i, fila in enumerate(self.patron):
            for j, c in enumerate(fila):
                if c:
                    r = pygame.Rect(x + j*pixel, y + i*pixel, pixel, pixel)
                    color = COLOR_BROWN if c == "B" else COLOR_SADDLE
                    self.partes.append([r, color])
    def bbox(self):
        xs = [p[0].left for p in self.partes] + [p[0].right for p in self.partes]
        ys = [p[0].top for p in self.partes] + [p[0].bottom for p in self.partes]
        return pygame.Rect(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
    def mover_x(self, dx):
        for r, _ in self.partes: r.x += dx
    def mover_y(self, dy):
        for r, _ in self.partes: r.y += dy
    def actualizar_gravedad(self):
        self.mover_y(self.vel_y)
        bb = self.bbox()
        if bb.bottom >= SUELO_Y:
            self.mover_y(SUELO_Y - bb.bottom)
            self.vel_y = 0; self.saltando = False
        else:
            self.vel_y += 1.2
    def saltar(self):
        if not self.saltando:
            self.vel_y = -18; self.saltando = True; sfx(jump_snd)
    def crouch_on(self):
        if not self.agachado: self.mover_y(5); self.agachado = True
    def crouch_off(self):
        if self.agachado: self.mover_y(-5); self.agachado = False
    def activar_escudo(self, dur_ms=4000):
        self.invencible_hasta = pygame.time.get_ticks() + dur_ms; sfx(pwr_snd)
    def es_invencible(self):
        return pygame.time.get_ticks() < self.invencible_hasta
    def dibujar(self, surf):
        bb = self.bbox()
        if self.frames:
            self.frame_timer += 1
            if self.frame_timer >= 8:
                self.frame_timer = 0
                self.frame_i = (self.frame_i + 1) % len(self.frames)
            img = scale_img(self.frames[self.frame_i], self.sprite_size)
            surf.blit(img, (bb.left, bb.top))
        else:
            for r, color in self.partes: surf.fill(color, r)
        if self.es_invencible():
            pygame.draw.rect(surf, AZUL, bb.inflate(10, 10), width=3)

# ---------------- Enemigos y proyectiles ----------------
class Enemigo:
    def __init__(self, x, y, w, h, vx, hacia_izquierda=True):
        self.rect = pygame.Rect(x, y, w, h); self.vx = vx; self.hacia_izquierda = hacia_izquierda
    def actualizar(self):
        if self.hacia_izquierda:
            self.rect.x -= self.vx
        else:
            self.rect.x += self.vx
    def fuera(self): return self.rect.right < 0 if self.hacia_izquierda else self.rect.left > ANCHO
    def dibujar(self, surf): pygame.draw.rect(surf, COLOR_ENEMIGO, self.rect)

class Cactus(Enemigo):
    def __init__(self, x, w=30, h=40, vx=6, sprite=None, hacia_izquierda=True):
        super().__init__(x, SUELO_Y - h, w, h, vx, hacia_izquierda); self.sprite = sprite
    def dibujar(self, surf):
        if self.sprite:
            img = scale_img(self.sprite, self.rect.size)
            if self.hacia_izquierda:
                img = pygame.transform.flip(img, True, False)
            surf.blit(img, self.rect)
        else: super().dibujar(surf)

class Abeja(Enemigo):
    def __init__(self, x, y_altura, w=28, h=24, vx=7, sprite=None, hacia_izquierda=True):
        super().__init__(x, y_altura, w, h, vx, hacia_izquierda); self.sprite = sprite
        self.base_y = y_altura; self.amp = 12
    def actualizar(self):
        if self.hacia_izquierda:
            self.rect.x -= self.vx
        else:
            self.rect.x += self.vx
        t = pygame.time.get_ticks()/200.0
        self.rect.y = self.base_y + int(self.amp * math.sin(t))
    def dibujar(self, surf):
        if self.sprite:
            img = scale_img(self.sprite, self.rect.size)
            if self.hacia_izquierda:
                img = pygame.transform.flip(img, True, False)
            surf.blit(img, self.rect)
        else: super().dibujar(surf)

class Elefante(Enemigo):
    def __init__(self, x, w=80, h=60, vx=5, sprite=None, hacia_izquierda=True):
        super().__init__(x, SUELO_Y - h, w, h, vx, hacia_izquierda); self.sprite = sprite
        self.cd = 0
    def actualizar(self):
        super().actualizar()
        if self.cd > 0: self.cd -= 1
    def intentar_disparar(self, projs):
        if self.cd <= 0:
            y = self.rect.top + self.rect.h//3
            vx_proj = 8 if not self.hacia_izquierda else -8
            x_proj = self.rect.right if not self.hacia_izquierda else self.rect.left
            projs.append(Hoja(x_proj, y, vx=vx_proj))
            self.cd = 90; sfx(shoot_snd)
    def dibujar(self, surf):
        if self.sprite:
            img = scale_img(self.sprite, self.rect.size)
            if self.hacia_izquierda:
                img = pygame.transform.flip(img, True, False)
            surf.blit(img, self.rect)
        else: super().dibujar(surf)

class Unicornio(Enemigo):
    def __init__(self, x, w=80, h=60, vx=5, sprite=None, hacia_izquierda=True):
        super().__init__(x, SUELO_Y - h, w, h, vx, hacia_izquierda); self.sprite = sprite
        self.cd = 0
    def actualizar(self):
        super().actualizar()
        if self.cd > 0: self.cd -= 1
    def intentar_disparar(self, projs):
        if self.cd <= 0:
            y = self.rect.top - 10
            vx_proj = 6 if not self.hacia_izquierda else -6
            x_proj = self.rect.right if not self.hacia_izquierda else self.rect.left
            projs.append(Edificio(x_proj, y, vx=vx_proj, vy=-4, gravedad=0.25))
            self.cd = 110; sfx(shoot_snd)
    def dibujar(self, surf):
        if self.sprite:
            img = scale_img(self.sprite, self.rect.size)
            if self.hacia_izquierda:
                img = pygame.transform.flip(img, True, False)
            surf.blit(img, self.rect)
        else: super().dibujar(surf)

class Proyectil:
    def __init__(self, x, y, w, h, vx, vy=0, gravedad=0, sprite=None, color=COLOR_ENEMIGO):
        self.rect = pygame.Rect(x, y, w, h)
        self.vx, self.vy, self.g = vx, vy, gravedad
        self.sprite = sprite; self.color = color
    def actualizar(self):
        self.rect.x += self.vx
        self.vy += self.g
        self.rect.y += int(self.vy)
    def fuera(self):
        return self.rect.right < 0 or self.rect.top > ALTO or self.rect.bottom < 0
    def dibujar(self, surf):
        if self.sprite:
            img = scale_img(self.sprite,self.rect.size)
            if self.vx > 0:
                img = pygame.transform.flip(img,True,False)
            surf.blit(img, self.rect)
        else:
            pygame.draw.rect(surf, self.color, self.rect)

class Hoja(Proyectil):
    def __init__(self, x, y, vx=8):
        super().__init__(x, y, 22, 16, vx=vx, sprite=sprite_sheet, color=BLANCO)

class Edificio(Proyectil):
    def __init__(self, x, y, vx=6, vy=-4, gravedad=0.25):
        super().__init__(x, y, 28, 28, vx=vx, vy=vy, gravedad=gravedad, sprite=sprite_building, color=GRIS)

# ---------------- Monedas & PowerUp ----------------
class Moneda:
    def __init__(self, x, y, r=10, vx=6):
        self.rect = pygame.Rect(x - r, y - r, r*2, r*2); self.vx = vx; self.r = r
    def actualizar(self): self.rect.x -= self.vx
    def fuera(self): return self.rect.right < 0
    def dibujar(self, surf): pygame.draw.ellipse(surf, AMARILLO, self.rect)

class PowerUpEscudo:
    def __init__(self, x, y, w=22, h=22, vx=6):
        self.rect = pygame.Rect(x, y, w, h); self.vx = vx
    def actualizar(self): self.rect.x -= self.vx
    def fuera(self): return self.rect.right < 0
    def dibujar(self, surf):
        pygame.draw.rect(surf, AZUL, self.rect, border_radius=6)
        pygame.draw.rect(surf, BLANCO, self.rect, 2, border_radius=6)

# ---------------- Patrones ----------------
PATRONES = [
    [
        {"tipo": "elefante"},
        {"tipo": "gap", "px": 260},
        {"tipo": "abeja", "y": SUELO_Y-150},
        {"tipo": "gap", "px": 240},
        {"tipo": "cactus", "w": 30, "h": 40},
        {"tipo": "gap", "px": 260},
        {"tipo": "unicornio"},
        {"tipo": "gap", "px": 300},
    ],
    [
        {"tipo": "cactus", "w": 25, "h": 36},
        {"tipo": "gap", "px": 200},
        {"tipo": "abeja", "y": SUELO_Y-120},
        {"tipo": "gap", "px": 200},
        {"tipo": "elefante"},
        {"tipo": "gap", "px": 220},
        {"tipo": "abeja", "y": SUELO_Y-170},
        {"tipo": "gap", "px": 240},
        {"tipo": "unicornio"},
        {"tipo": "gap", "px": 280},
    ],
]

pat_idx = 0
step_idx = 0
dist_px_hasta_siguiente = 0

def reset_patron(nuevo=None):
    global pat_idx, step_idx, dist_px_hasta_siguiente
    if nuevo is not None: pat_idx = nuevo % len(PATRONES)
    step_idx = 0; dist_px_hasta_siguiente = 0

def procesar_siguiente_item(vel_scroll, enemigos, extras_cb, lado="derecha"):
    global pat_idx, step_idx
    seq = PATRONES[pat_idx]
    item = seq[step_idx]
    step_idx = (step_idx + 1) % len(seq)
    spawn_izquierda = lado == "izquierda"
    x_spawn = -40 if spawn_izquierda else ANCHO + 40

    t = item["tipo"]
    if t == "gap":
        extras_cb(); return item["px"]
    if t == "cactus":
        enemigos.append(Cactus(ANCHO + 40, w=item.get("w", 30), h=item.get("h", 40),
                               vx=vel_scroll + 1, sprite=None))
        extras_cb(); return 200
    if t == "abeja":
        y = item.get("y", SUELO_Y - 140)
        enemigos.append(Abeja(x_spawn, y, w=28, h=24, vx=vel_scroll + 2, sprite=sprite_bee, hacia_izquierda=not spawn_izquierda))
        sfx(buzz_snd); extras_cb(); return 220
    if t == "elefante":
        enemigos.append(Elefante(x_spawn, w=80, h=60, vx=vel_scroll, sprite=sprite_elephant,hacia_izquierda=not spawn_izquierda))
        extras_cb(); return 260
    if t == "unicornio":
        enemigos.append(Unicornio(x_spawn, w=80, h=60, vx=vel_scroll, sprite=sprite_unicorn,hacia_izquierda=not spawn_izquierda))
        extras_cb(); return 280
    extras_cb(); return 220

# ---------------- High Score ----------------
def cargar_highscore():
    try:
        with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip())
    except Exception:
        return 0
def guardar_highscore(v):
    try:
        with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
            f.write(str(v))
    except Exception:
        pass

# ---------------- Juego ----------------
def main():
    # Fondo: usa el primero disponible background*.png (si hay)
    bg_idx = 0
    fondo = Fondo(backgrounds[0][1], speed=BG_SPEED) if backgrounds else Fondo(None, speed=BG_SPEED)

    nubes = [Nube(x, random.randint(30, 140), random.uniform(0.8, 1.3)) for x in [80, 260, 430, 620]]
    suelo = crear_suelo()

    oso = Oso(ANCHO // 2-30, SUELO_Y - 50)
    vel_scroll_base = 5
    vel_scroll = vel_scroll_base

    enemigos = []
    projs = []
    monedas = []
    pwrups = []
    puntos = 0
    monedas_c = 0
    nivel = 1
    vidas = 3
    game_over = False
    pausa = False

    reset_patron(0)
    global dist_px_hasta_siguiente
    dist_px_hasta_siguiente = 0

    highscore = cargar_highscore()

    def extras_spawn():
        if random.random() < 0.35:
            y = random.choice([SUELO_Y - 60, SUELO_Y - 120, SUELO_Y - 180])
            monedas.append(Moneda(ANCHO + 40, y, r=10, vx=vel_scroll))
        if random.random() < 0.08:
            y = random.choice([SUELO_Y - 120, SUELO_Y - 160])
            pwrups.append(PowerUpEscudo(ANCHO + 40, y, w=22, h=22, vx=vel_scroll))

    while True:
        # eventos
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
                if e.key == pygame.K_F11: toggle_fullscreen()
                if e.key == pygame.K_F5 and backgrounds:
                    # Cambiar de background
                    bg_idx = (bg_idx + 1) % len(backgrounds)
                    fondo.set_img(backgrounds[bg_idx][1])
                if e.key == pygame.K_F6:
                    # toggle suelo
                    global SHOW_SUELO
                    SHOW_SUELO = not SHOW_SUELO
                if e.key == pygame.K_p: pausa = not pausa
                if not game_over and not pausa:
                    if e.key == pygame.K_UP: oso.saltar()
                    elif e.key == pygame.K_DOWN: oso.crouch_on()
                if game_over and e.key == pygame.K_r: return main()
            if e.type == pygame.KEYUP:
                if e.key == pygame.K_DOWN: oso.crouch_off()

        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * 4

        # lógica
        if not game_over and not pausa:
            # fondo + scroll mundo
            fondo.update(vel_scroll)
            for nube in nubes:
                nube.mover(-int(vel_scroll * 0.2))
            mover_suelo(suelo, -vel_scroll)

            # patrones por distancia
            dist_px_hasta_siguiente -= vel_scroll
            while dist_px_hasta_siguiente <= 0:
                lado = random.choice(["izquierda","derecha"])
                dist_px_hasta_siguiente += procesar_siguiente_item(vel_scroll, enemigos, extras_spawn, lado = lado)

            # jugador
            oso.mover_x(dx)
            oso.actualizar_gravedad()

            # enemigos + disparos
            bb = oso.bbox()
            vivos = []
            for en in enemigos:
                en.actualizar()
                if isinstance(en, Elefante): en.intentar_disparar(projs)
                if isinstance(en, Unicornio): en.intentar_disparar(projs)
                if en.rect.colliderect(bb):
                    if not oso.es_invencible():
                        vidas -= 1; sfx(hit_snd); oso.activar_escudo(1200)
                    en.rect.x = -9999
                if not en.fuera():
                    vivos.append(en)
                else:
                    puntos += 1
                    if puntos % 10 == 0:
                        nivel += 1
                        vel_scroll = vel_scroll_base + nivel
                        reset_patron(pat_idx + 1)
            enemigos = vivos

            # proyectiles
            nuevos_projs = []
            for p in projs:
                p.actualizar()
                if p.rect.colliderect(bb):
                    if not oso.es_invencible():
                        vidas -= 1; sfx(hit_snd); oso.activar_escudo(1200)
                    p.rect.x = -9999
                if not p.fuera(): nuevos_projs.append(p)
            projs = nuevos_projs

            # monedas
            nuevas_m = []
            for m in monedas:
                m.actualizar()
                if m.rect.colliderect(bb):
                    monedas_c += 1; puntos += 1; sfx(coin_snd)
                elif not m.fuera(): nuevas_m.append(m)
            monedas = nuevas_m

            # powerups
            nuevos_pw = []
            for p in pwrups:
                p.actualizar()
                if p.rect.colliderect(bb): oso.activar_escudo(3500)
                elif not p.fuera(): nuevos_pw.append(p)
            pwrups = nuevos_pw

            if vidas <= 0:
                game_over = True
                if puntos > highscore:
                    highscore = puntos
                    guardar_highscore(highscore)

        # dibujo
        fondo.draw(superficie)
        for nube in nubes:
            nube.dibujar(superficie)
        if SHOW_SUELO:
            dibujar_suelo(superficie, suelo)

        hud_txt = f"Nivel: {nivel} | Puntos: {puntos} | Monedas: {monedas_c} | Vidas:"
        superficie.blit(font.render(hud_txt, True, COLOR_TEXTO), (20, 40))
        for i in range(3):
            dibujar_corazon(superficie, 330 + i*22, 46, t=5, color=(ROJO if i < vidas else GRIS))
        hs = font.render(f"High Score: {highscore}", True, COLOR_TEXTO)
        superficie.blit(hs, (ANCHO - hs.get_width() - 20, 40))
        titulo = font.render("F11 Fullscreen | F5 Fondo | F6 Suelo | P Pausa | ESC Salir", True, COLOR_TEXTO)
        superficie.blit(titulo, (ANCHO//2 - titulo.get_width()//2, 8))

        for en in enemigos: en.dibujar(superficie)
        for p in projs: p.dibujar(superficie)
        for m in monedas: m.dibujar(superficie)
        for p in pwrups: p.dibujar(superficie)
        oso.dibujar(superficie)

        if pausa and not game_over:
            px = font_big.render("PAUSA", True, COLOR_TEXTO)
            superficie.blit(px, (ANCHO//2 - px.get_width()//2, ALTO//2 - 20))

        if game_over:
            go = font_big.render("GAME OVER", True, COLOR_TEXTO)
            sc = font.render(f"Puntuación: {puntos}  |  Nivel: {nivel}", True, COLOR_TEXTO)
            re = font.render("Pulsa R para reiniciar", True, COLOR_TEXTO)
            superficie.blit(go, (ANCHO//2 - go.get_width()//2, ALTO//2 - 60))
            superficie.blit(sc, (ANCHO//2 - sc.get_width()//2, ALTO//2 - 18))
            superficie.blit(re, (ANCHO//2 - re.get_width()//2, ALTO//2 + 14))

        scaled = pygame.transform.scale(superficie, pantalla.get_size())
        pantalla.blit(scaled, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
