"""
Module de feedback audio (synthèse vocale).

Utilise pyttsx3 pour donner des indications vocales au patient
pendant les exercices. Les messages sont en français.
"""

import threading
import queue
from typing import Optional

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


class AudioFeedback:
    """
    Feedback audio non-bloquant via pyttsx3.

    Les messages sont mis en file d'attente et prononcés
    dans un thread séparé pour ne pas bloquer la boucle vidéo.
    """

    def __init__(self, rate: int = 130, enabled: bool = True):
        """
        Args:
            rate: Vitesse de parole (mots/min). 130 = lent, adapté aux PA.
            enabled: Active/désactive l'audio.
        """
        self.enabled = enabled and PYTTSX3_AVAILABLE
        self.rate = rate
        self._queue: queue.Queue = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._running = False

        if self.enabled:
            self._start_thread()

    def _start_thread(self):
        """Démarre le thread de synthèse vocale."""
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self):
        """Boucle du worker de synthèse vocale."""
        engine = pyttsx3.init()
        engine.setProperty("rate", self.rate)

        # Essayer de mettre une voix française
        voices = engine.getProperty("voices")
        for voice in voices:
            if "french" in voice.name.lower() or "fr" in voice.id.lower():
                engine.setProperty("voice", voice.id)
                break

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

    def speak(self, message: str):
        """
        Ajoute un message à la file d'attente vocale.

        Args:
            message: Texte à prononcer en français.
        """
        if not self.enabled:
            return
        # Éviter l'accumulation de messages
        if self._queue.qsize() < 3:
            self._queue.put(message)

    def speak_rep(self, rep_number: int, target: int):
        """Annonce le numéro de répétition."""
        if rep_number == target:
            self.speak("Bravo ! Exercice terminé !")
        elif rep_number == target - 1:
            self.speak(f"{rep_number}. Plus qu'une !")
        else:
            self.speak(str(rep_number))

    def speak_compensation(self, message: str):
        """Annonce une alerte de compensation."""
        self.speak(message)

    def speak_start(self, exercise_name: str):
        """Annonce le début d'un exercice."""
        self.speak(f"Exercice : {exercise_name}. Prêt ? C'est parti !")

    def speak_end(self, score: float):
        """Annonce la fin d'un exercice avec le score."""
        if score >= 80:
            self.speak(f"Excellent ! Score : {int(score)} sur 100")
        elif score >= 60:
            self.speak(f"Bien joué ! Score : {int(score)} sur 100")
        else:
            self.speak(f"Bon effort. Score : {int(score)} sur 100. On continue !")

    def stop(self):
        """Arrête le thread audio."""
        self._running = False
        self._queue.put(None)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
