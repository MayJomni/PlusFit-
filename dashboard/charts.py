"""
Fonctions de création de graphiques Plotly pour le dashboard.

Graphiques réutilisables : courbes de progression, radar charts,
histogrammes, box plots, barres de compensations.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


COLORS = {
    "green": "#4CAF50", "orange": "#FF9800", "red": "#F44336",
    "blue": "#2196F3", "purple": "#9C27B0", "teal": "#009688", "gray": "#9E9E9E",
}


def score_progression_chart(df: pd.DataFrame, title: str = "Evolution du score",
                             group_by: str = "patient_id") -> go.Figure:
    """Courbe d'évolution du score au fil des sessions."""
    fig = px.line(df, x="date", y="avg_score", color=group_by, title=title,
                  labels={"date": "Date", "avg_score": "Score moyen", group_by: "Patient"},
                  markers=True)
    fig.update_layout(template="plotly_dark", yaxis_range=[0, 105], hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02))
    fig.add_hline(y=80, line_dash="dot", line_color=COLORS["green"], annotation_text="Excellent (80)")
    fig.add_hline(y=60, line_dash="dot", line_color=COLORS["orange"], annotation_text="Bon (60)")
    return fig


def radar_chart(scores_by_category: dict, title: str = "Score par categorie") -> go.Figure:
    """Radar chart des scores moyens par catégorie d'exercice."""
    categories = list(scores_by_category.keys())
    values = list(scores_by_category.values())
    categories.append(categories[0])
    values.append(values[0])
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill="toself",
                                   name="Score", line_color=COLORS["blue"],
                                   fillcolor="rgba(33, 150, 243, 0.3)"))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                      title=title, template="plotly_dark")
    return fig


def amplitude_histogram(df: pd.DataFrame, title: str = "Amplitude moyenne par exercice") -> go.Figure:
    """Histogramme horizontal des amplitudes moyennes par exercice."""
    grouped = df.groupby("exercise_name")["avg_amplitude"].mean().sort_values()
    fig = go.Figure(go.Bar(
        x=grouped.values, y=grouped.index, orientation="h",
        marker_color=[COLORS["green"] if v >= 100 else COLORS["orange"] if v >= 60
                      else COLORS["red"] for v in grouped.values]))
    fig.update_layout(title=title, xaxis_title="Amplitude moyenne (degres)",
                      template="plotly_dark", height=max(300, len(grouped) * 40))
    return fig


def score_boxplot(df: pd.DataFrame, exercise_name: str = "",
                  title: str = "Distribution des scores") -> go.Figure:
    """Box plot de la distribution des scores."""
    if exercise_name:
        title = f"Distribution des scores - {exercise_name}"
    fig = px.box(df, x="patient_id" if "patient_id" in df.columns else None,
                 y="score", color="patient_id" if "patient_id" in df.columns else None,
                 title=title, labels={"score": "Score", "patient_id": "Patient"})
    fig.update_layout(template="plotly_dark", showlegend=False)
    return fig


def compensation_bar_chart(df: pd.DataFrame, title: str = "Compensations par type") -> go.Figure:
    """Barres horizontales des compensations par type."""
    comp_counts = {}
    for _, row in df.iterrows():
        summary = row.get("compensation_summary", {})
        if isinstance(summary, dict):
            for comp_type, data in summary.get("types", {}).items():
                comp_counts[comp_type] = comp_counts.get(comp_type, 0) + data.get("count", 0)
    if not comp_counts:
        fig = go.Figure()
        fig.update_layout(title=title, template="plotly_dark",
                          annotations=[dict(text="Aucune compensation", showarrow=False,
                                          xref="paper", yref="paper", x=0.5, y=0.5)])
        return fig
    type_names = {"TRUNK_LEAN": "Inclinaison tronc", "SHOULDER_ELEVATION": "Elevation epaule",
                  "HIP_SHIFT": "Decalage hanches", "TRUNK_ROTATION": "Rotation tronc",
                  "HEAD_TILT": "Inclinaison tete"}
    labels = [type_names.get(k, k) for k in comp_counts.keys()]
    fig = go.Figure(go.Bar(x=list(comp_counts.values()), y=labels, orientation="h",
                           marker_color=COLORS["orange"]))
    fig.update_layout(title=title, xaxis_title="Nombre", template="plotly_dark")
    return fig


def trend_indicator(current: float, previous: float) -> dict:
    """Calcule l'indicateur de tendance."""
    delta = current - previous
    if delta > 2:
        return {"delta": f"+{delta:.1f}", "color": COLORS["green"], "arrow": "up"}
    elif delta < -2:
        return {"delta": f"{delta:.1f}", "color": COLORS["red"], "arrow": "down"}
    return {"delta": f"{delta:+.1f}", "color": COLORS["gray"], "arrow": "right"}
