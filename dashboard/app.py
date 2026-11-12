"""
Tableau de bord Streamlit pour le suivi multi-patients.

Dépendances supplémentaires :
    pip install streamlit plotly pandas

Lancement :
    cd rehab-mirror
    streamlit run dashboard/app.py

4 pages :
1. Vue d'ensemble
2. Détail patient
3. Analyse d'exercice
4. Rapport
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px

from dashboard.data_loader import (
    load_all_sessions, load_all_exercises,
    get_patient_sessions, get_patient_exercises,
    get_exercise_stats, get_patient_list, get_exercise_list,
)
from dashboard.charts import (
    score_progression_chart, radar_chart, amplitude_histogram,
    score_boxplot, compensation_bar_chart, trend_indicator,
)

# ─── Configuration de la page ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Miroir de Reeducation - Dashboard",
    page_icon="🪞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Chemin des sessions ──────────────────────────────────────────────────────
SESSIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sessions")


def score_color_html(score: float) -> str:
    """Retourne la couleur CSS pour un score."""
    if score >= 80:
        return "#4CAF50"
    elif score >= 60:
        return "#FF9800"
    return "#F44336"


# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

st.sidebar.title("Miroir de Reeducation")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["Vue d'ensemble", "Detail patient", "Analyse exercice", "Rapport"],
)

st.sidebar.markdown("---")
st.sidebar.caption("v1.0 - Systeme de reeducation assiste par IA")


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 1 : VUE D'ENSEMBLE
# ═══════════════════════════════════════════════════════════════════════════════

if page == "Vue d'ensemble":
    st.title("Vue d'ensemble")

    sessions_df = load_all_sessions(SESSIONS_DIR)
    exercises_df = load_all_exercises(SESSIONS_DIR)

    if sessions_df.empty:
        st.warning("Aucune session trouvee dans le dossier data/sessions/. "
                    "Lancez des exercices pour generer des donnees.")
        st.info(f"Dossier scanne : {os.path.abspath(SESSIONS_DIR)}")
        st.stop()

    # ── Métriques ──────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Patients", sessions_df["patient_id"].nunique())
    col2.metric("Sessions", len(sessions_df))
    col3.metric("Exercices", len(exercises_df) if not exercises_df.empty else 0)
    col4.metric("Score moyen", f"{sessions_df['avg_score'].mean():.1f}/100")

    st.markdown("---")

    # ── Graphique temporel ─────────────────────────────────────────────────
    st.subheader("Evolution des scores")
    fig = score_progression_chart(sessions_df)
    st.plotly_chart(fig, use_container_width=True)

    # ── Tableau des patients ───────────────────────────────────────────────
    st.subheader("Resume par patient")

    patient_stats = sessions_df.groupby("patient_id").agg(
        sessions=("session_id", "count"),
        score_moyen=("avg_score", "mean"),
        derniere_session=("date", "max"),
    ).round(1).sort_values("score_moyen", ascending=False)

    st.dataframe(
        patient_stats.style.format({
            "score_moyen": "{:.1f}",
        }),
        use_container_width=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 2 : DÉTAIL PATIENT
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Detail patient":
    st.title("Detail patient")

    patients = get_patient_list(SESSIONS_DIR)
    if not patients:
        st.warning("Aucun patient trouve.")
        st.stop()

    selected_patient = st.selectbox("Selectionner un patient", patients)

    patient_sessions = get_patient_sessions(selected_patient, SESSIONS_DIR)
    patient_exercises = get_patient_exercises(selected_patient, SESSIONS_DIR)

    if patient_sessions.empty:
        st.info("Aucune session pour ce patient.")
        st.stop()

    # ── Métriques du patient ───────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Sessions", len(patient_sessions))
    avg = patient_sessions["avg_score"].mean()
    col2.metric("Score moyen", f"{avg:.1f}")

    if len(patient_sessions) >= 2:
        last_scores = patient_sessions["avg_score"].tail(2).values
        trend = trend_indicator(last_scores[-1], last_scores[-2])
        col3.metric("Derniere session", f"{last_scores[-1]:.0f}",
                     delta=trend["delta"])
    else:
        col3.metric("Derniere session", f"{patient_sessions['avg_score'].iloc[-1]:.0f}")

    if not patient_exercises.empty:
        col4.metric("Compensations totales",
                     int(patient_exercises["compensations_count"].sum()))

    st.markdown("---")

    # ── Courbe de progression ──────────────────────────────────────────────
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Progression du score")
        fig = score_progression_chart(
            patient_sessions, title=f"Score - {selected_patient}",
            group_by="patient_id",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Score par categorie")
        if not patient_exercises.empty:
            # Mapper les exercices aux catégories
            cat_map = {}
            for _, row in patient_exercises.iterrows():
                name = row["exercise_name"]
                if "epaule" in name.lower() or "coude" in name.lower():
                    cat = "Bras"
                elif "genou" in name.lower() or "hanche" in name.lower():
                    cat = "Jambes"
                elif "tronc" in name.lower() or "inclinaison" in name.lower():
                    cat = "Equilibre"
                elif "cognitif" in name.lower():
                    cat = "Cognitif"
                else:
                    cat = "Autre"
                if cat not in cat_map:
                    cat_map[cat] = []
                cat_map[cat].append(row["score"])

            scores_by_cat = {k: sum(v) / len(v) for k, v in cat_map.items()}
            fig_radar = radar_chart(scores_by_cat, f"Profil - {selected_patient}")
            st.plotly_chart(fig_radar, use_container_width=True)

    # ── Amplitude par exercice ─────────────────────────────────────────────
    if not patient_exercises.empty:
        st.subheader("Amplitude moyenne par exercice")
        fig_amp = amplitude_histogram(patient_exercises)
        st.plotly_chart(fig_amp, use_container_width=True)

    # ── Tableau détaillé ───────────────────────────────────────────────────
    st.subheader("Historique des sessions")
    display_df = patient_sessions[["date", "exercises_completed", "avg_score",
                                     "total_duration_seconds"]].copy()
    display_df.columns = ["Date", "Exercices", "Score", "Duree (s)"]
    st.dataframe(display_df, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 3 : ANALYSE EXERCICE
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Analyse exercice":
    st.title("Analyse par exercice")

    exercise_list = get_exercise_list(SESSIONS_DIR)
    if not exercise_list:
        st.warning("Aucun exercice trouve.")
        st.stop()

    selected_exercise = st.selectbox("Selectionner un exercice", exercise_list)
    ex_df = get_exercise_stats(selected_exercise, SESSIONS_DIR)

    if ex_df.empty:
        st.info("Aucune donnee pour cet exercice.")
        st.stop()

    # ── Métriques ──────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Realisations", len(ex_df))
    col2.metric("Score moyen", f"{ex_df['score'].mean():.1f}")
    col3.metric("Amplitude moy.", f"{ex_df['avg_amplitude'].mean():.0f} deg")
    col4.metric("Compensations", int(ex_df["compensations_count"].sum()))

    st.markdown("---")

    # ── Box plot ───────────────────────────────────────────────────────────
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Distribution des scores")
        fig_box = score_boxplot(ex_df, selected_exercise)
        st.plotly_chart(fig_box, use_container_width=True)

    with col_right:
        st.subheader("Compensations")
        fig_comp = compensation_bar_chart(ex_df)
        st.plotly_chart(fig_comp, use_container_width=True)

    # ── Évolution de l'amplitude ───────────────────────────────────────────
    st.subheader("Evolution de l'amplitude")
    fig_amp = px.line(
        ex_df, x="date", y="avg_amplitude", color="patient_id",
        title=f"Amplitude - {selected_exercise}",
        labels={"avg_amplitude": "Amplitude (deg)", "date": "Date"},
        markers=True,
    )
    fig_amp.update_layout(template="plotly_dark")
    st.plotly_chart(fig_amp, use_container_width=True)

    # ── Tableau par patient ────────────────────────────────────────────────
    st.subheader("Performance par patient")
    perf = ex_df.groupby("patient_id").agg(
        realisations=("score", "count"),
        score_moyen=("score", "mean"),
        amplitude_moy=("avg_amplitude", "mean"),
        compensations=("compensations_count", "sum"),
    ).round(1).sort_values("score_moyen", ascending=False)
    st.dataframe(perf, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 4 : RAPPORT
# ═══════════════════════════════════════════════════════════════════════════════

elif page == "Rapport":
    st.title("Generation de rapport")

    patients = get_patient_list(SESSIONS_DIR)
    if not patients:
        st.warning("Aucun patient trouve.")
        st.stop()

    selected_patient = st.selectbox("Patient", patients)

    patient_sessions = get_patient_sessions(selected_patient, SESSIONS_DIR)
    patient_exercises = get_patient_exercises(selected_patient, SESSIONS_DIR)

    if patient_sessions.empty:
        st.info("Aucune session pour ce patient.")
        st.stop()

    # ── Résumé textuel ─────────────────────────────────────────────────────
    st.subheader(f"Resume - {selected_patient}")

    nb_sessions = len(patient_sessions)
    avg_score = patient_sessions["avg_score"].mean()
    total_reps = int(patient_exercises["total_reps"].sum()) if not patient_exercises.empty else 0
    total_comp = int(patient_exercises["compensations_count"].sum()) if not patient_exercises.empty else 0

    if nb_sessions >= 2:
        first = patient_sessions["avg_score"].iloc[0]
        last = patient_sessions["avg_score"].iloc[-1]
        evolution = last - first
        evo_text = f"+{evolution:.1f}" if evolution >= 0 else f"{evolution:.1f}"
    else:
        evo_text = "N/A (1 seule session)"

    st.markdown(f"""
    **Patient** : {selected_patient}

    **Nombre de sessions** : {nb_sessions}

    **Score moyen global** : {avg_score:.1f} / 100

    **Repetitions totales** : {total_reps}

    **Compensations totales** : {total_comp}

    **Evolution du score** : {evo_text} points
    """)

    # ── Export PDF ─────────────────────────────────────────────────────────
    st.markdown("---")

    if st.button("Generer le rapport PDF", type="primary"):
        try:
            from data.pdf_report import SessionReportPDF

            reporter = SessionReportPDF()
            # Préparer les données
            sessions_data = []
            for _, row in patient_sessions.iterrows():
                raw = row.get("_raw", {})
                if raw:
                    sessions_data.append(raw)

            output_path = os.path.join(
                SESSIONS_DIR, f"rapport_{selected_patient}.pdf"
            )

            if sessions_data:
                reporter.generate_patient_report(
                    selected_patient, sessions_data, output_path
                )
                st.success(f"Rapport PDF genere : {output_path}")

                # Proposer le téléchargement
                if os.path.exists(output_path):
                    with open(output_path, "rb") as f:
                        st.download_button(
                            "Telecharger le PDF",
                            f.read(),
                            file_name=f"rapport_{selected_patient}.pdf",
                            mime="application/pdf",
                        )
            else:
                st.error("Impossible de preparer les donnees pour le rapport.")

        except ImportError:
            st.error("fpdf2 n'est pas installe. Executez : pip install fpdf2")
        except Exception as e:
            st.error(f"Erreur : {e}")
