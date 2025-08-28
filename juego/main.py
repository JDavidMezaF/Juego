# main.py
import pygame, sys, random
from backend import *
from frontend import *

def main():
    bg_idx = 0
    backgrounds = load_backgrounds()
    fondo = Fondo(backgrounds[0][1], speed=BG_SPEED) if backgrounds else Fondo(None, speed=BG_SPEED)

    nubes = [Nube(x, random.randint(30,140), random.uniform(0.8,1.3)) for x in [80,260,430,620]]
    suelo = crear_suelo()
    oso = Oso(ANCHO//2-30, SUELO_Y-50)
    vel_scroll_base = 5
    vel_scroll = vel_scroll_base
    enemigos, projs, monedas, pwrups = [], [], [], []
    puntos, monedas_c, nivel, vidas = 0, 0, 1, 3
    game_over, pausa = False, False

    reset_patron(0)
    global dist_px_hasta_siguiente
    dist_px_hasta_siguiente = 0

    highscore = cargar_highscore()

    def extras_spawn():
        if random.random() < 0.35:
            y = random.choice([SUELO_Y-60, SUELO_Y-120, SUELO_Y-180])
            monedas.append(Moneda(ANCHO+40, y, r=10, vx=vel_scroll))
        if random.random() < 0.08:
            y = random.choice([SUELO_Y-120, SUELO_Y-160])
            pwrups.append(PowerUpEscudo(ANCHO+40, y, w=22, h=22, vx=vel_scroll))

    # ---------------- Bucle principal ----------------
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
        pantalla.blit(scaled, (0,0))
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
