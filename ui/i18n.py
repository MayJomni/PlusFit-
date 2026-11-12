# -*- coding: utf-8 -*-
"""
Système de traduction multi-langues pour PlusFit.
Langues supportées : Français (fr), Anglais (en), Arabe (ar), Espagnol (es).
"""

LANGUES = {
    "fr": {
        "nom": "Français", "drapeau": "🇫🇷", "rtl": False,
        "TITRE_APP": "Miroir de Rééducation",
        "SOUS_TITRE": "Système de rééducation assisté par intelligence artificielle",
        "BTN_COMMENCER": "COMMENCER",
        "BTN_DEMARRER": "DÉMARRER",
        "BTN_ARRETER": "ARRÊTER",
        "BTN_RETOUR": "← Retour",
        "BTN_SUIVANT": "Exercice suivant",
        "BTN_TERMINER_SESSION": "Terminer la session",
        "BTN_EXPORTER_PDF": "Exporter en PDF",
        "BTN_PLANNING": "📅 Mon Planning",
        "LABEL_PATIENT": "Identifiant du patient :",
        "LABEL_REPETITIONS": "Répétitions",
        "LABEL_SCORE": "Score",
        "LABEL_DUREE": "Durée",
        "LABEL_AMPLITUDE": "Amplitude moy.",
        "LABEL_COMPENSATIONS": "Compensations",
        "LABEL_EXERCICE": "Exercice",
        "LABEL_LANGUE": "Langue",
        "MSG_CHARGEMENT_IA": "Chargement du modèle IA...",
        "MSG_PREPAREZ_VOUS": "Préparez-vous...",
        "MSG_BRAVO": "Bravo ! Exercice terminé !",
        "MSG_EXCELLENT": "Excellent travail !",
        "MSG_PAUSE": "Prenez une pause si nécessaire.",
        "MSG_SESSION_TERMINEE": "Session terminée !",
        "MSG_SAUVEGARDE": "Session sauvegardée.",
        "MSG_FACE_CAMERA": "Placez-vous face à la caméra",
        "MSG_FATIGUE": "😴 Fatigue détectée — Faites une pause",
        "TITRE_RESULTATS": "Résultats",
        "TITRE_RESUME": "Résumé de la session",
        "TITRE_EXERCICES": "Choisissez un exercice",
        "TITRE_PLANNING": "Mon Planning de la semaine",
        "NAV_TOUS": "Tous",
        "NAV_BRAS": "Bras",
        "NAV_JAMBES": "Jambes",
        "NAV_EQUILIBRE_ASSIS": "Équilibre assis",
        "NAV_EQUILIBRE_DEBOUT": "Équilibre debout",
        "NAV_COGNITIF": "Cognitif",
        "GUIDE_MODELE": "Modèle à suivre",
        "MICRO_ACTIF": "🎤 Micro actif",
        "MICRO_INACTIF": "🎤 Micro désactivé",
        "JOURS": ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"],
        "JOURS_COMPLETS": ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"],
        "VERSION": "v1.0 — MoveNet - Python - OpenCV",
    },
    "en": {
        "nom": "English", "drapeau": "🇬🇧", "rtl": False,
        "TITRE_APP": "Rehabilitation Mirror",
        "SOUS_TITRE": "AI-assisted rehabilitation system",
        "BTN_COMMENCER": "START",
        "BTN_DEMARRER": "BEGIN",
        "BTN_ARRETER": "STOP",
        "BTN_RETOUR": "← Back",
        "BTN_SUIVANT": "Next exercise",
        "BTN_TERMINER_SESSION": "End session",
        "BTN_EXPORTER_PDF": "Export PDF",
        "BTN_PLANNING": "📅 My Schedule",
        "LABEL_PATIENT": "Patient ID:",
        "LABEL_REPETITIONS": "Repetitions",
        "LABEL_SCORE": "Score",
        "LABEL_DUREE": "Duration",
        "LABEL_AMPLITUDE": "Avg amplitude",
        "LABEL_COMPENSATIONS": "Compensations",
        "LABEL_EXERCICE": "Exercise",
        "LABEL_LANGUE": "Language",
        "MSG_CHARGEMENT_IA": "Loading AI model...",
        "MSG_PREPAREZ_VOUS": "Get ready...",
        "MSG_BRAVO": "Well done! Exercise complete!",
        "MSG_EXCELLENT": "Excellent work!",
        "MSG_PAUSE": "Take a break if needed.",
        "MSG_SESSION_TERMINEE": "Session complete!",
        "MSG_SAUVEGARDE": "Session saved.",
        "MSG_FACE_CAMERA": "Stand in front of the camera",
        "MSG_FATIGUE": "😴 Fatigue detected — Take a break",
        "TITRE_RESULTATS": "Results",
        "TITRE_RESUME": "Session Summary",
        "TITRE_EXERCICES": "Choose an exercise",
        "TITRE_PLANNING": "My Weekly Schedule",
        "NAV_TOUS": "All",
        "NAV_BRAS": "Arms",
        "NAV_JAMBES": "Legs",
        "NAV_EQUILIBRE_ASSIS": "Sitting balance",
        "NAV_EQUILIBRE_DEBOUT": "Standing balance",
        "NAV_COGNITIF": "Cognitive",
        "GUIDE_MODELE": "Follow the guide",
        "MICRO_ACTIF": "🎤 Mic active",
        "MICRO_INACTIF": "🎤 Mic off",
        "JOURS": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "JOURS_COMPLETS": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
        "VERSION": "v1.0 — MoveNet - Python - OpenCV",
    },
    "ar": {
        "nom": "العربية", "drapeau": "🇸🇦", "rtl": True,
        "TITRE_APP": "مرآة إعادة التأهيل",
        "SOUS_TITRE": "نظام إعادة التأهيل بمساعدة الذكاء الاصطناعي",
        "BTN_COMMENCER": "ابدأ",
        "BTN_DEMARRER": "انطلق",
        "BTN_ARRETER": "توقف",
        "BTN_RETOUR": "رجوع →",
        "BTN_SUIVANT": "التمرين التالي",
        "BTN_TERMINER_SESSION": "إنهاء الجلسة",
        "BTN_EXPORTER_PDF": "تصدير PDF",
        "BTN_PLANNING": "📅 جدولي",
        "LABEL_PATIENT": "رقم المريض:",
        "LABEL_REPETITIONS": "التكرارات",
        "LABEL_SCORE": "النتيجة",
        "LABEL_DUREE": "المدة",
        "LABEL_AMPLITUDE": "متوسط السعة",
        "LABEL_COMPENSATIONS": "التعويضات",
        "LABEL_EXERCICE": "التمرين",
        "LABEL_LANGUE": "اللغة",
        "MSG_CHARGEMENT_IA": "جاري تحميل الذكاء الاصطناعي...",
        "MSG_PREPAREZ_VOUS": "استعد...",
        "MSG_BRAVO": "أحسنت! اكتمل التمرين!",
        "MSG_EXCELLENT": "عمل ممتاز!",
        "MSG_PAUSE": "خذ استراحة إذا لزم الأمر.",
        "MSG_SESSION_TERMINEE": "اكتملت الجلسة!",
        "MSG_SAUVEGARDE": "تم حفظ الجلسة.",
        "MSG_FACE_CAMERA": "قف أمام الكاميرا",
        "MSG_FATIGUE": "😴 تم اكتشاف الإرهاق — خذ استراحة",
        "TITRE_RESULTATS": "النتائج",
        "TITRE_RESUME": "ملخص الجلسة",
        "TITRE_EXERCICES": "اختر تمريناً",
        "TITRE_PLANNING": "الجدول الأسبوعي",
        "NAV_TOUS": "الكل",
        "NAV_BRAS": "الذراعان",
        "NAV_JAMBES": "الساقان",
        "NAV_EQUILIBRE_ASSIS": "توازن جلوس",
        "NAV_EQUILIBRE_DEBOUT": "توازن قائم",
        "NAV_COGNITIF": "إدراكي",
        "GUIDE_MODELE": "اتبع النموذج",
        "MICRO_ACTIF": "🎤 الميكروفون نشط",
        "MICRO_INACTIF": "🎤 الميكروفون معطل",
        "JOURS": ["إث","ثل","أرب","خم","جم","سب","أح"],
        "JOURS_COMPLETS": ["الإثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت","الأحد"],
        "VERSION": "v1.0 — MoveNet - Python - OpenCV",
    },
    "es": {
        "nom": "Español", "drapeau": "🇪🇸", "rtl": False,
        "TITRE_APP": "Espejo de Rehabilitación",
        "SOUS_TITRE": "Sistema de rehabilitación asistido por inteligencia artificial",
        "BTN_COMMENCER": "COMENZAR",
        "BTN_DEMARRER": "INICIAR",
        "BTN_ARRETER": "DETENER",
        "BTN_RETOUR": "← Volver",
        "BTN_SUIVANT": "Siguiente ejercicio",
        "BTN_TERMINER_SESSION": "Terminar sesión",
        "BTN_EXPORTER_PDF": "Exportar PDF",
        "BTN_PLANNING": "📅 Mi Agenda",
        "LABEL_PATIENT": "ID del paciente:",
        "LABEL_REPETITIONS": "Repeticiones",
        "LABEL_SCORE": "Puntuación",
        "LABEL_DUREE": "Duración",
        "LABEL_AMPLITUDE": "Amplitud media",
        "LABEL_COMPENSATIONS": "Compensaciones",
        "LABEL_EXERCICE": "Ejercicio",
        "LABEL_LANGUE": "Idioma",
        "MSG_CHARGEMENT_IA": "Cargando modelo IA...",
        "MSG_PREPAREZ_VOUS": "Prepárate...",
        "MSG_BRAVO": "¡Muy bien! ¡Ejercicio completado!",
        "MSG_EXCELLENT": "¡Excelente trabajo!",
        "MSG_PAUSE": "Descansa si es necesario.",
        "MSG_SESSION_TERMINEE": "¡Sesión completada!",
        "MSG_SAUVEGARDE": "Sesión guardada.",
        "MSG_FACE_CAMERA": "Colóquese frente a la cámara",
        "MSG_FATIGUE": "😴 Fatiga detectada — Descansa",
        "TITRE_RESULTATS": "Resultados",
        "TITRE_RESUME": "Resumen de sesión",
        "TITRE_EXERCICES": "Elige un ejercicio",
        "TITRE_PLANNING": "Mi agenda semanal",
        "NAV_TOUS": "Todos",
        "NAV_BRAS": "Brazos",
        "NAV_JAMBES": "Piernas",
        "NAV_EQUILIBRE_ASSIS": "Equilibrio sentado",
        "NAV_EQUILIBRE_DEBOUT": "Equilibrio de pie",
        "NAV_COGNITIF": "Cognitivo",
        "GUIDE_MODELE": "Sigue el modelo",
        "MICRO_ACTIF": "🎤 Micrófono activo",
        "MICRO_INACTIF": "🎤 Micrófono inactivo",
        "JOURS": ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"],
        "JOURS_COMPLETS": ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"],
        "VERSION": "v1.0 — MoveNet - Python - OpenCV",
    },
}


class Translator:
    """Gestionnaire de traductions — Singleton."""
    _instance = None

    def __init__(self, lang: str = "fr"):
        self._lang = lang if lang in LANGUES else "fr"

    @classmethod
    def get_instance(cls, lang: str = "fr") -> "Translator":
        if cls._instance is None:
            cls._instance = cls(lang)
        return cls._instance

    def set_lang(self, lang: str):
        if lang in LANGUES:
            self._lang = lang
            print(f"[i18n] Langue : {LANGUES[lang]['nom']} {LANGUES[lang]['drapeau']}")

    def t(self, key: str, default: str = "") -> str:
        return LANGUES[self._lang].get(key, LANGUES["fr"].get(key, default or key))

    @property
    def lang(self) -> str:
        return self._lang

    @property
    def is_rtl(self) -> bool:
        return LANGUES[self._lang].get("rtl", False)

    def get_all_langs(self) -> list:
        return [{"code": c, "nom": i["nom"], "drapeau": i["drapeau"]} for c, i in LANGUES.items()]
