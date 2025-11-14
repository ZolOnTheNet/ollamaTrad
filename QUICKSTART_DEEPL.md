# Démarrage rapide - DeepL et comptage de caractères

## En 5 minutes ⏱️

### 1. Obtenir une clé API DeepL (gratuit)

1. Allez sur https://www.deepl.com/pro-api
2. Créez un compte gratuit
3. Copiez votre clé API (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:fx`)

### 2. Configurer OllamaFic

Éditez `config/settings.json` et ajoutez/modifiez :

```json
{
  "ai_providers": {
    "deepl": {
      "api_url": "https://api-free.deepl.com/v2/translate",
      "api_key": "COLLEZ_VOTRE_CLE_ICI",
      "is_pro": false,
      "timeout": 30
    }
  }
}
```

### 3. Tester la connexion

```bash
python test_deepl_integration.py
```

Vous devriez voir :
```
✅ Connexion réussie!
✅ Test DeepL réussi!
```

### 4. Utiliser dans l'application

**En ligne de commande:**
```bash
# Charger un fichier
python ollamaTrad.py --file mon_fichier.json

# Basculer sur DeepL
provider set deepl

# Traduire
translate -fr app/title
translate -en app/description

# Voir l'utilisation
/show
```

**Dans l'interface graphique:**
1. Lancez : `python ollamaTrad.py --gui`
2. **Fichier** → **Options** → **Providers** → **DeepL**
3. Collez votre clé API
4. **Test Connection**
5. Utilisez normalement ! 🎉

## Suivi en temps réel 📊

### Dans la barre de statut
Regardez en bas à droite de l'application :
```
📊 1,245 car.
```

Ce compteur s'actualise toutes les 2 secondes.

### À la fermeture
Un résumé s'affiche automatiquement :
```
📊 Résumé de l'utilisation durant cette session:
  • DEEPL: 1,245 caractères
  • OPENAI: 523 caractères
  Total: 1,768 caractères

💰 Estimation:
  • DeepL: 1,245 / 500,000 chars gratuits
  • OpenAI: ~$0.0392
```

## Cas d'usage typiques

### Traduire un fichier complet

```bash
# 1. Charger
python ollamaTrad.py --file data.json

# 2. Activer DeepL
provider set deepl

# 3. Traduire tout en français
translate -fr /

# 4. Voir combien de caractères utilisés
/show
```

### Alterner entre providers

```bash
# Utiliser DeepL pour les traductions courtes
provider set deepl
translate -fr app/title

# Utiliser GPT-4 pour du contenu complexe avec contexte
provider set openai
ia "Améliore cette traduction en tenant compte du contexte médiéval..."

# Revenir à DeepL
provider set deepl
```

### Optimiser les coûts

**Pour économiser:**
- Utilisez **Ollama** (gratuit, local) pour les brouillons
- Utilisez **DeepL** pour les traductions finales de qualité
- Réservez **GPT-4** pour les cas complexes nécessitant du contexte

**Limites gratuites:**
- DeepL Free : 500,000 caractères/mois
- Ollama : Illimité (mais utilise vos ressources)
- OpenAI/Anthropic : Selon votre compte

## Résolution de problèmes ⚠️

### "Clé API non configurée"
→ Vérifiez `config/settings.json`, section `"deepl"`

### "Quota exceeded" (403)
→ Vous avez dépassé 500,000 chars ce mois-ci
→ Attendez le mois prochain ou passez en Pro

### "Connexion refuse"
→ Compte gratuit doit utiliser `api-free.deepl.com`
→ Compte Pro doit utiliser `api.deepl.com`

### Le compteur ne s'affiche pas
→ Vérifiez que la GUI est bien lancée avec `--gui`
→ Le compteur apparaît en bas à droite

### Les traductions ne fonctionnent pas avec DeepL
→ DeepL n'est PAS un chatbot
→ N'utilisez PAS `ia "message"` avec DeepL
→ Utilisez uniquement `translate -XX chemin`

## Astuces 💡

1. **Vérifier l'utilisation régulièrement** : `/show` affiche votre quota DeepL
2. **Mode debug** : `debug_mode: true` dans settings.json pour voir les détails
3. **Compte Pro** : Pour usage commercial, passez en Pro (changez `is_pro: true`)
4. **HTML** : DeepL gère parfaitement le HTML, pas besoin de prompt spécial
5. **Batch** : Utilisez `translate -fr /` pour tout traduire d'un coup

## Prochaines étapes

- Lisez `DEEPL_INTEGRATION.md` pour la documentation complète
- Explorez les autres providers dans l'interface **Options**
- Consultez `CLAUDE.md` pour l'architecture complète

---

**Besoin d'aide ?**
- Documentation DeepL : https://www.deepl.com/docs-api
- Issues GitHub : [votre repo]/issues
