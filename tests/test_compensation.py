"""
Tests unitaires pour le module analysis.compensation.

10 tests couvrant la détection des compensations :
calibration, détection, sévérité, résumé et réinitialisation.
"""

import pytest
import numpy as np

from analysis.compensation import (
    CompensationDetector, CompensationType, CompensationAlert,
)
from pose_detection.keypoints import Keypoint


class TestCalibration:
    """Tests de la calibration du détecteur."""

    def test_not_calibrated_returns_empty(self, sample_keypoints):
        """Sans calibration, check() retourne une liste vide."""
        detector = CompensationDetector()
        alerts = detector.check(sample_keypoints)
        assert alerts == [], "Sans calibration, aucune alerte ne devrait être émise"

    def test_calibrate_sets_baseline(self, sample_keypoints):
        """Après calibration, le détecteur est calibré."""
        detector = CompensationDetector()
        detector.calibrate(sample_keypoints)
        assert detector._calibrated is True, \
            "Après calibration, _calibrated devrait être True"
        assert detector._baseline_trunk_angle is not None


class TestCompensationDetection:
    """Tests de la détection de compensations."""

    def test_no_compensation_normal_posture(self, sample_keypoints):
        """Posture identique à la calibration : aucune alerte."""
        detector = CompensationDetector()
        detector.calibrate(sample_keypoints)
        alerts = detector.check(sample_keypoints)
        assert len(alerts) == 0, \
            f"Aucune compensation attendue avec une posture normale, obtenu {len(alerts)}"

    def test_trunk_lean_detected(self, sample_keypoints, sample_keypoints_leaning):
        """Inclinaison du tronc détectée quand la personne penche."""
        detector = CompensationDetector(trunk_threshold=5.0)
        detector.calibrate(sample_keypoints)

        alerts = detector.check(sample_keypoints_leaning)

        trunk_alerts = [a for a in alerts
                        if a.comp_type == CompensationType.TRUNK_LEAN]
        assert len(trunk_alerts) > 0, \
            "L'inclinaison du tronc devrait être détectée"

    def test_shoulder_elevation_detected(self, sample_keypoints):
        """Élévation d'épaule détectée quand une épaule monte."""
        detector = CompensationDetector(shoulder_threshold=0.02)
        detector.calibrate(sample_keypoints)

        # Modifier les keypoints : monter l'épaule gauche
        modified = sample_keypoints.copy()
        modified[Keypoint.LEFT_SHOULDER][0] -= 0.08  # Monter l'épaule de 8%

        alerts = detector.check(modified)
        shoulder_alerts = [a for a in alerts
                           if a.comp_type == CompensationType.SHOULDER_ELEVATION]
        assert len(shoulder_alerts) > 0, \
            "L'élévation de l'épaule devrait être détectée"

    def test_hip_shift_detected(self, sample_keypoints):
        """Décalage des hanches détecté quand les hanches bougent."""
        detector = CompensationDetector(hip_threshold=0.02)
        detector.calibrate(sample_keypoints)

        # Modifier : décaler les hanches latéralement
        modified = sample_keypoints.copy()
        modified[Keypoint.LEFT_HIP][1] += 0.05
        modified[Keypoint.RIGHT_HIP][1] += 0.05

        alerts = detector.check(modified)
        hip_alerts = [a for a in alerts
                      if a.comp_type == CompensationType.HIP_SHIFT]
        assert len(hip_alerts) > 0, \
            "Le décalage des hanches devrait être détecté"


class TestSeverity:
    """Tests de la classification de sévérité."""

    def test_severity_mild(self):
        """Petite déviation → sévérité 'mild'."""
        sev = CompensationDetector._classify_severity(12.0, 10.0)
        assert sev == "mild", f"Ratio 1.2x : sévérité 'mild' attendue, obtenu '{sev}'"

    def test_severity_moderate(self):
        """Déviation moyenne → sévérité 'moderate'."""
        sev = CompensationDetector._classify_severity(20.0, 10.0)
        assert sev == "moderate", f"Ratio 2.0x : sévérité 'moderate' attendue, obtenu '{sev}'"

    def test_severity_severe(self):
        """Grosse déviation → sévérité 'severe'."""
        sev = CompensationDetector._classify_severity(30.0, 10.0)
        assert sev == "severe", f"Ratio 3.0x : sévérité 'severe' attendue, obtenu '{sev}'"


class TestCompensationReset:
    """Tests de la réinitialisation et du résumé."""

    def test_reset_clears_state(self, sample_keypoints):
        """reset() efface toute la calibration et les alertes."""
        detector = CompensationDetector()
        detector.calibrate(sample_keypoints)
        detector.reset()

        assert detector._calibrated is False
        assert detector._baseline_trunk_angle is None
        assert len(detector.alerts) == 0

    def test_compensation_summary(self, sample_keypoints, sample_keypoints_leaning):
        """Le résumé agrège correctement les alertes."""
        detector = CompensationDetector(trunk_threshold=3.0)
        detector.calibrate(sample_keypoints)

        # Générer plusieurs alertes
        detector.check(sample_keypoints_leaning)
        detector.check(sample_keypoints_leaning)
        detector.check(sample_keypoints_leaning)

        summary = detector.get_compensation_summary()
        assert summary["total"] > 0, "Le résumé devrait avoir des alertes"
        assert isinstance(summary["types"], dict)
