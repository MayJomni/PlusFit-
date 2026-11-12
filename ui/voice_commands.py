"""
Reconnaissance vocale pour commander l'application à la voix.
Commandes en 4 langues : FR, EN, AR, ES.
Fonctionne hors-ligne avec CMU Sphinx ou en ligne avec Google.
"""

import threading
import queue
import time
from typing import Optional, Callable

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

# Mots-clés par langue et action
COMMANDES = {
    "fr": {
        "demarrer": ["commencer", "démarrer", "demarrer", "start", "allez", "go"],
        "arreter":  ["arrêter", "arreter", "stop", "fin", "pause"],
        "suivant":  ["suivant", "prochain", "next", "après"],
        "retour":   ["retour", "back", "précédent"],
        "pause":    ["pause", "attendre", "repos"],
    },
    "en": {
        "demarrer": ["start", "begin", "go", "commence"],
        "arreter":  ["stop", "end", "finish", "halt"],
        "suivant":  ["next", "continue", "forward"],
        "retour":   ["back", "return", "previous"],
        "pause":    ["pause", "wait", "rest"],
    },
    "ar": {
        "demarrer": ["ابدأ", "انطلق", "هيا"],
        "arreter":  ["توقف", "انتهى", "كفى"],
        "suivant":  ["التالي", "بعد"],
        "retour":   ["رجوع", "عودة"],
        "pause":    ["استراحة", "توقف مؤقت"],
    },
    "es": {
        "demarrer": ["comenzar", "empezar", "iniciar", "adelante"],
        "arreter":  ["parar", "detener", "fin", "stop"],
        "suivant":  ["siguiente", "próximo", "continuar"],
        "retour":   ["volver", "atrás", "regresar"],
        "pause":    ["pausa", "descanso"],
    },
}

LANG_SR = {"fr": "fr-FR", "en": "en-US", "ar": "ar-SA", "es": "es-ES"}


class VoiceCommandListener:
    """
    Écoute le microphone en continu et détecte les commandes vocales.

    Usage:
        listener = VoiceCommandListener(lang="fr", on_command=callback)
        listener.start()
        # ...
        listener.stop()
    """

    def __init__(self, lang: str = "fr", on_command: Optional[Callable] = None):
        self.lang = lang
        self.on_command = on_command
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.available = False
        self._last_command_time = 0.0
        self._cooldown = 2.0   # secondes entre deux commandes

        if not SR_AVAILABLE:
            print("[Voix] speech_recognition non installé — commandes vocales désactivées")
            return

        # Tester si un micro est disponible
        try:
            mic = sr.Microphone()
            with mic:
                pass
            self.available = True
            print("[Voix] ✓ Microphone détecté — commandes vocales actives")
        except Exception as e:
            print(f"[Voix] Microphone non disponible : {e}")

    def start(self):
        """Démarre l'écoute en arrière-plan."""
        if not self.available:
            return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Arrête l'écoute."""
        self._running = False

    def _listen_loop(self):
        """Boucle d'écoute continue."""
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.6

        try:
            mic = sr.Microphone()
        except Exception as e:
            print(f"[Voix] Erreur micro : {e}")
            return

        print("[Voix] Écoute démarrée...")
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)

        while self._running:
            try:
                with mic as source:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)

                # Essayer la reconnaissance Google (en ligne)
                try:
                    text = recognizer.recognize_google(
                        audio, language=LANG_SR.get(self.lang, "fr-FR")
                    ).lower()
                    print(f"[Voix] Entendu : '{text}'")
                    self._process(text)
                except sr.UnknownValueError:
                    pass  # Rien de reconnu — silence ou bruit
                except sr.RequestError:
                    # Pas de connexion — essai sphinx offline
                    try:
                        text = recognizer.recognize_sphinx(audio).lower()
                        self._process(text)
                    except Exception:
                        pass

            except sr.WaitTimeoutError:
                continue  # Pas de son pendant 5s — normal
            except Exception as e:
                if self._running:
                    time.sleep(1)

    def _process(self, text: str):
        """Cherche une commande dans le texte reconnu."""
        # Anti-spam
        now = time.time()
        if now - self._last_command_time < self._cooldown:
            return

        cmd = self._match_command(text)
        if cmd and self.on_command:
            print(f"[Voix] Commande détectée : {cmd}")
            self._last_command_time = now
            self.on_command(cmd)

    def _match_command(self, text: str) -> Optional[str]:
        """Cherche une correspondance avec les mots-clés."""
        cmds = COMMANDES.get(self.lang, COMMANDES["fr"])
        for action, mots in cmds.items():
            for mot in mots:
                if mot in text:
                    return action
        return None

    def set_lang(self, lang: str):
        """Change la langue de reconnaissance."""
        self.lang = lang
