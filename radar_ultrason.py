"""
Radar ultrason temps réel - Interface Python (Pygame + pyserial)

Installation :  pip install pygame pyserial
Lancement    :  python radar_ultrason.py                (auto-détection du port)
                python radar_ultrason.py --port COM3
                python radar_ultrason.py --sim          (sans matériel)
Touches      :  M = mode radar/jauge | ESC = quitter
"""
import argparse, math, random, threading, time
from collections import deque
import pygame

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    serial = None

MAX_CM, ALERT_CM, WARN_CM = 200, 15, 30
W, H = 960, 620
ORIGIN = (W // 2 - 90, H - 70)
RADIUS = H - 150

state = {"angle": 90, "dist": None, "raw": None}
points = deque(maxlen=400)           # (angle, dist, timestamp)
window = deque(maxlen=5)             # filtre médian
lock = threading.Lock()
running = True


def median_filter(d):
    window.append(d)
    s = sorted(window)
    return s[len(s) // 2]


def push(angle, d):
    if d is None or d < 0:
        with lock:
            state.update(angle=angle, dist=None, raw=None)
        return
    f = median_filter(d)
    with lock:
        state.update(angle=angle, dist=f, raw=d)
        points.append((angle, f, time.time()))


def find_port():
    for p in list_ports.comports():
        name = (p.description + p.device).lower()
        if any(k in name for k in ("arduino", "ch340", "usb serial", "ttyacm", "ttyusb")):
            return p.device
    ports = list(list_ports.comports())
    return ports[0].device if ports else None


def serial_thread(port, baud):
    try:
        ser = serial.Serial(port, baud, timeout=1)
    except Exception as e:
        print("Erreur port série :", e)
        return
    time.sleep(2)                    # reset auto de l'Arduino
    ser.reset_input_buffer()
    while running:
        try:
            line = ser.readline().decode(errors="ignore").strip()
            a, d = line.split(",")
            push(int(a), float(d))
        except ValueError:
            continue                 # ligne corrompue : on ignore
        except Exception:
            break
    ser.close()


def sim_thread():
    a, step, t = 0, 3, 0
    while running:
        t += 0.05
        d = 80 + 60 * math.sin(t) + random.uniform(-2, 2)
        if random.random() < 0.02:
            d = random.uniform(-5, 400)   # bruit parasite
        push(a, d)
        a += step
        if a >= 180 or a <= 0:
            step = -step
        time.sleep(0.04)


def color_for(d):
    if d is None:
        return (120, 120, 120)
    if d < ALERT_CM:
        return (255, 60, 60)
    if d < WARN_CM:
        return (255, 170, 40)
    return (60, 230, 120)


def polar(angle, dist):
    r = min(dist, MAX_CM) / MAX_CM * RADIUS
    rad = math.radians(angle)
    return ORIGIN[0] + r * math.cos(rad), ORIGIN[1] - r * math.sin(rad)


def draw_grid(screen, font):
    for k in range(1, 5):
        r = RADIUS * k / 4
        rect = pygame.Rect(ORIGIN[0] - r, ORIGIN[1] - r, 2 * r, 2 * r)
        pygame.draw.arc(screen, (40, 90, 60), rect, 0, math.pi, 1)
        screen.blit(font.render(f"{MAX_CM * k // 4}", True, (70, 140, 100)),
                    (ORIGIN[0] + r - 24, ORIGIN[1] + 4))
    for a in range(0, 181, 30):
        pygame.draw.line(screen, (30, 70, 50), ORIGIN, polar(a, MAX_CM), 1)
    # zone d'alerte
    r = RADIUS * ALERT_CM / MAX_CM
    rect = pygame.Rect(ORIGIN[0] - r, ORIGIN[1] - r, 2 * r, 2 * r)
    pygame.draw.arc(screen, (200, 50, 50), rect, 0, math.pi, 2)


def draw_gauge(screen, font, big, d):
    x, y, w, h = W - 110, 90, 50, H - 200
    pygame.draw.rect(screen, (35, 40, 45), (x, y, w, h), border_radius=8)
    if d is not None:
        fill = int(h * (1 - min(d, MAX_CM) / MAX_CM))   # plus proche = plus rempli
        pygame.draw.rect(screen, color_for(d), (x, y + h - fill, w, fill), border_radius=8)
    pygame.draw.rect(screen, (200, 200, 200), (x, y, w, h), 2, border_radius=8)
    screen.blit(font.render("PROXIMITE", True, (200, 200, 200)), (x - 18, y - 28))
    txt = "-- cm" if d is None else f"{d:.0f} cm"
    s = big.render(txt, True, color_for(d))
    screen.blit(s, (x + w // 2 - s.get_width() // 2, y + h + 12))


def main():
    global running
    ap = argparse.ArgumentParser()
    ap.add_argument("--port")
    ap.add_argument("--baud", type=int, default=9600)
    ap.add_argument("--sim", action="store_true")
    args = ap.parse_args()

    if args.sim or serial is None:
        threading.Thread(target=sim_thread, daemon=True).start()
        src = "SIMULATION"
    else:
        port = args.port or find_port()
        if not port:
            print("Aucun port série trouvé. Utilise --port COMx ou --sim")
            return
        threading.Thread(target=serial_thread, args=(port, args.baud), daemon=True).start()
        src = f"{port} @ {args.baud}"

    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Radar Ultrason - HC-SR04")
    font = pygame.font.SysFont("consolas", 16)
    big = pygame.font.SysFont("consolas", 34, bold=True)
    clock = pygame.time.Clock()
    radar_mode = True

    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                running = False
            if e.type == pygame.KEYDOWN and e.key == pygame.K_m:
                radar_mode = not radar_mode

        with lock:
            d, ang = state["dist"], state["angle"]
            pts = list(points)

        screen.fill((10, 16, 14))
        draw_grid(screen, font)

        now = time.time()
        for a, dist, t in pts:
            age = now - t
            if age > 3:
                continue
            c = color_for(dist)
            k = 1 - age / 3
            px, py = polar(a, dist)
            pygame.draw.circle(screen, tuple(int(v * k) for v in c), (int(px), int(py)), 5)

        # faisceau
        pygame.draw.line(screen, (80, 255, 160), ORIGIN, polar(ang, MAX_CM), 2)
        if d is not None:
            ox, oy = polar(ang, d)
            pygame.draw.circle(screen, color_for(d), (int(ox), int(oy)), 9, 2)
        pygame.draw.circle(screen, (230, 230, 230), ORIGIN, 8)

        draw_gauge(screen, font, big, d)

        # alerte collision
        if d is not None and d < ALERT_CM:
            if int(now * 4) % 2 == 0:
                pygame.draw.rect(screen, (255, 60, 60), (0, 0, W, H), 8)
            s = big.render("! ALERTE COLLISION !", True, (255, 60, 60))
            screen.blit(s, (W // 2 - s.get_width() // 2 - 90, 20))

        info = f"Source: {src} | Angle: {ang}° | [M] mode: {'RADAR' if radar_mode else 'JAUGE'}"
        screen.blit(font.render(info, True, (180, 180, 180)), (12, H - 26))

        if not radar_mode:               # mode jauge : on garde seulement le dernier point
            with lock:
                while len(points) > 1:
                    points.popleft()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
