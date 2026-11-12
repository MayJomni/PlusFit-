"""
Tests unitaires pour le module analysis.repetitions.

12 tests couvrant le compteur de répétitions : machine à états,
comptage, progression, amplitude, et cas limites.
"""

import pytest
from analysis.repetitions import RepCounter, RepState


class TestRepCounterInit:
    """Tests de l'état initial."""

    def test_initial_state(self):
        """Le compteur démarre à 0 en état IDLE."""
        counter = RepCounter(angle_start=20.0, angle_target=150.0)
        assert counter.count == 0, "Le compteur devrait démarrer à 0"
        assert counter.state == RepState.IDLE, "L'état initial devrait être IDLE"

    def test_initial_history_empty(self):
        """L'historique est vide au départ."""
        counter = RepCounter(angle_start=20.0, angle_target=150.0)
        assert len(counter.rep_history) == 0


class TestRepCounting:
    """Tests du comptage de répétitions."""

    def test_single_rep_complete(self):
        """Un cycle complet (start → target → start) = 1 répétition."""
        counter = RepCounter(angle_start=20.0, angle_target=150.0,
                              tolerance=15.0, hold_frames=2)

        # Position de départ
        counter.update(15.0)

        # Monter progressivement
        for angle in [30, 50, 80, 110, 140, 150, 155]:
            counter.update(angle)

        # Maintenir en haut
        counter.update(155.0)
        counter.update(155.0)
        counter.update(155.0)

        # Redescendre
        for angle in [140, 110, 80, 50, 30, 15]:
            result = counter.update(angle)

        assert counter.count == 1, f"Devrait avoir 1 rep, obtenu {counter.count}"

    def test_multiple_reps(self):
        """5 cycles complets = 5 répétitions."""
        counter = RepCounter(angle_start=20.0, angle_target=150.0,
                              tolerance=15.0, hold_frames=2)

        for _ in range(5):
            # Départ
            counter.update(15.0)
            # Montée
            for a in [50, 100, 140, 155]:
                counter.update(a)
            # Maintien
            counter.update(155.0)
            counter.update(155.0)
            counter.update(155.0)
            # Descente
            for a in [100, 50, 15]:
                counter.update(a)

        assert counter.count == 5, f"Devrait avoir 5 reps, obtenu {counter.count}"

    def test_partial_rep_not_counted(self):
        """Un mouvement incomplet ne compte pas."""
        counter = RepCounter(angle_start=20.0, angle_target=150.0, tolerance=15.0)

        counter.update(15.0)
        # Monter seulement à 80° (loin du target 150°)
        for angle in [30, 50, 70, 80]:
            counter.update(angle)
        # Redescendre sans atteindre le target
        for angle in [60, 40, 15]:
            counter.update(angle)

        assert counter.count == 0, "Un mouvement partiel ne devrait pas compter"

    def test_none_angle_ignored(self):
        """update(None) ne change pas l'état."""
        counter = RepCounter(angle_start=20.0, angle_target=150.0)
        initial_state = counter.state
        result = counter.update(None)
        assert result is None, "update(None) devrait retourner None"
        assert counter.state == initial_state, "L'état ne devrait pas changer"


class TestRepProgress:
    """Tests du calcul de progression."""

    def test_progress_at_start(self):
        """Angle = start → progression ~0%."""
        counter = RepCounter(angle_start=20.0, angle_target=150.0)
        pct = counter.get_progress_pct(20.0)
        assert pct == pytest.approx(0.0, abs=2.0), \
            f"Progression au départ devrait être ~0%, obtenu {pct}%"

    def test_progress_at_target(self):
        """Angle = target → progression ~100%."""
        counter = RepCounter(angle_start=20.0, angle_target=150.0)
        pct = counter.get_progress_pct(150.0)
        assert pct == pytest.approx(100.0, abs=2.0), \
            f"Progression à la cible devrait être ~100%, obtenu {pct}%"

    def test_progress_at_middle(self):
        """Angle = milieu → progression ~50%."""
        counter = RepCounter(angle_start=20.0, angle_target=150.0)
        middle = (20.0 + 150.0) / 2  # 85°
        pct = counter.get_progress_pct(middle)
        assert pct == pytest.approx(50.0, abs=2.0), \
            f"Progression au milieu devrait être ~50%, obtenu {pct}%"

    def test_progress_none_returns_zero(self):
        """get_progress_pct(None) retourne 0.0."""
        counter = RepCounter(angle_start=20.0, angle_target=150.0)
        assert counter.get_progress_pct(None) == 0.0


class TestRepReset:
    """Tests de la réinitialisation."""

    def test_reset(self):
        """reset() remet le compteur à zéro."""
        counter = RepCounter(angle_start=20.0, angle_target=150.0,
                              tolerance=15.0, hold_frames=2)
        # Faire une rep
        counter.update(15.0)
        for a in [50, 100, 140, 155]:
            counter.update(a)
        counter.update(155.0)
        counter.update(155.0)
        counter.update(155.0)
        for a in [100, 50, 15]:
            counter.update(a)

        counter.reset()
        assert counter.count == 0, "Après reset, count devrait être 0"
        assert counter.state == RepState.IDLE
        assert len(counter.rep_history) == 0


class TestRepHistory:
    """Tests de l'historique et de l'amplitude."""

    def test_rep_history_populated(self):
        """L'historique est rempli après une répétition."""
        counter = RepCounter(angle_start=20.0, angle_target=150.0,
                              tolerance=15.0, hold_frames=2)
        counter.update(15.0)
        for a in [50, 100, 140, 155]:
            counter.update(a)
        counter.update(155.0)
        counter.update(155.0)
        counter.update(155.0)
        for a in [100, 50, 15]:
            counter.update(a)

        assert len(counter.rep_history) == 1, "Devrait avoir 1 entrée dans l'historique"
        rep = counter.rep_history[0]
        assert "amplitude" in rep, "L'historique devrait contenir 'amplitude'"
        assert "duration_seconds" in rep
        assert rep["rep_number"] == 1

    def test_avg_amplitude_empty(self):
        """Amplitude moyenne = 0 sans répétitions."""
        counter = RepCounter(angle_start=20.0, angle_target=150.0)
        assert counter.get_avg_amplitude() == 0.0

    def test_going_down_exercise(self):
        """Exercice où l'angle diminue (flexion coude 160° → 40°)."""
        counter = RepCounter(angle_start=160.0, angle_target=40.0,
                              tolerance=15.0, hold_frames=2)

        assert counter.going_up is False, "L'exercice devrait être 'going down'"

        # Départ en haut
        counter.update(165.0)
        # Descente
        for a in [140, 110, 80, 50, 35]:
            counter.update(a)
        # Maintien
        counter.update(35.0)
        counter.update(35.0)
        counter.update(35.0)
        # Remontée
        for a in [50, 80, 110, 140, 165]:
            counter.update(a)

        assert counter.count == 1, \
            f"Exercice going-down devrait compter 1 rep, obtenu {counter.count}"
