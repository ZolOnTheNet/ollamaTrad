# Correction Bug: RuntimeWarning coroutine 'AIClient.chat' was never awaited

## 🐛 Problème

Lors du clic sur la baguette magique, l'erreur suivante apparaissait:

```
translation_form.py:271: RuntimeWarning: coroutine 'AIClient.chat' was never awaited
  self.on_magic_click(lang, action)
RuntimeWarning: Enable tracemalloc to get the object allocation traceback
```

## 🔍 Cause

La méthode `AIClient.chat()` est **asynchrone** (déclarée avec `async def`), mais elle était appelée de manière **synchrone** dans l'interface Tkinter.

```python
# ❌ AVANT (incorrect)
result = self.ai_client.chat(prompt)  # Appel synchrone d'une fonction async
```

En Python, les fonctions asynchrones (coroutines) doivent être appelées avec `await` dans un contexte asynchrone, ou exécutées via `asyncio.run()` ou `loop.run_until_complete()`.

## ✅ Solution Implémentée

La solution consiste à exécuter l'appel asynchrone dans un **thread séparé** avec sa propre boucle d'événements asyncio, puis mettre à jour l'interface Tkinter dans le thread principal.

### Modifications dans `gui/app_v2.py`

#### 1. Ajout des imports nécessaires

```python
import asyncio
import threading
```

#### 2. Refactoring de `_on_magic_click()`

La méthode a été divisée en 3 parties:

**a) Démarrage de la traduction (thread principal)**
```python
def _on_magic_click(self, lang: str, action: str):
    # Préparation du prompt
    path = self.translation_form.current_path
    entry = self.translation_form.current_entry
    original = entry["ori"]
    current_text = entry[lang]["text"]

    if action == "translate":
        prompt = f'Traduis "{original}" en {lang}...'
    else:  # improve
        prompt = f'Améliore cette traduction...'

    # Afficher le statut
    self.status_label.config(text=f"🪄 Traduction {lang} en cours...")
    self.root.update()

    # Lancer le thread de traduction
    def run_translation():
        # Code du thread (voir ci-dessous)

    thread = threading.Thread(target=run_translation, daemon=True)
    thread.start()
```

**b) Exécution asynchrone (thread séparé)**
```python
def run_translation():
    """Fonction exécutée dans un thread séparé"""
    try:
        # Créer une nouvelle boucle d'événements pour ce thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Exécuter l'appel asynchrone
        result = loop.run_until_complete(self.ai_client.chat(prompt))
        result = result.strip().strip('"').strip("'")

        # Fermer la boucle
        loop.close()

        # Mettre à jour l'UI dans le thread principal
        self.root.after(0, lambda: self._on_translation_success(
            path, lang, result, action, entry
        ))

    except Exception as e:
        # Afficher l'erreur dans le thread principal
        self.root.after(0, lambda: self._on_translation_error(str(e)))
```

**c) Mise à jour de l'interface (retour au thread principal)**
```python
def _on_translation_success(self, path: str, lang: str, result: str,
                           action: str, entry: dict):
    """Callback appelé après succès (dans le thread principal)"""
    try:
        # Mettre à jour avec historique
        self.got_manager.update_translation(path, lang, result)

        # Rafraîchir le formulaire
        self.translation_form.current_entry = self.got_manager._get_entry_by_path(path)
        self.translation_form.update_language_data(lang)

        # Mettre à jour les couleurs
        self._update_tree_colors(path)

        # Ajouter au chat
        validated = entry[lang]["valid"]
        self.chat_panel.add_magic_action(lang, action, result, validated)

        self.status_label.config(text="✓ Traduction terminée")

    except Exception as e:
        self._on_translation_error(str(e))

def _on_translation_error(self, error_message: str):
    """Callback appelé en cas d'erreur (dans le thread principal)"""
    messagebox.showerror("Erreur IA", f"Erreur lors de l'appel IA: {error_message}")
    self.chat_panel.add_error(error_message)
    self.status_label.config(text="❌ Erreur de traduction")
```

## 🎯 Architecture de la Solution

```
Thread Principal (Tkinter)          Thread Séparé (Asyncio)
─────────────────────────          ───────────────────────

1. Clic sur 🪄
   ↓
2. _on_magic_click()
   - Préparer prompt
   - Afficher statut "en cours..."
   ↓
3. Créer thread.start()  ────────→  4. run_translation()
                                       ↓
                                    5. Créer loop asyncio
                                       ↓
                                    6. loop.run_until_complete(
                                          ai_client.chat(prompt)
                                       )
                                       ↓
                                    7. Obtenir résultat
                                       ↓
                                    8. loop.close()
                                       ↓
9. root.after(0, ...)     ←────────  9. Envoyer callback
   ↓                                   au thread principal
10. _on_translation_success()
    - Mettre à jour got_manager
    - Rafraîchir formulaire
    - Mettre à jour arbre
    - Logger dans chat
    - Statut "✓ terminée"
```

## 🔑 Points Clés

### 1. Pourquoi un thread séparé ?

Tkinter n'est **pas thread-safe** et doit toujours être manipulé depuis le thread principal. Les opérations longues (comme les appels IA) bloqueraient l'interface si elles étaient exécutées dans le thread principal.

### 2. Pourquoi `asyncio.new_event_loop()` ?

Chaque thread Python ne peut avoir qu'une seule boucle d'événements asyncio. Comme le thread principal a déjà sa boucle (pour Tkinter), le thread séparé doit créer la sienne.

### 3. Pourquoi `root.after(0, ...)` ?

`root.after(0, callback)` permet d'exécuter le callback dans le thread principal de Tkinter, même si on l'appelle depuis un autre thread. C'est la manière sûre de mettre à jour l'UI depuis un thread.

### 4. Pourquoi `daemon=True` ?

Un thread daemon se termine automatiquement quand le programme principal se termine, évitant que l'application ne reste bloquée si un appel IA est en cours.

## 🧪 Test de la Correction

### Test 1: Traduction simple
```bash
python3 ollamaTrad.py --gui-v2 --file test.got.json
```

1. Sélectionner une entrée dans l'arbre
2. Cliquer sur 🪄 pour "fr"
3. Vérifier:
   - ✅ Pas de RuntimeWarning
   - ✅ Barre de statut affiche "en cours..."
   - ✅ Interface reste responsive
   - ✅ Résultat apparaît après quelques secondes
   - ✅ Formulaire se met à jour
   - ✅ Message dans le chat

### Test 2: Traduction rapide successive
1. Cliquer sur 🪄 pour "fr"
2. Immédiatement cliquer sur 🪄 pour "es"
3. Vérifier:
   - ✅ Les deux requêtes s'exécutent en parallèle
   - ✅ Pas de conflit
   - ✅ Les deux résultats arrivent

### Test 3: Erreur réseau
1. Arrêter Ollama: `systemctl stop ollama`
2. Cliquer sur 🪄
3. Vérifier:
   - ✅ Message d'erreur s'affiche
   - ✅ Pas de crash de l'application
   - ✅ Statut "❌ Erreur de traduction"

## 📊 Comparaison Avant/Après

### ❌ AVANT

```python
def _on_magic_click(self, lang: str, action: str):
    # ...
    result = self.ai_client.chat(prompt)  # ❌ RuntimeWarning
    # ...
```

**Problèmes:**
- RuntimeWarning
- Interface bloquée pendant l'appel IA
- Pas de gestion async

### ✅ APRÈS

```python
def _on_magic_click(self, lang: str, action: str):
    # ...
    def run_translation():
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(self.ai_client.chat(prompt))
        self.root.after(0, lambda: self._on_translation_success(...))

    threading.Thread(target=run_translation, daemon=True).start()
```

**Avantages:**
- ✅ Pas de warning
- ✅ Interface non bloquée
- ✅ Gestion async correcte
- ✅ Thread-safe

## 🔄 Alternative: Solution avec `asyncio.run()`

Si vous préférez une approche plus simple (mais qui bloque l'interface):

```python
def _on_magic_click(self, lang: str, action: str):
    # ...
    try:
        result = asyncio.run(self.ai_client.chat(prompt))
        # Mettre à jour l'UI
        self._on_translation_success(path, lang, result, action, entry)
    except Exception as e:
        self._on_translation_error(str(e))
```

**Inconvénient:** L'interface sera gelée pendant l'appel IA (pas recommandé).

## 📝 Notes pour le Développement Futur

### Si vous ajoutez d'autres appels async dans l'interface:

**Utilisez le même pattern:**

```python
def _on_some_action(self):
    def run_async_operation():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(async_function())
        loop.close()
        self.root.after(0, lambda: self._on_success(result))

    threading.Thread(target=run_async_operation, daemon=True).start()
```

### Bonnes pratiques:

1. **Toujours** utiliser un thread séparé pour les opérations async longues
2. **Toujours** mettre à jour l'UI via `root.after(0, ...)`
3. **Toujours** capturer les exceptions et les afficher proprement
4. **Toujours** utiliser `daemon=True` pour les threads de fond

## ✅ Statut

**Correction complétée et testée.**

Le problème de RuntimeWarning est résolu. L'interface graphique gère maintenant correctement les appels asynchrones à l'IA sans bloquer l'interface utilisateur.
