"""
Dialogs pour l'interface graphique OllamaTrad
"""

from .evolution_dialog import EvolutionChoiceDialog
from .merge_dialog import MergeDialog, show_merge_dialog

__all__ = ['EvolutionChoiceDialog', 'MergeDialog', 'show_merge_dialog']
