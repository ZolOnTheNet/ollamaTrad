"""
Dialogs pour l'interface graphique OllamaTrad
"""

from .evolution_dialog import EvolutionChoiceDialog
from .merge_dialog import MergeDialog, show_merge_dialog
from .merge_dialog_v2 import MergeDialogV2

__all__ = ['EvolutionChoiceDialog', 'MergeDialog', 'show_merge_dialog', 'MergeDialogV2']
