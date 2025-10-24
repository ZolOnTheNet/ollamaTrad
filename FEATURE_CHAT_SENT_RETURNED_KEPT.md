# Fonctionnalité : Affichage Envoyé/Retourné/Retenu dans le Chat

## Description

Le panneau de chat affiche maintenant les détails complets de chaque traduction en trois parties distinctes :
1. **Envoyé** : Le texte exact envoyé à l'IA
2. **Retourné** : La réponse brute de l'IA (avant nettoyage)
3. **Retenu** : Le texte finalement inséré dans le champ de traduction

Cette transparence permet de comprendre exactement ce qui se passe lors d'une traduction et de détecter les problèmes.

## Exemple d'affichage

### Cas 1 : Traduction de sélection réussie

```
[10:30:15] 🪄 FR: traduire (sélection)
   Envoyé: "Ambush"
   Retourné: "Embuscade"
   Retenu: "Embuscade"
   Longueur: envoyé=6, retourné=9, retenu=9
   [✓ Validé]
```

**Explication** :
- L'utilisateur a sélectionné "Ambush" dans le texte "Ambush, seize, protect, crush"
- L'IA a retourné "Embuscade"
- Le système a inséré "Embuscade" à la place de "Ambush"
- Résultat final : "Embuscade, seize, protect, crush"

### Cas 2 : IA retourne du texte supplémentaire

```
[10:32:45] 🪄 FR: traduire (sélection)
   Envoyé: "the cat"
   Retourné: "Traduction : le chat"
   Retenu: "le chat"
   Longueur: envoyé=7, retourné=21, retenu=7
   [✓ Validé]
```

**Explication** :
- L'utilisateur a sélectionné "the cat"
- L'IA a ajouté un préfixe : "Traduction : le chat"
- Le système a détecté et nettoyé le préfixe
- Seul "le chat" a été inséré (ce qui était souhaité)

### Cas 3 : Traduction complète avec contexte

```
[10:35:10] 🪄 EN: traduire
   Envoyé: "Bonjour le monde"
   Retourné: "Hello world"
   Retenu: "Hello world"
   Longueur: envoyé=17, retourné=11, retenu=11
   [❌ Non validé]
```

**Explication** :
- Traduction complète du champ (pas de sélection)
- Le texte original complet a été envoyé
- L'IA a correctement retourné uniquement la traduction
- Pas de nettoyage nécessaire

### Cas 4 : Amélioration de sélection

```
[10:40:00] 🪄 FR: améliorer (sélection)
   Envoyé: "le rapide renard"
   Retourné: "le renard rapide"
   Retenu: "le renard rapide"
   Longueur: envoyé=17, retourné=17, retenu=17
   [✓ Validé]
```

**Explication** :
- L'utilisateur a sélectionné "le rapide renard" pour correction
- L'IA a corrigé l'ordre : "le renard rapide" (plus idiomatique)
- Le texte corrigé a remplacé la sélection

## Mode Debug

Pour afficher le prompt complet envoyé à l'IA, activez le mode debug :

```python
# Dans gui/app_v2.py, ligne 56
self.debug_mode = True  # Mettre à True pour voir les prompts complets
```

### Exemple avec debug activé

```
[10:45:30] 🪄 FR: traduire (sélection)
   Envoyé: "Ambush"
   Retourné: "Embuscade"
   Retenu: "Embuscade"
   Longueur: envoyé=6, retourné=9, retenu=9
   [DEBUG] Prompt complet:
Traduis UNIQUEMENT ce fragment depuis l'anglais en fr.
Réponds UNIQUEMENT avec la traduction du fragment, sans guillemets, sans explication, RIEN d'autre.

Ambush
   [✓ Validé]
```

Le prompt complet est limité à 200 caractères dans l'affichage (avec "..." si plus long).

## Détails techniques

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Utilisateur sélectionne "Ambush" et clique sur 🪄       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Construction du prompt                                   │
│    "Traduis UNIQUEMENT ce fragment en fr..."                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Envoi à l'IA: "Ambush"                                   │
│    sent_text = "Ambush"                                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. IA retourne: "Embuscade"                                 │
│    raw_result = "Embuscade"                                 │
│    returned_by_ai = "Embuscade" (strip)                     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Nettoyage (strip quotes, détection préfixes)            │
│    kept_text = "Embuscade"                                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Insertion dans le texte                                  │
│    "Ambush, seize..." → "Embuscade, seize..."              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Affichage dans le chat                                   │
│    Envoyé: "Ambush"                                         │
│    Retourné: "Embuscade"                                    │
│    Retenu: "Embuscade"                                      │
└─────────────────────────────────────────────────────────────┘
```

### Code

#### chat_panel.py

```python
def add_magic_action(self, lang: str, action: str, sent_text: str,
                    returned_text: str, kept_text: str, validated: bool,
                    full_prompt: str = None):
    """
    Ajoute une action de baguette magique au chat.

    Args:
        sent_text: Texte envoyé à l'IA (sélection ou texte complet)
        returned_text: Réponse brute de l'IA
        kept_text: Texte finalement retenu/inséré
        full_prompt: Prompt complet (optionnel, pour debug)
    """
```

#### app_v2.py

```python
# Ligne 56 : Variable de mode debug
self.debug_mode = False  # True pour afficher les prompts

# Lignes 598-602 : Capture de la réponse brute
raw_result = loop.run_until_complete(self.ai_client.chat(prompt, timeout=captured_timeout))
returned_by_ai = raw_result.strip()
result = returned_by_ai.strip('"').strip("'")

# Ligne 644 : Détermination du texte envoyé
sent_to_ai = text_to_translate if is_selection and text_to_translate else (...)

# Lignes 721-729 : Appel au chat avec toutes les données
self.chat_panel.add_magic_action(
    lang=lang,
    action=action,
    sent_text=sent_text or "",
    returned_text=returned_text or "",
    kept_text=kept_text,
    validated=validated,
    full_prompt=debug_prompt  # Seulement si debug_mode = True
)
```

## Cas d'usage

### 1. Détecter les problèmes de traduction

**Problème** : L'IA ne traduit pas un mot

```
[11:00:00] 🪄 FR: traduire (sélection)
   Envoyé: "Ambush"
   Retourné: "Ambush"
   Retenu: "Ambush"
```

**Diagnostic** : L'IA n'a pas compris qu'il fallait traduire, ou a considéré que c'était un nom propre.

**Solution** : Réessayer ou modifier le prompt dans la configuration.

### 2. Vérifier le nettoyage

**Situation** : L'IA ajoute du contexte

```
[11:05:00] 🪄 FR: traduire (sélection)
   Envoyé: "cat"
   Retourné: "Voici la traduction : chat"
   Retenu: "chat"
```

**Constat** : Le système a correctement nettoyé le préfixe "Voici la traduction : ".

**Action** : Rien à faire, le nettoyage fonctionne.

### 3. Identifier les réponses verbeuses

**Situation** : L'IA explique au lieu de traduire

```
[11:10:00] 🪄 FR: traduire (sélection)
   Envoyé: "Hello"
   Retourné: "Bonjour (salutation formelle en français)"
   Retenu: "Bonjour (salutation formelle en français)"
⚠️ Résultat trop long (45 car. pour 5 car. originaux)
```

**Problème** : Le nettoyage n'a pas détecté l'explication entre parenthèses.

**Solution** : Utiliser l'historique (↶) pour revenir en arrière et réessayer.

### 4. Debug des prompts

**Mode debug activé** :

```
[11:15:00] 🪄 FR: traduire (sélection)
   Envoyé: "Ambush"
   Retourné: "Embuscade"
   Retenu: "Embuscade"
   Longueur: envoyé=6, retourné=9, retenu=9
   [DEBUG] Prompt complet:
Traduis UNIQUEMENT ce fragment depuis l'anglais en fr.
Réponds UNIQUEMENT avec la traduction du fragment, sans guillemets, sans explication, RIEN d'autre.

Ambush
   [✓ Validé]
```

**Utilité** : Voir exactement ce qui est envoyé à l'IA pour comprendre ou ajuster les prompts.

## Statistiques de longueur

Les longueurs affichées permettent de détecter rapidement les anomalies :

### Normal
```
Longueur: envoyé=10, retourné=12, retenu=12
```
→ Ratio normal (traduction peut être légèrement plus longue)

### Préfixe nettoyé
```
Longueur: envoyé=10, retourné=25, retenu=12
```
→ L'IA a ajouté du texte (25), mais il a été nettoyé (12)

### Problème
```
Longueur: envoyé=5, retourné=50, retenu=50
⚠️ Résultat trop long
```
→ Le nettoyage n'a pas réussi, vérification manuelle nécessaire

## Activation du mode debug

### Option 1 : Modifier le code

```python
# gui/app_v2.py, ligne 56
self.debug_mode = True
```

### Option 2 : Variable d'environnement (à implémenter)

```bash
export OLLAMAFIC_DEBUG=1
python ollamaTrad.py --gui
```

### Option 3 : Interface utilisateur (à implémenter)

```
Menu > Options > Mode Debug [✓]
```

## Limitations

1. **Prévisualisation** : Les textes de plus de 100 caractères sont tronqués avec "..."
2. **Prompt debug** : Limité à 200 caractères dans l'affichage
3. **Pas d'édition** : Le chat est en lecture seule, pas de modification possible
4. **Historique** : Le chat ne persiste pas entre les sessions

## Améliorations futures

1. **Export** : Sauvegarder l'historique du chat en fichier
2. **Filtres** : Afficher uniquement certains types d'actions
3. **Recherche** : Rechercher dans l'historique du chat
4. **Copie** : Copier facilement le texte envoyé/retourné/retenu
5. **Statistiques** : Graphiques de longueur, temps de réponse, etc.

## Avantages

✅ **Transparence totale** : Voir exactement ce qui se passe

✅ **Debug facile** : Identifier rapidement les problèmes

✅ **Confiance** : Comprendre comment l'IA traite les textes

✅ **Apprentissage** : Voir comment les prompts influencent les réponses

✅ **Traçabilité** : Historique complet de toutes les traductions

Cette fonctionnalité rend le processus de traduction complètement transparent et aide à comprendre et résoudre les problèmes rapidement !
