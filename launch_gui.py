"""
Script de lancement propre de la GUI — force le rechargement TFLite.
"""
import sys
import os

# S'assurer qu'on est dans le bon répertoire
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

# Vérification préalable du modèle TFLite
model_path = os.path.join(BASE_DIR, "models", "movenet_lightning.tflite")
if os.path.exists(model_path):
    size_kb = os.path.getsize(model_path) // 1024
    print(f"[OK] Modele TFLite trouve : {model_path} ({size_kb} KB)")
else:
    print(f"[ERREUR] Modele manquant : {model_path}")
    sys.exit(1)

# Test rapide du detecteur avant de lancer la GUI
print("[...] Test du detecteur MoveNet...")
try:
    import numpy as np
    from pose_detection.movenet import MoveNetDetector
    det = MoveNetDetector()
    # Test avec une image noire 192x192
    fake_frame = np.zeros((192, 192, 3), dtype=np.uint8)
    kps = det.detect(fake_frame)
    assert kps.shape == (17, 3), f"Forme inattendue: {kps.shape}"
    print(f"[OK] Detecteur TFLite operationnel - keypoints shape: {kps.shape}")
    del det
except Exception as e:
    print(f"[ERREUR] Detecteur: {e}")
    sys.exit(1)

# Lancer la GUI
print("[...] Lancement de la GUI...")
from ui.app_gui import RehabMirrorGUI
app = RehabMirrorGUI()
app.run()
