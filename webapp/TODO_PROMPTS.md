# TODO: Éditeur de Prompts dans Streamlit

## ✅ Déjà Fait

1. **Fichier de configuration** `configs/prompts.json`
   - System prompts pour plan et chapitres
   - Templates de prompts utilisateur
   - Format JSON éditable

2. **Chargement dans `celeste_llm.py`**
   - Fonction `load_prompts_config()`
   - Chargement automatique dans `__init__`
   - Méthodes `_get_plan_prompt()` et `_get_chapter_prompt()`
   - Fallback sur defaults si JSON manquant

3. **Helper utilitaire** `webapp/utils/prompt_editor.py`
   - `load_prompts()` → Charger le JSON
   - `save_prompts()` → Sauvegarder le JSON
   - `get_filled_prompt()` → Remplir les variables

## 📝 À Implémenter dans Streamlit

### Nouvel onglet "⚙️ Prompts"

Ajouter dans `webapp/streamlit_app.py`:

```python
from webapp.utils.prompt_editor import load_prompts, save_prompts, get_filled_prompt

# Dans les tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🎤 Prompt & Plan",
    "✍️ Génération Chapitres",
    "📚 Histoire Complète",
    "⚙️ Prompts"  # NOUVEAU
])

# Tab 4: Prompt Editor
with tab4:
    st.header("Éditeur de Prompts")

    # Charger les prompts
    try:
        prompts = load_prompts()
    except Exception as e:
        st.error(f"Erreur chargement: {e}")
        st.stop()

    # Section Plan
    st.subheader("📖 Génération du Plan")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**System Prompt**")
        plan_system = st.text_area(
            "System prompt pour le plan",
            value=prompts['plan']['system_prompt'],
            height=150,
            key="plan_system"
        )

    with col2:
        st.markdown("**User Template**")
        plan_template = st.text_area(
            "Template pour le plan",
            value=prompts['plan']['user_template'],
            height=150,
            key="plan_template"
        )

    # Preview avec variables
    st.markdown("**Preview avec variables**")
    preview_theme = st.text_input("Thème de test", "un robot qui découvre les émotions")
    preview_chapters = st.number_input("Nombre de chapitres", 3, 10, 5)

    filled_plan = get_filled_prompt(plan_template, {
        'theme': preview_theme,
        'num_chapters': preview_chapters
    })

    with st.expander("Voir le prompt final"):
        st.code(filled_plan, language="markdown")

    st.divider()

    # Section Chapter
    st.subheader("✍️ Génération des Chapitres")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**System Prompt**")
        chapter_system = st.text_area(
            "System prompt pour les chapitres",
            value=prompts['chapter']['system_prompt'],
            height=150,
            key="chapter_system"
        )

    with col2:
        st.markdown("**User Template**")
        chapter_template = st.text_area(
            "Template pour les chapitres",
            value=prompts['chapter']['user_template'],
            height=150,
            key="chapter_template"
        )

    st.divider()

    # Bouton sauvegarder
    col1, col2, col3 = st.columns([1, 1, 3])

    with col1:
        if st.button("💾 Sauvegarder", type="primary"):
            # Construire le nouveau config
            new_prompts = {
                "plan": {
                    "system_prompt": plan_system,
                    "user_template": plan_template
                },
                "chapter": {
                    "system_prompt": chapter_system,
                    "user_template": chapter_template
                }
            }

            # Sauvegarder
            if save_prompts(new_prompts):
                st.success("✅ Prompts sauvegardés!")
                st.info("ℹ️ Rechargez la page pour que les changements prennent effet")
            else:
                st.error("❌ Erreur lors de la sauvegarde")

    with col2:
        if st.button("🔄 Recharger"):
            st.cache_resource.clear()
            st.rerun()
```

### Variables disponibles

**Plan:**
- `{theme}` → Thème de l'histoire
- `{num_chapters}` → Nombre de chapitres

**Chapitre:**
- `{chapter_num}` → Numéro du chapitre
- `{chapter_title}` → Titre du chapitre
- `{cumulative_context}` → Contexte des chapitres précédents
- `{story_plan}` → Plan complet formaté
- `{min_words}` → Minimum de mots
- `{max_words}` → Maximum de mots

## 🚀 Améliorations Futures

### 1. Structured Output avec Pydantic

Celeste supporte le structured output pour forcer un format JSON:

```python
from pydantic import BaseModel
from typing import List

class Chapter(BaseModel):
    number: int
    title: str
    summary: str

class StoryPlanResponse(BaseModel):
    chapters: List[Chapter]

# Dans generate_story_plan()
response = await client.generate(
    prompt=prompt,
    response_format=StoryPlanResponse  # Force JSON structuré
)

# Retour garanti au format StoryPlanResponse
plan_data = response.content
```

**Avantages:**
- Pas besoin de parsing JSON manuel
- Format garanti (pas d'erreur de parsing)
- Type-safe
- Validation automatique

### 2. Templates de prompts multiples

Ajouter dans `configs/prompts.json`:

```json
{
  "plan": {
    "templates": {
      "default": "...",
      "aventure": "Crée un plan d'aventure...",
      "educatif": "Crée un plan éducatif..."
    }
  }
}
```

Sélectionner dans Streamlit avec un dropdown.

### 3. Historique des prompts

Sauvegarder les versions précédentes des prompts pour pouvoir revenir en arrière.

### 4. Métriques de qualité

Afficher des métriques sur les générations:
- Temps moyen
- Taux de succès du parsing JSON
- Longueur moyenne des chapitres

---

**Note:** Le système de base est fonctionnel. L'onglet Prompts est optionnel mais très utile pour itérer sur les prompts.
