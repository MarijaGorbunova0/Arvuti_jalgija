# Arvuti kasutaja jälgija (algversioon)

Python-programm, mis mõõdab hiire ja klaviatuuri tegevuse põhjal, kui kaua
arvutit tegelikult aktiivselt kasutatakse, ning võrdleb seda kasutaja enda
seatud päevase eesmärgiga.

## Paigaldus
    pip install -r requirements.txt

## Kasutamine
    python arvuti_jalgija.py              # käivita jälgimine (esimesel korral küsib eesmärki)
    python arvuti_jalgija.py statistika   # viimase 7 päeva kokkuvõte
    python arvuti_jalgija.py graafik      # päeva- ja nädalagraafik (salvestub graafik.png)
    python arvuti_jalgija.py eesmark      # muuda päevast eesmärki

## Failid
- `arvuti_jalgija.py` – programm
- `kasutus.csv` – tekib ise; päevade kaupa aktiivsed sekundid
- `seaded.json` – tekib ise; kasutaja eesmärk minutites

## Mis on algversioonis tehtud
- aktiivse aja mõõtmine (hiir + klaviatuur, 60 s tegevusetust ei loeta)
- andmete salvestamine CSV-faili
- päevase eesmärgi seadmine ja teavitus ületamisel
- statistika ja graafikud (päevad, nädalad)

## Plaanis
- automaatne käivitumine arvuti käivitamisel (ilma küsimata)
- ilusam teavitus (töölauateade)
- graafilise kasutajaliidese lisamine
