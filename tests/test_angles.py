"""
Tests unitaires pour le module analysis.angles.

15 tests couvrant le calcul d'angles articulaires,
les fonctions utilitaires et les cas limites.
"""

import pytest
import numpy as np

from analysis.angles import (
    calculate_angle, get_joint_angle,
    elbow_angle_left, elbow_angle_right,
    shoulder_angle_left, shoulder_angle_right,
    knee_angle_left, hip_angle_left,
    trunk_lateral_angle,
)
from pose_detection.keypoints import Keypoint


class TestCalculateAngle:
    """Tests pour la fonction calculate_angle."""

    def test_straight_line_180(self):
        """Trois points alignés horizontalement donnent 180°."""
        a = (0.0, 0.0)
        b = (0.0, 0.5)
        c = (0.0, 1.0)
        angle = calculate_angle(a, b, c)
        assert angle == pytest.approx(180.0, abs=1.0), \
            f"3 points alignés devraient donner ~180°, obtenu {angle}°"

    def test_right_angle_90(self):
        """Un angle droit donne 90°."""
        a = (0.0, 0.0)
        b = (0.0, 0.5)
        c = (0.5, 0.5)
        angle = calculate_angle(a, b, c)
        assert angle == pytest.approx(90.0, abs=1.0), \
            f"Un angle droit devrait donner ~90°, obtenu {angle}°"

    def test_acute_angle(self):
        """Un angle aigu donne < 90°."""
        # Vecteurs BA et BC proches → angle aigu
        a = (0.0, 0.5)   # au-dessus de B
        b = (0.5, 0.5)   # sommet
        c = (0.0, 0.6)   # au-dessus de B, légèrement à droite
        angle = calculate_angle(a, b, c)
        assert 0 < angle < 90, f"Angle aigu attendu, obtenu {angle}°"

    def test_obtuse_angle(self):
        """Un angle obtus donne > 90°."""
        a = (0.0, 0.2)
        b = (0.0, 0.5)
        c = (0.1, 0.8)
        angle = calculate_angle(a, b, c)
        assert 90 < angle < 180, f"Angle obtus attendu, obtenu {angle}°"

    def test_zero_length_vectors(self):
        """Points confondus retournent 0°."""
        a = (0.5, 0.5)
        b = (0.5, 0.5)
        c = (0.5, 0.5)
        angle = calculate_angle(a, b, c)
        assert angle == pytest.approx(0.0, abs=0.1), \
            "Points confondus devraient donner 0°"

    def test_symmetry(self):
        """L'angle est le même en inversant A et C."""
        a = (0.0, 0.0)
        b = (0.5, 0.5)
        c = (1.0, 0.0)
        angle_1 = calculate_angle(a, b, c)
        angle_2 = calculate_angle(c, b, a)
        assert angle_1 == pytest.approx(angle_2, abs=0.01), \
            "L'angle devrait être identique en inversant A et C"


class TestGetJointAngle:
    """Tests pour get_joint_angle avec les keypoints MoveNet."""

    def test_visible_keypoints(self, sample_keypoints):
        """Trois keypoints visibles retournent un angle valide."""
        angle = get_joint_angle(
            sample_keypoints,
            Keypoint.LEFT_SHOULDER, Keypoint.LEFT_ELBOW, Keypoint.LEFT_WRIST,
        )
        assert angle is not None, "L'angle devrait être calculé"
        assert 0 < angle < 180, f"L'angle devrait être entre 0 et 180, obtenu {angle}"

    def test_hidden_keypoint_returns_none(self, sample_keypoints_low_confidence):
        """Un keypoint invisible (confiance < 0.3) retourne None."""
        angle = get_joint_angle(
            sample_keypoints_low_confidence,
            Keypoint.RIGHT_SHOULDER, Keypoint.RIGHT_ELBOW, Keypoint.RIGHT_WRIST,
            min_confidence=0.3,
        )
        assert angle is None, \
            "L'angle devrait être None quand un keypoint est invisible"


class TestSpecificAngles:
    """Tests pour les fonctions d'angles spécifiques."""

    def test_elbow_angle_left(self, sample_keypoints):
        """L'angle du coude gauche est calculable."""
        angle = elbow_angle_left(sample_keypoints)
        assert angle is not None
        assert 0 < angle < 180

    def test_elbow_angle_right(self, sample_keypoints):
        """L'angle du coude droit est calculable."""
        angle = elbow_angle_right(sample_keypoints)
        assert angle is not None
        assert 0 < angle < 180

    def test_shoulder_angle_left_arm_down(self, sample_keypoints):
        """Épaule gauche avec bras le long du corps : angle petit."""
        angle = shoulder_angle_left(sample_keypoints)
        assert angle is not None
        assert angle < 60, f"Bras le long du corps : angle épaule < 60°, obtenu {angle}°"

    def test_shoulder_angle_left_arm_raised(self, sample_keypoints_arm_raised):
        """Épaule gauche avec bras levé : angle grand."""
        angle = shoulder_angle_left(sample_keypoints_arm_raised)
        assert angle is not None
        assert angle > 100, f"Bras levé : angle épaule > 100°, obtenu {angle}°"

    def test_shoulder_angle_right(self, sample_keypoints):
        """L'angle de l'épaule droite est calculable."""
        angle = shoulder_angle_right(sample_keypoints)
        assert angle is not None

    def test_knee_angle_left(self, sample_keypoints):
        """L'angle du genou gauche est calculable."""
        angle = knee_angle_left(sample_keypoints)
        assert angle is not None
        assert 0 < angle < 180

    def test_hip_angle_left(self, sample_keypoints):
        """L'angle de la hanche gauche est calculable."""
        angle = hip_angle_left(sample_keypoints)
        assert angle is not None
        assert 0 < angle < 180


class TestTrunkAngle:
    """Tests pour l'inclinaison du tronc."""

    def test_trunk_straight(self, sample_keypoints):
        """Personne droite : inclinaison du tronc < 5°."""
        angle = trunk_lateral_angle(sample_keypoints)
        assert angle is not None
        assert angle < 8, f"Personne droite : inclinaison < 8°, obtenu {angle}°"

    def test_trunk_leaning(self, sample_keypoints_leaning):
        """Personne penchée : inclinaison du tronc > 5°."""
        angle = trunk_lateral_angle(sample_keypoints_leaning)
        assert angle is not None
        assert angle > 5, f"Personne penchée : inclinaison > 5°, obtenu {angle}°"
