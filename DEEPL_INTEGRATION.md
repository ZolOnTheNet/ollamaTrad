# Intégration DeepL dans OllamaFic

## Vue d'ensemble

OllamaFic supporte désormais **DeepL** comme provider de traduction professionnel. DeepL est reconnu pour la qualité supérieure de ses traductions, notamment pour les langues européennes.

## Différences avec les autres providers

DeepL est différent des autres providers (OpenAI, Mistral, Anthropic, Ollama) car :
- ✅ **Service de traduction pur** : Pas de système de chat, uniquement de la traduction
- ✅ **Pas de prompt nécessaire** : On envoie directement le texte avec les codes langues source/cible
- ✅ **Gestion native du HTML** : DeepL préserve automatiquement les balises HTML
- ✅ **Comptage des caractères** : Système de facturation basé sur le nombre de caractères envoyés

## Configuration

### 1. Obtenir une clé API DeepL

**Compte gratuit (Free API):**
- Rendez-vous sur https://www.deepl.com/pro-api
- Inscrivez-vous pour un compte gratuit
- Limite : 500,000 caractères/mois
- URL API : `https://api-free.deepl.com/v2/translate`

**Compte Pro:**
- Souscription payante
- Facturation selon volume utilisé
- URL API : `https://api.deepl.com/v2/translate`

### 2. Configurer dans settings.json

Éditez `config/settings.json` :

```json
{
  "ai_providers": {
    "deepl": {
      "api_url": "https://api-free.deepl.com/v2/translate",
      "api_key": "VOTRE_CLE_API_ICI",
      "is_pro": false,
      "timeout": 30,
      "available_languages": ["fr", "en", "es", "de", "it", "pt", "nl", "pl", "ru", "ja", "zh"]
    }
  }
}
```

**Pour un compte Pro**, changez :
```json
{
  "api_url": "https://api.deepl.com/v2/translate",
  "is_pro": true
}
```

## Utilisation

### En ligne de commande

```bash
# Définir DeepL comme provider actif
provider set deepl

# Vérifier la connexion et voir l'utilisation
/show

# Traduire (via le système de traduction standard)
translate -fr app/title
```

**Note importante** : Comme DeepL n'est pas un chatbot, la commande `ia "message"` ne fonctionnera pas. Utilisez uniquement les commandes de traduction.

### Dans l'interface graphique

1. **Options** → **Providers** → **DeepL**
2. Entrez votre clé API
3. Sélectionnez le type de compte (Free/Pro)
4. Testez la connexion
5. Utilisez les boutons de traduction normalement

L'application utilisera automatiquement DeepL si c'est le provider actif.

## Suivi de l'utilisation

### Barre de statut

La barre de statut en bas de l'application affiche en temps réel :
```
📊 15,420 car.
```

Ce compteur inclut tous les caractères envoyés aux APIs payantes durant la session.

### Au démarrage avec /show

```bash
/show
```

Affiche :
```
🤖 Provider: DeepL
📋 Service: Traduction professionnelle
🔗 Statut: ✅ Connecté
💳 Type de compte: Free
📊 Caractères envoyés: 15,420
🔑 API Key: **********abc1
🌐 URL API: https://api-free.deepl.com/v2/translate
💰 Limite gratuite: 500,000 caractères/mois
📈 Utilisation API: 125,420 / 500,000 (25.1%)
```

### À la fermeture de l'application

Une boîte de dialogue affiche le résumé complet :

```
📊 Résumé de l'utilisation durant cette session:

  • DEEPL: 15,420 caractères
  • OPENAI: 5,230 caractères

  Total: 20,650 caractères

💰 Estimation de coût approximative:
  • OpenAI: ~$0.0392
  • DeepL: 15,420 / 500,000 chars gratuits

ℹ️ Ces estimations sont approximatives.
```

## Langues supportées

DeepL supporte actuellement les langues suivantes :

| Code | Langue | Remarques |
|------|--------|-----------|
| FR | Français | |
| EN | Anglais | EN-US ou EN-GB |
| ES | Espagnol | |
| DE | Allemand | |
| IT | Italien | |
| PT | Portugais | PT-BR ou PT-PT |
| NL | Néerlandais | |
| PL | Polonais | |
| RU | Russe | |
| JA | Japonais | |
| ZH | Chinois | |
| ... | Autres | Voir documentation DeepL |

**Note** : OllamaFic convertit automatiquement les codes langue standards (ex: "en") en codes DeepL (ex: "EN-US").

## Gestion du HTML

DeepL gère nativement les balises HTML :

```python
# L'application envoie automatiquement
params = {
    "text": "<p>Hello <strong>world</strong></p>",
    "target_lang": "FR",
    "preserve_formatting": "1",
    "tag_handling": "html"
}

# DeepL retourne
"<p>Bonjour <strong>monde</strong></p>"
```

Les balises sont préservées sans instruction particulière dans le prompt.

## Limites et quotas

### Compte gratuit (Free API)
- ✅ 500,000 caractères/mois
- ⚠️ Usage non-commercial uniquement
- ⚠️ Pas de garantie SLA

### Compte Pro
- ✅ Facturation selon volume
- ✅ Usage commercial
- ✅ SLA garanti
- 💰 Tarifs : voir https://www.deepl.com/pro-api

## Comptage des caractères

**Important** : DeepL compte les caractères avant traduction, y compris :
- Tous les caractères du texte source
- Les espaces et ponctuation
- Les balises HTML (mais optimisé par DeepL)

**Exemple de comptage dans OllamaFic** :
```python
text = "Hello world!"  # 12 caractères
# Le compteur s'incrémente de 12
```

## Dépannage

### Erreur "API Key non configurée"
→ Vérifiez que la clé API est bien dans `config/settings.json`

### Erreur 403 "Quota exceeded"
→ Vous avez dépassé la limite mensuelle gratuite
→ Solution : Attendre le mois suivant ou passer en Pro

### Erreur 456 "Quota exceeded"
→ Pour compte Pro : solde insuffisant
→ Solution : Recharger votre compte

### Connexion refuse
→ Vérifiez l'URL API (Free vs Pro)
→ Compte Free doit utiliser `api-free.deepl.com`
→ Compte Pro doit utiliser `api.deepl.com`

### La traduction ne fonctionne pas
→ DeepL n'est PAS un chatbot
→ Ne peut pas répondre à `ia "message"`
→ Utilisez uniquement les commandes de traduction

## Avantages de DeepL

1. **Qualité supérieure** : Traductions plus naturelles et contextuelles
2. **Rapidité** : Plus rapide que les LLMs généralistes
3. **Coût** : Souvent moins cher que GPT-4 pour la traduction
4. **Simplicité** : Pas besoin de prompt engineering
5. **HTML natif** : Gestion parfaite des balises

## Comparaison des coûts

Pour 1 million de caractères :

| Provider | Coût approximatif | Notes |
|----------|-------------------|-------|
| DeepL Free | Gratuit | Limite 500K/mois |
| DeepL Pro | ~€20 | Facturation variable |
| OpenAI GPT-4 | ~$30 | Via tokens |
| Anthropic Claude | ~$15 | Via tokens |
| Mistral | ~$2 | Via tokens |
| Ollama | Gratuit | Local, pas de limite |

## Exemple d'utilisation complète

```bash
# 1. Charger un fichier
python ollamaTrad.py --file mon_fichier.json

# 2. Définir DeepL
provider set deepl

# 3. Vérifier la connexion
/show

# 4. Traduire un champ
translate -fr app/title

# 5. Traduire tout un sous-arbre
translate -fr app

# 6. Vérifier l'utilisation
/show

# Résultat affiché :
# 📊 Caractères envoyés: 2,450
# 📈 Utilisation API: 127,870 / 500,000 (25.6%)
```

## Support et ressources

- Documentation DeepL API : https://www.deepl.com/docs-api
- Tableau de bord DeepL : https://www.deepl.com/pro-account
- Support DeepL : support@deepl.com
- Issues GitHub OllamaFic : https://github.com/votre-repo/issues

---

**Note** : Cette intégration respecte les termes d'utilisation de DeepL. Assurez-vous d'avoir un compte et une clé API valides avant utilisation.
