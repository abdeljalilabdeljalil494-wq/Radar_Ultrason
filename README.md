# Radar ultrason HC-SR04 (Arduino + Python)

## Câblage
| HC-SR04 | Arduino |
|---|---|
| VCC | 5V |
| GND | GND |
| Trig | D9 |
| Echo | D10 |

SG90 (option radar) : signal D6, rouge 5V, marron GND.

## Étapes
1. Ouvrir `radar_ultrason.ino` dans l'Arduino IDE, téléverser (9600 baud).
   Pour le radar 180° : mettre `RADAR_MODE = true`.
2. `pip install pygame pyserial`
3. Fermer le Moniteur Série de l'IDE (il bloque le port).
4. `python radar_ultrason.py --port COM3` (ou sans `--port` pour l'auto-détection).
   Test sans matériel : `python radar_ultrason.py --sim`

## Seuils
- Vert > 30 cm, orange 15-30 cm, rouge < 15 cm + alerte clignotante.

## Étalonnage (Phase 5)
Place un obstacle plat à 10, 20, 50, 100, 200 cm (mètre ruban) et note l'erreur.
Si l'erreur est constante, ajuste le facteur 0.034 (vitesse du son ≈ 343 m/s
à 20 °C : 0.0343 cm/µs).
