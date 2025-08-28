# frontend.py
import pygame
from backend import *

fullscreen = False
pantalla = pygame.display.set_mode((ANCHO, ALTO))
superficie = pygame.Surface((ANCHO, ALTO))

clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 22, bold=True)
font_big = pygame.font.SysFont("arial", 40, bold=True)

def toggle_fullscreen():
    global pantalla, fullscreen
    fullscreen = not fullscreen
    if fullscreen:
        pantalla = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
    else:
        pantalla = pygame.display.set_mode((ANCHO, ALTO))

def dibujar_corazon(surface, x, y, t=6, color=ROJO):
    pts = [
        (x, y), (x - t, y - t), (x - 2*t, y), (x - t, y + 2*t),
        (x, y + 3*t), (x + t, y + 2*t), (x + 2*t, y), (x + t, y - t),
    ]
    pygame.draw.polygon(surface, color, pts)

def dibujar_suelo(surf, bloques):
    for b in bloques:
        pygame.draw.rect(surf, COLOR_SUELO, b)
