"""
Détection des mouvements compensatoires.

Les compensations sont des mouvements parasites que le patient
effectue inconsciemment pour « tricher » un exercice. Par exemple :
- Pencher le tronc latéralement pour lever le bras plus haut
- Soulever l'épaule au lieu de fléchir le coude
- Rotation du bassin pour simuler une extension de jambe

Ce module détecte ces compensations en temps réel.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from enum import Enum, auto

from pose_detection.keypoints import Keypoint
from analysis.angles import trunk_lateral_angle


class CompensationType(Enum):
    """Types de compensations détectables."""
    TRUNK_LEAN = auto()          # Inclinaison latérale du tronc
    SHOULDER_ELEVATION = auto()  # Élévation de l'épaule (haussement)
    HIP_SHIFT = auto()           # Décalage latéral des hanches
    TRUNK_ROTATION = auto()      # Rotation du tronc
    HEAD_TILT = auto()           # Inclinaison de la tête


@dataclass
class CompensationAlert:
    """Alerte de compensation détectée."""
    comp_type: CompensationType
    severity: str         # "mild", "moderate", "severe"
    message: str          # Message pour l'utilisateur (en français)
    deviation: float      # Déviation mesurée en degrés ou unités
    timestamp: float = 0.0


@dataclass
class CompensationDetector:
    """
    Détecte les mouvements compensatoires pendant les exercices.

    Attributes:
        trunk_threshold: Déviation du tronc (degrés) déclenchant une alerte.
        shoulder_threshold: Différence de hauteur des épaules (normalisée).
        hip_threshold: Décalage latéral des hanches (normalisé).
    """
    trunk_threshold: float = 10.0
    shoulder_threshold: float = 0.03   # 3% de la hauteur de l'image
    hip_threshold: float = 0.03

    # Référence de posture initiale
    _baseline_trunk_angle: Optional[float] = field(default=None, init=False)
    _baseline_shoulder_diff: Optional[float] = field(default=None, init=False)
    _baseline_hip_center_x: Optional[float] = field(default=None, init=False)
    _calibrated: bool = field(default=False, init=False)

    # Historique des alertes
    alerts: List[CompensationAlert] = field(default_factory=list, init=False)

    def calibrate(self, keypoints: np.ndarray):
        """
        Enregistre la posture de référence du patient.

        Doit être appelé au début de l'exercice, quand le patient
        est bien positionné.

        Args:
            keypoints: Keypoints MoveNet (17, 3) en position neutre.
        """
        # Angle du tronc de référence
        self._baseline_trunk_angle = trunk_lateral_angle(keypoints)

        # Différence de hauteur des épaules
        left_sh = keypoints[Keypoint.LEFT_SHOULDER]
        right_sh = keypoints[Keypoint.RIGHT_SHOULDER]
        if left_sh[2] > 0.3 and right_sh[2] > 0.3:
            self._baseline_shoulder_diff = left_sh[0] - right_sh[0]

        # Centre des hanches (position x)
        left_hip = keypoints[Keypoint.LEFT_HIP]
        right_hip = keypoints[Keypoint.RIGHT_HIP]
        if left_hip[2] > 0.3 and right_hip[2] > 0.3:
            self._baseline_hip_center_x = (left_hip[1] + right_hip[1]) / 2

        self._calibrated = True
        print("[Compensation] Posture de référence enregistrée.")

    def check(self, keypoints: np.ndarray) -> List[CompensationAlert]:
        """
        Vérifie les compensations sur la frame actuelle.

        Args:
            keypoints: Keypoints MoveNet (17, 3) de la frame courante.

        Returns:
            Liste des alertes de compensation détectées.
        """
        if not self._calibrated:
            return []

        current_alerts = []

        # 1. Inclinaison du tronc
        alert = self._check_trunk_lean(keypoints)
        if alert:
            current_alerts.append(alert)

        # 2. Élévation de l'épaule
        alert = self._check_shoulder_elevation(keypoints)
        if alert:
            current_alerts.append(alert)

        # 3. Décalage des hanches
        alert = self._check_hip_shift(keypoints)
        if alert:
            current_alerts.append(alert)

        self.alerts.extend(current_alerts)
        return current_alerts

    def _check_trunk_lean(self, keypoints: np.ndarray) -> Optional[CompensationAlert]:
        """Vérifie l'inclinaison latérale du tronc."""
        if self._baseline_trunk_angle is None:
            return None

        current_angle = trunk_lateral_angle(keypoints)
        if current_angle is None:
            return None

        deviation = abs(current_angle - self._baseline_trunk_angle)

        if deviation < self.trunk_threshold:
            return None

        severity = self._classify_severity(deviation, self.trunk_threshold)
        return CompensationAlert(
            comp_type=CompensationType.TRUNK_LEAN,
            severity=severity,
            message=self._trunk_message(severity),
            deviation=deviation,
        )

    def _check_shoulder_elevation(
        self, keypoints: np.ndarray
    ) -> Optional[CompensationAlert]:
        """Vérifie si une épaule est anormalement surélevée."""
        if self._baseline_shoulder_diff is None:
            return None

        left_sh = keypoints[Keypoint.LEFT_SHOULDER]
        right_sh = keypoints[Keypoint.RIGHT_SHOULDER]

        if left_sh[2] < 0.3 or right_sh[2] < 0.3:
            return None

        current_diff = left_sh[0] - right_sh[0]
        deviation = abs(current_diff - self._baseline_shoulder_diff)

        if deviation < self.shoulder_threshold:
            return None

        severity = self._classify_severity(
            deviation, self.shoulder_threshold
        )
        return CompensationAlert(
            comp_type=CompensationType.SHOULDER_ELEVATION,
            severity=severity,
            message=self._shoulder_message(severity),
            deviation=deviation,
        )

    def _check_hip_shift(
        self, keypoints: np.ndarray
    ) -> Optional[CompensationAlert]:
        """Vérifie le décalage latéral des hanches."""
        if self._baseline_hip_center_x is None:
            return None

        left_hip = keypoints[Keypoint.LEFT_HIP]
        right_hip = keypoints[Keypoint.RIGHT_HIP]

        if left_hip[2] < 0.3 or right_hip[2] < 0.3:
            return None

        current_center_x = (left_hip[1] + right_hip[1]) / 2
        deviation = abs(current_center_x - self._baseline_hip_center_x)

        if deviation < self.hip_threshold:
            return None

        severity = self._classify_severity(deviation, self.hip_threshold)
        return CompensationAlert(
            comp_type=CompensationType.HIP_SHIFT,
            severity=severity,
            message=self._hip_message(severity),
            deviation=deviation,
        )

    @staticmethod
    def _classify_severity(deviation: float, threshold: float) -> str:
        """Classifie la sévérité d'une compensation."""
        ratio = deviation / threshold
        if ratio < 1.5:
            return "mild"
        elif ratio < 2.5:
            return "moderate"
        return "severe"

    @staticmethod
    def _trunk_message(severity: str) -> str:
        """Message d'alerte pour l'inclinaison du tronc."""
        messages = {
            "mild": "Attention : gardez le dos droit",
            "moderate": "⚠ Vous penchez le corps — redressez-vous",
            "severe": "⛔ Trop d'inclinaison ! Revenez au centre",
        }
        return messages.get(severity, messages["mild"])

    @staticmethod
    def _shoulder_message(severity: str) -> str:
        """Message d'alerte pour l'élévation de l'épaule."""
        messages = {
            "mild": "Détendez votre épaule, ne la montez pas",
            "moderate": "⚠ Épaule trop haute — relâchez-la",
            "severe": "⛔ Gardez l'épaule basse et détendue",
        }
        return messages.get(severity, messages["mild"])

    @staticmethod
    def _hip_message(severity: str) -> str:
        """Message d'alerte pour le décalage des hanches."""
        messages = {
            "mild": "Gardez vos hanches bien centrées",
            "moderate": "⚠ Vos hanches se décalent — recentrez-vous",
            "severe": "⛔ Repositionnez vos hanches au centre",
        }
        return messages.get(severity, messages["mild"])

    def reset(self):
        """Réinitialise le détecteur."""
        self._baseline_trunk_angle = None
        self._baseline_shoulder_diff = None
        self._baseline_hip_center_x = None
        self._calibrated = False
        self.alerts.clear()

    def get_compensation_summary(self) -> dict:
        """Résumé des compensations détectées pendant la session."""
        if not self.alerts:
            return {"total": 0, "types": {}}

        summary = {
            "total": len(self.alerts),
            "types": {},
        }
        for alert in self.alerts:
            name = alert.comp_type.name
            if name not in summary["types"]:
                summary["types"][name] = {"count": 0, "max_severity": "mild"}
            summary["types"][name]["count"] += 1
            # Mettre à jour la sévérité max
            severity_order = {"mild": 0, "moderate": 1, "severe": 2}
            current_max = summary["types"][name]["max_severity"]
            if severity_order[alert.severity] > severity_order[current_max]:
                summary["types"][name]["max_severity"] = alert.severity

        return summary
