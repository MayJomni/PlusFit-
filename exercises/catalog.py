"""
Catalogue des 12 exercices de rééducation.

Fournit une fonction pour lister, filtrer et instancier
les exercices disponibles.
"""

from typing import List, Optional
from exercises.base import Exercise, ExerciseCategory
from exercises.upper_limb import (
    ShoulderFlexion,
    ShoulderAbduction,
    ElbowFlexion,
    ElbowExtension,
    BilateralShoulderFlexion,
    ShoulderFlexionCognitive,
)
from exercises.lower_limb import (
    KneeExtension,
    HipFlexion,
    KneeExtensionCognitive,
)
from exercises.balance import (
    SeatedTrunkLean,
    StandingWeightShift,
    StandingWeightShiftCognitive,
)


def get_all_exercises(target_reps: int = 10) -> List[Exercise]:
    """
    Retourne la liste complète des 12 exercices.

    Args:
        target_reps: Nombre de répétitions cible par défaut.

    Returns:
        Liste de 12 exercices instanciés.
    """
    return [
        # ─── Membres supérieurs (6) ───
        ShoulderFlexion(side="left", target_reps=target_reps),
        ShoulderFlexion(side="right", target_reps=target_reps),
        ShoulderAbduction(side="left", target_reps=target_reps),
        ElbowFlexion(side="right", target_reps=target_reps),
        BilateralShoulderFlexion(target_reps=target_reps),
        ShoulderFlexionCognitive(side="right", target_reps=target_reps),

        # ─── Membres inférieurs (3) ───
        KneeExtension(side="left", target_reps=target_reps),
        HipFlexion(side="right", target_reps=target_reps),
        KneeExtensionCognitive(side="left", target_reps=target_reps),

        # ─── Équilibre (3) ───
        SeatedTrunkLean(side="left", target_reps=8),
        StandingWeightShift(target_reps=8),
        StandingWeightShiftCognitive(target_reps=8),
    ]


def get_exercises_by_category(
    category: ExerciseCategory, target_reps: int = 10
) -> List[Exercise]:
    """Filtre les exercices par catégorie."""
    return [ex for ex in get_all_exercises(target_reps) if ex.category == category]


def get_exercise_by_index(index: int, target_reps: int = 10) -> Optional[Exercise]:
    """Récupère un exercice par son index (0-11)."""
    exercises = get_all_exercises(target_reps)
    if 0 <= index < len(exercises):
        return exercises[index]
    return None


# Descriptions des catégories pour l'interface
CATEGORY_LABELS = {
    ExerciseCategory.UPPER_LIMB: "🦾 Membres supérieurs",
    ExerciseCategory.LOWER_LIMB: "🦵 Membres inférieurs",
    ExerciseCategory.BALANCE_SITTING: "🪑 Équilibre assis",
    ExerciseCategory.BALANCE_STANDING: "🧍 Équilibre debout",
    ExerciseCategory.COGNITIVE_MOTOR: "🧠 Double tâche cognitivo-motrice",
}
