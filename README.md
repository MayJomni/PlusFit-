# Rehab Mirror 🪞 – Système de Rééducation Miroir avec IA

Système de rééducation assistée par vision par ordinateur pour personnes âgées.
Détection de pose en temps réel avec MoveNet, analyse du mouvement, et feedback adapté.

## ⚡ Installation rapide

```bash
# 1. Créer un environnement virtuel
python -m venv venv

# Windows
venv\Scripts\activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer l'application
python main.py
```

## 🎮 Utilisation

```bash
# Lancer avec les options par défaut
python main.py

# Choisir le modèle et la caméra
python main.py --model thunder --camera 1 --patient patient001
```

### Contrôles clavier

| Touche  | Action                    |
|---------|---------------------------|
| ESPACE  | Démarrer/arrêter exercice |
| N       | Exercice suivant          |
| P       | Exercice précédent        |
| R       | Réinitialiser             |
| M       | Menu de sélection         |
| Q / ESC | Quitter                   |

## 📋 Les 12 exercices

### 🦾 Membres supérieurs (6)
1. Flexion épaule gauche
2. Flexion épaule droite
3. Abduction épaule gauche
4. Flexion coude droit
5. Flexion bilatérale épaules
6. Flexion épaule + tâche cognitive 🧠

### 🦵 Membres inférieurs (3)
7. Extension genou gauche
8. Flexion hanche droite
9. Extension genou + tâche cognitive 🧠

### 🪑🧍 Équilibre (3)
10. Inclinaison du tronc (assis)
11. Transfert de poids (debout)
12. Transfert de poids + tâche cognitive 🧠

## 🏗️ Architecture

```
rehab-mirror/
├── main.py                    # Point d'entrée
├── config.py                  # Configuration globale
├── requirements.txt           # Dépendances
│
├── pose_detection/            # Détection de pose
│   ├── keypoints.py          #   Définition des 17 keypoints MoveNet
│   └── movenet.py            #   Wrapper du modèle MoveNet
│
├── exercises/                 # Exercices de rééducation
│   ├── base.py               #   Classe de base Exercise
│   ├── upper_limb.py         #   Épaules, coudes (6 exercices)
│   ├── lower_limb.py         #   Genoux, hanches (3 exercices)
│   ├── balance.py            #   Équilibre assis/debout (3 exercices)
│   └── catalog.py            #   Catalogue complet
│
├── analysis/                  # Analyse du mouvement
│   ├── angles.py             #   Calcul d'angles articulaires
│   ├── repetitions.py        #   Comptage des répétitions
│   └── compensation.py       #   Détection des compensations
│
├── ui/                        # Interface utilisateur
│   ├── mirror.py             #   Rendu miroir + squelette
│   └── feedback.py           #   Synthèse vocale
│
└── data/
    ├── session_logger.py     #   Sauvegarde des sessions
    └── sessions/             #   Fichiers JSON des sessions
```

## 🧠 Comment ça marche

1. **Capture vidéo** : La webcam capture l'image du patient
2. **MoveNet** : Détecte 17 points du corps en temps réel
3. **Analyse d'angles** : Calcule les angles articulaires (épaule, coude, genou…)
4. **Comptage** : Machine à états pour compter les répétitions (repos → cible → repos)
5. **Compensation** : Détecte les mouvements parasites (inclinaison du tronc, élévation d'épaule…)
6. **Feedback** : Affichage visuel (couleurs, barres) + vocal (pyttsx3)
7. **Logging** : Sauvegarde JSON de chaque session pour le suivi

## 📊 Données de session

Les sessions sont sauvegardées en JSON dans `data/sessions/` :

```json
{
  "session_id": "20261110_143000",
  "patient_id": "patient001",
  "date": "2026-11-10T14:30:00",
  "exercises": [
    {
      "exercise_name": "Flexion épaule gauche",
      "total_reps": 10,
      "avg_amplitude": 125.3,
      "compensations_count": 2,
      "score": 85.0,
      "rep_details": [...]
    }
  ]
}
```

## 🔧 Configuration

Modifiez `config.py` pour ajuster :
- Résolution caméra, FPS
- Modèle MoveNet (lightning / thunder)
- Seuils d'angles et de compensation
- Vitesse de la voix, langue
- Répertoire de sauvegarde
