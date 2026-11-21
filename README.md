# Radar ultrason HC-SR04 (Arduino + Python)

Radar à ultrasons en temps réel. L'Arduino mesure la distance avec un HC-SR04
(optionnel : balayage 0-180° avec un servo SG90) et l'envoie par port série.
Une interface Pygame affiche le radar, une jauge de proximité et une alerte
clignotante quand un obstacle est à moins de 15 cm.

## Fonctionnalités
- Mesure de distance 2 cm - 4 m
- Mode radar 180° (servo) ou mode jauge
- Filtre médian contre le bruit
- Alerte collision (vert / orange / rouge)
- Mode simulation sans matériel (`--sim`)
