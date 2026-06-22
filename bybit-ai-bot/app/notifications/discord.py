import aiohttp
import logging
from app.config import Config

logger = logging.getLogger("DiscordNotifier")

class DiscordNotifier:
    def __init__(self):
        self.webhook_url = getattr(Config, "DISCORD_WEBHOOK_URL", "")
        
    async def send_message(self, message: str):
        if not self.webhook_url:
            logger.debug(f"[DISCORD] Webhook no configurado. Mensaje no enviado: {message}")
            return
            
        payload = {"content": message}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload, timeout=5) as resp:
                    if resp.status not in (200, 204):
                        logger.error(f"[DISCORD] Error enviando mensaje: HTTP {resp.status}")
        except Exception as e:
            logger.error(f"[DISCORD] Exception enviando mensaje: {e}")

    async def notify_open(self, symbol: str, side: str, entry_price: float, qty: float, strategy: str = "UNKNOWN"):
        msg = f"🟢 **NUEVA POSICIÓN ABIERTA (DEMO)** 🟢\n" \
              f"**Par:** {symbol}\n" \
              f"**Dirección:** {side}\n" \
              f"**Precio:** {entry_price:.6f}\n" \
              f"**Tamaño:** {qty}\n" \
              f"**Estrategia:** {strategy}"
        await self.send_message(msg)

    async def notify_tp1(self, symbol: str, price: float):
        msg = f"🎯 **TP1 ALCANZADO (30%)** 🎯\n" \
              f"**Par:** {symbol}\n" \
              f"**Precio de ejecución:** {price:.6f}\n" \
              f"Beneficio parcial asegurado."
        await self.send_message(msg)

    async def notify_lock(self, symbol: str, lock_price: float):
        msg = f"🔒 **PROFIT LOCK ACTIVADO (40% del recorrido)** 🔒\n" \
              f"**Par:** {symbol}\n" \
              f"**Stop Loss movido a:** {lock_price:.6f}\n" \
              f"La operación tiene un ~10% de ganancia asegurada."
        await self.send_message(msg)

    async def notify_tp2(self, symbol: str, price: float):
        msg = f"🚀 **TP2 ALCANZADO (30%)** 🚀\n" \
              f"**Par:** {symbol}\n" \
              f"**Precio de ejecución:** {price:.6f}\n" \
              f"Activando Trailing Stop para el 40% restante."
        await self.send_message(msg)

    async def notify_trailing_update(self, symbol: str, new_stop: float):
        # Para evitar spam, quizás solo loguear internamente.
        pass

    async def notify_close(self, symbol: str, side: str, reason: str):
        msg = f"🏁 **POSICIÓN CERRADA** 🏁\n" \
              f"**Par:** {symbol} ({side})\n" \
              f"**Razón:** {reason}"
        await self.send_message(msg)
        
    async def notify_error(self, message: str):
        msg = f"⚠️ **ERROR DEL SISTEMA** ⚠️\n{message}"
        await self.send_message(msg)

discord_notifier = DiscordNotifier()
