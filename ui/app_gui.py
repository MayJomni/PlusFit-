"""
Interface graphique CustomTkinter pour le Miroir de Rééducation.

Interface adaptée aux personnes âgées :
- Gros boutons (60px minimum)
- Polices larges (20px+)
- Contraste élevé (fond sombre, texte blanc)
- Navigation simple par écrans successifs

Usage:
    python run_gui.py
"""

import sys
import os
import time
import threading
import cv2
import numpy as np
from PIL import Image, ImageTk

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import customtkinter as ctk
except ImportError:
    print("Installez customtkinter : pip install customtkinter")
    sys.exit(1)

import config
from exercises.catalog import get_all_exercises, get_exercises_by_category, CATEGORY_LABELS
from exercises.base import Exercise, ExerciseCategory
from ui.mirror import draw_mirror_frame, draw_calibration_screen
from ui.feedback import AudioFeedback
from ui.silhouette import SilhouetteGuide
from ui.voice_commands import VoiceCommandListener
from ui.i18n import Translator
from data.session_logger import SessionLogger
from data.calendar import SessionCalendar


# ─── Thème et constantes UI ───────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FONT_TITLE = ("Helvetica", 42, "bold")
FONT_LARGE = ("Helvetica", 32, "bold")
FONT_MEDIUM = ("Helvetica", 24)
FONT_BUTTON = ("Helvetica", 22, "bold")
FONT_SMALL = ("Helvetica", 18)
FONT_SCORE = ("Helvetica", 72, "bold")

COLOR_BG = "#1a1a2e"
COLOR_CARD = "#16213e"
COLOR_ACCENT = "#0f3460"
COLOR_GREEN = "#4CAF50"
COLOR_ORANGE = "#FF9800"
COLOR_RED = "#F44336"
COLOR_BLUE = "#2196F3"
COLOR_TEXT = "#e0e0e0"

BTN_HEIGHT = 65
BTN_CORNER = 16


def score_color(score: float) -> str:
    """Retourne la couleur hex correspondant au score."""
    if score >= 80:
        return COLOR_GREEN
    elif score >= 60:
        return COLOR_ORANGE
    return COLOR_RED


# ═══════════════════════════════════════════════════════════════════════════════
#  APPLICATION PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════

class RehabMirrorGUI:
    """Application GUI complète du miroir de rééducation."""

    def __init__(self):
        # ── Fenêtre principale ─────────────────────────────────────────────
        self.root = ctk.CTk()
        self.root.title(config.WINDOW_TITLE)
        self.root.geometry("1280x800")
        self.root.minsize(1024, 700)
        self.root.configure(fg_color=COLOR_BG)

        # ── État application ──────────────────────────────────────────────
        self.patient_id = "patient"
        self.exercises = get_all_exercises(target_reps=10)
        self.current_exercise_idx = 0
        self.current_exercise: Exercise = self.exercises[0]
        self.exercise_active = False
        self.session_results = []

        # ── Caméra & détection ────────────────────────────────────────────
        self.cap = None
        self.detector = None
        self._detector_loaded = False
        self._camera_running = False

        # ── Audio ─────────────────────────────────────────────────────────
        self.audio = AudioFeedback(rate=config.SPEECH_RATE, enabled=config.AUDIO_ENABLED)

        # ── Traducteur (multi-langues) ────────────────────────────────────
        self.tr = Translator.get_instance(lang="fr")

        # ── Calendrier ────────────────────────────────────────────────────
        self.calendar = SessionCalendar()

        # ── Commandes vocales ─────────────────────────────────────────────
        self.voice_listener = VoiceCommandListener(
            lang="fr", on_command=self._on_voice_command
        )

        # ── Silhouette guide ──────────────────────────────────────────────
        self._silhouette: SilhouetteGuide | None = None

        # ── Session logger ────────────────────────────────────────────────
        self.session_logger = None

        # ── Calibration ──────────────────────────────────────────────────
        self._calibrating = False
        self._calibration_start = 0.0
        self._calibration_duration = 3
        self._last_keypoints = None

        # ── Guidage vocal du mouvement ────────────────────────────────────
        self._prev_angle = None       # Angle frame précédente
        self._angle_history = []      # Historique angles (lissage sur 5 frames)
        self._voice_phase = None      # Phase vocale actuelle ("montee"/"tenue"/"descente")
        self._comp_cooldown = 0       # Anti-spam alertes compensation (en frames)

        # ── Construire les écrans ─────────────────────────────────────────
        self._current_frame = None
        self._build_welcome_screen()

    # ═══════════════════════════════════════════════════════════════════════
    #  ÉCRAN 1 : ACCUEIL
    # ═══════════════════════════════════════════════════════════════════════

    def _build_welcome_screen(self):
        """Écran d'accueil avec saisie de l'identifiant patient."""
        self._clear_screen()

        frame = ctk.CTkFrame(self.root, fg_color=COLOR_BG)
        frame.pack(expand=True, fill="both", padx=40, pady=30)
        self._current_frame = frame

        # Spacer
        ctk.CTkLabel(frame, text="", height=40).pack()

        # Titre
        ctk.CTkLabel(
            frame, text="Miroir de Reeducation",
            font=FONT_TITLE, text_color="white",
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            frame, text="Systeme de reeducation assiste par intelligence artificielle",
            font=FONT_SMALL, text_color="#aaaaaa",
        ).pack(pady=(0, 50))

        # Carte de saisie
        card = ctk.CTkFrame(frame, fg_color=COLOR_CARD, corner_radius=20)
        card.pack(pady=10, padx=100, fill="x")

        ctk.CTkLabel(
            card, text="Identifiant du patient :",
            font=FONT_MEDIUM, text_color=COLOR_TEXT,
        ).pack(pady=(30, 10), padx=40, anchor="w")

        self._patient_entry = ctk.CTkEntry(
            card, font=FONT_LARGE, height=60,
            placeholder_text="Ex: patient001",
            corner_radius=12,
        )
        self._patient_entry.pack(pady=(0, 30), padx=40, fill="x")
        self._patient_entry.insert(0, "patient001")

        # Bouton COMMENCER
        ctk.CTkButton(
            frame,
            text="COMMENCER",
            font=FONT_LARGE,
            height=100,
            corner_radius=20,
            fg_color=COLOR_GREEN,
            hover_color="#388E3C",
            command=self._on_start_session,
        ).pack(pady=40, padx=100, fill="x")

        # Version
        ctk.CTkLabel(
            frame, text="v1.0 -- MoveNet - Python - OpenCV",
            font=("Helvetica", 14), text_color="#666666",
        ).pack(side="bottom", pady=10)

        # ── Sélecteur de langue ───────────────────────────────────────────
        lang_frame = ctk.CTkFrame(frame, fg_color="transparent")
        lang_frame.pack(side="bottom", pady=5)
        ctk.CTkLabel(lang_frame, text="Langue / Language / اللغة / Idioma :",
                     font=("Helvetica", 14), text_color="#888888").pack(side="left", padx=5)
        for info in self.tr.get_all_langs():
            code = info["code"]
            ctk.CTkButton(
                lang_frame,
                text=f"{info['drapeau']} {info['nom']}",
                font=("Helvetica", 14),
                width=110, height=35, corner_radius=8,
                fg_color=COLOR_ACCENT if code != self.tr.lang else COLOR_BLUE,
                command=lambda c=code: self._change_lang(c),
            ).pack(side="left", padx=3)

    def _on_start_session(self):
        """Callback du bouton COMMENCER."""
        self.patient_id = self._patient_entry.get().strip() or "patient"
        self.session_logger = SessionLogger(
            log_dir=config.SESSION_LOG_DIR, patient_id=self.patient_id,
        )
        self.session_results = []
        # Annonce séances du jour
        today_sessions = self.calendar.get_today_sessions(self.patient_id)
        if today_sessions:
            nb = len(today_sessions)
            self.audio.speak(f"Bonjour ! Vous avez {nb} séance{'s' if nb>1 else ''} prévue{'s' if nb>1 else ''} aujourd'hui.")
        self._build_exercise_selection()

    def _change_lang(self, lang_code: str):
        """Change la langue de l'interface."""
        self.tr.set_lang(lang_code)
        if hasattr(self, "voice_listener"):
            self.voice_listener.set_lang(lang_code)
        self._build_welcome_screen()  # Rafraîchit l'écran

    # ═══════════════════════════════════════════════════════════════════════
    #  ÉCRAN 2 : SÉLECTION D'EXERCICE
    # ═══════════════════════════════════════════════════════════════════════

    def _build_exercise_selection(self):
        """Écran de sélection d'exercice avec onglets par catégorie."""
        self._clear_screen()

        frame = ctk.CTkFrame(self.root, fg_color=COLOR_BG)
        frame.pack(expand=True, fill="both", padx=20, pady=15)
        self._current_frame = frame

        # ── Barre du haut ─────────────────────────────────────────────────
        top_bar = ctk.CTkFrame(frame, fg_color=COLOR_BG, height=50)
        top_bar.pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            top_bar, text="<- Retour", font=FONT_SMALL,
            width=120, height=45, fg_color=COLOR_ACCENT,
            command=self._build_welcome_screen,
        ).pack(side="left")

        ctk.CTkLabel(
            top_bar, text=f"Patient : {self.patient_id}",
            font=FONT_MEDIUM, text_color=COLOR_TEXT,
        ).pack(side="right", padx=20)

        # ── Titre ─────────────────────────────────────────────────────────
        ctk.CTkLabel(
            frame, text="Choisissez un exercice",
            font=FONT_LARGE, text_color="white",
        ).pack(pady=(5, 15))

        # ── Onglets ───────────────────────────────────────────────────────
        tabview = ctk.CTkTabview(
            frame, fg_color=COLOR_CARD, corner_radius=16,
            segmented_button_fg_color=COLOR_ACCENT,
            segmented_button_selected_color=COLOR_BLUE,
        )
        tabview.pack(expand=True, fill="both", padx=10)

        # Onglet "Tous"
        tab_all = tabview.add("Tous")
        self._populate_exercise_list(tab_all, self.exercises)

        # Onglets par catégorie
        cat_map = {
            "Bras": ExerciseCategory.UPPER_LIMB,
            "Jambes": ExerciseCategory.LOWER_LIMB,
            "Equilibre assis": ExerciseCategory.BALANCE_SITTING,
            "Equilibre debout": ExerciseCategory.BALANCE_STANDING,
            "Cognitif": ExerciseCategory.COGNITIVE_MOTOR,
        }
        for label, cat in cat_map.items():
            tab = tabview.add(label)
            filtered = [e for e in self.exercises if e.category == cat]
            self._populate_exercise_list(tab, filtered)

        # ── Bouton terminer session ───────────────────────────────────────
        if self.session_results:
            ctk.CTkButton(
                frame,
                text=f"Terminer la session ({len(self.session_results)} exercices faits)",
                font=FONT_BUTTON, height=BTN_HEIGHT, corner_radius=BTN_CORNER,
                fg_color=COLOR_ORANGE, hover_color="#F57C00",
                command=self._build_session_summary,
            ).pack(pady=10, padx=10, fill="x")

    def _populate_exercise_list(self, parent, exercises: list):
        """Remplit une liste scrollable de boutons d'exercice."""
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent", corner_radius=0)
        scroll.pack(expand=True, fill="both", padx=5, pady=5)

        for i, ex in enumerate(exercises):
            idx = self.exercises.index(ex)
            cognitive = " [Cognitif]" if ex.has_cognitive_task else ""

            btn_frame = ctk.CTkFrame(scroll, fg_color=COLOR_ACCENT, corner_radius=12)
            btn_frame.pack(fill="x", pady=4, padx=5)

            btn = ctk.CTkButton(
                btn_frame,
                text=f"  {ex.name}{cognitive}",
                font=FONT_BUTTON,
                height=BTN_HEIGHT,
                corner_radius=12,
                fg_color=COLOR_ACCENT,
                hover_color="#1a4a8a",
                anchor="w",
                command=lambda idx=idx: self._select_exercise(idx),
            )
            btn.pack(fill="x", padx=2, pady=2)

            # Description en sous-texte
            ctk.CTkLabel(
                btn_frame, text=f"    {ex.description}",
                font=("Helvetica", 16), text_color="#999999",
                anchor="w",
            ).pack(fill="x", padx=15, pady=(0, 8))

    def _select_exercise(self, idx: int):
        """Sélectionne un exercice et passe à l'écran d'exercice."""
        self.current_exercise_idx = idx
        self.current_exercise = self.exercises[idx]
        # 🔊 Annonce vocale : description complète de l'exercice
        self.audio.speak_introduction(self.current_exercise.name)
        # 🎬 Silhouette animée pour cet exercice
        self._silhouette = SilhouetteGuide(self.current_exercise.name)
        self._fatigue_alerted = False
        self._build_exercise_screen()

    # ═══════════════════════════════════════════════════════════════════════
    #  ÉCRAN 3 : EXERCICE ACTIF
    # ═══════════════════════════════════════════════════════════════════════

    def _build_exercise_screen(self):
        """Écran d'exercice avec vidéo, compteur et feedback."""
        self._clear_screen()

        frame = ctk.CTkFrame(self.root, fg_color=COLOR_BG)
        frame.pack(expand=True, fill="both")
        self._current_frame = frame

        # ── Layout principal : vidéo à gauche, panneau à droite ──────────
        frame.grid_columnconfigure(0, weight=3)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        # ── Zone vidéo ────────────────────────────────────────────────────
        video_frame = ctk.CTkFrame(frame, fg_color=COLOR_CARD, corner_radius=16)
        video_frame.grid(row=0, column=0, sticky="nsew", padx=(15, 8), pady=15)

        self._video_label = ctk.CTkLabel(
            video_frame, text="Chargement de la camera...",
            font=FONT_MEDIUM, text_color="#999999",
        )
        self._video_label.pack(expand=True, fill="both", padx=5, pady=5)

        # ── Panneau de droite ─────────────────────────────────────────────
        panel = ctk.CTkFrame(frame, fg_color=COLOR_BG)
        panel.grid(row=0, column=1, sticky="nsew", padx=(8, 15), pady=15)

        # Nom de l'exercice
        ctk.CTkLabel(
            panel, text=self.current_exercise.name,
            font=FONT_BUTTON, text_color="white",
            wraplength=300,
        ).pack(pady=(10, 5))

        # Catégorie
        cat_label = CATEGORY_LABELS.get(self.current_exercise.category, "")
        ctk.CTkLabel(
            panel, text=cat_label,
            font=FONT_SMALL, text_color=COLOR_BLUE,
        ).pack(pady=(0, 15))

        # ── Compteur de répétitions ───────────────────────────────────────
        counter_card = ctk.CTkFrame(panel, fg_color=COLOR_CARD, corner_radius=16)
        counter_card.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            counter_card, text="Repetitions",
            font=FONT_SMALL, text_color="#aaaaaa",
        ).pack(pady=(15, 0))

        self._rep_label = ctk.CTkLabel(
            counter_card, text="0/10",
            font=FONT_SCORE, text_color=COLOR_GREEN,
        )
        self._rep_label.pack(pady=(0, 5))

        # ── Barre de progression ──────────────────────────────────────────
        self._progress_bar = ctk.CTkProgressBar(
            counter_card, height=20, corner_radius=10,
            progress_color=COLOR_BLUE,
        )
        self._progress_bar.pack(fill="x", padx=20, pady=(0, 15))
        self._progress_bar.set(0)

        # ── Angle actuel ──────────────────────────────────────────────────
        angle_card = ctk.CTkFrame(panel, fg_color=COLOR_CARD, corner_radius=16)
        angle_card.pack(fill="x", padx=10, pady=5)

        self._angle_label = ctk.CTkLabel(
            angle_card, text="--",
            font=FONT_LARGE, text_color="#ccccff",
        )
        self._angle_label.pack(pady=15)

        # ── Feedback ──────────────────────────────────────────────────────
        self._feedback_card = ctk.CTkFrame(panel, fg_color=COLOR_CARD, corner_radius=16)
        self._feedback_card.pack(fill="x", padx=10, pady=5)

        # Affiche les instructions dès l'ouverture
        instructions_text = self.current_exercise.get_instructions()
        self._feedback_label = ctk.CTkLabel(
            self._feedback_card,
            text=f"🔊 {instructions_text}",
            font=FONT_SMALL, text_color="#aaddff",
            wraplength=280,
        )
        self._feedback_label.pack(pady=15, padx=10)

        # ── Tâche cognitive ───────────────────────────────────────────────
        if self.current_exercise.has_cognitive_task:
            cog_card = ctk.CTkFrame(panel, fg_color="#2d1f4e", corner_radius=16)
            cog_card.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(
                cog_card, text="Tache cognitive",
                font=FONT_SMALL, text_color="#bb86fc",
            ).pack(pady=(10, 2))
            ctk.CTkLabel(
                cog_card, text=self.current_exercise.cognitive_instruction,
                font=("Helvetica", 16), text_color="#e0c0ff",
                wraplength=280,
            ).pack(pady=(0, 10), padx=10)

        # ── Boutons ───────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(panel, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(15, 10), side="bottom")

        self._start_btn = ctk.CTkButton(
            btn_frame, text="DEMARRER",
            font=FONT_BUTTON, height=BTN_HEIGHT, corner_radius=BTN_CORNER,
            fg_color=COLOR_GREEN, hover_color="#388E3C",
            command=self._on_exercise_start,
        )
        self._start_btn.pack(fill="x", pady=3)

        self._stop_btn = ctk.CTkButton(
            btn_frame, text="ARRETER",
            font=FONT_BUTTON, height=BTN_HEIGHT, corner_radius=BTN_CORNER,
            fg_color=COLOR_RED, hover_color="#C62828",
            command=self._on_exercise_stop,
        )
        self._stop_btn.pack(fill="x", pady=3)

        ctk.CTkButton(
            btn_frame, text="<- Retour aux exercices",
            font=FONT_SMALL, height=45, corner_radius=12,
            fg_color=COLOR_ACCENT, hover_color="#1a4a8a",
            command=self._on_back_to_selection,
        ).pack(fill="x", pady=3)

        # ── Démarrer la caméra ────────────────────────────────────────────
        self._start_camera()

    def _start_camera(self):
        """Ouvre la webcam et lance la boucle vidéo."""
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(config.CAMERA_INDEX)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)

        if not self._detector_loaded:
            self._video_label.configure(text="Chargement du modele IA...")
            threading.Thread(target=self._load_detector, daemon=True).start()
        else:
            self._camera_running = True
            self._video_loop()

    def _load_detector(self):
        """Charge MoveNet dans un thread séparé."""
        try:
            from pose_detection.movenet import MoveNetDetector
            self.detector = MoveNetDetector(
                model_name=config.MOVENET_MODEL,
                min_confidence=config.MIN_CONFIDENCE,
            )
            self._detector_loaded = True
            self._camera_running = True
            self.root.after(0, self._video_loop)
        except Exception as e:
            err_msg = str(e)
            print(f"[Erreur] Chargement MoveNet : {err_msg}")
            self.root.after(0, lambda msg=err_msg: self._video_label.configure(
                text=f"Erreur : {msg}\n\nVerifiez l'installation de TensorFlow."
            ))

    def _video_loop(self):
        """Boucle de capture et affichage vidéo."""
        if not self._camera_running or self.cap is None:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.root.after(33, self._video_loop)
            return

        # Détection de pose
        keypoints = None
        if self.detector:
            keypoints = self.detector.detect(frame)
            self._last_keypoints = keypoints

        # Traitement selon l'état
        if self._calibrating:
            elapsed = time.time() - self._calibration_start
            countdown = max(1, self._calibration_duration - int(elapsed))
            display = draw_calibration_screen(
                frame, keypoints, countdown=countdown,
                min_confidence=config.MIN_CONFIDENCE,
            )
            if elapsed >= self._calibration_duration:
                self._calibrating = False
                self.exercise_active = True
                if keypoints is not None:
                    self.current_exercise.start(keypoints)
                    # 🔊 Signal de départ dynamique
                    self.audio.speak_start(self.current_exercise.name)
                self._start_btn.configure(state="disabled")

        elif self.exercise_active:
            exercise_state = self.current_exercise.update(keypoints)
            display = draw_mirror_frame(
                frame, keypoints,
                exercise_state=exercise_state,
                exercise_name="",
                min_confidence=config.MIN_CONFIDENCE,
            )
            self._update_panel(exercise_state)

            # 🔊 Guidage vocal du mouvement (phase par phase)
            angle = exercise_state.get("angle")
            if angle is not None:
                # Lissage sur 5 frames pour éviter les faux positifs
                self._angle_history.append(angle)
                if len(self._angle_history) > 5:
                    self._angle_history.pop(0)
                smooth_angle = sum(self._angle_history) / len(self._angle_history)

                angle_start  = self.current_exercise.angle_start
                angle_target = self.current_exercise.angle_target
                angle_range  = angle_target - angle_start
                pct = (smooth_angle - angle_start) / angle_range if angle_range else 0

                # Déterminer la phase du mouvement
                if self._prev_angle is not None:
                    delta = smooth_angle - self._prev_angle
                    if pct >= 0.85:
                        new_phase = "tenue"
                    elif delta > 0.5:
                        new_phase = "montee"
                    elif delta < -0.5:
                        new_phase = "descente"
                    else:
                        new_phase = self._voice_phase  # Pas de changement

                    if new_phase and new_phase != self._voice_phase:
                        self._voice_phase = new_phase
                        self.audio.speak_mouvement(
                            self.current_exercise.name, new_phase
                        )
                self._prev_angle = smooth_angle

            # 🔊 Comptage des répétitions
            if exercise_state.get("new_rep"):
                self._prev_angle = None
                self._angle_history = []
                self._voice_phase = None
                self.audio.speak_rep(
                    exercise_state["reps"], exercise_state["target_reps"]
                )

            # 🔊 Alertes de compensation (anti-spam : 1 alerte / 90 frames)
            self._comp_cooldown = max(0, self._comp_cooldown - 1)
            if exercise_state.get("compensations") and self._comp_cooldown == 0:
                worst = max(
                    exercise_state["compensations"],
                    key=lambda a: {"mild": 0, "moderate": 1, "severe": 2}[a.severity],
                )
                if worst.severity in ("moderate", "severe"):
                    self.audio.speak_compensation(worst.message)
                    self._comp_cooldown = 90  # ~3 secondes à 30fps

            # 😴 Détection de fatigue
            fatigue_info = exercise_state.get("fatigue_info")
            if fatigue_info and not getattr(self, "_fatigue_alerted", False):
                self._fatigue_alerted = True
                msg = fatigue_info["message"] + ". " + fatigue_info["suggestion"]
                self.audio.speak(msg, priority=True)
                self._show_fatigue_alert(fatigue_info)

            if exercise_state.get("completed"):
                self._on_exercise_complete()
        else:
            display = draw_mirror_frame(
                frame, keypoints,
                min_confidence=config.MIN_CONFIDENCE,
            )

        # 🎨 Silhouette guide animée (toujours affichée quand exercice sélectionné)
        if self._silhouette is not None:
            display = self._silhouette.draw(display, x=15, y=15)

        # Convertir pour affichage Tkinter
        display_rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(display_rgb)

        try:
            label_w = self._video_label.winfo_width()
            label_h = self._video_label.winfo_height()
            if label_w > 10 and label_h > 10:
                img = img.resize((label_w, label_h), Image.LANCZOS)
        except Exception:
            pass

        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        self._video_label.configure(image=ctk_img, text="")
        self._video_label._ctk_image = ctk_img

        self.root.after(33, self._video_loop)

    def _update_panel(self, state: dict):
        """Met à jour les widgets du panneau latéral."""
        reps = state.get("reps", 0)
        target = state.get("target_reps", 10)
        self._rep_label.configure(text=f"{reps}/{target}")

        progress = state.get("progress_pct", 0.0) / 100.0
        self._progress_bar.set(progress)

        angle = state.get("angle")
        self._angle_label.configure(text=f"{int(angle)} deg" if angle is not None else "--")

        msg = state.get("feedback_message", "")
        color = state.get("feedback_color", "#FFFFFF")
        self._feedback_label.configure(text=msg, text_color=color)

        comps = state.get("compensations", [])
        if comps:
            worst_sev = max(
                comps,
                key=lambda a: {"mild": 0, "moderate": 1, "severe": 2}[a.severity],
            ).severity
            bg_colors = {"mild": "#3d2e00", "moderate": "#4a1a00", "severe": "#4a0000"}
            self._feedback_card.configure(fg_color=bg_colors.get(worst_sev, COLOR_CARD))
        else:
            self._feedback_card.configure(fg_color=COLOR_CARD)

    def _on_exercise_start(self):
        """Lance la calibration puis l'exercice."""
        self._calibrating = True
        self._calibration_start = time.time()
        # Reset guidage vocal
        self._prev_angle = None
        self._angle_history = []
        self._voice_phase = None
        self._comp_cooldown = 0
        # 🔊 Instructions de calibration
        self.audio.speak_calibration()

    def _on_exercise_stop(self):
        """Arrête l'exercice en cours."""
        if self.exercise_active or self._calibrating:
            self.exercise_active = False
            self._calibrating = False
            self._start_btn.configure(state="normal")
            if hasattr(self.current_exercise, 'rep_counter') and self.current_exercise.rep_counter.count > 0:
                self._on_exercise_complete()

    def _on_exercise_complete(self):
        """Gère la fin d'un exercice."""
        self.exercise_active = False
        self._camera_running = False
        result = self.current_exercise.get_result()
        self.session_results.append(result)
        if self.session_logger:
            self.session_logger.log_exercise(result)
        # 🔊 Bilan vocal du score + invitation à continuer
        self.audio.speak_end(result.score)
        self.root.after(3000, lambda: self.audio.speak_pause())
        self._build_result_screen(result)

    def _on_back_to_selection(self):
        """Retour à la sélection d'exercice."""
        self._camera_running = False
        self.exercise_active = False
        self._calibrating = False
        self._build_exercise_selection()

    # ═══════════════════════════════════════════════════════════════════════
    #  ÉCRAN 4 : RÉSULTATS
    # ═══════════════════════════════════════════════════════════════════════

    def _build_result_screen(self, result):
        """Écran de résultats après un exercice."""
        self._clear_screen()

        frame = ctk.CTkFrame(self.root, fg_color=COLOR_BG)
        frame.pack(expand=True, fill="both", padx=40, pady=30)
        self._current_frame = frame

        ctk.CTkLabel(
            frame, text="Resultats",
            font=FONT_TITLE, text_color="white",
        ).pack(pady=(10, 5))

        ctk.CTkLabel(
            frame, text=result.exercise_name,
            font=FONT_MEDIUM, text_color=COLOR_BLUE,
        ).pack(pady=(0, 20))

        # ── Score principal ───────────────────────────────────────────────
        score_card = ctk.CTkFrame(frame, fg_color=COLOR_CARD, corner_radius=20)
        score_card.pack(fill="x", padx=60, pady=10)

        color = score_color(result.score)
        ctk.CTkLabel(
            score_card, text=f"{result.score:.0f}",
            font=FONT_SCORE, text_color=color,
        ).pack(pady=(20, 0))
        ctk.CTkLabel(
            score_card, text="/ 100",
            font=FONT_MEDIUM, text_color="#888888",
        ).pack(pady=(0, 20))

        # ── Détails ───────────────────────────────────────────────────────
        details_frame = ctk.CTkFrame(frame, fg_color="transparent")
        details_frame.pack(fill="x", padx=60, pady=15)
        details_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        metrics = [
            ("Repetitions", f"{result.total_reps}/{result.target_reps}", COLOR_GREEN),
            ("Amplitude moy.", f"{result.avg_amplitude:.0f} deg", COLOR_BLUE),
            ("Compensations", str(result.compensations_count),
             COLOR_GREEN if result.compensations_count == 0 else COLOR_ORANGE),
            ("Duree", f"{result.duration_seconds:.0f}s", COLOR_TEXT),
        ]
        for col, (label, value, c) in enumerate(metrics):
            card = ctk.CTkFrame(details_frame, fg_color=COLOR_CARD, corner_radius=14)
            card.grid(row=0, column=col, padx=6, pady=5, sticky="nsew")
            ctk.CTkLabel(card, text=label, font=FONT_SMALL, text_color="#aaaaaa").pack(pady=(15, 2))
            ctk.CTkLabel(card, text=value, font=FONT_LARGE, text_color=c).pack(pady=(0, 15))

        # ── Boutons ───────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=60, pady=20)

        next_idx = (self.current_exercise_idx + 1) % len(self.exercises)
        next_name = self.exercises[next_idx].name

        ctk.CTkButton(
            btn_frame, text=f"Exercice suivant : {next_name}",
            font=FONT_BUTTON, height=BTN_HEIGHT, corner_radius=BTN_CORNER,
            fg_color=COLOR_GREEN, hover_color="#388E3C",
            command=lambda: self._select_exercise(next_idx),
        ).pack(fill="x", pady=4)

        ctk.CTkButton(
            btn_frame, text="Recommencer cet exercice",
            font=FONT_BUTTON, height=BTN_HEIGHT, corner_radius=BTN_CORNER,
            fg_color=COLOR_BLUE, hover_color="#1565C0",
            command=lambda: self._select_exercise(self.current_exercise_idx),
        ).pack(fill="x", pady=4)

        ctk.CTkButton(
            btn_frame, text="Choisir un autre exercice",
            font=FONT_BUTTON, height=BTN_HEIGHT, corner_radius=BTN_CORNER,
            fg_color=COLOR_ACCENT, hover_color="#1a4a8a",
            command=self._build_exercise_selection,
        ).pack(fill="x", pady=4)

        ctk.CTkButton(
            btn_frame,
            text=f"Terminer la session ({len(self.session_results)} exercices)",
            font=FONT_BUTTON, height=BTN_HEIGHT, corner_radius=BTN_CORNER,
            fg_color=COLOR_ORANGE, hover_color="#F57C00",
            command=self._build_session_summary,
        ).pack(fill="x", pady=4)

    # ═══════════════════════════════════════════════════════════════════════
    #  ÉCRAN 5 : FIN DE SESSION
    # ═══════════════════════════════════════════════════════════════════════

    def _build_session_summary(self):
        """Écran récapitulatif de la session complète."""
        self._clear_screen()
        self._camera_running = False

        # 🔊 Résumé vocal de la session
        if self.session_results:
            avg = sum(r.score for r in self.session_results) / len(self.session_results)
            self.audio.speak_session_end(len(self.session_results), avg)

        frame = ctk.CTkFrame(self.root, fg_color=COLOR_BG)
        frame.pack(expand=True, fill="both", padx=40, pady=20)
        self._current_frame = frame

        ctk.CTkLabel(
            frame, text="Resume de la session",
            font=FONT_TITLE, text_color="white",
        ).pack(pady=(10, 5))

        ctk.CTkLabel(
            frame, text=f"Patient : {self.patient_id}",
            font=FONT_MEDIUM, text_color=COLOR_BLUE,
        ).pack(pady=(0, 15))

        # ── Score moyen ───────────────────────────────────────────────────
        avg_score = (sum(r.score for r in self.session_results) / len(self.session_results)
                     if self.session_results else 0)

        score_card = ctk.CTkFrame(frame, fg_color=COLOR_CARD, corner_radius=20)
        score_card.pack(fill="x", padx=100, pady=10)

        ctk.CTkLabel(score_card, text="Score moyen", font=FONT_MEDIUM, text_color="#aaaaaa").pack(pady=(15, 0))
        ctk.CTkLabel(
            score_card, text=f"{avg_score:.0f} / 100",
            font=FONT_SCORE, text_color=score_color(avg_score),
        ).pack(pady=(0, 15))

        # ── Tableau des exercices ─────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent", corner_radius=12, height=280)
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        header = ctk.CTkFrame(scroll, fg_color=COLOR_ACCENT, corner_radius=8)
        header.pack(fill="x", pady=(0, 5))
        header.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        for col, h in enumerate(["Exercice", "Reps", "Amplitude", "Comp.", "Score"]):
            ctk.CTkLabel(header, text=h, font=("Helvetica", 16, "bold"),
                         text_color="white").grid(row=0, column=col, padx=5, pady=8)

        for i, r in enumerate(self.session_results):
            row_color = COLOR_CARD if i % 2 == 0 else "#1a2540"
            row = ctk.CTkFrame(scroll, fg_color=row_color, corner_radius=6)
            row.pack(fill="x", pady=1)
            row.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

            vals = [r.exercise_name[:30], f"{r.total_reps}/{r.target_reps}",
                    f"{r.avg_amplitude:.0f} deg", str(r.compensations_count), f"{r.score:.0f}"]
            colors = [COLOR_TEXT, COLOR_TEXT, COLOR_TEXT, COLOR_TEXT, score_color(r.score)]
            for col, (v, c) in enumerate(zip(vals, colors)):
                ctk.CTkLabel(row, text=v, font=FONT_SMALL, text_color=c).grid(
                    row=0, column=col, padx=5, pady=8)

        # ── Boutons ───────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=60, pady=15)

        ctk.CTkButton(
            btn_frame, text="Sauvegarder et quitter",
            font=FONT_BUTTON, height=BTN_HEIGHT, corner_radius=BTN_CORNER,
            fg_color=COLOR_GREEN, hover_color="#388E3C",
            command=self._save_and_quit,
        ).pack(fill="x", pady=4)

        ctk.CTkButton(
            btn_frame, text="Exporter en PDF",
            font=FONT_BUTTON, height=BTN_HEIGHT, corner_radius=BTN_CORNER,
            fg_color=COLOR_BLUE, hover_color="#1565C0",
            command=self._export_pdf,
        ).pack(fill="x", pady=4)

        ctk.CTkButton(
            btn_frame, text="Ajouter un exercice",
            font=FONT_BUTTON, height=BTN_HEIGHT, corner_radius=BTN_CORNER,
            fg_color=COLOR_ACCENT, hover_color="#1a4a8a",
            command=self._build_exercise_selection,
        ).pack(fill="x", pady=4)

    # ═══════════════════════════════════════════════════════════════════════
    #  UTILITAIRES
    # ═══════════════════════════════════════════════════════════════════════

    def _save_and_quit(self):
        """Sauvegarde la session et ferme l'application."""
        if self.session_logger and self.session_results:
            self.session_logger.save()
            print(self.session_logger.get_summary())
            self.audio.speak("Session sauvegardee. Au revoir !")
        time.sleep(1)
        self._cleanup()
        self.root.quit()

    def _export_pdf(self):
        """Exporte la session en PDF."""
        try:
            from data.pdf_report import SessionReportPDF
            reporter = SessionReportPDF()
            if self.session_logger:
                session_data = {
                    "session_id": self.session_logger.session_id,
                    "patient_id": self.patient_id,
                    "date": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "exercises": self.session_logger.results,
                    "avg_score": self.session_logger._avg_score(),
                }
                output = os.path.join(
                    config.SESSION_LOG_DIR,
                    f"rapport_{self.patient_id}_{self.session_logger.session_id}.pdf",
                )
                reporter.generate_session_report(session_data, output)
                self.audio.speak("Rapport PDF genere avec succes")
        except ImportError:
            print("[PDF] fpdf2 non installe. pip install fpdf2")
        except Exception as e:
            print(f"[PDF] Erreur : {e}")

    def _clear_screen(self):
        """Supprime tous les widgets de la fenêtre."""
        self._camera_running = False
        if self._current_frame:
            self._current_frame.destroy()
        for widget in self.root.winfo_children():
            widget.destroy()

    def _cleanup(self):
        """Nettoyage des ressources."""
        self._camera_running = False
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.audio.stop()
        if hasattr(self, "voice_listener"):
            self.voice_listener.stop()

    def _on_voice_command(self, command: str):
        """Callback des commandes vocales — exécuté dans le thread principal."""
        def _exec():
            if command == "demarrer" and not self.exercise_active and not self._calibrating:
                self._on_exercise_start()
            elif command == "arreter":
                self._on_exercise_stop()
            elif command == "suivant":
                next_idx = (self.current_exercise_idx + 1) % len(self.exercises)
                self._select_exercise(next_idx)
            elif command == "retour":
                self._on_back_to_selection()
            elif command == "pause":
                self._on_exercise_stop()
        self.root.after(0, _exec)

    def _show_fatigue_alert(self, fatigue_info: dict):
        """Affiche une alerte de fatigue dans le panneau latéral."""
        try:
            niveau = fatigue_info.get("niveau", "moderee")
            couleur = "#4a1a00" if niveau == "severe" else "#3d2e00"
            self._feedback_card.configure(fg_color=couleur)
            self._feedback_label.configure(
                text=f"😴 {fatigue_info['message']}\n{fatigue_info['suggestion']}",
                text_color="#FFB74D",
            )
        except Exception:
            pass

    def run(self):
        """Lance l'application."""
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        # Démarrer l'écoute vocale si disponible
        if hasattr(self, "voice_listener"):
            self.voice_listener.start()
        self.root.mainloop()

    def _on_close(self):
        """Gère la fermeture de la fenêtre."""
        self._cleanup()
        self.root.quit()
        self.root.destroy()
