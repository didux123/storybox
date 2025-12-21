# StoryBox - Interface Web Streamlit

Interface de test pour le pipeline de génération d'histoires avec Celeste LLM.

## 🚀 Lancement Rapide

### Prérequis

```bash
# Installation des dépendances (avec uv)
uv pip install 'celeste-ai[text-generation]' streamlit

# Configuration
# Éditer .env et ajouter:
GOOGLE_API_KEY=votre-clé-api-google
LLM_MODEL_PATH=gemini-1.5-flash
```

### Démarrage

```bash
# Depuis la racine du projet
streamlit run webapp/streamlit_app.py

# Ou avec le script de lancement
./run_webapp.sh
```

L'application s'ouvrira automatiquement dans votre navigateur à `http://localhost:8501`.

## 📖 Utilisation

### 1. Configuration (Sidebar)

- **Nombre de chapitres**: 3-10 chapitres
- **Température**: Contrôle la créativité (0.1 = conservateur, 1.0 = très créatif)
- **Longueur des chapitres**: Court (100-150), Moyen (150-250), Long (250-400 mots)

### 2. Onglet "Prompt & Plan"

1. **Entrez votre prompt** dans le champ texte
   - Écrivez comme si vous parliez: "Raconte-moi l'histoire d'un petit robot..."
   - Le prompt simule ce que vous diriez oralement au StoryBox

2. **Cliquez sur "Générer le Plan"**
   - Génère un plan structuré avec N chapitres
   - Chaque chapitre a un titre et un résumé
   - Temps de génération affiché

3. **Consultez le plan généré**
   - Titres et résumés de chaque chapitre
   - Structure narrative complète

### 3. Onglet "Génération Chapitres"

1. **Sélectionnez un chapitre** dans la liste déroulante

2. **Consultez le contexte**
   - Résumé du chapitre actuel
   - Contexte des chapitres précédents (si applicable)

3. **Cliquez sur "Générer Chapitre X"**
   - Génère le texte complet du chapitre
   - Métriques affichées: mots, temps, vitesse

4. **Répétez** pour chaque chapitre

### 4. Onglet "Histoire Complète"

1. **Vue d'ensemble**
   - Barre de progression (X/N chapitres)
   - Tous les chapitres générés affichés

2. **Génération automatique**
   - Bouton "Générer tous les chapitres restants"
   - Génère séquentiellement tous les chapitres manquants

3. **Export**
   - Une fois l'histoire complète, téléchargez-la en Markdown
   - Bouton "Télécharger l'histoire"

## 🎨 Fonctionnalités

### Interface

- **Layout responsive**: Adapté aux différentes tailles d'écran
- **Tabs organisés**: Workflow logique en 3 étapes
- **Métriques en temps réel**: Temps, nombre de mots, vitesse
- **Cache intelligent**: Le LLM est initialisé une seule fois
- **Session state**: Conservation du plan et des chapitres générés

### Génération

- **Modèles supportés**:
  - Gemini 1.5 Flash (rapide, gratuit)
  - Gemini 1.5 Pro (meilleure qualité)
  - GPT-4o Mini (OpenAI)
  - Claude 3.5 Sonnet (Anthropic)

- **Contexte cumulatif**: Chaque chapitre prend en compte les précédents
- **Prompts structurés**: Templates optimisés pour les histoires jeunesse
- **Contrôle précis**: Température, longueur, nombre de chapitres

### Export

- **Format Markdown**: Compatible avec n'importe quel éditeur
- **Structure préservée**: Titres, chapitres, numérotation
- **Nom de fichier horodaté**: `histoire_timestamp.md`

## ⚙️ Configuration Avancée

### Modèles Alternatifs

Pour utiliser un autre modèle, modifiez `.env`:

#### OpenAI

```env
OPENAI_API_KEY=sk-...
LLM_MODEL_PATH=gpt-4o-mini
```

#### Anthropic

```env
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL_PATH=claude-3-5-sonnet-20241022
```

#### Gemini Pro

```env
GOOGLE_API_KEY=AIza...
LLM_MODEL_PATH=gemini-1.5-pro
```

### Personnalisation

L'application peut être personnalisée en modifiant `webapp/streamlit_app.py`:

- **Prompts**: Modifiez `app/llm/celeste_llm.py` (méthodes `_get_default_plan_prompt` et `_get_default_chapter_prompt`)
- **Styles CSS**: Section `st.markdown("""<style>...""")` dans `streamlit_app.py`
- **Paramètres par défaut**: Variables dans la sidebar

## 🐛 Dépannage

### Erreur "Config not found"

```bash
# Vérifiez que .env existe et contient GOOGLE_API_KEY
cat .env | grep GOOGLE_API_KEY
```

### Erreur "Model not found"

Vérifiez que le modèle est supporté:
- Gemini: `gemini-1.5-flash`, `gemini-1.5-pro`
- OpenAI: `gpt-4o`, `gpt-4o-mini`
- Anthropic: `claude-3-5-sonnet-20241022`

### Génération lente

- Utilisez `gemini-1.5-flash` au lieu de `gemini-1.5-pro`
- Réduisez la longueur des chapitres
- Réduisez le nombre de chapitres

### Erreur API Key

```bash
# Testez votre clé API avec le script de test
python3 test_celeste_local.py
```

## 📊 Métriques

L'application affiche plusieurs métriques utiles:

- **Temps de génération**: Latence pour générer un plan ou un chapitre
- **Nombre de mots**: Longueur du contenu généré
- **Vitesse**: Mots générés par seconde
- **Progression**: Pourcentage de chapitres générés

## 🔄 Workflow Complet

1. **Setup**: Configurer `.env` avec clé API
2. **Lancement**: `streamlit run webapp/streamlit_app.py`
3. **Configuration**: Ajuster paramètres dans sidebar
4. **Prompt**: Entrer le thème de l'histoire
5. **Plan**: Générer le plan (N chapitres)
6. **Chapitres**: Générer chaque chapitre ou tous automatiquement
7. **Export**: Télécharger l'histoire complète en Markdown

## 📝 Notes

- **Cache**: Le LLM est en cache, rechargez la page pour réinitialiser
- **Session State**: Les données persistent pendant la session
- **Async**: Utilise `asyncio.run()` pour les appels API
- **Sécurité**: Ne committez jamais `.env` avec vos clés API

## 🆘 Support

En cas de problème:

1. Vérifiez les logs dans le terminal Streamlit
2. Testez avec `python3 test_celeste_local.py`
3. Consultez la doc Celeste: https://docs.withceleste.ai/
4. Vérifiez votre quota API

---

**Dernière mise à jour**: 21 décembre 2024
**Version**: 0.1.0 (Alpha)
