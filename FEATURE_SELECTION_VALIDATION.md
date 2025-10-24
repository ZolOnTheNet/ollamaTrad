# Fonctionnalité : Validation et Nettoyage des Traductions Partielles

## Description

Lors de la traduction ou amélioration d'une sélection partielle, l'IA peut parfois retourner plus de texte que demandé (ajout de contexte, explications, etc.). Cette fonctionnalité détecte et nettoie automatiquement ces réponses pour garantir que seule la traduction demandée remplace la sélection.

## Problème résolu

### Avant
- L'utilisateur sélectionne "le chat" dans "Bonjour, voici le chat noir"
- L'IA retourne "Traduction : the cat (c'est une amélioration de la traduction précédente)"
- Le texte devient : "Bonjour, voici Traduction : the cat (c'est une amélioration de la traduction précédente) noir"
- ❌ Le texte est pollué par des explications non désirées

### Après
- L'utilisateur sélectionne "le chat" dans "Bonjour, voici le chat noir"
- L'IA retourne "Traduction : the cat (c'est une amélioration de la traduction précédente)"
- Le système détecte le préfixe et nettoie : "the cat"
- Le texte devient : "Bonjour, voici the cat noir"
- ✅ Seule la traduction est insérée

## Mécanismes de protection

### 1. Prompts renforcés

Pour les sélections, les prompts sont plus stricts :

#### Traduction de sélection (sans HTML)
```
Traduis UNIQUEMENT ce fragment [depuis le xxx] en yyy.
Réponds UNIQUEMENT avec la traduction du fragment, sans guillemets, sans explication, RIEN d'autre.

[texte sélectionné]
```

#### Traduction de sélection (avec HTML)
```
Traduis UNIQUEMENT ce fragment [depuis le xxx] en yyy.
IMPORTANT: Préserve TOUTES les balises HTML.
Réponds UNIQUEMENT avec la traduction du fragment, RIEN d'autre.

[texte sélectionné]
```

#### Amélioration de sélection (sans HTML)
```
Améliore UNIQUEMENT ce fragment de traduction [depuis le xxx] vers yyy.
Réponds UNIQUEMENT avec le fragment amélioré, sans guillemets, sans explication, RIEN d'autre.

Texte: "[texte sélectionné]"
Contexte: [contexte]
```

#### Amélioration de sélection (avec HTML)
```
Améliore UNIQUEMENT ce fragment de traduction [depuis le xxx] vers yyy.
IMPORTANT: Préserve TOUTES les balises HTML.
Réponds UNIQUEMENT avec le fragment amélioré, RIEN d'autre.

Texte: [texte sélectionné]
Contexte: [contexte]
```

### 2. Validation de longueur

Le système vérifie que le résultat n'est pas excessivement long :

```python
original_length = len(text_to_translate)
result_length = len(result)

# Tolérance : 2.5x la longueur originale
# (certaines langues sont plus verbeuses)
max_acceptable_length = original_length * 2.5

if result_length > max_acceptable_length:
    # Nettoyer le résultat
```

#### Exemples de ratio acceptable

| Langue source | Langue cible | Ratio typique | Exemple |
|---------------|--------------|---------------|---------|
| EN → FR | 1.2x | "cat" (3) → "chat" (4) |
| FR → EN | 0.8x | "bibliothèque" (13) → "library" (7) |
| EN → DE | 1.3x | "cat" (3) → "Katze" (5) |
| EN → JA | 1.0x | "cat" (3) → "猫" (1 en glyphes, ~3 en UTF-8) |

Le ratio 2.5x laisse une bonne marge pour les variations linguistiques.

### 3. Nettoyage par pattern matching

Si le résultat est trop long, le système cherche des motifs communs d'ajout de contexte :

```python
patterns = [
    r'^.*?[Tt]raduction\s*:?\s*(.+)$',    # "Traduction : xxx"
    r'^.*?[Vv]oici\s*:?\s*(.+)$',         # "Voici : xxx" ou "Voici la traduction : xxx"
    r'^.*?[Rr]ésultat\s*:?\s*(.+)$',      # "Résultat : xxx"
]
```

Ces patterns capturent le texte après les préfixes communs et ne gardent que la partie utile.

### 4. Avertissement utilisateur

Si même après nettoyage le résultat est trop long, un avertissement est affiché :

```
⚠️ Résultat trop long (500 car. pour 50 car. originaux).
Utilisation du résultat tel quel - vérifiez manuellement.
```

L'utilisateur peut alors :
- Vérifier le résultat dans le champ
- Utiliser Undo (↶) pour revenir en arrière
- Modifier manuellement si nécessaire

## Flux de traitement

```
┌─────────────────────────────────────────────────┐
│ 1. Utilisateur sélectionne du texte             │
│    "le chat" dans "Bonjour le chat noir"        │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ 2. Prompt strict envoyé à l'IA                  │
│    "Traduis UNIQUEMENT ce fragment..."          │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ 3. IA retourne la réponse                       │
│    "Traduction : the cat"                       │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ 4. Nettoyage de base                            │
│    .strip().strip('"').strip("'")               │
│    → "Traduction : the cat"                     │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ 5. Validation de longueur                       │
│    original: 7 car, résultat: 19 car            │
│    19 > 7 * 2.5 ? Non, mais proche              │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ 6. Nettoyage par pattern (si nécessaire)        │
│    Motif trouvé: "Traduction : (.+)"            │
│    → "the cat"                                  │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ 7. Remplacement de la sélection                 │
│    "Bonjour " + "the cat" + " noir"             │
│    → "Bonjour the cat noir"                     │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ 8. Sauvegarde dans l'historique                 │
│    history[0] = "Bonjour le chat noir"          │
│    text = "Bonjour the cat noir"                │
└─────────────────────────────────────────────────┘
```

## Exemples de nettoyage

### Cas 1 : Préfixe "Traduction :"

```
Input IA  : "Traduction : the black cat"
Original  : "le chat noir"
Nettoyage : "the black cat"
Résultat  : ✅ OK (ratio 14/13 = 1.08)
```

### Cas 2 : Explication ajoutée

```
Input IA  : "Voici la traduction : the cat (amélioration)"
Original  : "le chat"
Longueur  : 43 caractères > 7 * 2.5 = 17.5
Nettoyage : "the cat (amélioration)"
Longueur  : 22 caractères > 17.5
Résultat  : ⚠️ Avertissement affiché
Action    : Utilisation de "the cat (amélioration)" avec warning
```

### Cas 3 : HTML avec contexte

```
Input IA  : "Résultat : <strong>the cat</strong>"
Original  : "<strong>le chat</strong>"
Nettoyage : "<strong>the cat</strong>"
Résultat  : ✅ OK (balises HTML préservées)
```

## Configuration

Les prompts de sélection peuvent être personnalisés via `config/translation_config.json` :

```json
{
  "prompts": {
    "translate_selection": "Votre prompt personnalisé pour {lang} : {text}",
    "translate_selection_html": "Votre prompt HTML pour {lang} : {text}",
    "improve_selection": "Votre prompt d'amélioration pour {lang} : {current}",
    "improve_selection_html": "Votre prompt d'amélioration HTML pour {lang} : {current}"
  }
}
```

## Limitations connues

1. **Multi-lignes avec contexte** : Si l'IA ajoute du texte multi-lignes avant/après, le nettoyage peut échouer
2. **Langues non supportées** : Les patterns de nettoyage sont en français/anglais
3. **HTML complexe** : Les structures HTML très imbriquées peuvent tromper la validation de longueur

## Recommandations

### Pour de meilleurs résultats

1. **Sélections claires** : Sélectionnez des unités sémantiques complètes (mots, phrases)
2. **Contexte limité** : Évitez de sélectionner des fragments au milieu de mots
3. **Vérification** : Vérifiez toujours le résultat, surtout si un avertissement apparaît
4. **Historique** : Utilisez l'historique (↶) pour revenir en arrière si nécessaire

### En cas de problème

1. **Résultat trop long** : Vérifiez le warning, utilisez Undo si nécessaire
2. **Traduction incomplète** : Réessayez ou ajustez la sélection
3. **HTML cassé** : Vérifiez que les balises sont bien fermées dans la sélection

## Impact sur les performances

- **Overhead** : ~1-5ms pour la validation et le nettoyage
- **Mémoire** : Négligeable (regex compilées à la volée)
- **Réseau** : Aucun (traitement local)

Le coût est négligeable par rapport au temps de traduction par l'IA (plusieurs secondes).
