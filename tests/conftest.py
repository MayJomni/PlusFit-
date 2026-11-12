"""
Fixtures partagées pour les tests unitaires.

Fournit des arrays numpy simulant des keypoints MoveNet
dans différentes postures, sans avoir besoin de TensorFlow
ni de webcam.
"""

import os
import sys
import pytest
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_keypoints():
    """Personne debout, bras le long du corps."""
    return np.array([
        [0.15, 0.50, 0.95],  # 0  NOSE
        [0.14, 0.48, 0.90],  # 1  LEFT_EYE
        [0.14, 0.52, 0.90],  # 2  RIGHT_EYE
        [0.15, 0.45, 0.85],  # 3  LEFT_EAR
        [0.15, 0.55, 0.85],  # 4  RIGHT_EAR
        [0.25, 0.40, 0.95],  # 5  LEFT_SHOULDER
        [0.25, 0.60, 0.95],  # 6  RIGHT_SHOULDER
        [0.38, 0.35, 0.90],  # 7  LEFT_ELBOW
        [0.38, 0.65, 0.90],  # 8  RIGHT_ELBOW
        [0.50, 0.33, 0.90],  # 9  LEFT_WRIST
        [0.50, 0.67, 0.90],  # 10 RIGHT_WRIST
        [0.55, 0.43, 0.95],  # 11 LEFT_HIP
        [0.55, 0.57, 0.95],  # 12 RIGHT_HIP
        [0.72, 0.42, 0.90],  # 13 LEFT_KNEE
        [0.72, 0.58, 0.90],  # 14 RIGHT_KNEE
        [0.90, 0.41, 0.85],  # 15 LEFT_ANKLE
        [0.90, 0.59, 0.85],  # 16 RIGHT_ANKLE
    ], dtype=np.float32)


@pytest.fixture
def sample_keypoints_arm_raised():
    """Personne debout, bras gauche levé à ~150°."""
    return np.array([
        [0.15, 0.50, 0.95],
        [0.14, 0.48, 0.90],
        [0.14, 0.52, 0.90],
        [0.15, 0.45, 0.85],
        [0.15, 0.55, 0.85],
        [0.25, 0.40, 0.95],  # LEFT_SHOULDER
        [0.25, 0.60, 0.95],
        [0.12, 0.38, 0.90],  # LEFT_ELBOW (levé)
        [0.38, 0.65, 0.90],
        [0.05, 0.40, 0.90],  # LEFT_WRIST (très haut)
        [0.50, 0.67, 0.90],
        [0.55, 0.43, 0.95],
        [0.55, 0.57, 0.95],
        [0.72, 0.42, 0.90],
        [0.72, 0.58, 0.90],
        [0.90, 0.41, 0.85],
        [0.90, 0.59, 0.85],
    ], dtype=np.float32)


@pytest.fixture
def sample_keypoints_arm_half():
    """Personne debout, bras gauche à mi-chemin (~90°)."""
    return np.array([
        [0.15, 0.50, 0.95],
        [0.14, 0.48, 0.90],
        [0.14, 0.52, 0.90],
        [0.15, 0.45, 0.85],
        [0.15, 0.55, 0.85],
        [0.25, 0.40, 0.95],
        [0.25, 0.60, 0.95],
        [0.25, 0.25, 0.90],  # LEFT_ELBOW (horizontal)
        [0.38, 0.65, 0.90],
        [0.25, 0.10, 0.90],  # LEFT_WRIST (tendu côté)
        [0.50, 0.67, 0.90],
        [0.55, 0.43, 0.95],
        [0.55, 0.57, 0.95],
        [0.72, 0.42, 0.90],
        [0.72, 0.58, 0.90],
        [0.90, 0.41, 0.85],
        [0.90, 0.59, 0.85],
    ], dtype=np.float32)


@pytest.fixture
def sample_keypoints_leaning():
    """Personne penchée sur le côté (tronc incliné ~15°)."""
    return np.array([
        [0.15, 0.55, 0.95],
        [0.14, 0.53, 0.90],
        [0.14, 0.57, 0.90],
        [0.15, 0.50, 0.85],
        [0.15, 0.60, 0.85],
        [0.25, 0.47, 0.95],  # LEFT_SHOULDER (décalée)
        [0.25, 0.67, 0.95],  # RIGHT_SHOULDER (décalée)
        [0.38, 0.42, 0.90],
        [0.38, 0.72, 0.90],
        [0.50, 0.40, 0.90],
        [0.50, 0.74, 0.90],
        [0.55, 0.43, 0.95],  # LEFT_HIP (centrée)
        [0.55, 0.57, 0.95],  # RIGHT_HIP (centrée)
        [0.72, 0.42, 0.90],
        [0.72, 0.58, 0.90],
        [0.90, 0.41, 0.85],
        [0.90, 0.59, 0.85],
    ], dtype=np.float32)


@pytest.fixture
def sample_keypoints_low_confidence():
    """Keypoints avec certains points à faible confiance (< 0.3)."""
    return np.array([
        [0.15, 0.50, 0.95],  # NOSE
        [0.14, 0.48, 0.10],  # LEFT_EYE - invisible
        [0.14, 0.52, 0.10],  # RIGHT_EYE - invisible
        [0.15, 0.45, 0.05],  # LEFT_EAR - invisible
        [0.15, 0.55, 0.05],  # RIGHT_EAR - invisible
        [0.25, 0.40, 0.95],  # LEFT_SHOULDER
        [0.25, 0.60, 0.95],  # RIGHT_SHOULDER
        [0.38, 0.35, 0.90],  # LEFT_ELBOW
        [0.38, 0.65, 0.15],  # RIGHT_ELBOW - invisible
        [0.50, 0.33, 0.90],  # LEFT_WRIST
        [0.50, 0.67, 0.10],  # RIGHT_WRIST - invisible
        [0.55, 0.43, 0.95],  # LEFT_HIP
        [0.55, 0.57, 0.95],  # RIGHT_HIP
        [0.72, 0.42, 0.20],  # LEFT_KNEE - invisible
        [0.72, 0.58, 0.20],  # RIGHT_KNEE - invisible
        [0.90, 0.41, 0.10],  # LEFT_ANKLE - invisible
        [0.90, 0.59, 0.10],  # RIGHT_ANKLE - invisible
    ], dtype=np.float32)


@pytest.fixture
def tmp_session_dir(tmp_path):
    """Dossier temporaire pour les sessions de test."""
    d = tmp_path / "sessions"
    d.mkdir()
    return str(d)
