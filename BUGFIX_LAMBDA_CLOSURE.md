# Correction Bug: NameError avec Lambda et Changement de Sélection

## 🐛 Problèmes Identifiés

### Problème 1: NameError dans le Lambda

```
Exception in Tkinter callback
NameError: cannot access free variable 'e' where it is not associated with a value in enclosing scope
```

**Cause:** Le lambda `lambda: self._on_translation_error(str(e))` capturait la variable `e` par référence, mais quand le lambda était exécuté plus tard, la variable `e` n'existait plus dans la portée.

### Problème 2: Changement de Sélection pendant la Traduction

**Symptôme:** Quand l'utilisateur sélectionne un deuxième champ pendant qu'une traduction est en cours sur le premier, le formulaire ne se met pas à jour correctement et peut afficher les mauvaises données.

## ✅ Solutions Implémentées

### Solution 1: Capture Correcte des Variables dans les Lambdas

**❌ AVANT (incorrect):**
```python
except Exception as e:
    self.root.after(0, lambda: self._on_translation_error(str(e)))
```

**Problème:** La variable `e` est capturée par référence, pas par valeur.

**✅ APRÈS (correct):**
```python
except Exception as ex:
    error_msg = str(ex)  # Capturer la valeur immédiatement
    self.root.after(0, lambda msg=error_msg: self._on_translation_error(msg))
```

**Explication:**
- On renomme `e` en `ex` pour éviter les confusions
- On capture `str(ex)` dans une variable locale `error_msg`
- Le lambda utilise un paramètre par défaut `msg=error_msg` qui capture la **valeur** immédiatement

### Solution 2: Capture Correcte de Toutes les Variables

Pour le callback de succès aussi:

**❌ AVANT:**
```python
self.root.after(0, lambda: self._on_translation_success(path, lang, result, action, entry))
```

**✅ APRÈS:**
```python
self.root.after(0, lambda p=path, l=lang, r=result, a=action, e=entry:
                          self._on_translation_success(p, l, r, a, e))
```

**Avantage:** Toutes les variables sont capturées par valeur au moment de la création du lambda.

### Solution 3: Vérification du Contexte avant Mise à Jour

**Logique ajoutée dans `_on_translation_success()`:**

```python
def _on_translation_success(self, path: str, lang: str, result: str, action: str, entry: dict):
    # 1. Toujours mettre à jour got_manager (données persistées)
    self.got_manager.update_translation(path, lang, result)

    # 2. Toujours mettre à jour l'arbre (visuel)
    self._update_tree_colors(path)

    # 3. Toujours logger dans le chat
    updated_entry = self.got_manager._get_entry_by_path(path)
    validated = updated_entry[lang]["valid"]
    self.chat_panel.add_magic_action(lang, action, result, validated)

    # 4. NE rafraîchir le formulaire QUE si c'est toujours le même chemin
    if self.translation_form.current_path == path:
        self.translation_form.current_entry = updated_entry
        self.translation_form.update_language_data(lang)
        self.status_label.config(text="✓ Traduction terminée")
    else:
        # L'utilisateur a changé de sélection
        self.status_label.config(text=f"✓ Traduction terminée pour {path}")
```

## 📊 Scénarios Corrigés

### Scénario 1: Erreur Réseau

```
1. Clic sur 🪄
   ↓
2. Thread lancé
   ↓
3. Exception levée (Ollama arrêté)
   ↓
4. error_msg = str(ex) ✓ Capture immédiate
   ↓
5. Lambda avec msg=error_msg ✓ Valeur capturée
   ↓
6. root.after(0, ...) exécuté plus tard
   ↓
7. _on_translation_error(msg) ✓ Pas de NameError
```

### Scénario 2: Changement de Sélection Rapide

```
État Initial:
- Sélection: app/title
- Formulaire: app/title

1. Clic sur 🪄 pour app/title [fr]
   ↓
2. Thread démarre...
   ↓
3. Utilisateur sélectionne app/version
   ↓
4. Formulaire change: app/version
   ↓
5. Thread termine avec résultat pour app/title
   ↓
6. _on_translation_success() appelé
   ↓
7. Vérification: current_path == "app/version" != "app/title"
   ↓
8. Mise à jour got_manager ✓
9. Mise à jour arbre ✓
10. Log chat ✓
11. Formulaire NON mis à jour ✓ (car sélection différente)
12. Statut: "✓ Traduction terminée pour app/title"
```

### Scénario 3: Traductions Multiples en Parallèle

```
1. Sélection: app/title
   Clic 🪄 [fr] → Thread 1 démarre

2. Clic 🪄 [es] → Thread 2 démarre

3. Thread 1 termine
   → Mise à jour [fr] ✓
   → Formulaire rafraîchi (si toujours app/title) ✓

4. Thread 2 termine
   → Mise à jour [es] ✓
   → Formulaire rafraîchi (si toujours app/title) ✓

Résultat: Les deux traductions sont appliquées correctement
```

## 🔍 Comprendre les Closures Python

### Problème des Variables dans les Lambdas

```python
# ❌ CAPTURE PAR RÉFÉRENCE
for i in range(3):
    callbacks.append(lambda: print(i))

for cb in callbacks:
    cb()  # Affiche: 2, 2, 2 (toutes capturent la dernière valeur de i)

# ✅ CAPTURE PAR VALEUR
for i in range(3):
    callbacks.append(lambda x=i: print(x))

for cb in callbacks:
    cb()  # Affiche: 0, 1, 2 (chacune capture sa propre valeur)
```

### Application à notre Bug

```python
# ❌ PROBLÉMATIQUE
try:
    # code...
except Exception as e:
    # 'e' existe seulement dans ce bloc
    later_callback = lambda: handle_error(e)
    # Quand later_callback() est appelé plus tard, 'e' n'existe plus

# ✅ SOLUTION
try:
    # code...
except Exception as e:
    error_msg = str(e)  # Capturer immédiatement
    later_callback = lambda msg=error_msg: handle_error(msg)
    # 'msg' a une valeur capturée, indépendante de 'e'
```

## 🧪 Tests de Validation

### Test 1: Gestion d'Erreur
```bash
# Arrêter Ollama
sudo systemctl stop ollama

# Lancer l'app
python3 ollamaTrad.py --gui-v2 --file test.got.json

# Cliquer sur 🪄
# Vérifier:
✓ Message d'erreur s'affiche
✓ Pas de NameError dans la console
✓ Application reste stable
```

### Test 2: Changement de Sélection Rapide
```bash
python3 ollamaTrad.py --gui-v2 --file test.got.json

1. Sélectionner app/title
2. Cliquer 🪄 [fr]
3. IMMÉDIATEMENT sélectionner app/version
4. Attendre fin de traduction

Vérifier:
✓ app/title[fr] est mis à jour dans got_manager
✓ Arbre montre app/title en rouge/vert
✓ Chat montre "Traduction pour app/title"
✓ Formulaire affiche toujours app/version (pas changé)
✓ Statut: "✓ Traduction terminée pour app/title"
```

### Test 3: Traductions Parallèles
```bash
1. Sélectionner app/title
2. Cliquer 🪄 [fr]
3. Cliquer 🪄 [es]
4. Attendre

Vérifier:
✓ Les deux threads s'exécutent
✓ Les deux résultats arrivent
✓ Formulaire se met à jour deux fois
✓ Chat montre les deux actions
```

## 📝 Bonnes Pratiques pour les Closures

### 1. Toujours Capturer par Valeur pour `root.after()`

```python
# ✅ BON
value = compute_something()
root.after(0, lambda v=value: callback(v))

# ❌ MAUVAIS
root.after(0, lambda: callback(value))  # value peut changer
```

### 2. Utiliser des Noms Explicites

```python
# ✅ BON
except Exception as ex:
    error_msg = str(ex)
    root.after(0, lambda msg=error_msg: handle_error(msg))

# ❌ CONFUS
except Exception as e:
    root.after(0, lambda: handle_error(str(e)))
```

### 3. Documenter les Captures

```python
# Variables capturées par valeur pour éviter les closures
self.root.after(0, lambda p=path, l=lang, r=result:
                          self._on_success(p, l, r))
```

## 📊 Comparaison Avant/Après

### ❌ AVANT

**Problèmes:**
1. NameError avec la variable `e`
2. Formulaire peut afficher les mauvaises données
3. Confus pour l'utilisateur

**Code:**
```python
except Exception as e:
    self.root.after(0, lambda: self._on_translation_error(str(e)))

def _on_translation_success(...):
    # Toujours mettre à jour le formulaire
    self.translation_form.update_language_data(lang)
```

### ✅ APRÈS

**Améliorations:**
1. ✅ Variables capturées correctement par valeur
2. ✅ Vérification du contexte avant mise à jour
3. ✅ Messages clairs pour l'utilisateur

**Code:**
```python
except Exception as ex:
    error_msg = str(ex)
    self.root.after(0, lambda msg=error_msg: self._on_translation_error(msg))

def _on_translation_success(...):
    # Vérifier si c'est toujours le bon contexte
    if self.translation_form.current_path == path:
        self.translation_form.update_language_data(lang)
    else:
        self.status_label.config(text=f"✓ Terminée pour {path}")
```

## 🎯 Résumé des Corrections

| Bug | Cause | Solution |
|-----|-------|----------|
| NameError | Variable `e` capturée par référence | Capture par valeur avec `msg=error_msg` |
| Mauvais contexte | Pas de vérification du chemin | `if current_path == path` |
| Variables perdues | Lambda sans paramètres par défaut | Lambda avec `p=path, l=lang, ...` |

## ✅ Statut

**Corrections complétées et testées.**

Les deux bugs sont résolus:
1. Plus de NameError avec les lambdas
2. Le formulaire reste cohérent même si l'utilisateur change de sélection pendant une traduction
