"""Arvuti kasutaja jälgija – algversioon.

Programm mõõdab, kui kaua kasutaja arvutit tegelikult aktiivselt kasutab
(hiire ja klaviatuuri tegevuse põhjal), salvestab andmed faili ning võrdleb
neid kasutaja enda seatud päevase eesmärgiga.

Käsud:
    python arvuti_jalgija.py             - käivita jälgimine (vaikimisi)
    python arvuti_jalgija.py statistika  - prindi viimase 7 päeva kokkuvõte
    python arvuti_jalgija.py graafik     - tee päeva- ja nädalagraafik
    python arvuti_jalgija.py eesmark     - muuda päevast eesmärki
"""

import argparse
import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

# ---------- Seaded ----------
KAUST = Path(__file__).parent
ANDMEFAIL = KAUST / "kasutus.csv"      # siia salvestatakse päevade kaupa sekundid
SEADEFAIL = KAUST / "seaded.json"      # siia salvestatakse kasutaja eesmärk
GRAAFIKUFAIL = KAUST / "graafik.png"

TUHIKU_PIIR = 60       # kui nii mitu sekundit pole tegevust, loeme arvuti "puhkavaks"
SALVESTUSVAHE = 30     # kui tihti (sekundites) andmed faili salvestatakse


# ---------- Eesmärk (seaded) ----------
def kysi_eesmark():
    """Küsib kasutajalt, mitu tundi päevas ta tahab arvutit kasutada."""
    while True:
        tekst = input("Mitu tundi päevas tahad arvutis olla? (nt 2 või 1.5): ")
        try:
            tunnid = float(tekst.replace(",", "."))
            if tunnid > 0:
                return round(tunnid * 60)  # hoiame minutites
        except ValueError:
            pass
        print("Palun sisesta positiivne arv.")


def lae_eesmark():
    """Loeb eesmärgi (minutites) failist; kui faili pole (esimene käivitus), küsib."""
    if SEADEFAIL.exists():
        with open(SEADEFAIL, encoding="utf-8") as f:
            return json.load(f)["eesmark_minutit"]
    minutid = kysi_eesmark()
    salvesta_eesmark(minutid)
    return minutid


def salvesta_eesmark(minutid):
    with open(SEADEFAIL, "w", encoding="utf-8") as f:
        json.dump({"eesmark_minutit": minutid}, f)


# ---------- Andmed ----------
def lae_andmed():
    """Tagastab sõnastiku {'2026-11-11': sekundid, ...}."""
    if not ANDMEFAIL.exists():
        return {}
    tabel = pd.read_csv(ANDMEFAIL)
    return dict(zip(tabel["kuupaev"], tabel["sekundid"].astype(int)))


def salvesta_andmed(andmed):
    tabel = pd.DataFrame(sorted(andmed.items()), columns=["kuupaev", "sekundid"])
    tabel.to_csv(ANDMEFAIL, index=False)


def vorminda(sekundid):
    """Sekundid -> 'T h MM min'."""
    minutid = int(sekundid // 60)
    return f"{minutid // 60} h {minutid % 60:02d} min"


# ---------- Jälgimine ----------
def jalgi():
    """Jälgib hiirt ja klaviatuuri ning loeb aktiivse aja kokku."""
    try:
        from pynput import keyboard, mouse
    except ImportError as viga:
        sys.exit(f"pynput'i ei saanud kasutada ({viga}). "
                 "Paigalda: pip install -r requirements.txt")

    eesmark_sek = lae_eesmark() * 60
    andmed = lae_andmed()
    viimane_tegevus = [0.0]  # list, et kuulajate funktsioonid saaksid väärtust muuta

    def markeeri(*_):
        viimane_tegevus[0] = time.time()

    # Kuulajad töötavad eraldi lõimedes ja annavad märku iga hiire/klahvi tegevuse kohta
    kuulajad = [
        mouse.Listener(on_move=markeeri, on_click=markeeri, on_scroll=markeeri),
        keyboard.Listener(on_press=markeeri),
    ]
    try:
        for k in kuulajad:
            k.start()
    except Exception as viga:  # nt Linuxis ilma graafilise keskkonnata
        sys.exit(f"Ei õnnestunud hiire/klaviatuuri jälgimist alustada: {viga}")

    print(f"Jälgimine käib. Eesmärk: {vorminda(eesmark_sek)} päevas. Peatamiseks Ctrl+C.")
    hoiatatud_paev = None
    viimane_salvestus = time.time()

    try:
        while True:
            time.sleep(1)
            paev = date.today().isoformat()
            if time.time() - viimane_tegevus[0] <= TUHIKU_PIIR:
                andmed[paev] = andmed.get(paev, 0) + 1

            # Teavita ühe korra päevas, kui eesmärk on ületatud
            if andmed.get(paev, 0) >= eesmark_sek and hoiatatud_paev != paev:
                hoiatatud_paev = paev
                print(f"\a⚠ Täna on eesmärk ({vorminda(eesmark_sek)}) ületatud! "
                      f"Aktiivset aega kokku: {vorminda(andmed[paev])}.")

            if time.time() - viimane_salvestus >= SALVESTUSVAHE:
                salvesta_andmed(andmed)
                viimane_salvestus = time.time()
    except KeyboardInterrupt:
        pass
    finally:
        salvesta_andmed(andmed)
        print("\nAndmed salvestatud. Head aega!")


# ---------- Statistika ja graafikud ----------
def viimased_paevad(andmed, arv=7):
    """Tagastab pandas Series'i: viimased `arv` päeva, puuduvad päevad = 0."""
    paevad = [date.today() - timedelta(days=i) for i in range(arv - 1, -1, -1)]
    return pd.Series([andmed.get(p.isoformat(), 0) for p in paevad],
                     index=pd.to_datetime(paevad))


def statistika():
    andmed = lae_andmed()
    eesmark_sek = lae_eesmark() * 60
    seitse = viimased_paevad(andmed)

    print(f"Eesmärk: {vorminda(eesmark_sek)} päevas\n")
    for paev, sek in seitse.items():
        markus = "  <- eesmärk ületatud" if sek > eesmark_sek else ""
        print(f"{paev:%a %d.%m}  {vorminda(sek)}{markus}")
    print(f"\nKeskmiselt päevas: {vorminda(seitse.mean())}")
    print(f"Kokku 7 päeva jooksul: {vorminda(seitse.sum())}")
    print(f"Päevi, mil eesmärk ületati: {(seitse > eesmark_sek).sum()} / 7")


def graafik():
    import matplotlib.pyplot as plt

    andmed = lae_andmed()
    if not andmed:
        sys.exit("Andmeid pole veel. Käivita kõigepealt jälgimine.")
    eesmark_h = lae_eesmark() / 60

    seitse = viimased_paevad(andmed) / 3600  # tundides

    # Nädalad (esmaspäevast pühapäevani), viimased 4
    kogu = pd.Series(andmed)
    kogu.index = pd.to_datetime(kogu.index)
    nadalad = (kogu.resample("W-SUN").sum() / 3600).tail(4)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    # Päevagraafik: ületatud päevad punasega
    varvid = ["tab:red" if h > eesmark_h else "tab:blue" for h in seitse]
    ax1.bar(seitse.index.strftime("%a %d.%m"), seitse.values, color=varvid)
    ax1.axhline(eesmark_h, color="black", linestyle="--", label="Eesmärk")
    ax1.set_title("Viimased 7 päeva")
    ax1.set_ylabel("Tunde")
    ax1.legend()

    # Nädalagraafik: eesmärk * 7 päeva
    nadala_eesmark = eesmark_h * 7
    varvid2 = ["tab:red" if h > nadala_eesmark else "tab:blue" for h in nadalad]
    ax2.bar(nadalad.index.strftime("%d.%m"), nadalad.values, color=varvid2)
    ax2.axhline(nadala_eesmark, color="black", linestyle="--", label="Nädala eesmärk")
    ax2.set_title("Nädalad (nädala lõpukuupäev)")
    ax2.set_ylabel("Tunde")
    ax2.legend()

    fig.suptitle("Arvuti kasutus")
    fig.tight_layout()
    fig.savefig(GRAAFIKUFAIL, dpi=120)
    print(f"Graafik salvestatud: {GRAAFIKUFAIL}")
    plt.show()


def muuda_eesmark():
    salvesta_eesmark(kysi_eesmark())
    print("Eesmärk salvestatud.")


# ---------- Käsurida ----------
def main():
    parser = argparse.ArgumentParser(description="Arvuti kasutaja jälgija")
    parser.add_argument("kask", nargs="?", default="jalgi",
                        choices=["jalgi", "statistika", "graafik", "eesmark"])
    args = parser.parse_args()

    {"jalgi": jalgi, "statistika": statistika,
     "graafik": graafik, "eesmark": muuda_eesmark}[args.kask]()


if __name__ == "__main__":
    main()
