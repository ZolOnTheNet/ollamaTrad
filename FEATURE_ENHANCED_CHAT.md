# Fonctionnalité : Chat Amélioré avec Dialogue Direct

## Description

Le panneau de chat a été amélioré pour afficher des informations complètes sur les traductions et permettre un dialogue direct avec l'IA via une zone de saisie intégrée.

## Améliorations apportées

### 1. Affichage d'informations complètes

Chaque action de traduction affiche maintenant :
- **Type d'action** : Traduire, Améliorer, Traduire (sélection), Améliorer (sélection)
- **Texte original** : Le texte source (prévisualisation de 100 caractères)
- **Texte avant** : Le texte actuel avant modification (pour les améliorations)
- **Résultat** : Le texte traduit/amélioré
- **Longueur** : Nombre de caractères du résultat
- **Statut** : ✓ Validé ou ❌ Non validé

### 2. Zone de dialogue direct avec l'IA

Une zone de saisie en bas du chat permet de :
- Poser des questions à l'IA
- Demander des explications sur les traductions
- Obtenir des suggestions d'amélioration
- Dialoguer librement sur n'importe quel sujet

## Interface utilisateur

### Panneau de chat

```
┌─────────────────────────────────────────────────┐
│ ▼ Chat & Historique (app/title)         🗙     │
├─────────────────────────────────────────────────┤
│ [10:30:15] 🪄 FR: traduire                     │
│   Original: "The quick brown fox..."           │
│   Résultat: "Le renard brun rapide..."         │
│   Longueur: 156 caractères                     │
│   [✓ Validé]                                   │
│                                                 │
│ [10:31:20] > Pourquoi "rapide" après "brun"?   │
│                                                 │
│ [10:31:23] 💭 Réflexion en cours...            │
│                                                 │
│ [10:31:25] < En français, l'adjectif qualifi-  │
│   catif se place généralement après le nom...  │
│                                                 │
├─────────────────────────────────────────────────┤
│ 💬 [Votre message ici...    ] [ Envoyer ]     │
└─────────────────────────────────────────────────┘
```

### Zone de saisie

- **Icône** : 💬 (bulle de dialogue)
- **Champ** : Entrée de texte extensible
- **Bouton** : "Envoyer" (fond vert)
- **Raccourci** : Appuyer sur `Entrée` pour envoyer

## Exemples d'utilisation

### Exemple 1 : Demander des explications

**Utilisateur** : `Pourquoi as-tu utilisé "améliorer" au lieu de "renforcer"?`

**IA** : `"Améliorer" est plus général et convient dans ce contexte car il s'agit d'une augmentation de qualité globale. "Renforcer" implique une consolidation ou une amplification spécifique, ce qui pourrait ne pas correspondre au sens originel du texte anglais "improve".`

### Exemple 2 : Obtenir des suggestions

**Utilisateur** : `Comment rendre cette traduction plus idiomatique?`

**IA** : `Pour une traduction plus idiomatique en français, je suggère :
1. Remplacer "obtenir des informations" par "se renseigner"
2. Utiliser "mettre en place" au lieu de "établir"
3. Préférer "au quotidien" à "tous les jours"

Ces expressions sont plus naturelles en français moderne.`

### Exemple 3 : Vérification contextuelle

**Utilisateur** : `Est-ce que "chat" dans ce contexte signifie l'animal ou la conversation?`

**IA** : `Dans le contexte "app/messages/title", il s'agit très probablement de la conversation (discussion en ligne), pas de l'animal. Je recommande de traduire par "Discussion" ou "Messagerie" plutôt que "Chat" en français.`

### Exemple 4 : Questions générales

**Utilisateur** : `Quelle est la différence entre "vous" et "tu" en français formel?`

**IA** : `En français :
- "Vous" (vouvoiement) : forme de politesse, situations formelles, personnes inconnues ou hiérarchiquement supérieures
- "Tu" (tutoiement) : forme familière, amis, famille, contextes décontractés

Pour une application professionnelle, utilisez systématiquement "vous".`

## Détails d'affichage des actions

### Format d'une action de traduction complète

```
[10:30:15] 🪄 EN: traduire
   Original: "Welcome to our application! Click here to start..."
   Résultat: "Bienvenue dans notre application ! Cliquez ici pour commencer..."
   Longueur: 65 caractères
   [✓ Validé]
```

### Format d'une action d'amélioration

```
[10:32:45] 🪄 FR: améliorer
   Original: "Welcome to our application"
   Avant: "Bienvenue à notre application"
   Résultat: "Bienvenue dans notre application"
   Longueur: 35 caractères
   [❌ Non validé]
```

### Format d'une traduction de sélection

```
[10:35:10] 🪄 FR: traduire (sélection)
   Original: "the quick brown fox"
   Résultat: "le renard brun rapide"
   Longueur: 21 caractères
   [✓ Validé]
```

### Format d'autres actions

**Validation/Invalidation** :
```
[10:40:00] > Traduction FR validée
```

**Rollback** :
```
[10:42:30] ↶ FR: Retour à "Ancienne traduction..."
```

**Édition manuelle** :
```
[10:45:15] ✏ FR: Édition manuelle → "Nouvelle traduction..."
```

**Erreur** :
```
[10:50:20] ❌ Erreur: Timeout après 120 secondes
```

## Fonctionnement technique

### Affichage des informations complètes

La méthode `add_magic_action` a été enrichie :

```python
def add_magic_action(self, lang: str, action: str, result: str, validated: bool,
                    original: str = None, current: str = None, is_selection: bool = False):
```

Paramètres :
- `lang` : Code langue (ex: "fr")
- `action` : Type d'action ("translate", "improve", "translate_selection", "improve_selection")
- `result` : Texte résultant de la traduction
- `validated` : État de validation
- `original` : Texte original (optionnel)
- `current` : Texte avant modification (optionnel, pour amélioration)
- `is_selection` : Indique si c'est une sélection partielle

### Dialogue avec l'IA

#### Flux de traitement

1. **Utilisateur envoie un message** → `_on_send_message()`
2. **Affichage dans le chat** → Message utilisateur visible
3. **Callback app_v2** → `_on_user_chat_message(message)`
4. **Thread séparé** → Appel à l'IA via `ai_client.chat(message, timeout=60)`
5. **Réponse reçue** → `_on_chat_response_success(response)`
6. **Affichage dans le chat** → Réponse IA visible

#### Gestion des erreurs

En cas d'erreur (timeout, connexion, etc.) :
1. Capture de l'exception dans le thread
2. Callback `_on_chat_response_error(error_message)`
3. Affichage de l'erreur dans le chat
4. Mise à jour de la barre de statut

### Timeout

- **Traduction** : Calculé dynamiquement selon la longueur du texte (120s minimum)
- **Dialogue** : Timeout fixe de 60 secondes
- Plus court pour le dialogue car les réponses sont généralement brèves

### Threading

Les appels à l'IA sont exécutés dans des threads séparés pour :
- Ne pas bloquer l'interface utilisateur
- Permettre d'annuler les opérations longues
- Continuer à utiliser l'application pendant le traitement

## Coloration des messages

Le chat utilise différentes couleurs pour distinguer les types de messages :

| Type | Couleur | Police | Utilisation |
|------|---------|--------|-------------|
| `user` | Bleu | Gras | Messages de l'utilisateur |
| `assistant` | Vert | Normal | Réponses de l'IA |
| `system` | Orange | Italique | Messages système |
| `error` | Rouge | Gras | Messages d'erreur |
| `timestamp` | Gris | Petite (7pt) | Horodatage |
| `magic` | Violet | Gras | Actions de baguette magique |

## Raccourcis clavier

- **Entrée** : Envoyer le message
- **Shift+Entrée** : (Réservé pour futur multi-lignes, actuellement sans effet)

## Limitations

### Longueur des messages

- **Prévisualisation** : Les textes de plus de 100 caractères sont tronqués avec "..."
- **Message complet** : Toujours disponible dans les données, seul l'affichage est tronqué

### Contexte de conversation

- L'IA ne conserve PAS l'historique de conversation entre les messages
- Chaque message est traité de manière indépendante
- Pour des questions contextuelles, répétez le contexte dans chaque message

### Exemple de limitation contextuelle

❌ **Mauvais** :
```
Utilisateur: Traduis "hello" en français
IA: Bonjour
Utilisateur: Et en espagnol?
IA: [Confusion - ne sait pas de quoi on parle]
```

✅ **Bon** :
```
Utilisateur: Traduis "hello" en français
IA: Bonjour
Utilisateur: Traduis "hello" en espagnol
IA: Hola
```

## Améliorations futures possibles

1. **Historique de conversation persistant** : Garder le contexte entre les messages
2. **Multi-lignes** : Permettre Shift+Entrée pour saut de ligne
3. **Commandes slash** : `/clear`, `/help`, `/context` dans le chat
4. **Export** : Sauvegarder l'historique du chat
5. **Suggestions** : Auto-complétion de questions courantes
6. **Modes** : Mode "traduction", "explication", "suggestion"

## Conseils d'utilisation

### Pour de meilleures réponses

1. **Questions claires** : Posez des questions précises et complètes
2. **Contexte** : Donnez le contexte si nécessaire
3. **Exemples** : Incluez des exemples dans vos questions
4. **Format** : Utilisez des guillemets pour délimiter les textes

### Questions utiles

- `Pourquoi as-tu choisi ce mot plutôt que cet autre?`
- `Comment rendre cette phrase plus naturelle en [langue]?`
- `Quelle est la différence entre [expression A] et [expression B]?`
- `Est-ce que [mot] a plusieurs sens en [langue]?`
- `Suggère 3 alternatives pour traduire [phrase]`

### Éviter

- Questions sans contexte : `C'est quoi?`
- Questions trop vagues : `C'est bien?`
- Demandes d'action : `Traduis ça` (utilisez la baguette magique à la place)
