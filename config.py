"""
Configuration globale du système Rehab Mirror.
Paramètres ajustables pour l'ensemble de l'application.
"""

# ─── Caméra ────────────────────────────────────────────────────────────────────
CAMERA_INDEX = 0          # Index de la webcam (0 = défaut)
CAMERA_WIDTH = 1280       # Résolution largeur
CAMERA_HEIGHT = 720       # Résolution hauteur
FPS_TARGET = 30           # Images par seconde cible

# ─── MoveNet ───────────────────────────────────────────────────────────────────
# "lightning" = rapide (recommandé pour temps réel)
# "thunder"   = plus précis mais plus lent
MOVENET_MODEL = "lightning"
MIN_CONFIDENCE = 0.3      # Score minimum de confiance pour un keypoint

# ─── Interface ─────────────────────────────────────────────────────────────────
WINDOW_TITLE = "Miroir de Rééducation"
FONT_SIZE_LARGE = 32      # Taille police pour les personnes âgées
FONT_SIZE_MEDIUM = 24
FONT_SIZE_SMALL = 18
COLOR_GOOD = "#4CAF50"    # Vert – mouvement correct
COLOR_WARNING = "#FF9800" # Orange – attention
COLOR_BAD = "#F44336"     # Rouge – erreur / compensation
COLOR_BG = "#1E1E2E"     # Fond sombre pour contraste
COLOR_TEXT = "#FFFFFF"    # Texte blanc

# ─── Exercices ─────────────────────────────────────────────────────────────────
# Seuils d'angles (en degrés) – ajustables par exercice
DEFAULT_ANGLE_TOLERANCE = 15   # Tolérance d'angle en degrés
REP_HOLD_FRAMES = 5           # Nb de frames pour valider une position
COMPENSATION_THRESHOLD = 10    # Degrés de déviation du tronc = compensation

# ─── Audio ─────────────────────────────────────────────────────────────────────
AUDIO_ENABLED = True
SPEECH_RATE = 130         # Vitesse de parole (lent pour personnes âgées)
SPEECH_LANG = "fr"        # Langue

# ─── Logging / Sessions ───────────────────────────────────────────────────────
SESSION_LOG_DIR = "data/sessions"
LOG_INTERVAL_SECONDS = 1  # Intervalle d'enregistrement des données
