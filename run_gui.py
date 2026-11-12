"""
Lanceur de l'interface graphique CustomTkinter.

Usage:
    python run_gui.py
"""

import sys
import os

# S'assurer que le répertoire du projet est dans le path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app_gui import RehabMirrorGUI


def main():
    app = RehabMirrorGUI()
    app.run()


if __name__ == "__main__":
    main()
