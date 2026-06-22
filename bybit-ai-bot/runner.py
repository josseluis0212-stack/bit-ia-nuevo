import subprocess
import sys
import time
import threading

print("🚀 Iniciando gestor de procesos multi-bot...", flush=True)

# Darle tiempo a Render de conectar los logs a la consola antes de lanzar nada
print("⏳ Esperando 10 segundos para asegurar que Render capture todos los logs...", flush=True)
time.sleep(10)
print("✅ Espera terminada. Levantando bots...", flush=True)

def monitor_process(proc, name):
    proc.wait()
    print(f"❌ ALERTA FATAL: El proceso {name} ha terminado inesperadamente con código {proc.returncode}!", flush=True)

try:
    print("🚀 Levantando SuperTrend Bot...", flush=True)
    import os
    os.makedirs("/app/storage", exist_ok=True)
    supertrend_log = open("/app/storage/supertrend_raw.log", "a")
    supertrend_proc = subprocess.Popen(
        [sys.executable, "-u", "/app/supertrend_ema_bot/main.py"],
        stdout=supertrend_log,
        stderr=subprocess.STDOUT
    )
    threading.Thread(target=monitor_process, args=(supertrend_proc, "SUPERTREND_BOT"), daemon=True).start()

    print("🚀 Levantando QUANTUM BYBIT (Uvicorn)...", flush=True)
    uvicorn_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    threading.Thread(target=monitor_process, args=(uvicorn_proc, "UVICORN_WEB"), daemon=True).start()

    # Mantenemos el runner vivo
    while True:
        time.sleep(60)
except Exception as e:
    print(f"Error fatal en el gestor de procesos: {e}", flush=True)
