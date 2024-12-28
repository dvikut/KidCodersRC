import requests
import time

# Ez egy csúnya, de praktikus kód

with open("kisauto.ip", "r") as ipfile:
    ip = ipfile.read().strip()
api_url = f"http://{ip}/move"


def hivas(parancs, ido: float):
    try:
        move_data = {
            "direction": parancs,
            "voltage": 6.0,
            "duration": ido
        }
        response = requests.post(api_url, json=move_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Hiba történt: {e}")
        return False


def elore(ido=1.0):
    return hivas("forward", ido)


def balra(ido=1.0):
    return hivas("turn_left", ido)


def jobbra(ido=1.0):
    return hivas("turn_right", ido)


def hatra(ido=1.0):
    return hivas("backward", ido)


def hatra_balra(ido=1.0):
    return hivas("back_left", ido)


def hatra_jobbra(ido=1.0):
    return hivas("back_right", ido)


def varj(ido=1.0):
    time.sleep(ido)


