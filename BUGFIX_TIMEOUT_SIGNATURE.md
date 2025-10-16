# Correction: Signature de la Méthode chat() avec Timeout

## 📅 Date: 2025-10-16

## 🐛 Problème

Erreur lors de l'appel avec timeout dynamique:
```
Erreur: AIClient.chat() got an unexpected keyword argument 'timeout'
```

## 🔍 Cause

Le paramètre `timeout` avait été ajouté uniquement à `OllamaProvider.chat()`, mais pas aux autres méthodes:
- `AIProvider.chat()` (méthode abstraite)
- `AIClient.chat()` (wrapper)
- `OpenAIProvider.chat()`
- `MistralProvider.chat()`
- `AnthropicProvider.chat()`

## ✅ Solution

Ajout du paramètre `timeout: Optional[int] = None` à **toutes** les signatures de méthode `chat()`.

### Modifications (`core/ai_client.py`)

**1. Méthode abstraite (ligne 24)**
```python
@abstractmethod
async def chat(self, message: str, system_prompt: Optional[str] = None, timeout: Optional[int] = None) -> str:
    """Envoie un message de chat et retourne la réponse"""
    pass
```

**2. OllamaProvider (ligne 244)** - Déjà fait
```python
async def chat(self, message: str, system_prompt: Optional[str] = None, timeout: Optional[int] = None) -> str:
    # Utilise le timeout
    effective_timeout = timeout if timeout is not None else self.timeout
    # ...
```

**3. OpenAIProvider (ligne 421)**
```python
async def chat(self, message: str, system_prompt: Optional[str] = None, timeout: Optional[int] = None) -> str:
    """Chat avec OpenAI"""
    # Note: timeout pas utilisé pour OpenAI (pour l'instant)
```

**4. MistralProvider (ligne 540)**
```python
async def chat(self, message: str, system_prompt: Optional[str] = None, timeout: Optional[int] = None) -> str:
    """Chat avec Mistral"""
    # Note: timeout pas utilisé pour Mistral (pour l'instant)
```

**5. AnthropicProvider (ligne 624)**
```python
async def chat(self, message: str, system_prompt: Optional[str] = None, timeout: Optional[int] = None) -> str:
    """Chat avec Anthropic"""
    # Note: timeout pas utilisé pour Anthropic (pour l'instant)
```

**6. AIClient.chat() (ligne 761)**
```python
async def chat(self, message: str, system_prompt: Optional[str] = None, timeout: Optional[int] = None) -> str:
    """Envoie un message de chat au provider actuel"""
    if not self.current_provider:
        raise Exception("Aucun provider AI configuré")

    return await self.current_provider.chat(message, system_prompt, timeout)
```

## 📊 Résultat

Toutes les signatures sont maintenant cohérentes:
- ✅ Méthode abstraite accepte `timeout`
- ✅ Tous les providers acceptent `timeout`
- ✅ AIClient propage `timeout` au provider actuel
- ✅ Ollama utilise le timeout dynamique
- ✅ Autres providers ignorent le timeout (pour l'instant)

## 🔄 Compatibilité

Le paramètre étant optionnel (`Optional[int] = None`), tous les appels existants continuent de fonctionner:

```python
# Appel sans timeout (utilise timeout par défaut)
result = await client.chat("Hello")  ✅

# Appel avec timeout dynamique
result = await client.chat("Hello", timeout=500)  ✅
```

## 💡 Améliorations Futures

Les autres providers (OpenAI, Mistral, Anthropic) pourraient aussi utiliser le timeout dynamique en ajoutant:

```python
# OpenAIProvider
effective_timeout = timeout if timeout is not None else 120
async with session.post(..., timeout=aiohttp.ClientTimeout(total=effective_timeout))

# MistralProvider
effective_timeout = timeout if timeout is not None else 120
async with session.post(..., timeout=aiohttp.ClientTimeout(total=effective_timeout))

# AnthropicProvider
effective_timeout = timeout if timeout is not None else 120
async with session.post(..., timeout=aiohttp.ClientTimeout(total=effective_timeout))
```

---

**Auteur**: Claude (Anthropic)
**Date**: 2025-10-16
**Version**: OllamaFic v2.0 - Correction Signature Timeout
