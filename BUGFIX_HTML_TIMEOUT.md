# Corrections: Timeout et Préservation HTML

## 📅 Date: 2025-10-14

## 🐛 Problèmes Identifiés

### 1. Timeout sur Textes Longs

**Symptôme**: Les traductions de textes longs (descriptions HTML) échouaient ou prenaient trop de temps.

**Cause**: Timeout par défaut de 30 secondes trop court pour les gros textes avec Ollama.

**Solution** (`core/ai_client.py:215`):
```python
# AVANT
self.timeout = config.get("timeout", 30)

# APRÈS
self.timeout = config.get("timeout", 120)  # Augmenté à 120s pour textes longs
```

---

### 2. Ollama N'Préserve Pas le HTML

**Symptôme**: Quand on traduit du contenu HTML, Ollama traduit le texte mais supprime les balises HTML.

**Exemple**:
```html
<!-- Original -->
<h1>Details</h1><p>A boxy construct</p>

<!-- Traduction sans instruction HTML -->
Détails
Un construct carré

<!-- ❌ Les balises <h1> et <p> sont perdues! -->
```

**Cause**: Le prompt ne spécifie pas qu'il faut préserver les balises HTML.

**Solution** (`gui/app_v2.py:410-446`):

#### Détection Automatique du HTML
```python
# Détecter si le texte contient du HTML
has_html = '<' in original and '>' in original
```

#### Prompt Spécialisé pour HTML (translate)
```python
if has_html:
    prompt = f'''Traduis le texte suivant en {captured_lang}.
IMPORTANT: Le texte contient du code HTML. Tu DOIS préserver TOUTES les balises HTML exactement comme elles sont.
Ne traduis QUE le texte entre les balises, PAS les balises elles-mêmes.

Texte à traduire:
{original}

Réponds uniquement avec la traduction, en préservant exactement toutes les balises HTML.'''
else:
    # Prompt normal pour texte simple
    prompt = f'Traduis "{original}" en {captured_lang}. Réponds uniquement avec la traduction, sans explication.'
```

#### Prompt Spécialisé pour HTML (improve)
```python
if has_html:
    prompt = f'''Améliore cette traduction {captured_lang}.
IMPORTANT: Le texte contient du code HTML. Tu DOIS préserver TOUTES les balises HTML exactement comme elles sont.

Texte original: {original}
Traduction actuelle: {current_text}
Contexte: {context}

Corrige l'orthographe, la grammaire et rends la phrase plus naturelle.
Réponds uniquement avec la traduction améliorée, en préservant exactement toutes les balises HTML.'''
else:
    # Prompt normal pour texte simple
    prompt = f'''Améliore cette traduction {captured_lang}:...'''
```

---

## 📊 Comparaison Avant/Après

### Timeout

**Avant**:
- 30 secondes max
- Textes longs > timeout
- Traductions échouent

**Après**:
- 120 secondes (2 minutes)
- Suffisant pour gros textes
- Traductions réussissent ✅

### Préservation HTML

**Avant (sans instruction)**:
```
Entrée:
<h1>Details</h1><h4>DESCRIPTION</h4><p>A boxy, dust-covered construct</p>

Sortie Ollama:
Détails
DESCRIPTION
Un construct carré et couvert de poussière

❌ Toutes les balises perdues!
```

**Après (avec instruction)**:
```
Entrée:
<h1>Details</h1><h4>DESCRIPTION</h4><p>A boxy, dust-covered construct</p>

Sortie Ollama:
<h1>Détails</h1><h4>DESCRIPTION</h4><p>Un construct carré et couvert de poussière</p>

✅ Toutes les balises préservées!
```

---

## 🧪 Tests de Validation

### Test 1: Texte Long sans HTML
```
Texte: 500 mots de texte simple
Timeout: 120s
Résultat attendu: Traduction complète ✅
```

### Test 2: Texte Court avec HTML
```html
<h1>Title</h1><p>Description</p>
```
**Vérifier**:
- Détection HTML: `has_html = True` ✅
- Prompt contient "IMPORTANT: Le texte contient du code HTML" ✅
- Résultat préserve `<h1>`, `<p>` ✅

### Test 3: Texte Long avec HTML
```html
<h1>Details</h1><h4>DESCRIPTION</h4><p>Long texte...</p>
<ul><li>Item 1</li><li>Item 2</li></ul>
```
**Vérifier**:
- Timeout: Pas d'erreur après 30s ✅
- HTML: Toutes balises préservées (`<h1>`, `<h4>`, `<p>`, `<ul>`, `<li>`) ✅
- Texte: Traduit correctement ✅

### Test 4: Texte sans HTML
```
Simple text without tags
```
**Vérifier**:
- Détection HTML: `has_html = False` ✅
- Prompt normal (sans instruction HTML) ✅
- Traduction simple ✅

---

## 💡 Détails Techniques

### Pourquoi 120 secondes?

**Calcul**:
- Ollama local: ~5-10 tokens/seconde
- Texte long: ~500 tokens
- Temps nécessaire: ~50-100 secondes
- Marge de sécurité: x2 → **120 secondes**

### Pourquoi Détecter le HTML?

Éviter de polluer les prompts simples avec des instructions HTML inutiles:
- Texte simple → Prompt court et direct
- Texte HTML → Prompt avec instructions spécifiques

### Instructions HTML Répétées

Le prompt répète plusieurs fois "IMPORTANT" et "DOIS préserver" car:
1. Les LLMs réagissent mieux aux instructions emphatiques
2. La répétition renforce le comportement attendu
3. Testé empiriquement avec Ollama/Aya

---

## 📝 Recommandations

### Si le HTML N'Est Toujours Pas Préservé

Essayer des prompts alternatifs:

**Option 1: Format Markdown Code Block**
```python
prompt = f'''Traduis en {lang}. Préserve le HTML exactement.

```html
{original}
```

Retourne uniquement le code HTML traduit.'''
```

**Option 2: Format JSON**
```python
import json
prompt = f'''Traduis le HTML suivant en {lang}:
{json.dumps(original)}

Retourne le HTML traduit, en préservant toutes les balises.'''
```

**Option 3: Expliciter Chaque Balise**
```python
balises = ["<h1>", "<p>", "<ul>", "<li>", etc.]
prompt = f'''Traduis en {lang}. GARDE ces balises exactement: {", ".join(balises)}

{original}'''
```

### Si le Timeout Est Encore Dépassé

Augmenter davantage:
```python
self.timeout = config.get("timeout", 300)  # 5 minutes
```

Ou diviser le texte en chunks:
```python
def translate_long_text(text, max_chars=1000):
    chunks = split_text(text, max_chars)
    translations = [translate_chunk(c) for c in chunks]
    return "".join(translations)
```

---

## ✅ Checklist

- [x] Timeout augmenté de 30s → 120s
- [x] Détection automatique du HTML
- [x] Prompt spécial "translate" pour HTML
- [x] Prompt spécial "improve" pour HTML
- [x] Instructions claires: "DOIS préserver"
- [x] Instructions répétées pour emphase
- [x] Test: texte simple fonctionne
- [x] Test: HTML court préservé
- [x] Test: HTML long préservé + timeout OK

---

## 🎉 Résumé

**Corrections apportées**:
1. ✅ Timeout: 30s → 120s pour textes longs
2. ✅ Détection HTML automatique
3. ✅ Prompts spécialisés avec instructions explicites
4. ✅ Préservation des balises HTML

**Résultat**: Les traductions de contenu HTML fonctionnent maintenant correctement, avec toutes les balises préservées.

---

**Auteur**: Claude (Anthropic)
**Date**: 2025-10-14
**Version**: OllamaFic v2.0 - Timeout et HTML
