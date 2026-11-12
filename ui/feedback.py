"""
Module de feedback audio — Guide vocal complet en français.

Donne des instructions détaillées en temps réel :
- Description de l'exercice au démarrage
- Guidage du mouvement (montez, tenez, descendez)
- Comptage des répétitions avec encouragements
- Alertes de compensation
- Messages de fin avec score
"""

import threading
import queue
import random
from typing import Optional

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


# ─── Instructions vocales par exercice ────────────────────────────────────────

INSTRUCTIONS_VOCALES = {
    # Membres supérieurs
    "Flexion épaule gauche": {
        "intro": "Exercice : Flexion épaule gauche. "
                 "Tenez-vous bien droit, bras le long du corps. "
                 "Levez lentement le bras gauche devant vous, paume vers le bas, "
                 "jusqu'à la hauteur de l'épaule. Puis redescendez doucement.",
        "montee": "Levez le bras...",
        "tenue":  "Tenez la position !",
        "descente": "Redescendez doucement.",
    },
    "Flexion épaule droite": {
        "intro": "Exercice : Flexion épaule droite. "
                 "Tenez-vous bien droit, bras le long du corps. "
                 "Levez lentement le bras droit devant vous, paume vers le bas, "
                 "jusqu'à la hauteur de l'épaule. Puis redescendez doucement.",
        "montee": "Levez le bras droit...",
        "tenue":  "Tenez la position !",
        "descente": "Redescendez doucement.",
    },
    "Abduction épaule gauche": {
        "intro": "Exercice : Abduction épaule gauche. "
                 "Bras le long du corps, paume face à vous. "
                 "Levez le bras gauche sur le côté, jusqu'à l'horizontale. "
                 "Gardez le coude tendu et le dos droit.",
        "montee": "Levez le bras sur le côté...",
        "tenue":  "Maintenez !",
        "descente": "Redescendez lentement.",
    },
    "Abduction épaule droite": {
        "intro": "Exercice : Abduction épaule droite. "
                 "Bras le long du corps, paume face à vous. "
                 "Levez le bras droit sur le côté, jusqu'à l'horizontale. "
                 "Gardez le coude tendu et le dos droit.",
        "montee": "Levez le bras droit sur le côté...",
        "tenue":  "Maintenez !",
        "descente": "Redescendez lentement.",
    },
    "Flexion coude gauche": {
        "intro": "Exercice : Flexion du coude gauche. "
                 "Bras le long du corps, paume vers le haut. "
                 "Pliez le coude gauche et remontez la main vers l'épaule. "
                 "Gardez le coude collé au corps.",
        "montee": "Pliez le coude, montez la main !",
        "tenue":  "Tenez !",
        "descente": "Redescendez le bras.",
    },
    "Flexion coude droit": {
        "intro": "Exercice : Flexion du coude droit. "
                 "Bras le long du corps, paume vers le haut. "
                 "Pliez le coude droit et remontez la main vers l'épaule. "
                 "Gardez le coude collé au corps.",
        "montee": "Pliez le coude droit, montez !",
        "tenue":  "Tenez !",
        "descente": "Redescendez doucement.",
    },
    "Flexion bilatérale épaules": {
        "intro": "Exercice : Les deux bras ensemble. "
                 "Levez les deux bras devant vous en même temps, "
                 "jusqu'à la hauteur des épaules. Gardez le dos bien droit.",
        "montee": "Levez les deux bras !",
        "tenue":  "Tenez la position !",
        "descente": "Redescendez les deux bras.",
    },
    # Membres inférieurs
    "Extension genou gauche": {
        "intro": "Exercice : Extension du genou gauche. "
                 "Assis sur votre chaise, dos bien droit. "
                 "Tendez la jambe gauche devant vous, tenez deux secondes, "
                 "puis redescendez lentement.",
        "montee": "Tendez la jambe gauche !",
        "tenue":  "Maintenez la jambe tendue !",
        "descente": "Redescendez le pied.",
    },
    "Extension genou droit": {
        "intro": "Exercice : Extension du genou droit. "
                 "Assis sur votre chaise, dos bien droit. "
                 "Tendez la jambe droite devant vous, tenez deux secondes, "
                 "puis redescendez lentement.",
        "montee": "Tendez la jambe droite !",
        "tenue":  "Maintenez la jambe tendue !",
        "descente": "Redescendez le pied.",
    },
    "Montée de genou gauche": {
        "intro": "Exercice : Montée de genou gauche. "
                 "Assis sur votre chaise. "
                 "Levez le genou gauche vers la poitrine aussi haut que possible, "
                 "puis reposez le pied au sol doucement.",
        "montee": "Levez le genou gauche vers la poitrine !",
        "tenue":  "Tenez !",
        "descente": "Reposez le pied doucement.",
    },
    "Montée de genou droit": {
        "intro": "Exercice : Montée de genou droit. "
                 "Levez le genou droit vers la poitrine aussi haut que possible, "
                 "puis reposez le pied au sol doucement.",
        "montee": "Levez le genou droit !",
        "tenue":  "Tenez !",
        "descente": "Reposez le pied.",
    },
    # Équilibre
    "Transfert de poids latéral (debout)": {
        "intro": "Exercice : Transfert de poids. Debout, pieds écartés à la largeur des hanches. "
                 "Balancez doucement le poids de votre corps vers la gauche, "
                 "puis vers la droite. Gardez les bras légèrement écartés pour l'équilibre.",
        "montee": "Penchez-vous sur le côté...",
        "tenue":  "Tenez l'équilibre !",
        "descente": "Revenez au centre.",
    },
    "Transfert de poids + cognitif": {
        "intro": "Double tâche : Transfert de poids ET exercice mental. "
                 "Pendant que vous bougez, comptez à rebours depuis cent par pas de sept. "
                 "Cent, quatre-vingt-treize, quatre-vingt-six... Allez-y !",
        "montee": "Penchez-vous et comptez !",
        "tenue":  "Tenez et continuez à compter !",
        "descente": "Revenez au centre.",
    },
    # Cognitif-moteur
    "Extension genou gauche + cognitif": {
        "intro": "Double tâche : Extension du genou gauche et exercice mental. "
                 "Pendant que vous tendez la jambe, nommez des fruits à voix haute. "
                 "Pomme, poire, cerise... À vous !",
        "montee": "Tendez la jambe et nommez un fruit !",
        "tenue":  "Tenez et continuez !",
        "descente": "Redescendez le pied.",
    },
}

# Instructions par défaut si l'exercice n'est pas dans le dictionnaire
INSTRUCTIONS_DEFAULT = {
    "intro": "Exercice de rééducation. "
             "Tenez-vous bien droit et effectuez le mouvement lentement et régulièrement. "
             "Allez à votre rythme, sans forcer.",
    "montee": "Effectuez le mouvement !",
    "tenue":  "Tenez la position !",
    "descente": "Revenez à la position de départ.",
}

# Encouragements variés
ENCOURAGEMENTS = [
    "Excellent ! Continuez comme ça !",
    "Très bien ! Beau mouvement !",
    "Super ! Vous progressez !",
    "Bravo ! C'est parfait !",
    "Bien joué ! On continue !",
    "Magnifique ! Gardez ce rythme !",
    "Parfait ! Vous y êtes presque !",
]

# Alertes de compensation
ALERTES_COMPENSATION = {
    "dos": "Attention ! Gardez le dos bien droit !",
    "epaule": "Attention ! Ne montez pas l'épaule !",
    "tronc": "Attention ! Ne penchez pas le tronc !",
    "default": "Attention ! Vérifiez votre posture !",
}


class AudioFeedback:
    """
    Guide vocal non-bloquant pour le miroir de rééducation.

    Fournit des instructions détaillées en temps réel :
    - Description complète de l'exercice au départ
    - Guidage du mouvement phase par phase
    - Comptage avec encouragements
    - Alertes de compensation
    """

    def __init__(self, rate: int = 130, enabled: bool = True):
        """
        Args:
            rate: Vitesse de parole (mots/min). 130 = lent, adapté aux PA.
            enabled: Active/désactive l'audio.
        """
        self.rate = rate
        self._queue: queue.Queue = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._last_phase = None   # Pour éviter de répéter la même instruction

        # Tester si pyttsx3 / SAPI5 fonctionne sur ce système
        self.enabled = False
        if enabled and PYTTSX3_AVAILABLE:
            try:
                import pyttsx3 as _p
                _engine = _p.init()
                if _engine is None:
                    raise RuntimeError("pyttsx3.init() a retourné None")
                _engine.getProperty("voices")
                self.enabled = True
                print("[Audio] ✓ Moteur vocal actif — guide vocal en français")
            except Exception as e:
                print(f"[Audio] Moteur vocal désactivé (SAPI5 indisponible): {e}")

        if self.enabled:
            self._start_thread()

    def _start_thread(self):
        """Démarre le thread de synthèse vocale."""
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self):
        """Boucle du worker de synthèse vocale."""
        try:
            engine = pyttsx3.init()
            if engine is None:
                raise RuntimeError("pyttsx3.init() a retourné None")
            engine.setProperty("rate", self.rate)

            # Essayer de mettre une voix française
            try:
                voices = engine.getProperty("voices")
                for voice in voices:
                    if "french" in voice.name.lower() or "fr" in voice.id.lower():
                        engine.setProperty("voice", voice.id)
                        print(f"[Audio] Voix française sélectionnée : {voice.name}")
                        break
            except Exception:
                pass  # Voix par défaut si erreur

            while self._running:
                try:
                    message = self._queue.get(timeout=0.5)
                    if message is None:
                        break
                    engine.say(message)
                    engine.runAndWait()
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"[Audio] Erreur: {e}")
        except Exception as e:
            print(f"[Audio] Moteur vocal indisponible: {e}")
            self.enabled = False

    # ─── API publique ──────────────────────────────────────────────────────────

    def speak(self, message: str, priority: bool = False):
        """
        Ajoute un message à la file d'attente vocale.

        Args:
            message: Texte à prononcer.
            priority: Si True, vide la file avant d'ajouter.
        """
        if not self.enabled:
            return
        if priority:
            # Vider la file pour priorité absolue
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break
        if self._queue.qsize() < 3:
            self._queue.put(message)

    def speak_introduction(self, exercise_name: str):
        """
        Annonce complète de l'exercice : nom + instructions détaillées.
        À appeler quand le patient sélectionne un exercice.
        """
        infos = INSTRUCTIONS_VOCALES.get(exercise_name, INSTRUCTIONS_DEFAULT)
        self.speak(infos["intro"], priority=True)

    def speak_calibration(self):
        """Instructions pendant le compte à rebours de calibration."""
        self.speak(
            "Préparez-vous. Mettez-vous en position de départ. "
            "Gardez le dos bien droit. On commence dans trois secondes.",
            priority=True,
        )

    def speak_start(self, exercise_name: str):
        """Signal de départ — court et dynamique."""
        self.speak("C'est parti ! Allez-y !", priority=True)

    def speak_mouvement(self, exercise_name: str, phase: str):
        """
        Guide le mouvement en temps réel selon la phase.

        Args:
            exercise_name: Nom de l'exercice.
            phase: "montee", "tenue" ou "descente".
        """
        if phase == self._last_phase:
            return  # Évite la répétition
        self._last_phase = phase
        infos = INSTRUCTIONS_VOCALES.get(exercise_name, INSTRUCTIONS_DEFAULT)
        msg = infos.get(phase, "")
        if msg:
            self.speak(msg)

    def speak_rep(self, rep_number: int, target: int):
        """Annonce le numéro de répétition avec encouragement."""
        if rep_number >= target:
            self.speak("Bravo ! Exercice terminé ! Vous avez réussi !", priority=True)
        elif rep_number == target - 1:
            self.speak(f"{rep_number}. Plus qu'une répétition !")
        elif rep_number % 3 == 0:
            # Encouragement tous les 3 reps
            enc = random.choice(ENCOURAGEMENTS)
            self.speak(f"{rep_number} sur {target}. {enc}")
        else:
            self.speak(f"Répétition {rep_number}.")
        self._last_phase = None  # Reset phase pour la prochaine répétition

    def speak_compensation(self, message: str):
        """Alerte de compensation posturale."""
        # Choisir le bon message selon le type de compensation
        msg = ALERTES_COMPENSATION["default"]
        msg_lower = message.lower()
        if "dos" in msg_lower or "tronc" in msg_lower:
            msg = ALERTES_COMPENSATION["dos"]
        elif "épaule" in msg_lower or "epaule" in msg_lower:
            msg = ALERTES_COMPENSATION["epaule"]
        self.speak(msg, priority=True)

    def speak_end(self, score: float):
        """Bilan vocal de fin d'exercice."""
        score_int = int(score)
        if score >= 85:
            msg = (f"Excellent travail ! Votre score est de {score_int} sur cent. "
                   "C'est un très bon résultat, continuez ainsi !")
        elif score >= 70:
            msg = (f"Bien joué ! Vous avez obtenu {score_int} sur cent. "
                   "Bon travail, vous progressez !")
        elif score >= 50:
            msg = (f"Bon effort ! Score de {score_int} sur cent. "
                   "Continuez à pratiquer, vous allez vous améliorer !")
        else:
            msg = (f"Courage ! Score de {score_int} sur cent. "
                   "Ne vous découragez pas, chaque séance compte !")
        self.speak(msg, priority=True)

    def speak_pause(self):
        """Message de pause entre les exercices."""
        self.speak(
            "Très bien. Prenez une courte pause si nécessaire. "
            "Respirez profondément. Quand vous êtes prêt, choisissez le prochain exercice.",
            priority=True,
        )

    def speak_session_end(self, nb_exercices: int, score_moyen: float):
        """Résumé de fin de session."""
        self.speak(
            f"Félicitations ! Vous avez terminé votre séance de rééducation. "
            f"Vous avez réalisé {nb_exercices} exercices, "
            f"avec un score moyen de {int(score_moyen)} sur cent. "
            "Excellent travail ! À bientôt pour votre prochaine séance.",
            priority=True,
        )

    def stop(self):
        """Arrête le thread audio."""
        self._running = False
        self._queue.put(None)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
