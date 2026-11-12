"""
Rehab Mirror – Application principale.

Point d'entrée de l'application de rééducation miroir.
Gère la boucle principale :
1. Capture vidéo
2. Détection de pose MoveNet
3. Analyse du mouvement
4. Affichage miroir avec feedback
5. Interactions utilisateur (clavier)

Usage:
    python main.py [--model lightning|thunder] [--camera 0] [--patient ID]
"""

import sys
import time
import argparse
import cv2
import numpy as np

import config
from pose_detection.movenet import MoveNetDetector
from exercises.catalog import get_all_exercises, CATEGORY_LABELS
from exercises.base import Exercise, ExerciseCategory
from ui.mirror import draw_mirror_frame, draw_calibration_screen
from ui.feedback import AudioFeedback
from data.session_logger import SessionLogger


class RehabMirrorApp:
    """
    Application principale du miroir de rééducation.

    Contrôles clavier :
        ESPACE  : Démarrer/arrêter l'exercice
        N       : Exercice suivant
        P       : Exercice précédent
        R       : Réinitialiser l'exercice
        M       : Menu de sélection
        Q / ESC : Quitter
    """

    def __init__(
        self,
        model_name: str = "lightning",
        camera_index: int = 0,
        patient_id: str = "default",
    ):
        # Initialiser le détecteur de pose
        self.detector = MoveNetDetector(
            model_name=model_name,
            min_confidence=config.MIN_CONFIDENCE,
        )

        # Initialiser la caméra
        self.camera_index = camera_index
        self.cap = None

        # Exercices
        self.exercises = get_all_exercises(target_reps=10)
        self.current_exercise_idx = 0
        self.current_exercise: Exercise = self.exercises[0]
        self.exercise_active = False

        # Feedback audio
        self.audio = AudioFeedback(
            rate=config.SPEECH_RATE,
            enabled=config.AUDIO_ENABLED,
        )

        # Logger de session
        self.session_logger = SessionLogger(
            log_dir=config.SESSION_LOG_DIR,
            patient_id=patient_id,
        )

        # État de calibration
        self._calibrating = False
        self._calibration_start = 0
        self._calibration_duration = 3  # secondes

        # État de l'interface
        self._show_menu = False
        self._last_keypoints = None
        self._fps_counter = FPSCounter()

    def run(self):
        """Boucle principale de l'application."""
        # Ouvrir la caméra
        self.cap = cv2.VideoCapture(self.camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)

        if not self.cap.isOpened():
            print(f"[Erreur] Impossible d'ouvrir la caméra {self.camera_index}")
            return

        print(f"\n{'='*50}")
        print(f"  MIROIR DE RÉÉDUCATION")
        print(f"  Modèle : MoveNet {self.detector.model_name}")
        print(f"  Caméra : {self.camera_index}")
        print(f"{'='*50}")
        print(f"\nContrôles :")
        print(f"  ESPACE  : Démarrer/arrêter l'exercice")
        print(f"  N       : Exercice suivant")
        print(f"  P       : Exercice précédent")
        print(f"  R       : Réinitialiser")
        print(f"  Q / ESC : Quitter\n")

        self.audio.speak("Bienvenue dans le miroir de rééducation")

        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("[Erreur] Lecture de la caméra échouée.")
                    break

                # Détection de pose
                keypoints = self.detector.detect(frame)
                self._last_keypoints = keypoints

                # Traitement selon l'état
                if self._calibrating:
                    display = self._handle_calibration(frame, keypoints)
                elif self.exercise_active:
                    display = self._handle_exercise(frame, keypoints)
                elif self._show_menu:
                    display = self._handle_menu(frame, keypoints)
                else:
                    display = self._handle_idle(frame, keypoints)

                # Afficher le FPS
                self._fps_counter.update()
                fps_text = f"FPS: {self._fps_counter.fps:.0f}"
                cv2.putText(
                    display, fps_text,
                    (display.shape[1] - 150, display.shape[0] - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1,
                )

                # Afficher l'image
                cv2.imshow(config.WINDOW_TITLE, display)

                # Gestion des touches
                key = cv2.waitKey(1) & 0xFF
                if not self._handle_key(key):
                    break

        finally:
            self._cleanup()

    def _handle_idle(
        self, frame: np.ndarray, keypoints: np.ndarray
    ) -> np.ndarray:
        """Mode idle : affiche le miroir avec le squelette et le nom de l'exercice."""
        display = draw_mirror_frame(
            frame, keypoints,
            exercise_name=self.current_exercise.name,
            min_confidence=config.MIN_CONFIDENCE,
        )

        h, w = display.shape[:2]

        # Instructions en bas
        instructions = [
            "ESPACE : Démarrer  |  N/P : Changer exercice  |  Q : Quitter",
            f"Exercice {self.current_exercise_idx + 1}/{len(self.exercises)}",
        ]
        for i, text in enumerate(instructions):
            cv2.putText(
                display, text,
                (20, h - 70 + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (200, 200, 200), 1, cv2.LINE_AA,
            )

        # Description de l'exercice
        cv2.putText(
            display, self.current_exercise.description,
            (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.9,
            (200, 200, 255), 2, cv2.LINE_AA,
        )

        # Indicateur de catégorie
        cat_label = CATEGORY_LABELS.get(self.current_exercise.category, "")
        cv2.putText(
            display, cat_label,
            (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
            (150, 200, 255), 2, cv2.LINE_AA,
        )

        # Tâche cognitive si applicable
        if self.current_exercise.has_cognitive_task:
            cv2.putText(
                display, f"🧠 {self.current_exercise.cognitive_instruction}",
                (20, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (255, 200, 100), 2, cv2.LINE_AA,
            )

        return display

    def _handle_calibration(
        self, frame: np.ndarray, keypoints: np.ndarray
    ) -> np.ndarray:
        """Phase de calibration : compte à rebours avant le début."""
        elapsed = time.time() - self._calibration_start
        countdown = max(1, self._calibration_duration - int(elapsed))

        display = draw_calibration_screen(
            frame, keypoints,
            countdown=countdown,
            min_confidence=config.MIN_CONFIDENCE,
        )

        if elapsed >= self._calibration_duration:
            self._calibrating = False
            self.exercise_active = True
            self.current_exercise.start(keypoints)
            self.audio.speak_start(self.current_exercise.name)

        return display

    def _handle_exercise(
        self, frame: np.ndarray, keypoints: np.ndarray
    ) -> np.ndarray:
        """Mode exercice actif : analyse et feedback en temps réel."""
        state = self.current_exercise.update(keypoints)

        # Audio pour les nouvelles reps
        if state["new_rep"]:
            self.audio.speak_rep(state["reps"], state["target_reps"])

        # Audio pour les compensations
        if state["compensations"]:
            worst = max(
                state["compensations"],
                key=lambda a: {"mild": 0, "moderate": 1, "severe": 2}[a.severity],
            )
            if worst.severity in ("moderate", "severe"):
                self.audio.speak_compensation(worst.message)

        # Exercice terminé
        if state["completed"]:
            self._finish_exercise()

        display = draw_mirror_frame(
            frame, keypoints,
            exercise_state=state,
            exercise_name=self.current_exercise.name,
            min_confidence=config.MIN_CONFIDENCE,
        )

        return display

    def _handle_menu(
        self, frame: np.ndarray, keypoints: np.ndarray
    ) -> np.ndarray:
        """Menu de sélection des exercices."""
        display = cv2.flip(frame, 1)
        h, w = display.shape[:2]

        # Fond semi-transparent
        overlay = display.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (30, 30, 50), -1)
        cv2.addWeighted(overlay, 0.85, display, 0.15, 0, display)

        # Titre
        cv2.putText(
            display, "SÉLECTION D'EXERCICE",
            (w // 2 - 250, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5,
            (255, 255, 255), 3, cv2.LINE_AA,
        )

        # Liste des exercices
        y = 120
        for i, ex in enumerate(self.exercises):
            is_selected = (i == self.current_exercise_idx)
            color = (0, 255, 200) if is_selected else (200, 200, 200)
            prefix = "► " if is_selected else "  "

            cat_label = CATEGORY_LABELS.get(ex.category, "")
            text = f"{prefix}{i+1}. {ex.name}"

            cv2.putText(
                display, text,
                (50, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                color, 2 if is_selected else 1, cv2.LINE_AA,
            )
            y += 45

        # Instructions
        cv2.putText(
            display, "N/P : Naviguer  |  ESPACE : Sélectionner  |  M : Fermer",
            (50, h - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
            (150, 150, 150), 1, cv2.LINE_AA,
        )

        return display

    def _start_exercise(self):
        """Lance la calibration puis l'exercice."""
        self._calibrating = True
        self._calibration_start = time.time()
        self._show_menu = False
        self.audio.speak("Préparez-vous. Restez bien droit.")

    def _finish_exercise(self):
        """Termine l'exercice et enregistre les résultats."""
        self.exercise_active = False
        result = self.current_exercise.get_result()
        self.session_logger.log_exercise(result)
        self.audio.speak_end(result.score)

        print(f"\n{'─'*40}")
        print(f"  {result.exercise_name}")
        print(f"  Reps: {result.total_reps}/{result.target_reps}")
        print(f"  Amplitude moy: {result.avg_amplitude:.1f}°")
        print(f"  Compensations: {result.compensations_count}")
        print(f"  Score: {result.score}/100")
        print(f"{'─'*40}\n")

    def _handle_key(self, key: int) -> bool:
        """
        Gère les entrées clavier.

        Returns:
            False si l'utilisateur veut quitter, True sinon.
        """
        if key == ord("q") or key == 27:  # Q ou ESC
            return False

        elif key == ord(" "):  # ESPACE
            if self.exercise_active:
                # Arrêter l'exercice
                self._finish_exercise()
            elif self._calibrating:
                pass  # Ignore pendant la calibration
            else:
                self._start_exercise()

        elif key == ord("n"):  # Suivant
            if not self.exercise_active:
                self.current_exercise_idx = (
                    (self.current_exercise_idx + 1) % len(self.exercises)
                )
                self.current_exercise = self.exercises[self.current_exercise_idx]
                self.audio.speak(self.current_exercise.name)

        elif key == ord("p"):  # Précédent
            if not self.exercise_active:
                self.current_exercise_idx = (
                    (self.current_exercise_idx - 1) % len(self.exercises)
                )
                self.current_exercise = self.exercises[self.current_exercise_idx]
                self.audio.speak(self.current_exercise.name)

        elif key == ord("r"):  # Réinitialiser
            if self.exercise_active:
                self.exercise_active = False
                self.current_exercise.rep_counter.reset()
                self.current_exercise.compensation_detector.reset()
                self.audio.speak("Exercice réinitialisé")

        elif key == ord("m"):  # Menu
            if not self.exercise_active:
                self._show_menu = not self._show_menu

        return True

    def _cleanup(self):
        """Nettoyage à la fermeture."""
        # Sauvegarder la session
        if self.session_logger.results:
            filepath = self.session_logger.save()
            print(self.session_logger.get_summary())

        # Libérer les ressources
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        self.audio.stop()
        print("[Rehab Mirror] Application fermée.")


class FPSCounter:
    """Compteur de FPS simple."""

    def __init__(self, avg_frames: int = 30):
        self.avg_frames = avg_frames
        self._times = []
        self.fps = 0.0

    def update(self):
        current = time.time()
        self._times.append(current)
        if len(self._times) > self.avg_frames:
            self._times.pop(0)
        if len(self._times) >= 2:
            self.fps = (len(self._times) - 1) / (self._times[-1] - self._times[0])


def main():
    """Point d'entrée en ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Miroir de Rééducation – Système de vision par ordinateur"
    )
    parser.add_argument(
        "--model", choices=["lightning", "thunder"], default="lightning",
        help="Modèle MoveNet : lightning (rapide) ou thunder (précis)",
    )
    parser.add_argument(
        "--camera", type=int, default=0,
        help="Index de la webcam (défaut: 0)",
    )
    parser.add_argument(
        "--patient", type=str, default="default",
        help="Identifiant du patient",
    )
    args = parser.parse_args()

    app = RehabMirrorApp(
        model_name=args.model,
        camera_index=args.camera,
        patient_id=args.patient,
    )
    app.run()


if __name__ == "__main__":
    main()
