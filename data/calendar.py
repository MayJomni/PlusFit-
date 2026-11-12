"""
Calendrier de séances de rééducation.
Permet de planifier, suivre et analyser les séances hebdomadaires.
"""

import json
import os
import uuid
from datetime import datetime, timedelta, date
from typing import List, Optional


JOURS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


class SessionCalendar:
    """
    Gestion du planning hebdomadaire de rééducation.

    Format du fichier calendar.json :
    {
      "patient001": {
        "sessions_planifiees": [
          {
            "id": "uuid",
            "jour": "lundi",
            "heure": "10:00",
            "exercises": ["Flexion épaule gauche", "Extension genou gauche"],
            "recurrent": true,
            "completions": ["2026-11-11", "2026-11-04"]
          }
        ]
      }
    }
    """

    def __init__(self, calendar_file: str = "data/calendar.json"):
        self.calendar_file = calendar_file
        self._data: dict = {}
        self._load()

    def _load(self):
        """Charge le calendrier depuis le fichier JSON."""
        if os.path.exists(self.calendar_file):
            try:
                with open(self.calendar_file, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}
        else:
            self._data = {}
            self._create_demo()

    def _save(self):
        """Sauvegarde le calendrier."""
        os.makedirs(os.path.dirname(self.calendar_file), exist_ok=True)
        with open(self.calendar_file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def _create_demo(self):
        """Crée un planning de démonstration pour patient001."""
        demo_sessions = [
            {
                "id": str(uuid.uuid4()),
                "jour": "lundi",
                "heure": "10:00",
                "exercises": ["Flexion épaule gauche", "Extension genou gauche"],
                "recurrent": True,
                "completions": [],
            },
            {
                "id": str(uuid.uuid4()),
                "jour": "mercredi",
                "heure": "14:30",
                "exercises": ["Abduction épaule droite", "Flexion coude gauche"],
                "recurrent": True,
                "completions": [],
            },
            {
                "id": str(uuid.uuid4()),
                "jour": "vendredi",
                "heure": "11:00",
                "exercises": ["Transfert de poids latéral (debout)", "Extension genou droit"],
                "recurrent": True,
                "completions": [],
            },
        ]
        self._data = {"patient001": {"sessions_planifiees": demo_sessions}}
        self._save()

    def _get_patient(self, patient_id: str) -> dict:
        if patient_id not in self._data:
            self._data[patient_id] = {"sessions_planifiees": []}
        return self._data[patient_id]

    def add_session(self, patient_id: str, jour: str, heure: str,
                    exercises: List[str], recurrent: bool = True) -> str:
        """Planifie une nouvelle séance. Retourne l'ID créé."""
        session_id = str(uuid.uuid4())
        session = {
            "id": session_id,
            "jour": jour.lower(),
            "heure": heure,
            "exercises": exercises,
            "recurrent": recurrent,
            "completions": [],
        }
        self._get_patient(patient_id)["sessions_planifiees"].append(session)
        self._save()
        return session_id

    def get_today_sessions(self, patient_id: str) -> List[dict]:
        """Retourne les séances prévues aujourd'hui."""
        today = JOURS_FR[date.today().weekday()]
        sessions = self._get_patient(patient_id)["sessions_planifiees"]
        return [s for s in sessions if s["jour"] == today]

    def get_week_schedule(self, patient_id: str) -> dict:
        """
        Retourne le planning de la semaine courante.

        Retourne: dict {jour: [sessions]} avec statut de chaque session.
        """
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        sessions = self._get_patient(patient_id)["sessions_planifiees"]

        schedule = {j: [] for j in JOURS_FR}
        for s in sessions:
            jour = s["jour"]
            if jour not in schedule:
                continue
            # Calculer la date de cette session cette semaine
            jour_idx = JOURS_FR.index(jour)
            session_date = (monday + timedelta(days=jour_idx)).isoformat()
            done = session_date in s.get("completions", [])
            missed = not done and session_date < today.isoformat()

            schedule[jour].append({
                **s,
                "statut": "fait" if done else ("manque" if missed else "prevu"),
                "date": session_date,
            })
        return schedule

    def mark_completed(self, patient_id: str, session_id: str,
                       session_date: Optional[str] = None):
        """Marque une séance comme réalisée."""
        if session_date is None:
            session_date = date.today().isoformat()
        sessions = self._get_patient(patient_id)["sessions_planifiees"]
        for s in sessions:
            if s["id"] == session_id:
                if session_date not in s["completions"]:
                    s["completions"].append(session_date)
                self._save()
                return

    def get_compliance_rate(self, patient_id: str, weeks: int = 4) -> float:
        """Taux d'observance sur N semaines (0–100%)."""
        sessions = self._get_patient(patient_id)["sessions_planifiees"]
        if not sessions:
            return 0.0

        today = date.today()
        start = today - timedelta(weeks=weeks)
        total_attendu = 0
        total_realise = 0

        for s in sessions:
            if not s.get("recurrent"):
                continue
            jour_idx = JOURS_FR.index(s["jour"])
            # Compter les occurrences dans la période
            d = start + timedelta(days=(jour_idx - start.weekday()) % 7)
            while d <= today:
                total_attendu += 1
                if d.isoformat() in s.get("completions", []):
                    total_realise += 1
                d += timedelta(weeks=1)

        if total_attendu == 0:
            return 0.0
        return round(100 * total_realise / total_attendu, 1)

    def delete_session(self, patient_id: str, session_id: str):
        """Supprime une séance planifiée."""
        patient = self._get_patient(patient_id)
        patient["sessions_planifiees"] = [
            s for s in patient["sessions_planifiees"] if s["id"] != session_id
        ]
        self._save()
