"""
Basit terminal kontrolu ile Stewart platformu motor kontrolu.

Baslangicta hiz ve sure degerleri bir kez sorulur. Sonrasinda her Enter'a
basildiginda motorlar belirtilen hizda belirtilen sure kadar hareket eder;
bir sonraki Enter'da yon otomatik olarak tersine doner. Cikmak icin 'q' + Enter.

Karttaki watchdog timer, haberlesme kesilirse tetiklenip karti resetliyor.
Bu yuzden haberlesme HIC durmamali:
  - comm_loop ayri bir thread'de, arada hicbir sleep olmadan, arka arkaya
    dev.update() cagirir. Dongu hizini sadece seri port turu suresi belirler.
  - Ana thread input() ile Enter'i beklerken bloklanir ama bu comm_loop'u
    etkilemez; sadece paylasilan komut degerlerini degistirir.
  - Ekrana yazdirma da ayri bir thread'de ve dusuk frekansta yapilir, cunku
    print cagrisi (ozellikle SSH uzerinden) bloklanip haberlesmeyi geciktirebilir.

Enable baslangicta kapalidir; haberlesme enable kapali halde baslar, kart ile
baglanti kurulduktan sonra enable acilir ve session boyunca acik kalir.
"""
import threading
import time

from acrome import controller

PORT = "/dev/ttyAMA0"
BAUDRATE = 115200
PRINT_INTERVAL = 0.1  # ekrana yazdirma periyodu (haberlesme hizini etkilemez)
ENABLE_DELAY = 0.5  # enable acilmadan once enable kapali olarak haberlesilen sure

dev = controller.Stewart(PORT, baudrate=BAUDRATE)

state_lock = threading.Lock()
command = {"value": 0, "enabled": False, "presses": 0, "phase": "IDLE"}
feedback = {
    "ok": False,
    "motors": [0] * 6,
    "position": [0] * 6,
    "imu": [0.0] * 3,
    "cycles": 0,
    "errors": 0,
}
stop_event = threading.Event()


def comm_loop():
    """Kesintisiz haberlesme dongusu: arada bekleme yok."""
    cycles = 0
    errors = 0
    port = dev._Controller__ph

    while not stop_event.is_set():
        with state_lock:
            value = command["value"]
            enabled = command["enabled"]

        dev.enable(enabled)
        dev.set_motors([value] * 6)
        # Kutuphane degerleri +-1000'e kirpiyor; ekrana karta giden gercek
        # degerleri basmak icin kirpma sonrasini oku.
        motors = list(dev._Stewart__motors)
        ok = dev.update()

        cycles += 1
        if not ok:
            errors += 1
            # Eksik/bozuk cevaptan sonra tamponda artik byte kalirsa sonraki
            # tum okumalar kayar ve kendiliginden duzelmez; temizleyip resenkron ol.
            port.reset_input_buffer()

        with state_lock:
            feedback["ok"] = ok
            feedback["motors"] = motors
            feedback["position"] = list(dev.position)
            feedback["imu"] = list(dev.imu)
            feedback["cycles"] = cycles
            feedback["errors"] = errors


def print_loop():
    last_cycles = 0
    last_time = time.monotonic()

    while not stop_event.is_set():
        time.sleep(PRINT_INTERVAL)

        with state_lock:
            snap = dict(feedback)
            enabled = command["enabled"]
            presses = command["presses"]
            phase = command["phase"]

        now = time.monotonic()
        hz = (snap["cycles"] - last_cycles) / (now - last_time)
        last_cycles = snap["cycles"]
        last_time = now

        mot = " ".join(f"{m:5d}" for m in snap["motors"])
        pos = " ".join(f"{p:5d}" for p in snap["position"])
        imu = " ".join(f"{v:7.2f}" for v in snap["imu"])
        print(
            f"[{'OK ' if snap['ok'] else 'NAK'}] {phase:4} en={int(enabled)} enter={presses} | "
            f"mot: {mot} | pos: {pos} | imu: {imu} | "
            f"{hz:6.1f} Hz  err={snap['errors']}",
            flush=True,
        )


def ask_float(prompt):
    while True:
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            print("Gecersiz deger, tekrar deneyin.")


def set_command(value, enabled):
    with state_lock:
        command["value"] = int(value)
        command["enabled"] = enabled


speed = ask_float("Hiz degeri (-1000..1000): ")
duration = ask_float("Sure (saniye): ")

print("6 motorun tamami ayni degerle surulur. Sutunlar soldan saga M1..M6.")
print("mot: karta giden komut (+-1000'e kirpilmis), pos: karttan gelen pozisyon.")

comm_thread = threading.Thread(target=comm_loop, daemon=True)
comm_thread.start()
print_thread = threading.Thread(target=print_loop, daemon=True)
print_thread.start()

time.sleep(ENABLE_DELAY)  # enable kapali halde haberlesme oturuyor
set_command(0, True)

print("Hazir. Harekete baslamak icin Enter'a basin, cikmak icin 'q' + Enter.")

direction = 1
try:
    while True:
        cmd = input()
        if cmd.strip().lower() == "q":
            print("Cikiliyor...")
            break

        value = direction * speed
        print(f">>> Hareket: deger={int(value)}, sure={duration}s")

        with state_lock:
            command["presses"] += 1
            command["phase"] = "MOVE"
        set_command(value, True)

        time.sleep(duration)

        set_command(0, True)
        with state_lock:
            command["phase"] = "IDLE"
        direction *= -1

finally:
    set_command(0, False)
    time.sleep(0.1)  # enable=0 komutunun karta ulasmasi icin
    stop_event.set()
    comm_thread.join(timeout=1)
    print_thread.join(timeout=1)
