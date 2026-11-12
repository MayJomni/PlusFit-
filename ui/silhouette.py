"""
Silhouette guide animée — montre le bon mouvement à effectuer.
Dessinée en coin supérieur gauche du miroir avec OpenCV.
"""

import cv2
import numpy as np
import math
import time

ANIMATIONS = {
    "Flexion épaule gauche":        {"membre": "bras_gauche",  "a_debut": 0,  "a_fin": 150},
    "Flexion épaule droite":        {"membre": "bras_droit",   "a_debut": 0,  "a_fin": 150},
    "Abduction épaule gauche":      {"membre": "bras_gauche",  "a_debut": 0,  "a_fin": 130},
    "Abduction épaule droite":      {"membre": "bras_droit",   "a_debut": 0,  "a_fin": 130},
    "Flexion coude gauche":         {"membre": "avant_bras_g", "a_debut": 10, "a_fin": 140},
    "Flexion coude droit":          {"membre": "avant_bras_d", "a_debut": 10, "a_fin": 140},
    "Flexion bilatérale épaules":   {"membre": "deux_bras",    "a_debut": 0,  "a_fin": 150},
    "Extension genou gauche":       {"membre": "jambe_gauche", "a_debut": 90, "a_fin": 170},
    "Extension genou droit":        {"membre": "jambe_droite", "a_debut": 90, "a_fin": 170},
    "Montée de genou gauche":       {"membre": "cuisse_g",     "a_debut": 90, "a_fin": 40},
    "Montée de genou droit":        {"membre": "cuisse_d",     "a_debut": 90, "a_fin": 40},
    "Transfert de poids latéral (debout)": {"membre": "tronc", "a_debut": 90, "a_fin": 75},
    "Transfert de poids + cognitif":       {"membre": "tronc", "a_debut": 90, "a_fin": 75},
    "Extension genou gauche + cognitif":   {"membre": "jambe_gauche", "a_debut": 90, "a_fin": 170},
}
_DEFAULT = {"membre": "bras_gauche", "a_debut": 0, "a_fin": 120}

PERIODE = 2.5   # secondes aller-retour


class SilhouetteGuide:
    """Bonhomme animé qui montre le bon mouvement."""

    W, H = 115, 170

    def __init__(self, exercise_name: str):
        self.exercise_name = exercise_name
        self._anim = ANIMATIONS.get(exercise_name, _DEFAULT)
        self._t0 = time.time()

    def _angle_courant(self) -> float:
        t = (time.time() - self._t0) % PERIODE
        pct = (1 - math.cos(2 * math.pi * t / PERIODE)) / 2
        return self._anim["a_debut"] + pct * (self._anim["a_fin"] - self._anim["a_debut"])

    def draw(self, frame: np.ndarray, x: int = 15, y: int = 15) -> np.ndarray:
        angle  = self._angle_courant()
        BLANC  = (210, 210, 210)
        VERT   = (60,  220,  80)
        JAUNE  = (40,  220, 220)

        # Fond semi-transparent
        ov = frame.copy()
        cv2.rectangle(ov, (x, y), (x + self.W, y + self.H), (15, 15, 35), -1)
        cv2.addWeighted(ov, 0.65, frame, 0.35, 0, frame)
        cv2.rectangle(frame, (x, y), (x + self.W, y + self.H), (70, 70, 110), 1, cv2.LINE_AA)
        cv2.putText(frame, "Modele a suivre", (x + 5, y + 13),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (160, 160, 255), 1, cv2.LINE_AA)

        cx, cy = x + self.W // 2, y + 28

        # Anatomie de base
        tete      = (cx, cy + 10)
        ep_g      = (cx - 20, cy + 30)
        ep_d      = (cx + 20, cy + 30)
        hanche_g  = (cx - 14, cy + 70)
        hanche_d  = (cx + 14, cy + 70)

        cv2.circle(frame, tete, 9, BLANC, 2, cv2.LINE_AA)
        cv2.line(frame, (cx, cy + 19), (cx, cy + 70), BLANC, 2, cv2.LINE_AA)
        cv2.line(frame, ep_g, ep_d, BLANC, 2, cv2.LINE_AA)
        cv2.line(frame, hanche_g, hanche_d, BLANC, 2, cv2.LINE_AA)

        pied_g = (cx - 14, cy + 112)
        pied_d = (cx + 14, cy + 112)
        membre = self._anim["membre"]

        # Bras au repos (remplacés si animés)
        def bras_repos(ep, sign):
            c = (ep[0], ep[1] + 28)
            p = (ep[0], ep[1] + 50)
            cv2.line(frame, ep, c, BLANC, 2, cv2.LINE_AA)
            cv2.line(frame, c,  p, BLANC, 2, cv2.LINE_AA)

        # Jambes au repos
        for h, p in [(hanche_g, pied_g), (hanche_d, pied_d)]:
            cv2.line(frame, h, (h[0], h[1] + 42), BLANC, 2, cv2.LINE_AA)
            cv2.line(frame, (h[0], h[1] + 42), p, BLANC, 2, cv2.LINE_AA)

        rad = math.radians(angle)

        if membre == "bras_gauche":
            coude   = (int(ep_g[0] - 28 * math.sin(rad)), int(ep_g[1] + 28 * math.cos(rad)))
            poignet = (int(coude[0] - 22 * math.sin(rad)), int(coude[1] + 22 * math.cos(rad)))
            cv2.line(frame, ep_g, coude,   VERT, 3, cv2.LINE_AA)
            cv2.line(frame, coude, poignet, VERT, 3, cv2.LINE_AA)
            cv2.circle(frame, poignet, 4, JAUNE, -1, cv2.LINE_AA)
            bras_repos(ep_d, 1)

        elif membre == "bras_droit":
            coude   = (int(ep_d[0] + 28 * math.sin(rad)), int(ep_d[1] + 28 * math.cos(rad)))
            poignet = (int(coude[0] + 22 * math.sin(rad)), int(coude[1] + 22 * math.cos(rad)))
            cv2.line(frame, ep_d, coude,   VERT, 3, cv2.LINE_AA)
            cv2.line(frame, coude, poignet, VERT, 3, cv2.LINE_AA)
            cv2.circle(frame, poignet, 4, JAUNE, -1, cv2.LINE_AA)
            bras_repos(ep_g, -1)

        elif membre == "deux_bras":
            for ep, sign in [(ep_g, -1), (ep_d, 1)]:
                coude   = (int(ep[0] + sign * 28 * math.sin(rad)), int(ep[1] + 28 * math.cos(rad)))
                poignet = (int(coude[0] + sign * 22 * math.sin(rad)), int(coude[1] + 22 * math.cos(rad)))
                cv2.line(frame, ep, coude,   VERT, 3, cv2.LINE_AA)
                cv2.line(frame, coude, poignet, VERT, 3, cv2.LINE_AA)

        elif membre in ("avant_bras_g", "avant_bras_d"):
            ep = ep_g if "_g" in membre else ep_d
            coude = (ep[0], ep[1] + 30)
            cv2.line(frame, ep, coude, BLANC, 2, cv2.LINE_AA)
            flex  = math.radians(180 - angle)
            poignet = (int(coude[0] - 25 * math.cos(flex)), int(coude[1] - 25 * math.sin(flex)))
            cv2.line(frame, coude, poignet, VERT, 3, cv2.LINE_AA)
            cv2.circle(frame, poignet, 4, JAUNE, -1, cv2.LINE_AA)

        elif membre in ("jambe_gauche", "jambe_droite"):
            h = hanche_g if "gauche" in membre else hanche_d
            ext = (angle - 90) / 80.0
            genou = (h[0], h[1] + 42)
            pied_a = (int(h[0] + 20 * ext), h[1] + 42 + int(28 * max(0, 1 - ext)))
            cv2.line(frame, h,     genou,  VERT, 3, cv2.LINE_AA)
            cv2.line(frame, genou, pied_a, VERT, 3, cv2.LINE_AA)
            cv2.circle(frame, pied_a, 4, JAUNE, -1, cv2.LINE_AA)

        elif membre in ("cuisse_g", "cuisse_d"):
            h = hanche_g if "_g" in membre else hanche_d
            genou = (int(h[0]), int(h[1] + 38 * math.sin(rad)))
            cv2.line(frame, h, genou, VERT, 3, cv2.LINE_AA)
            cv2.circle(frame, genou, 4, JAUNE, -1, cv2.LINE_AA)

        elif membre == "tronc":
            lean = int(18 * math.sin((angle - 90) * math.pi / 15))
            cv2.line(frame, (cx, cy + 19), (cx + lean, cy + 70), VERT, 3, cv2.LINE_AA)

        # Flèche montée/descente
        pct = ((time.time() - self._t0) % PERIODE) / PERIODE
        fleche = "^ Montee" if pct < 0.5 else "v Descend"
        cv2.putText(frame, fleche, (x + 5, y + self.H - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.33,
                    VERT if pct < 0.5 else (100, 100, 220), 1, cv2.LINE_AA)

        return frame
