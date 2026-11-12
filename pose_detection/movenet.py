"""
Wrapper MoveNet pour la détection de pose en temps réel.

Charge le modèle MoveNet (Lightning ou Thunder) depuis TensorFlow Hub
et fournit une interface simple pour détecter les poses image par image.
"""

import numpy as np
import tensorflow as tf
from typing import Optional, Tuple

from pose_detection.keypoints import Keypoint


class MoveNetDetector:
    """
    Détecteur de pose utilisant MoveNet (single-person).

    Attributes:
        model_name: 'lightning' (rapide) ou 'thunder' (précis).
        min_confidence: Score minimum pour considérer un keypoint valide.
    """

    # URLs des modèles sur TensorFlow Hub
    MODEL_URLS = {
        "lightning": "https://tfhub.dev/google/movenet/singlepose/lightning/4",
        "thunder": "https://tfhub.dev/google/movenet/singlepose/thunder/4",
    }

    # Taille d'entrée attendue par chaque modèle
    INPUT_SIZES = {
        "lightning": 192,
        "thunder": 256,
    }

    def __init__(self, model_name: str = "lightning", min_confidence: float = 0.3):
        """
        Initialise le détecteur MoveNet.

        Args:
            model_name: 'lightning' ou 'thunder'.
            min_confidence: Score de confiance minimum (0.0 à 1.0).
        """
        if model_name not in self.MODEL_URLS:
            raise ValueError(f"Modèle inconnu: {model_name}. Utilisez 'lightning' ou 'thunder'.")

        self.model_name = model_name
        self.min_confidence = min_confidence
        self.input_size = self.INPUT_SIZES[model_name]

        # Charger le modèle
        print(f"[MoveNet] Chargement du modèle '{model_name}'...")
        self._module = tf.saved_model.load(
            tf.keras.utils.get_file(
                f"movenet_{model_name}",
                self.MODEL_URLS[model_name],
                untar=True,
            )
        )
        self._movenet = self._module.signatures["serving_default"]
        print(f"[MoveNet] Modèle '{model_name}' chargé avec succès.")

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

        # Redimensionner à la taille attendue
        input_image = tf.image.resize_with_pad(
            tf.expand_dims(rgb, axis=0),
            self.input_size,
            self.input_size,
        )
        input_image = tf.cast(input_image, dtype=tf.int32)

        # Inférence
        outputs = self._movenet(input_image)
        keypoints = outputs["output_0"].numpy().squeeze()  # (17, 3)

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
