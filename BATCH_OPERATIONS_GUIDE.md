# Guide des opérations par lot (Batch Operations)

## Vue d'ensemble

Le système de traitements par lot permet d'effectuer des opérations sur plusieurs champs JSON simultanément, avec un système d'onglets pour différents types de traitements.

## Architecture

### Fichiers principaux

```
gui/
├── batch_translation_form.py      # Gestionnaire principal des onglets + progression
├── field_selector.py              # Widget réutilisable de sélection de champs
└── batch_tabs/
    ├── __init__.py                # Package des onglets
    ├── translation_tab.py          # Onglet de traduction
    ├── search_replace_tab.py       # Onglet rechercher & remplacer
    └── undo_tab.py                 # Onglet annulation de modifications
```

### Composants

#### 1. **FieldSelector** (`field_selector.py`)
Widget réutilisable pour sélectionner les champs à traiter.

**Fonctionnalités:**
- Liste scrollable de checkboxes (un par nom de champ unique)
- Affiche le nombre d'occurrences pour chaque champ (ex: "name (3×)")
- Boutons "Tout sélectionner" / "Tout désélectionner"
- Compteur de sélection
- Par défaut, tous les champs sont cochés

**Méthodes principales:**
```python
load_fields(leaves: list)           # Charge les champs depuis une liste de chemins
get_selected_paths() -> list        # Retourne les chemins sélectionnés
get_selected_fields() -> list       # Retourne les noms de champs sélectionnés
```

#### 2. **TranslationTab** (`batch_tabs/translation_tab.py`)
Onglet pour la traduction par lot.

**Fonctionnalités:**
- Sélection de champs (via FieldSelector)
- Boutons pour chaque langue cible
- Callback: `on_translate(lang, selected_paths)`

#### 3. **SearchReplaceTab** (`batch_tabs/search_replace_tab.py`)
Onglet pour rechercher et remplacer dans les champs sélectionnés.

**Fonctionnalités:**
- Sélection de champs (via FieldSelector)
- Champ "Rechercher"
- Champ "Remplacer par"
- Options:
  - Sensible à la casse
  - Utiliser regex
  - Mot entier uniquement
- Callback: `on_search_replace(search_text, replace_text, selected_paths, options)`

#### 4. **UndoTab** (`batch_tabs/undo_tab.py`)
Onglet pour annuler les modifications de champs sélectionnés.

**Fonctionnalités:**
- Sélection de champs (via FieldSelector)
- Modes d'annulation:
  - Annuler la dernière modification
  - Restaurer depuis la dernière sauvegarde
  - Restaurer toutes les modifications (retour initial)
- Callback: `on_undo(selected_paths, mode)`

#### 5. **BatchTranslationForm** (`batch_translation_form.py`)
Gestionnaire principal qui coordonne les onglets et la progression.

**Fonctionnalités:**
- Système d'onglets (Notebook Tkinter)
- Barre de progression avec bouton d'arrêt
- Gestion de la visibilité (onglets cachés pendant traitement)
- Callbacks pour chaque type d'opération

## Flux de traitement

### 1. Configuration (onglets visibles)
```
┌─────────────────────────────────┐
│ 📦 Traitements par lot          │
│ 📍 Branche: entries             │
├─────────────────────────────────┤
│ ┌─────┬───────┬────────┐        │
│ │ 🔄  │  🔍   │   ↶    │        │
│ └─────┴───────┴────────┘        │
│                                 │
│ [Sélection des champs]          │
│ ☑ name (3×)                     │
│ ☑ tokenName (2×)                │
│ ☐ description (3×)              │
│                                 │
│ [Boutons d'action]              │
└─────────────────────────────────┘
```

### 2. Traitement en cours (progression visible)
```
┌─────────────────────────────────┐
│ 📦 Traitements par lot          │
│ 📍 Branche: entries             │
├─────────────────────────────────┤
│ Progression:                    │
│ ████████░░░░░░░░░░  3 / 5      │
│                                 │
│ En cours:                       │
│ entries/Demon/name              │
│                                 │
│     [⏹ Arrêter]                 │
└─────────────────────────────────┘
```

### 3. Terminé (retour aux onglets après 3s)
```
┌─────────────────────────────────┐
│ 📦 Traitements par lot          │
│ 📍 Branche: entries             │
├─────────────────────────────────┤
│ Progression:                    │
│ ████████████████████  5 / 5    │
│                                 │
│ ✓ Traitement terminé avec succès│
│                                 │
│     [⏹ Arrêter]                 │
└─────────────────────────────────┘
```

## Utilisation dans app_v2.py

### Initialisation

```python
from gui.batch_translation_form import BatchTranslationForm

# Créer le formulaire
self.batch_form = BatchTranslationForm(
    parent=self.batch_panel,
    visible_languages=["fr", "en", "es"],
    on_batch_translate=self._on_batch_translate,
    on_search_replace=self._on_search_replace,
    on_undo=self._on_undo
)
```

### Callbacks à implémenter

#### 1. Traduction
```python
def _on_batch_translate(self, lang: str, selected_paths: list):
    """
    Effectue la traduction par lot.

    Args:
        lang: Code langue cible (ex: "fr")
        selected_paths: Liste des chemins à traduire
    """
    if not selected_paths:
        messagebox.showinfo("Aucune sélection", "Veuillez sélectionner au moins un champ.")
        return

    # Démarrer le traitement
    self.batch_form.start_processing(len(selected_paths))

    # Lancer dans un thread
    def batch_process():
        for i, path in enumerate(selected_paths):
            if self.batch_form.is_stopped():
                break

            # Traiter le chemin
            self._translate_path(path, lang)

            # Mettre à jour la progression
            self.batch_form.update_progress(i + 1, len(selected_paths), path)

        # Terminer
        success = not self.batch_form.is_stopped()
        self.batch_form.finish_processing(success)

    threading.Thread(target=batch_process, daemon=True).start()
```

#### 2. Rechercher & Remplacer
```python
def _on_search_replace(self, search_text: str, replace_text: str,
                       selected_paths: list, options: dict):
    """
    Effectue la recherche et le remplacement.

    Args:
        search_text: Texte à rechercher
        replace_text: Texte de remplacement
        selected_paths: Liste des chemins à traiter
        options: Dict avec 'case_sensitive', 'use_regex', 'whole_word'
    """
    if not search_text:
        messagebox.showwarning("Recherche vide", "Veuillez saisir un texte à rechercher.")
        return

    # Implémenter la logique de recherche/remplacement
    # ...
```

#### 3. Annuler modifications
```python
def _on_undo(self, selected_paths: list, mode: str):
    """
    Annule les modifications des champs sélectionnés.

    Args:
        selected_paths: Liste des chemins à restaurer
        mode: 'last', 'last_save', ou 'all'
    """
    # Implémenter la logique d'annulation avec l'historique
    # ...
```

## Principe de fonctionnement

### Sélection de champs

Le système groupe les champs par **nom de champ final** :

**Exemple :**
```json
Chemins:
  - entries/Demon/name
  - entries/Angel/name
  - entries/Beast/name
  - entries/Demon/tokenName
  - entries/Angel/tokenName

Groupement:
  - name (3×)      → [entries/Demon/name, entries/Angel/name, entries/Beast/name]
  - tokenName (2×) → [entries/Demon/tokenName, entries/Angel/tokenName]
```

**Si l'utilisateur coche "name" :**
→ Les 3 chemins contenant "name" seront traités

**Si l'utilisateur décoche "tokenName" :**
→ Les 2 chemins contenant "tokenName" ne seront PAS traités

### Visibilité dynamique

**Pendant le traitement :**
- ❌ Onglets cachés (économise l'espace)
- ✅ Barre de progression affichée
- ✅ Bouton "Arrêter" actif

**Avant/après le traitement :**
- ✅ Onglets visibles
- ❌ Barre de progression cachée

## Tests

### Test manuel de l'interface

```bash
python3 test_tabbed_interface.py
```

Ce script de test affiche:
- Les 3 onglets fonctionnels
- Des boutons de test pour simuler la progression
- Des callbacks qui affichent les sélections dans la console

### Vérification du système

1. **Onglet Traduction** : Sélectionner des champs, cliquer sur une langue
2. **Onglet Rechercher & Remplacer** : Remplir les champs, sélectionner les options
3. **Onglet Annuler** : Choisir le mode d'annulation
4. **Progression** : Tester les boutons "Démarrer", "Mettre à jour", "Terminer"

## Extension future

Pour ajouter un nouvel onglet :

1. Créer `gui/batch_tabs/nouveau_tab.py` héritant de `ttk.Frame`
2. Utiliser `FieldSelector` pour la sélection de champs
3. Définir un callback `on_nouvelle_operation`
4. Ajouter l'onglet dans `BatchTranslationForm._create_widgets()`
5. Mettre à jour les méthodes `_enable_tabs()` et `_disable_tabs()`

## Notes importantes

- **Thread safety** : Les opérations longues doivent être dans un thread séparé
- **Interruption** : Vérifier `batch_form.is_stopped()` régulièrement
- **Mise à jour UI** : Appeler `update_progress()` pour rafraîchir l'interface
- **Timeout** : La barre de progression disparaît après 3 secondes
