"""
Comptage automatique des répétitions.

Utilise une machine à états pour détecter les cycles de mouvement
(position de départ → position cible → retour) et compter les
répétitions de manière fiable.
"""

import time
from enum import Enum, auto
from typing import Optional, Callable, List
from dataclasses import dataclass, field

import numpy as np


class RepState(Enum):
    """États du cycle de répétition."""
    IDLE = auto()       # En attente du début
    GOING_UP = auto()   # Mouvement vers la position cible
    AT_TOP = auto()     # Position cible atteinte
    GOING_DOWN = auto() # Retour à la position de départ
    COMPLETED = auto()  # Répétition terminée


@dataclass
class RepCounter:
    """
    Compteur de répétitions basé sur l'angle d'une articulation.

    Le compteur suit un cycle :
    1. L'angle descend sous le seuil bas → début du mouvement
    2. L'angle monte au-dessus du seuil haut → position atteinte
    3. L'angle redescend sous le seuil bas → répétition complète

    Attributes:
        angle_start: Angle de la position de repos (ex: bras le long du corps ≈ 20°).
        angle_target: Angle de la position cible (ex: bras levé ≈ 160°).
        tolerance: Marge de tolérance en degrés.
        hold_frames: Nombre de frames minimum en position cible.
    """
    angle_start: float
    angle_target: float
    tolerance: float = 15.0
    hold_frames: int = 5

    # État interne
    state: RepState = field(default=RepState.IDLE, init=False)
    count: int = field(default=0, init=False)
    hold_counter: int = field(default=0, init=False)
    max_angle_reached: float = field(default=0.0, init=False)
    min_angle_reached: float = field(default=180.0, init=False)
    rep_history: List[dict] = field(default_factory=list, init=False)
    _rep_start_time: Optional[float] = field(default=None, init=False)

    @property
    def going_up(self) -> bool:
        """Est-ce que l'angle cible est plus grand que l'angle de départ ?"""
        return self.angle_target > self.angle_start

    @property
    def threshold_low(self) -> float:
        """Seuil bas pour considérer le retour à la position de repos."""
        if self.going_up:
            return self.angle_start + self.tolerance
        return self.angle_start - self.tolerance

    @property
    def threshold_high(self) -> float:
        """Seuil haut pour considérer que la position cible est atteinte."""
        if self.going_up:
            return self.angle_target - self.tolerance
        return self.angle_target + self.tolerance

    def update(self, current_angle: Optional[float]) -> Optional[int]:
        """
        Met à jour le compteur avec l'angle actuel.

        Args:
            current_angle: Angle articulaire actuel en degrés.
                          None si le keypoint n'est pas visible.

        Returns:
            Le numéro de la nouvelle répétition si une vient d'être
            complétée, None sinon.
        """
        if current_angle is None:
            return None

        completed_rep = None

        if self.going_up:
            completed_rep = self._update_going_up(current_angle)
        else:
            completed_rep = self._update_going_down(current_angle)

        # Tracker les amplitudes
        self.max_angle_reached = max(self.max_angle_reached, current_angle)
        self.min_angle_reached = min(self.min_angle_reached, current_angle)

        return completed_rep

    def _update_going_up(self, angle: float) -> Optional[int]:
        """Logique pour les exercices où l'angle augmente (ex: lever le bras)."""
        if self.state == RepState.IDLE:
            if angle <= self.threshold_low:
                self.state = RepState.GOING_UP
                self._rep_start_time = time.time()
                self.max_angle_reached = angle
                self.min_angle_reached = angle

        elif self.state == RepState.GOING_UP:
            if angle >= self.threshold_high:
                self.state = RepState.AT_TOP
                self.hold_counter = 0

        elif self.state == RepState.AT_TOP:
            if angle >= self.threshold_high:
                self.hold_counter += 1
                if self.hold_counter >= self.hold_frames:
                    self.state = RepState.GOING_DOWN
            else:
                # Retombé trop vite, on recommence
                self.state = RepState.GOING_UP

        elif self.state == RepState.GOING_DOWN:
            if angle <= self.threshold_low:
                return self._complete_rep()

        return None

    def _update_going_down(self, angle: float) -> Optional[int]:
        """Logique pour les exercices où l'angle diminue (ex: flexion du genou)."""
        if self.state == RepState.IDLE:
            if angle >= self.threshold_low:
                self.state = RepState.GOING_UP
                self._rep_start_time = time.time()
                self.max_angle_reached = angle
                self.min_angle_reached = angle

        elif self.state == RepState.GOING_UP:
            if angle <= self.threshold_high:
                self.state = RepState.AT_TOP
                self.hold_counter = 0

        elif self.state == RepState.AT_TOP:
            if angle <= self.threshold_high:
                self.hold_counter += 1
                if self.hold_counter >= self.hold_frames:
                    self.state = RepState.GOING_DOWN
            else:
                self.state = RepState.GOING_UP

        elif self.state == RepState.GOING_DOWN:
            if angle >= self.threshold_low:
                return self._complete_rep()

        return None

    def _complete_rep(self) -> int:
        """Enregistre une répétition complète."""
        self.count += 1
        duration = time.time() - self._rep_start_time if self._rep_start_time else 0

        self.rep_history.append({
            "rep_number": self.count,
            "max_angle": self.max_angle_reached,
            "min_angle": self.min_angle_reached,
            "amplitude": abs(self.max_angle_reached - self.min_angle_reached),
            "duration_seconds": round(duration, 2),
            "timestamp": time.time(),
        })

        # Réinitialiser pour la prochaine rep
        self.state = RepState.IDLE
        self.hold_counter = 0
        self.max_angle_reached = 0.0
        self.min_angle_reached = 180.0
        self._rep_start_time = None

        return self.count

    def reset(self):
        """Remet le compteur à zéro."""
        self.state = RepState.IDLE
        self.count = 0
        self.hold_counter = 0
        self.max_angle_reached = 0.0
        self.min_angle_reached = 180.0
        self.rep_history.clear()
        self._rep_start_time = None

    def get_progress_pct(self, current_angle: Optional[float]) -> float:
        """
        Pourcentage de progression vers la position cible (0% → 100%).

        Args:
            current_angle: Angle actuel.

        Returns:
            Pourcentage entre 0.0 et 100.0.
        """
        if current_angle is None:
            return 0.0

        total_range = abs(self.angle_target - self.angle_start)
        if total_range < 1e-6:
            return 0.0

        current_progress = abs(current_angle - self.angle_start)
        pct = (current_progress / total_range) * 100.0
        return max(0.0, min(100.0, pct))

    def get_avg_amplitude(self) -> float:
        """Amplitude moyenne sur toutes les répétitions effectuées."""
        if not self.rep_history:
            return 0.0
        return sum(r["amplitude"] for r in self.rep_history) / len(self.rep_history)
