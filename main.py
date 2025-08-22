import tkinter as tk
import random

# Crear ventana
ventana = tk.Tk()
ventana.title("Cielo y Pasto con Oso Pixelado")
ventana.geometry("800x600")

# Crear canvas
canvas = tk.Canvas(ventana, width=800, height=600)
canvas.pack()

# Dibujar cielo y pasto
canvas.create_rectangle(0, 0, 800, 300, fill="skyblue", outline="")
canvas.create_rectangle(0, 300, 800, 600, fill="green", outline="")

# Texto arriba
canvas.create_text(400, 20, text="Esquiva a los enemigos!!", font=("Arial", 24, "bold"), fill="black")
nivel_texto = canvas.create_text(400, 50, text="Nivel: 1", font=("Arial", 18, "bold"), fill="black")

# Corazón pequeño
def dibujar_corazon(x, y, tamaño=15):
    coords = [
        x, y,
        x-tamaño, y-tamaño,
        x-tamaño*2, y,
        x-tamaño, y+tamaño*2,
        x, y+tamaño*3,
        x+tamaño, y+tamaño*2,
        x+tamaño*2, y,
        x+tamaño, y-tamaño
    ]
    return canvas.create_polygon(coords, fill="red", outline="red")

dibujar_corazon(770, 30, tamaño=8)

# Crear nubes más separadas
nubes = []

def crear_nube(x, y, escala=1):
    partes = []
    offsets = [(-30,0), (-15,-15), (0,0), (15,-10), (30,0), (-10,10), (10,10)]
    for dx, dy in offsets:
        radio = int(20 * escala)
        parte = canvas.create_oval(x+dx, y+dy, x+dx+radio*2, y+dy+radio*2, fill="white", outline="white")
        partes.append(parte)
    return partes

# Posiciones bien separadas
posiciones_nubes = [50, 200, 350, 500, 650]
for x in posiciones_nubes:
    y = random.randint(20, 150)
    escala = random.uniform(0.8, 1.3)
    nubes.append(crear_nube(x, y, escala))

def mover_nubes():
    for nube in nubes:
        for parte in nube:
            canvas.move(parte, 1, 0)
            pos = canvas.coords(parte)
            if pos[2] > 800:
                canvas.move(parte, -900, 0)
    ventana.after(50, mover_nubes)

mover_nubes()

# Crear oso pixelado
oso_pixeles = []
oso_x = 100
oso_y = 260
pixel_size = 10

oso_patron = [
    ["", "D", "D", "D", "D", ""],
    ["D", "B", "B", "B", "B", "D"],
    ["D", "B", "B", "B", "B", "D"],
    ["", "B", "B", "B", "B", ""],
    ["", "B", "B", "B", "B", ""]
]

for i, fila in enumerate(oso_patron):
    for j, color in enumerate(fila):
        if color:
            pixel = canvas.create_rectangle(
                oso_x + j*pixel_size,
                oso_y + i*pixel_size,
                oso_x + (j+1)*pixel_size,
                oso_y + (i+1)*pixel_size,
                fill="brown" if color=="B" else "saddlebrown",
                outline=""
            )
            oso_pixeles.append(pixel)

# Movimiento del oso
vel_x = 0
vel_y = 0
gravedad = 2
saltando = False
agachado = False

def tecla_presionada(event):
    global vel_x, vel_y, saltando, agachado
    if event.keysym == "Left":
        vel_x = -5
    elif event.keysym == "Right":
        vel_x = 5
    elif event.keysym == "Up":
        if not saltando:
            vel_y = -20
            saltando = True
    elif event.keysym == "Down":
        if not agachado:
            for pixel in oso_pixeles:
                canvas.move(pixel, 0, 5)  # agacharse
            agachado = True

def tecla_suelta(event):
    global vel_x, agachado
    if event.keysym in ("Left", "Right"):
        vel_x = 0
    elif event.keysym == "Down":
        if agachado:
            for pixel in oso_pixeles:
                canvas.move(pixel, 0, -5)  # volver a tamaño normal
            agachado = False

ventana.bind("<KeyPress>", tecla_presionada)
ventana.bind("<KeyRelease>", tecla_suelta)

def actualizar_oso():
    global vel_y, saltando
    for pixel in oso_pixeles:
        canvas.move(pixel, vel_x, vel_y)
    coords = [canvas.coords(pixel) for pixel in oso_pixeles]
    y_max = max(c[3] for c in coords)
    # Suelo
    if y_max >= 300:
        vel_y = 0
        saltando = False
        for pixel in oso_pixeles:
            canvas.move(pixel, 0, 300 - y_max)
    else:
        vel_y += gravedad
    # Limites
    x_min = min(c[0] for c in coords)
    x_max = max(c[2] for c in coords)
    if x_min < 0:
        for pixel in oso_pixeles:
            canvas.move(pixel, -x_min, 0)
    if x_max > 800:
        for pixel in oso_pixeles:
            canvas.move(pixel, 800-x_max, 0)

    ventana.after(30, actualizar_oso)

actualizar_oso()
ventana.mainloop()
