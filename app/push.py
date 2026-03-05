"""
Utilidad para enviar push notifications a través de la API de Expo.
No lanza excepción si falla — el flujo principal no debe verse afectado.
"""

import requests

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def send_push(token: str, title: str, body: str, data: dict | None = None) -> None:
    if not token or not token.startswith("ExponentPushToken["):
        return

    payload: dict = {"to": token, "title": title, "body": body, "sound": "default"}
    if data:
        payload["data"] = data

    try:
        requests.post(EXPO_PUSH_URL, json=payload, timeout=5)
    except Exception:
        pass
