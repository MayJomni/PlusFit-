"""
Wrapper MoveNet pour la détection de pose en temps réel.

Utilise le modèle MoveNet Lightning en format TFLite (local),
sans nécessiter de connexion internet au démarrage.
"""

import os
import numpy as np
import tensorflow as tf
from typing import Optional, Tuple

from pose_detection.keypoints import Keypoint

# Chemin local du modèle TFLite
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODEL_PATH = os.path.join(_BASE_DIR, "models", "movenet_lightning.tflite")
_MODEL_URL = "https://tfhub.dev/google/lite-model/movenet/singlepose/lightning/tflite/float16/4?lite-format=tflite"


def _ensure_model():
    """Télécharge le modèle TFLite s'il n'est pas déjà présent."""
    if os.path.exists(_MODEL_PATH) and os.path.getsize(_MODEL_PATH) > 100_000:
        return  # déjà présent

    os.makedirs(os.path.dirname(_MODEL_PATH), exist_ok=True)
    print(f"[MoveNet] Téléchargement du modèle TFLite...")
    try:
        import requests
        r = requests.get(_MODEL_URL, headers={"User-Agent": "Mozilla/5.0"},
                         allow_redirects=True, timeout=60)
        if r.status_code == 200 and len(r.content) > 100_000:
            with open(_MODEL_PATH, "wb") as f:
                f.write(r.content)
            print(f"[MoveNet] Modèle sauvegardé ({len(r.content)//1024} KB)")
        else:
            raise RuntimeError(f"Téléchargement échoué: HTTP {r.status_code}")
    except Exception as e:
        raise RuntimeError(
            f"Impossible de télécharger MoveNet TFLite.\n"
            f"Vérifiez votre connexion internet.\nErreur: {e}"
        )


class MoveNetDetector:
    """
    Détecteur de pose utilisant MoveNet Lightning (TFLite).

    Utilise le modèle local `models/movenet_lightning.tflite`.
    Plus rapide et ne nécessite pas de connexion internet au démarrage.

    Attributes:
        min_confidence: Score minimum pour considérer un keypoint valide.
    """

    # Taille d'entrée MoveNet Lightning
    INPUT_SIZE = 192

    def __init__(self, model_name: str = "lightning", min_confidence: float = 0.3):
        """
        Initialise le détecteur MoveNet TFLite.

        Args:
            model_name: ignoré (toujours lightning TFLite).
            min_confidence: Score de confiance minimum (0.0 à 1.0).
        """
        self.model_name = model_name
        self.min_confidence = min_confidence
        self.input_size = self.INPUT_SIZE

        # S'assurer que le modèle est disponible localement
        _ensure_model()

        # Charger l'interpréteur TFLite
        print(f"[MoveNet] Chargement du modèle TFLite depuis {_MODEL_PATH}...")
        self._interpreter = tf.lite.Interpreter(model_path=_MODEL_PATH)
        self._interpreter.allocate_tensors()

        # Récupérer les indices d'entrée/sortie
        self._input_details = self._interpreter.get_input_details()
        self._output_details = self._interpreter.get_output_details()

        print("[MoveNet] Modèle TFLite prêt ✓")

        # Cache du dernier résultat
        self._last_keypoints: Optional[np.ndarray] = None

    def detect(self, frame: np.ndarray) -> np.ndarray:
        """
        Détecte la pose dans une image.

        Args:
            frame: Image BGR (OpenCV) de forme (H, W, 3).

        Returns:
            Array (17, 3) avec [y, x, confidence] pour chaque keypoint.
            Les coordonnées y et x sont normalisées entre 0 et 1.
        """
        # Convertir BGR → RGB
        rgb = frame[:, :, ::-1]

        # Redimensionner à 192×192
        input_image = tf.image.resize_with_pad(
            tf.expand_dims(rgb, axis=0),
            self.INPUT_SIZE,
            self.INPUT_SIZE,
        )

        # Le modèle TFLite float16 attend des uint8
        input_data = tf.cast(input_image, dtype=tf.uint8).numpy()

        # Inférence TFLite
        self._interpreter.set_tensor(self._input_details[0]['index'], input_data)
        self._interpreter.invoke()

        # Résultat : (1, 1, 17, 3)
        keypoints_raw = self._interpreter.get_tensor(
            self._output_details[0]['index']
        )
        keypoints = keypoints_raw.squeeze()  # → (17, 3)

        self._last_keypoints = keypoints
        return keypoints

    def get_keypoint(
        self, keypoints: np.ndarray, kp: Keypoint
    ) -> Tuple[float, float, float]:
        """
        Récupère un keypoint spécifique.

        Args:
            keypoints: Résultat de detect() – array (17, 3).
            kp: Le keypoint voulu (enum Keypoint).

        Returns:
            Tuple (y, x, confidence). Coordonnées normalisées [0, 1].
        """
        y, x, conf = keypoints[kp.value]
        return float(y), float(x), float(conf)

    def get_pixel_coords(
        self,
        keypoints: np.ndarray,
        kp: Keypoint,
        frame_height: int,
        frame_width: int,
    ) -> Tuple[int, int, float]:
        """
        Convertit les coordonnées normalisées en pixels.

        Args:
            keypoints: Résultat de detect().
            kp: Le keypoint voulu.
            frame_height: Hauteur de l'image en pixels.
            frame_width: Largeur de l'image en pixels.

        Returns:
            Tuple (px_x, px_y, confidence). Coordonnées en pixels.
        """
        y, x, conf = self.get_keypoint(keypoints, kp)
        px_x = int(x * frame_width)
        px_y = int(y * frame_height)
        return px_x, px_y, conf

    def is_visible(self, keypoints: np.ndarray, kp: Keypoint) -> bool:
        """Vérifie si un keypoint est détecté avec assez de confiance."""
        _, _, conf = self.get_keypoint(keypoints, kp)
        return conf >= self.min_confidence

    def get_visible_keypoints(self, keypoints: np.ndarray) -> dict:
        """
        Retourne uniquement les keypoints visibles (confiance suffisante).

        Returns:
            Dict {Keypoint: (y, x, confidence)} pour les points visibles.
        """
        visible = {}
        for kp in Keypoint:
            y, x, conf = self.get_keypoint(keypoints, kp)
            if conf >= self.min_confidence:
                visible[kp] = (y, x, conf)
        return visible
