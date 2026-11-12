"""
Génération de rapports PDF pour le Miroir de Rééducation.

Utilise fpdf2 pour créer des rapports professionnels en français.
Dépendance : pip install fpdf2

Trois types de rapports :
1. Rapport de session (une séance)
2. Rapport patient (évolution multi-sessions)
3. Rapport global (tous les patients)
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False
    print("[PDF] fpdf2 non installe. Installez avec : pip install fpdf2")


# ─── Couleurs ──────────────────────────────────────────────────────────────────
COLOR_GREEN = (76, 175, 80)
COLOR_ORANGE = (255, 152, 0)
COLOR_RED = (244, 67, 54)
COLOR_BLUE = (33, 150, 243)
COLOR_DARK = (30, 30, 46)
COLOR_GRAY = (100, 100, 100)
COLOR_LIGHT_GRAY = (220, 220, 220)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)


def _score_color(score: float):
    """Retourne le tuple RGB correspondant au score."""
    if score >= 80:
        return COLOR_GREEN
    elif score >= 60:
        return COLOR_ORANGE
    return COLOR_RED


def _safe_text(text: str) -> str:
    """Nettoie le texte pour la compatibilité PDF (remplace les emojis)."""
    replacements = {
        "\U0001fa9e": "[M]", "\U0001f4ca": "[G]", "\U0001f9be": "[Bras]",
        "\U0001f9b5": "[Jambe]", "\U0001fa91": "[Assis]", "\U0001f9cd": "[Debout]",
        "\U0001f9e0": "[Cognitif]", "\u2705": "[OK]", "\u26a0": "[!]",
        "\u26d4": "[X]", "\u25ba": ">",
    }
    for emoji, repl in replacements.items():
        text = text.replace(emoji, repl)
    return text.encode("latin-1", "replace").decode("latin-1")


class SessionReportPDF:
    """Générateur de rapports PDF pour les sessions de rééducation."""

    def generate_session_report(self, session_data: dict, output_path: str):
        """
        Génère un rapport PDF pour une seule session.

        Args:
            session_data: Dictionnaire des données de session (format JSON).
            output_path: Chemin du fichier PDF de sortie.
        """
        if not FPDF_AVAILABLE:
            raise ImportError("fpdf2 est requis. Installez avec : pip install fpdf2")

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()

        self._add_header(pdf, session_data)
        self._add_session_info(pdf, session_data)
        self._add_exercises_table(pdf, session_data.get("exercises", []))
        self._add_score_section(pdf, session_data)
        self._add_score_bars(pdf, session_data.get("exercises", []))
        self._add_compensation_summary(pdf, session_data.get("exercises", []))
        self._add_recommendations(pdf, session_data)
        self._add_footer(pdf)

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        pdf.output(output_path)
        print(f"[PDF] Rapport de session genere : {output_path}")

    def generate_patient_report(
        self, patient_id: str, sessions: List[dict], output_path: str
    ):
        """
        Génère un rapport complet pour un patient (multi-sessions).

        Args:
            patient_id: Identifiant du patient.
            sessions: Liste des données de sessions.
            output_path: Chemin du fichier PDF de sortie.
        """
        if not FPDF_AVAILABLE:
            raise ImportError("fpdf2 est requis.")

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()

        # En-tête
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(*COLOR_BLUE)
        pdf.cell(0, 15, _safe_text("Rapport patient"), ln=True, align="C")
        pdf.set_font("Helvetica", "", 14)
        pdf.set_text_color(*COLOR_BLACK)
        pdf.cell(0, 10, f"Patient : {patient_id}", ln=True, align="C")

        if sessions:
            dates = [s.get("date", "")[:10] for s in sessions]
            pdf.cell(0, 8, f"Periode : {min(dates)} au {max(dates)}", ln=True, align="C")
        pdf.ln(10)

        # Statistiques globales
        total_reps = 0
        total_comp = 0
        total_duration = 0
        scores = []
        for s in sessions:
            for ex in s.get("exercises", []):
                total_reps += ex.get("total_reps", 0)
                total_comp += ex.get("compensations_count", 0)
                total_duration += ex.get("duration_seconds", 0)
            scores.append(s.get("avg_score", 0))

        self._add_section_title(pdf, "Statistiques globales")
        stats = [
            f"Sessions : {len(sessions)}",
            f"Repetitions totales : {total_reps}",
            f"Compensations totales : {total_comp}",
            f"Temps total : {int(total_duration // 60)} min {int(total_duration % 60)} s",
            f"Score moyen : {sum(scores) / len(scores):.1f} / 100" if scores else "Score moyen : N/A",
        ]
        pdf.set_font("Helvetica", "", 12)
        for stat in stats:
            pdf.cell(0, 8, _safe_text(stat), ln=True)
        pdf.ln(5)

        # Tableau récapitulatif des sessions
        self._add_section_title(pdf, "Recapitulatif par session")
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(*COLOR_BLUE)
        pdf.set_text_color(*COLOR_WHITE)
        col_widths = [40, 30, 35, 35, 30, 20]
        headers = ["Date", "Exercices", "Reps", "Amplitude", "Comp.", "Score"]
        for w, h in zip(col_widths, headers):
            pdf.cell(w, 8, h, border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*COLOR_BLACK)
        for i, s in enumerate(sessions):
            fill = i % 2 == 0
            if fill:
                pdf.set_fill_color(*COLOR_LIGHT_GRAY)
            exs = s.get("exercises", [])
            date_str = s.get("date", "")[:10]
            nb_ex = len(exs)
            total_r = sum(e.get("total_reps", 0) for e in exs)
            avg_amp = sum(e.get("avg_amplitude", 0) for e in exs) / max(1, nb_ex)
            total_c = sum(e.get("compensations_count", 0) for e in exs)
            avg_s = s.get("avg_score", 0)
            vals = [date_str, str(nb_ex), str(total_r), f"{avg_amp:.0f} deg",
                    str(total_c), f"{avg_s:.0f}"]
            for w, v in zip(col_widths, vals):
                pdf.cell(w, 7, v, border=1, fill=fill, align="C")
            pdf.ln()
        pdf.ln(5)

        # Barres de progression des scores
        self._add_section_title(pdf, "Evolution du score")
        if scores:
            bar_max_width = 120
            for i, (s, sc) in enumerate(zip(sessions, scores)):
                date_str = s.get("date", "")[:10]
                pdf.set_font("Helvetica", "", 9)
                pdf.cell(35, 7, date_str)
                bar_width = max(1, (sc / 100) * bar_max_width)
                color = _score_color(sc)
                pdf.set_fill_color(*color)
                pdf.cell(bar_width, 7, "", fill=True)
                pdf.set_fill_color(*COLOR_WHITE)
                pdf.cell(bar_max_width - bar_width, 7, "")
                pdf.cell(20, 7, f"  {sc:.0f}", align="L")
                pdf.ln()
        pdf.ln(5)

        # Meilleur et pire exercice
        if sessions:
            all_exercises = {}
            for s in sessions:
                for ex in s.get("exercises", []):
                    name = ex.get("exercise_name", "Inconnu")
                    if name not in all_exercises:
                        all_exercises[name] = []
                    all_exercises[name].append(ex.get("score", 0))

            if all_exercises:
                avg_by_ex = {n: sum(sc) / len(sc) for n, sc in all_exercises.items()}
                best = max(avg_by_ex, key=avg_by_ex.get)
                worst = min(avg_by_ex, key=avg_by_ex.get)

                self._add_section_title(pdf, "Points forts et axes d'amelioration")
                pdf.set_font("Helvetica", "", 11)
                pdf.set_text_color(*COLOR_GREEN)
                pdf.cell(0, 8, _safe_text(f"Meilleur exercice : {best} ({avg_by_ex[best]:.0f}/100)"), ln=True)
                pdf.set_text_color(*COLOR_RED)
                pdf.cell(0, 8, _safe_text(f"A ameliorer : {worst} ({avg_by_ex[worst]:.0f}/100)"), ln=True)
                pdf.set_text_color(*COLOR_BLACK)

            if len(scores) >= 2:
                improvement = scores[-1] - scores[0]
                pdf.ln(3)
                pdf.set_font("Helvetica", "B", 12)
                if improvement > 0:
                    pdf.set_text_color(*COLOR_GREEN)
                    pdf.cell(0, 8, f"Amelioration : +{improvement:.1f} points depuis la 1ere session", ln=True)
                elif improvement < 0:
                    pdf.set_text_color(*COLOR_RED)
                    pdf.cell(0, 8, f"Regression : {improvement:.1f} points depuis la 1ere session", ln=True)
                else:
                    pdf.set_text_color(*COLOR_ORANGE)
                    pdf.cell(0, 8, "Score stable depuis la 1ere session", ln=True)
                pdf.set_text_color(*COLOR_BLACK)

        self._add_footer(pdf)
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        pdf.output(output_path)
        print(f"[PDF] Rapport patient genere : {output_path}")

    def generate_summary_report(self, all_sessions: List[dict], output_path: str):
        """
        Génère un rapport global de tous les patients.

        Args:
            all_sessions: Liste de toutes les sessions (tous patients).
            output_path: Chemin du fichier PDF de sortie.
        """
        if not FPDF_AVAILABLE:
            raise ImportError("fpdf2 est requis.")

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()

        pdf.set_font("Helvetica", "B", 24)
        pdf.set_text_color(*COLOR_BLUE)
        pdf.cell(0, 15, "Rapport global - Miroir de Reeducation", ln=True, align="C")
        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(*COLOR_GRAY)
        pdf.cell(0, 8, f"Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')}", ln=True, align="C")
        pdf.ln(10)

        patients = {}
        for s in all_sessions:
            pid = s.get("patient_id", "inconnu")
            if pid not in patients:
                patients[pid] = []
            patients[pid].append(s)

        self._add_section_title(pdf, "Vue d'ensemble")
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 8, f"Nombre de patients : {len(patients)}", ln=True)
        pdf.cell(0, 8, f"Nombre total de sessions : {len(all_sessions)}", ln=True)
        pdf.ln(5)

        self._add_section_title(pdf, "Classement par score moyen")
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(*COLOR_BLUE)
        pdf.set_text_color(*COLOR_WHITE)

        col_widths = [50, 30, 40, 30, 40]
        headers = ["Patient", "Sessions", "Dernier score", "Tendance", "Score moyen"]
        for w, h in zip(col_widths, headers):
            pdf.cell(w, 8, h, border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*COLOR_BLACK)

        patient_avgs = {}
        for pid, sess in patients.items():
            scores = [s.get("avg_score", 0) for s in sess]
            patient_avgs[pid] = sum(scores) / len(scores) if scores else 0

        for pid in sorted(patient_avgs, key=patient_avgs.get, reverse=True):
            sess = patients[pid]
            scores = [s.get("avg_score", 0) for s in sess]
            avg = patient_avgs[pid]
            last = scores[-1] if scores else 0
            trend = ""
            if len(scores) >= 2:
                diff = scores[-1] - scores[-2]
                trend = f"+{diff:.0f}" if diff >= 0 else f"{diff:.0f}"
            vals = [pid, str(len(sess)), f"{last:.0f}", trend, f"{avg:.0f}"]
            for w, v in zip(col_widths, vals):
                pdf.cell(w, 7, v, border=1, align="C")
            pdf.ln()

        self._add_footer(pdf)
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        pdf.output(output_path)
        print(f"[PDF] Rapport global genere : {output_path}")

    # ═══════════════════════════════════════════════════════════════════════
    #  COMPOSANTS INTERNES
    # ═══════════════════════════════════════════════════════════════════════

    def _add_header(self, pdf: "FPDF", session_data: dict):
        """En-tête du rapport."""
        pdf.set_font("Helvetica", "B", 24)
        pdf.set_text_color(*COLOR_BLUE)
        pdf.cell(0, 15, "Miroir de Reeducation", ln=True, align="C")
        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(*COLOR_GRAY)
        pdf.cell(0, 8, "Rapport de session", ln=True, align="C")
        pdf.set_draw_color(*COLOR_BLUE)
        pdf.set_line_width(0.5)
        pdf.line(20, pdf.get_y() + 3, 190, pdf.get_y() + 3)
        pdf.ln(8)

    def _add_session_info(self, pdf: "FPDF", session_data: dict):
        """Informations de la session."""
        self._add_section_title(pdf, "Informations de la session")
        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(*COLOR_BLACK)

        date_str = session_data.get("date", "N/A")
        try:
            dt = datetime.fromisoformat(date_str)
            date_str = dt.strftime("%d/%m/%Y a %H:%M")
        except (ValueError, TypeError):
            pass

        info = [
            f"Patient : {session_data.get('patient_id', 'N/A')}",
            f"Date : {date_str}",
            f"Duree : {session_data.get('total_duration_seconds', 0):.0f} secondes",
            f"Exercices : {len(session_data.get('exercises', []))}",
        ]
        for line in info:
            pdf.cell(0, 7, _safe_text(line), ln=True)
        pdf.ln(5)

    def _add_exercises_table(self, pdf: "FPDF", exercises: List[dict]):
        """Tableau des exercices."""
        if not exercises:
            return
        self._add_section_title(pdf, "Detail des exercices")
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(*COLOR_BLUE)
        pdf.set_text_color(*COLOR_WHITE)
        col_widths = [55, 25, 30, 25, 25, 30]
        headers = ["Exercice", "Reps", "Amplitude", "Comp.", "Duree", "Score"]
        for w, h in zip(col_widths, headers):
            pdf.cell(w, 8, h, border=1, fill=True, align="C")
        pdf.ln()
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*COLOR_BLACK)
        for i, ex in enumerate(exercises):
            fill = i % 2 == 0
            if fill:
                pdf.set_fill_color(*COLOR_LIGHT_GRAY)
            name = _safe_text(ex.get("exercise_name", "N/A"))[:28]
            reps = f"{ex.get('total_reps', 0)}/{ex.get('target_reps', 10)}"
            amp = f"{ex.get('avg_amplitude', 0):.0f} deg"
            comp = str(ex.get("compensations_count", 0))
            dur = f"{ex.get('duration_seconds', 0):.0f}s"
            score = f"{ex.get('score', 0):.0f}"
            vals = [name, reps, amp, comp, dur, score]
            for w, v in zip(col_widths, vals):
                pdf.cell(w, 7, v, border=1, fill=fill, align="C")
            pdf.ln()
        pdf.ln(5)

    def _add_score_section(self, pdf: "FPDF", session_data: dict):
        """Section score global."""
        avg_score = session_data.get("avg_score", 0)
        self._add_section_title(pdf, "Score global")
        pdf.set_font("Helvetica", "B", 36)
        color = _score_color(avg_score)
        pdf.set_text_color(*color)
        pdf.cell(0, 20, f"{avg_score:.0f} / 100", ln=True, align="C")
        pdf.set_text_color(*COLOR_BLACK)
        pdf.set_font("Helvetica", "I", 14)
        if avg_score >= 80:
            pdf.cell(0, 10, "Excellent travail !", ln=True, align="C")
        elif avg_score >= 60:
            pdf.cell(0, 10, "Bon travail, continuez vos efforts !", ln=True, align="C")
        else:
            pdf.cell(0, 10, "Continuez, chaque session compte !", ln=True, align="C")
        pdf.ln(5)

    def _add_score_bars(self, pdf: "FPDF", exercises: List[dict]):
        """Barres horizontales des scores par exercice."""
        if not exercises:
            return
        self._add_section_title(pdf, "Scores par exercice")
        bar_max_width = 100
        for ex in exercises:
            name = _safe_text(ex.get("exercise_name", "N/A"))[:25]
            score = ex.get("score", 0)
            bar_width = max(1, (score / 100) * bar_max_width)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(55, 7, name)
            color = _score_color(score)
            pdf.set_fill_color(*color)
            pdf.cell(bar_width, 7, "", fill=True)
            pdf.set_fill_color(*COLOR_WHITE)
            pdf.cell(bar_max_width - bar_width, 7, "")
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(20, 7, f"  {score:.0f}", align="L")
            pdf.ln()
        pdf.ln(5)

    def _add_compensation_summary(self, pdf: "FPDF", exercises: List[dict]):
        """Résumé des compensations."""
        total_comp = sum(ex.get("compensations_count", 0) for ex in exercises)
        if total_comp == 0:
            self._add_section_title(pdf, "Compensations")
            pdf.set_font("Helvetica", "", 12)
            pdf.set_text_color(*COLOR_GREEN)
            pdf.cell(0, 8, "Aucune compensation detectee. Excellent !", ln=True)
            pdf.set_text_color(*COLOR_BLACK)
            pdf.ln(5)
            return

        self._add_section_title(pdf, f"Compensations ({total_comp} au total)")
        comp_types = {}
        for ex in exercises:
            summary = ex.get("compensation_summary", {})
            for comp_type, data in summary.get("types", {}).items():
                if comp_type not in comp_types:
                    comp_types[comp_type] = {"count": 0, "max_severity": "mild"}
                comp_types[comp_type]["count"] += data.get("count", 0)
                sev_order = {"mild": 0, "moderate": 1, "severe": 2}
                if sev_order.get(data.get("max_severity", "mild"), 0) > sev_order.get(
                    comp_types[comp_type]["max_severity"], 0
                ):
                    comp_types[comp_type]["max_severity"] = data["max_severity"]

        type_names = {
            "TRUNK_LEAN": "Inclinaison du tronc",
            "SHOULDER_ELEVATION": "Elevation de l'epaule",
            "HIP_SHIFT": "Decalage des hanches",
            "TRUNK_ROTATION": "Rotation du tronc",
            "HEAD_TILT": "Inclinaison de la tete",
        }
        pdf.set_font("Helvetica", "", 11)
        for ctype, data in sorted(comp_types.items(), key=lambda x: x[1]["count"], reverse=True):
            name = type_names.get(ctype, ctype)
            sev = data["max_severity"]
            color = {"mild": COLOR_ORANGE, "moderate": COLOR_RED, "severe": COLOR_RED}.get(sev, COLOR_GRAY)
            pdf.set_text_color(*color)
            pdf.cell(0, 7, f"  - {name} : {data['count']} fois (severite max : {sev})", ln=True)
        pdf.set_text_color(*COLOR_BLACK)
        pdf.ln(5)

    def _add_recommendations(self, pdf: "FPDF", session_data: dict):
        """Recommandations automatiques basées sur les résultats."""
        exercises = session_data.get("exercises", [])
        if not exercises:
            return
        self._add_section_title(pdf, "Recommandations")
        pdf.set_font("Helvetica", "", 11)
        recommendations = []
        total_comp = sum(ex.get("compensations_count", 0) for ex in exercises)
        if total_comp > 5:
            recommendations.append(
                "- Travailler le maintien postural : des compensations frequentes "
                "ont ete detectees. Concentrez-vous sur le controle du tronc."
            )
        low_score_exercises = [ex for ex in exercises if ex.get("score", 0) < 60]
        if low_score_exercises:
            names = ", ".join(_safe_text(ex.get("exercise_name", ""))[:20] for ex in low_score_exercises)
            recommendations.append(f"- Exercices a retravailler : {names}. Reduisez le nombre de repetitions si necessaire.")
        low_amp = [ex for ex in exercises if ex.get("avg_amplitude", 0) < 60]
        if low_amp:
            recommendations.append(
                "- L'amplitude de certains mouvements est limitee. "
                "Echauffez-vous bien et allez progressivement plus loin."
            )
        if not recommendations:
            recommendations.append("- Excellente session ! Maintenez cette qualite de mouvement.")
            recommendations.append("- Vous pouvez augmenter le nombre de repetitions pour progresser davantage.")
        for rec in recommendations:
            pdf.multi_cell(0, 7, _safe_text(rec))
            pdf.ln(2)

    def _add_section_title(self, pdf: "FPDF", title: str):
        """Ajoute un titre de section."""
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*COLOR_BLUE)
        pdf.cell(0, 10, _safe_text(title), ln=True)
        pdf.set_draw_color(*COLOR_LIGHT_GRAY)
        pdf.set_line_width(0.3)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(3)
        pdf.set_text_color(*COLOR_BLACK)

    def _add_footer(self, pdf: "FPDF"):
        """Pied de page."""
        pdf.ln(10)
        pdf.set_draw_color(*COLOR_LIGHT_GRAY)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(3)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*COLOR_GRAY)
        pdf.cell(0, 5, f"Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')} "
                        "- Miroir de Reeducation v1.0", align="C")


# ═══════════════════════════════════════════════════════════════════════════════
#  FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def generate_report_from_file(session_json_path: str, output_pdf_path: str):
    """
    Charge un fichier JSON de session et génère le PDF correspondant.

    Args:
        session_json_path: Chemin vers le fichier JSON de session.
        output_pdf_path: Chemin du fichier PDF de sortie.
    """
    with open(session_json_path, "r", encoding="utf-8") as f:
        session_data = json.load(f)
    reporter = SessionReportPDF()
    reporter.generate_session_report(session_data, output_pdf_path)


def generate_patient_report_from_dir(
    sessions_dir: str, patient_id: str, output_pdf_path: str
):
    """
    Charge toutes les sessions d'un patient et génère un rapport complet.

    Args:
        sessions_dir: Dossier contenant les fichiers JSON de session.
        patient_id: Identifiant du patient à filtrer.
        output_pdf_path: Chemin du fichier PDF de sortie.
    """
    sessions = []
    for filename in sorted(os.listdir(sessions_dir)):
        if filename.endswith(".json") and patient_id in filename:
            filepath = os.path.join(sessions_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                sessions.append(json.load(f))
    if not sessions:
        print(f"[PDF] Aucune session trouvee pour le patient '{patient_id}'.")
        return
    reporter = SessionReportPDF()
    reporter.generate_patient_report(patient_id, sessions, output_pdf_path)
