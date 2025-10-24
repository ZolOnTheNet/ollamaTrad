# Corrections de bugs : Sélection partielle et Timeout

## Date
2025-10-21

## Bugs corrigés

### 1. Erreur `_mark_modified` inexistante

#### Symptôme
```
Erreur: 'GotJsonManager' object has no attribute '_mark_modified'
```

#### Cause
Dans `app_v2.py`, ligne 634, appel à une méthode `_mark_modified()` qui n'existe pas dans la classe `GotJsonManager`.

#### Solution
- Suppression de l'appel à `self.got_manager._mark_modified()`
- Utilisation directe de `self.got_manager.update_translation()` qui gère automatiquement l'historique et les modifications
- Simplification du code pour la traduction partielle

#### Code avant (gui/app_v2.py:614-634)
```python
# Sauvegarder l'ancien texte dans l'historique
if "history" not in current_entry[lang]:
    current_entry[lang]["history"] = []
current_entry[lang]["history"].insert(0, current_text)

# Construire le nouveau texte en remplaçant la sélection
# Utiliser les index de sélection pour remplacer
text_widget = self.translation_form.text_widgets.get(lang)
if text_widget:
    # Obtenir les positions actuelles
    start_idx = selection_data["start"]
    end_idx = selection_data["end"]

    # Construire le nouveau texte
    text_before = text_widget.get("1.0", start_idx)
    text_after = text_widget.get(end_idx, "end-1c")
    new_full_text = text_before + result + text_after

    # Mettre à jour dans got_manager
    current_entry[lang]["text"] = new_full_text
    self.got_manager._mark_modified()  # ❌ ERREUR: méthode inexistante

    # Mettre à jour l'UI
    updated_entry = current_entry
```

#### Code après (gui/app_v2.py:614-629)
```python
# Construire le nouveau texte en remplaçant la sélection
# Utiliser les index de sélection pour remplacer
text_widget = self.translation_form.text_widgets.get(lang)
if text_widget:
    # Obtenir les positions actuelles
    start_idx = selection_data["start"]
    end_idx = selection_data["end"]

    # Construire le nouveau texte
    text_before = text_widget.get("1.0", start_idx)
    text_after = text_widget.get(end_idx, "end-1c")
    new_full_text = text_before + result + text_after

    # Mettre à jour dans got_manager (gère automatiquement l'historique)
    self.got_manager.update_translation(path, lang, new_full_text)  # ✅ OK
    updated_entry = self.got_manager._get_entry_by_path(path)
```

### 2. Calcul de timeout incorrect

#### Symptôme
Le timeout était calculé sur la longueur totale du texte original + texte actuel, même pour les traductions partielles (sélections).

#### Cause
Le calcul du timeout était effectué AVANT de déterminer quel texte serait réellement envoyé à l'IA.

#### Impact
- Timeout trop long pour les sélections courtes
- Gaspillage de temps d'attente
- Expérience utilisateur dégradée

#### Solution
- Déplacement du calcul du timeout APRÈS la détermination du texte à traduire
- Calcul adapté selon le type d'action :
  - **Sélection** : taille de la sélection uniquement
  - **Traduction** : taille de l'original ou de la sélection
  - **Amélioration** : taille de l'original + texte actuel

#### Code avant (gui/app_v2.py:470-477)
```python
# Calculer un timeout dynamique basé sur la taille du texte
# Formule: timeout_base + (nb_caractères / vitesse_estimation) * marge
# Ollama local avec HTML: ~5 tokens/sec, avec ~4 chars/token = ~20 chars/sec (théorique)
# En pratique, avec HTML complexe: beaucoup plus lent
# Utiliser une vitesse très conservatrice de 5 chars/sec et marge x4
text_length = len(original) + len(current_text)  # ❌ Toujours la somme totale
estimated_time = text_length / 5  # secondes (vitesse très conservatrice)
captured_timeout = max(120, int(estimated_time * 4))  # minimum 120s, marge x4

# Construire le prompt à partir de la configuration
prompts = self.translation_config.get("prompts", {})

# Gérer les actions de sélection
is_selection = captured_action in ("translate_selection", "improve_selection")
text_to_translate = captured_selection["text"] if is_selection and captured_selection else None
```

#### Code après (gui/app_v2.py:470-493)
```python
# Construire le prompt à partir de la configuration
prompts = self.translation_config.get("prompts", {})

# Gérer les actions de sélection
is_selection = captured_action in ("translate_selection", "improve_selection")
text_to_translate = captured_selection["text"] if is_selection and captured_selection else None

# Calculer un timeout dynamique basé sur la taille du texte RÉELLEMENT ENVOYÉ
# Formule: timeout_base + (nb_caractères / vitesse_estimation) * marge
# Ollama local avec HTML: ~5 tokens/sec, avec ~4 chars/token = ~20 chars/sec (théorique)
# En pratique, avec HTML complexe: beaucoup plus lent
# Utiliser une vitesse très conservatrice de 5 chars/sec et marge x4
if is_selection and text_to_translate:
    # Pour une sélection, calculer sur la taille de la sélection
    text_length = len(text_to_translate)  # ✅ Sélection uniquement
elif captured_action in ("translate", "translate_selection"):
    # Pour une traduction, calculer sur la taille de l'original ou de la sélection
    text_length = len(text_to_translate) if text_to_translate else len(original)  # ✅ Texte à traduire
else:
    # Pour une amélioration, calculer sur l'original + texte actuel
    text_length = len(original) + len(current_text)  # ✅ Contexte complet

estimated_time = text_length / 5  # secondes (vitesse très conservatrice)
captured_timeout = max(120, int(estimated_time * 4))  # minimum 120s, marge x4
```

## Tests effectués

### Test de compilation
```bash
python3 -m py_compile gui/app_v2.py
# ✅ Aucune erreur de syntaxe
```

## Bénéfices

### Erreur `_mark_modified`
- ✅ Plus d'erreur lors de la traduction partielle
- ✅ Code plus simple et maintainable
- ✅ Utilisation cohérente de l'API `GotJsonManager`

### Timeout optimisé
- ✅ Timeout adapté à la taille réelle du texte
- ✅ Réponse plus rapide pour les petites sélections
- ✅ Meilleure expérience utilisateur

## Exemple d'impact

### Avant correction

Texte original de 5000 caractères, sélection de 50 caractères :
- Timeout calculé : max(120, (5000 + 0) / 5 * 4) = max(120, 4000) = **4000 secondes** ❌

### Après correction

Texte original de 5000 caractères, sélection de 50 caractères :
- Timeout calculé : max(120, 50 / 5 * 4) = max(120, 40) = **120 secondes** ✅

**Gain : 3880 secondes = 64 minutes !**
