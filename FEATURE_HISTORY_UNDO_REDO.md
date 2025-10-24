# Feature: Navigation Bidirectionnelle dans l'Historique

## 📅 Date: 2025-10-16

## 🎯 Objectif

Permettre la navigation bidirectionnelle dans l'historique des traductions avec deux boutons séparés:
- **↶ Undo**: Reculer dans l'historique (vers les anciennes versions)
- **↷ Redo**: Avancer dans l'historique (revenir vers les versions plus récentes)

---

## 📊 Avant / Après

### ❌ Avant

```
🪄 FR: ☑ ↶
```

**Limitations**:
- Un seul bouton ↶ (rollback)
- Navigation unidirectionnelle uniquement
- Impossible de revenir en arrière après un rollback
- Perte du texte actuel après rollback

---

### ✅ Après

```
🪄 FR: ☑ ↶ ↷
```

**Améliorations**:
- ✅ Deux boutons: ↶ (undo) et ↷ (redo)
- ✅ Navigation bidirectionnelle complète
- ✅ Possibilité de revenir au texte actuel après undo
- ✅ État des boutons dynamique selon la position
- ✅ Réinitialisation automatique au changement d'entrée

---

## 🔧 Modifications Apportées

### 1. Ajout de Structures de Données

**Fichier**: `gui/translation_form_v2.py`

```python
# Ligne 59-60
self.history_indices = {}  # lang -> index courant dans l'historique (0 = texte actuel, 1 = premier historique, etc.)
self.current_texts_before_undo = {}  # lang -> texte actuel avant le premier undo (pour pouvoir redo jusqu'à lui)
```

**Fonctionnement**:
- `history_indices[lang]`: Tracker la position courante dans l'historique
  - `0`: Texte actuel (pas d'undo effectué)
  - `1`: Premier élément de l'historique
  - `2`: Deuxième élément de l'historique, etc.
- `current_texts_before_undo[lang]`: Sauvegarder le texte actuel avant le premier undo pour pouvoir y revenir avec redo

---

### 2. Remplacement du Bouton Rollback Unique

**Avant** (lignes 231-247):
```python
# ↶ Bouton rollback
rollback_btn = tk.Button(...)
```

**Après** (lignes 232-259):
```python
# Initialiser l'index d'historique à 0 (texte actuel)
self.history_indices[lang] = 0

# ↶ Bouton undo (reculer dans l'historique)
undo_btn = tk.Button(header_frame, text="↶", font=("Arial", 12),
                    width=2, relief="raised",
                    state="normal" if has_history else "disabled",
                    command=lambda: self._on_history_undo(lang))
undo_btn.pack(side="left", padx=(0, 2))

# ↷ Bouton redo (avancer dans l'historique)
redo_btn = tk.Button(header_frame, text="↷", font=("Arial", 12),
                    width=2, relief="raised",
                    state="disabled",  # Désactivé au départ (on est au texte actuel)
                    command=lambda: self._on_history_redo(lang))
redo_btn.pack(side="left")
```

**Changements**:
- ✅ Deux boutons distincts au lieu d'un
- ✅ Espacement de 2px entre les boutons (`padx=(0, 2)`)
- ✅ Undo activé si historique disponible
- ✅ Redo désactivé au départ (index = 0)
- ✅ Callbacks séparés pour chaque action

---

### 3. Mise à Jour du Dictionnaire de Widgets

**Avant** (lignes 311-318):
```python
self.language_rows[lang] = {
    "frame": row_frame,
    "magic_btn": magic_btn,
    "text_widget": text_widget,
    "valid_check": valid_check,
    "rollback_btn": rollback_btn
}
```

**Après** (lignes 311-318):
```python
self.language_rows[lang] = {
    "frame": row_frame,
    "magic_btn": magic_btn,
    "text_widget": text_widget,
    "valid_check": valid_check,
    "undo_btn": undo_btn,
    "redo_btn": redo_btn
}
```

---

### 4. Logique de Navigation dans l'Historique

#### A. Méthode `_on_history_undo()` (lignes 338-365)

```python
def _on_history_undo(self, lang: str):
    """Recule dans l'historique (undo)."""
    # Vérifications
    if not self.current_entry or lang not in self.current_entry:
        return

    lang_data = self.current_entry[lang]
    current_index = self.history_indices.get(lang, 0)

    # Vérifier qu'on peut reculer
    if current_index >= len(lang_data["history"]):
        return

    # Sauvegarder le texte actuel avant le premier undo
    if current_index == 0:
        self.current_texts_before_undo[lang] = lang_data["text"]

    # Passer à l'historique précédent
    new_index = current_index + 1
    self.history_indices[lang] = new_index

    # Récupérer le texte de l'historique
    history_text = lang_data["history"][new_index - 1]

    # Mettre à jour le texte et l'interface
    lang_data["text"] = history_text
    self.update_language_data(lang)
    self._update_history_buttons_state(lang)
```

**Fonctionnement**:
1. Vérifier qu'on peut reculer (index < longueur historique)
2. Sauvegarder le texte actuel lors du premier undo
3. Incrémenter l'index (0 → 1 → 2...)
4. Récupérer le texte de `history[index-1]`
5. Mettre à jour l'affichage
6. Actualiser l'état des boutons

---

#### B. Méthode `_on_history_redo()` (lignes 367-394)

```python
def _on_history_redo(self, lang: str):
    """Avance dans l'historique (redo)."""
    # Vérifications
    if not self.current_entry or lang not in self.current_entry:
        return

    lang_data = self.current_entry[lang]
    current_index = self.history_indices.get(lang, 0)

    # Vérifier qu'on peut avancer
    if current_index <= 0:
        return

    # Revenir vers le texte actuel ou un historique plus récent
    new_index = current_index - 1
    self.history_indices[lang] = new_index

    if new_index == 0:
        # Retour au texte actuel (celui qui était avant les undo)
        if lang in self.current_texts_before_undo:
            lang_data["text"] = self.current_texts_before_undo[lang]
    else:
        # Récupérer le texte de l'historique
        history_text = lang_data["history"][new_index - 1]
        lang_data["text"] = history_text

    # Mettre à jour l'affichage et l'état des boutons
    self.update_language_data(lang)
    self._update_history_buttons_state(lang)
```

**Fonctionnement**:
1. Vérifier qu'on peut avancer (index > 0)
2. Décrémenter l'index (3 → 2 → 1 → 0)
3. Si retour à l'index 0: restaurer le texte sauvegardé
4. Sinon: récupérer le texte de `history[index-1]`
5. Mettre à jour l'affichage
6. Actualiser l'état des boutons

---

#### C. Méthode `_update_history_buttons_state()` (lignes 395-422)

```python
def _update_history_buttons_state(self, lang: str):
    """Met à jour l'état des boutons undo/redo selon la position dans l'historique."""
    if not self.current_entry or lang not in self.current_entry:
        return

    if lang not in self.language_rows:
        return

    lang_data = self.current_entry[lang]
    current_index = self.history_indices.get(lang, 0)
    history_length = len(lang_data["history"])

    # Bouton undo (↶): activé si on peut reculer dans l'historique
    can_undo = current_index < history_length
    self.language_rows[lang]["undo_btn"].config(
        state="normal" if can_undo else "disabled"
    )

    # Bouton redo (↷): activé si on peut avancer (si on n'est pas à l'index 0)
    can_redo = current_index > 0
    self.language_rows[lang]["redo_btn"].config(
        state="normal" if can_redo else "disabled"
    )
```

**Fonctionnement**:
- **Undo activé**: Si `index < longueur_historique` (il reste de l'historique à explorer)
- **Redo activé**: Si `index > 0` (on n'est pas au texte actuel)

---

### 5. Réinitialisation au Changement d'Entrée

**Fichier**: `gui/translation_form_v2.py` (lignes 182-183)

```python
self.history_indices.clear()  # Réinitialiser les indices d'historique
self.current_texts_before_undo.clear()  # Réinitialiser les textes sauvegardés
```

**Quand**: À chaque appel de `load_entry()` (changement d'entrée)

**Effet**: Les index reviennent à 0 pour toutes les langues de la nouvelle entrée

---

### 6. Mise à Jour dans `update_language_data()`

**Avant** (lignes 427-432):
```python
# Mettre à jour l'état du bouton rollback
has_history = len(lang_data["history"]) > 0
if lang in self.language_rows:
    self.language_rows[lang]["rollback_btn"].config(
        state="normal" if has_history else "disabled"
    )
```

**Après** (lignes 456-457):
```python
# Mettre à jour l'état des boutons undo/redo
self._update_history_buttons_state(lang)
```

**Changement**: Utilisation de la méthode centralisée pour gérer l'état des deux boutons

---

## 📐 Schéma de Navigation

### Structure de l'Historique

```
Index:    0          1          2          3
       ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐
       │Actuel│ ← │Hist[0]│ ← │Hist[1]│ ← │Hist[2]│
       └─────┘    └─────┘    └─────┘    └─────┘
          ↑          ↑          ↑          ↑
       (Texte    (Plus      (Moyen     (Plus
        actuel)   récent)    ancien)    ancien)
```

### Navigation Undo (↶)

```
Clic sur ↶:
Index 0 → 1 → 2 → 3
┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐
│Actuel│    │Hist[0]│    │Hist[1]│    │Hist[2]│
└─────┘    └─────┘    └─────┘    └─────┘
   ●    ↶     ●     ↶     ●     ↶     ●
```

**Actions**:
1. Index 0 → 1: Sauvegarder texte actuel, afficher `history[0]`
2. Index 1 → 2: Afficher `history[1]`
3. Index 2 → 3: Afficher `history[2]`

---

### Navigation Redo (↷)

```
Clic sur ↷:
Index 3 → 2 → 1 → 0
┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐
│Actuel│    │Hist[0]│    │Hist[1]│    │Hist[2]│
└─────┘    └─────┘    └─────┘    └─────┘
   ●     ↷     ●     ↷     ●     ↷     ●
```

**Actions**:
1. Index 3 → 2: Afficher `history[1]`
2. Index 2 → 1: Afficher `history[0]`
3. Index 1 → 0: Restaurer texte actuel sauvegardé

---

## 🎯 États des Boutons

| Index | Texte Affiché | Undo (↶) | Redo (↷) |
|-------|---------------|----------|----------|
| **0** | Texte actuel | ✅ Normal | ❌ Disabled |
| **1** | history[0] | ✅ Normal | ✅ Normal |
| **2** | history[1] | ✅ Normal | ✅ Normal |
| **3** | history[2] (dernier) | ❌ Disabled | ✅ Normal |

**Règles**:
- **Undo activé**: `index < len(history)`
- **Redo activé**: `index > 0`

---

## 🧪 Scénarios de Test

### Test 1: Navigation Complète

**Procédure**:
1. Charger une entrée avec historique (ex: 3 éléments)
2. Vérifier état initial: Undo ✅, Redo ❌
3. Cliquer Undo → Voir history[0], Undo ✅, Redo ✅
4. Cliquer Undo → Voir history[1], Undo ✅, Redo ✅
5. Cliquer Undo → Voir history[2], Undo ❌, Redo ✅
6. Cliquer Redo → Voir history[1], Undo ✅, Redo ✅
7. Cliquer Redo → Voir history[0], Undo ✅, Redo ✅
8. Cliquer Redo → Voir texte actuel, Undo ✅, Redo ❌

**Résultat attendu**: Navigation fluide dans les deux sens

---

### Test 2: Sauvegarde du Texte Actuel

**Procédure**:
1. Charger une entrée, noter le texte actuel: "Version actuelle"
2. Cliquer Undo → Voir "Version précédente"
3. Cliquer Redo → Doit revoir "Version actuelle"

**Résultat attendu**: Le texte actuel est correctement restauré

---

### Test 3: Réinitialisation au Changement d'Entrée

**Procédure**:
1. Charger entrée A, cliquer Undo 2 fois (index = 2)
2. Charger entrée B
3. Vérifier état: Undo ✅, Redo ❌ (index = 0)

**Résultat attendu**: L'index est réinitialisé à 0 pour la nouvelle entrée

---

### Test 4: Pas d'Historique

**Procédure**:
1. Charger une entrée sans historique
2. Vérifier état: Undo ❌, Redo ❌

**Résultat attendu**: Les deux boutons sont désactivés

---

### Test 5: Navigation Partielle

**Procédure**:
1. Charger une entrée avec 5 éléments d'historique
2. Cliquer Undo 3 fois (index = 3)
3. Cliquer Redo 1 fois (index = 2)
4. Cliquer Undo 2 fois (index = 4)
5. Vérifier: history[3] affiché, Undo ✅, Redo ✅

**Résultat attendu**: Navigation dans les deux sens fonctionne à n'importe quel point

---

## 💡 Avantages

### 1. 🔄 Navigation Flexible

**Avant**: Rollback irréversible
```
Texte actuel → Undo → history[0]
                       ⚠ Impossible de revenir au texte actuel
```

**Après**: Navigation bidirectionnelle
```
Texte actuel ⇄ history[0] ⇄ history[1] ⇄ history[2]
```

---

### 2. 🛡️ Sécurité des Données

**Problème résolu**: Perte du texte actuel après rollback

**Solution**:
- Sauvegarde automatique dans `current_texts_before_undo`
- Restauration garantie avec Redo

---

### 3. 🎯 Exploration de l'Historique

**Use case**: Comparer plusieurs versions
```
1. Voir texte actuel
2. Undo → Voir version précédente
3. Undo → Voir version encore avant
4. Redo → Revenir à la version précédente
5. Redo → Revenir au texte actuel
```

**Bénéfice**: Pouvoir explorer sans perdre sa position

---

### 4. 🔍 Interface Intuitive

**Symboles universels**:
- ↶ = Undo (reculer dans le temps)
- ↷ = Redo (avancer dans le temps)

**États visuels**:
- Gris (disabled) = Action impossible
- Normal = Action disponible

---

## 🎓 Détails Techniques

### Gestion de l'Index

**Convention**:
```
index = 0  →  Texte actuel (pas d'undo)
index = 1  →  history[0] (premier élément)
index = 2  →  history[1] (deuxième élément)
...
```

**Accès à l'historique**:
```python
history_text = lang_data["history"][index - 1]
```

**Raison**: `history[0]` est le texte le plus récent de l'historique (avant le texte actuel)

---

### Sauvegarde du Texte Actuel

**Quand**: Lors du premier undo (index 0 → 1)

**Pourquoi**: Le texte actuel n'est pas dans l'historique, il faut le sauvegarder pour pouvoir le restaurer

**Code**:
```python
if current_index == 0:
    self.current_texts_before_undo[lang] = lang_data["text"]
```

---

### Mise à Jour de l'Interface

**Ordre des opérations**:
1. Modifier `lang_data["text"]`
2. Appeler `update_language_data(lang)` → Met à jour le widget Text
3. Appeler `_update_history_buttons_state(lang)` → Met à jour les boutons

**Important**: Mettre à jour `last_saved_texts` pour éviter que FocusOut déclenche un événement d'édition

---

## ✅ Checklist de Validation

- [x] Ajout de `history_indices` pour tracker la position
- [x] Ajout de `current_texts_before_undo` pour sauvegarder le texte actuel
- [x] Remplacement du bouton rollback par deux boutons undo/redo
- [x] Implémentation de `_on_history_undo()`
- [x] Implémentation de `_on_history_redo()`
- [x] Implémentation de `_update_history_buttons_state()`
- [x] Mise à jour de `update_language_data()`
- [x] Réinitialisation dans `load_entry()`
- [x] Tests de compilation (Python 3)
- [x] Vérification de la logique de navigation
- [x] Gestion des cas limites (pas d'historique, fin d'historique)

---

## 🎉 Résultat

Les utilisateurs peuvent maintenant:
- ✅ Naviguer librement dans l'historique des traductions
- ✅ Reculer avec ↶ (undo) pour voir les anciennes versions
- ✅ Avancer avec ↷ (redo) pour revenir aux versions plus récentes
- ✅ Revenir au texte actuel après exploration de l'historique
- ✅ Voir l'état des boutons (activé/désactivé) selon la position
- ✅ Navigation réinitialisée automatiquement au changement d'entrée

**L'interface est maintenant plus flexible et sécurisée pour l'exploration de l'historique!**

---

**Auteur**: Claude (Anthropic)
**Date**: 2025-10-16
**Version**: OllamaFic v2.0 - Navigation Bidirectionnelle Historique
