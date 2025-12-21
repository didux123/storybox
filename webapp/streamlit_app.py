#!/usr/bin/env python3
"""
StoryBox - Interface Streamlit pour Test de Génération d'Histoires

Interface de test pour le pipeline de génération d'histoires avec Celeste LLM.
Permet de tester la génération de plans et de chapitres depuis le Mac.

Usage:
    streamlit run webapp/streamlit_app.py

Author: StoryBox IA Team
Date: 2024-12-21
"""

import streamlit as st
import asyncio
import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.llm.celeste_llm import CelesteLLM, StoryPlan
from app.utils.config import get_config


def run_async(coro):
    """
    Helper to run async functions in Streamlit

    Handles event loop management to avoid "Event loop is closed" errors
    """
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            # Create new loop if closed
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    except RuntimeError:
        # Fallback: create new loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            # Don't close the loop, Streamlit might reuse it
            pass


# Configuration de la page
st.set_page_config(
    page_title="StoryBox - Générateur d'Histoires",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .chapter-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .metric-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_llm():
    """Initialiser et cacher Celeste LLM"""
    try:
        config = get_config()
        llm = CelesteLLM(config.llm)
        return llm
    except Exception as e:
        st.error(f"❌ Erreur initialisation LLM: {e}")
        st.info("""
        **Vérifiez votre configuration:**
        1. GOOGLE_API_KEY définie dans .env
        2. LLM_MODEL_PATH=gemini-1.5-flash (ou gemini-1.5-pro)
        3. Celeste installé: `uv pip install 'celeste-ai[text-generation]'`
        """)
        return None


def main():
    """Application principale"""

    # Header
    st.markdown('<div class="main-header">📖 StoryBox - Générateur d\'Histoires</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Testez la génération d\'histoires avec Celeste LLM</div>', unsafe_allow_html=True)

    # Sidebar - Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Obtenir la config
        try:
            config = get_config()
            model_name = config.llm.model_path
            st.success(f"✓ Modèle: {model_name}")
        except Exception as e:
            st.error(f"❌ Config error: {e}")
            return

        st.divider()

        # Paramètres de génération
        st.subheader("Paramètres de génération")

        num_chapters = st.slider(
            "Nombre de chapitres",
            min_value=3,
            max_value=10,
            value=5,
            help="Nombre de chapitres pour le plan"
        )

        temperature = st.slider(
            "Température",
            min_value=0.1,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Créativité de la génération (plus élevé = plus créatif)"
        )

        chapter_length = st.select_slider(
            "Longueur des chapitres",
            options=["Court (100-150 mots)", "Moyen (150-250 mots)", "Long (250-400 mots)"],
            value="Moyen (150-250 mots)",
            help="Longueur approximative de chaque chapitre"
        )

        # Mapper la longueur
        length_map = {
            "Court (100-150 mots)": (100, 150),
            "Moyen (150-250 mots)": (150, 250),
            "Long (250-400 mots)": (250, 400)
        }
        min_words, max_words = length_map[chapter_length]

        st.divider()

        # Info
        with st.expander("ℹ️ À propos"):
            st.markdown("""
            **StoryBox** est un générateur d'histoires pour enfants.

            Cette interface permet de tester le pipeline de génération:
            1. Entrez un prompt (comme si vous parliez)
            2. Générez un plan d'histoire
            3. Générez les chapitres un par un

            **Modèles supportés:**
            - Gemini 1.5 Flash (rapide, gratuit)
            - Gemini 1.5 Pro (meilleur qualité)
            - GPT-4o Mini (OpenAI)
            - Claude 3.5 Sonnet (Anthropic)
            """)

    # Main content - Tabs
    tab1, tab2, tab3 = st.tabs(["🎤 Prompt & Plan", "✍️ Génération Chapitres", "📚 Histoire Complète"])

    # Tab 1: Prompt & Plan Generation
    with tab1:
        st.header("Étape 1: Entrez votre prompt")

        # Zone de saisie du prompt
        user_prompt = st.text_area(
            "Que voulez-vous raconter ? (parlez comme si vous parliez à l'appareil)",
            placeholder="Exemple: Raconte-moi l'histoire d'un petit robot qui découvre les émotions",
            height=100,
            help="Écrivez ce que vous diriez oralement à StoryBox"
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            generate_plan_btn = st.button("📋 Générer le Plan", type="primary", disabled=not user_prompt)

        if generate_plan_btn and user_prompt:
            llm = get_llm()
            if llm:
                with st.spinner(f"Génération du plan ({num_chapters} chapitres)..."):
                    start_time = time.time()

                    try:
                        # Générer le plan
                        plan = run_async(llm.generate_story_plan(user_prompt, num_chapters=num_chapters))

                        generation_time = time.time() - start_time

                        if plan:
                            # Stocker dans session state
                            st.session_state['story_plan'] = plan
                            st.session_state['user_prompt'] = user_prompt
                            st.session_state['chapters_generated'] = {}

                            # Afficher succès
                            st.success(f"✅ Plan généré en {generation_time:.1f}s")

                            # Métriques
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Chapitres", len(plan.chapters))
                            with col2:
                                st.metric("Temps", f"{generation_time:.1f}s")
                            with col3:
                                st.metric("Thème", user_prompt[:20] + "...")

                            # Afficher le plan
                            st.subheader("📖 Plan de l'histoire")
                            for chapter in plan.chapters:
                                with st.container():
                                    st.markdown(f"### Chapitre {chapter['number']}: {chapter['title']}")
                                    st.markdown(f"_{chapter['summary']}_")
                                    st.divider()
                        else:
                            st.error("❌ Échec de la génération du plan")

                    except Exception as e:
                        st.error(f"❌ Erreur: {e}")
                        st.exception(e)

        # Afficher le plan existant si disponible
        if 'story_plan' in st.session_state:
            st.divider()
            st.subheader("📖 Plan actuel")
            plan = st.session_state['story_plan']

            for chapter in plan.chapters:
                with st.expander(f"Chapitre {chapter['number']}: {chapter['title']}"):
                    st.markdown(f"**Résumé:** {chapter['summary']}")

    # Tab 2: Chapter Generation
    with tab2:
        st.header("Étape 2: Générer les chapitres")

        if 'story_plan' not in st.session_state:
            st.info("👈 Générez d'abord un plan dans l'onglet 'Prompt & Plan'")
        else:
            plan = st.session_state['story_plan']

            # Sélection du chapitre
            chapter_num = st.selectbox(
                "Choisissez le chapitre à générer",
                options=range(1, len(plan.chapters) + 1),
                format_func=lambda x: f"Chapitre {x}: {plan.chapters[x-1]['title']}"
            )

            chapter_info = plan.chapters[chapter_num - 1]

            # Afficher les infos du chapitre
            st.info(f"**Résumé:** {chapter_info['summary']}")

            # Contexte cumulatif
            if chapter_num > 1:
                with st.expander("📚 Contexte des chapitres précédents"):
                    for i in range(chapter_num - 1):
                        prev_chapter = plan.chapters[i]
                        st.markdown(f"**Ch. {prev_chapter['number']}: {prev_chapter['title']}**")
                        st.markdown(f"_{prev_chapter['summary']}_")
                        if i + 1 in st.session_state.get('chapters_generated', {}):
                            st.markdown("✅ _Généré_")
                        st.divider()

            # Bouton de génération
            col1, col2 = st.columns([1, 4])
            with col1:
                generate_chapter_btn = st.button(f"✍️ Générer Chapitre {chapter_num}", type="primary")

            if generate_chapter_btn:
                llm = get_llm()
                if llm:
                    with st.spinner(f"Génération du chapitre {chapter_num}..."):
                        start_time = time.time()

                        try:
                            # Construire contexte cumulatif
                            cumulative_context = ""
                            if chapter_num > 1:
                                summaries = []
                                for i in range(chapter_num - 1):
                                    prev = plan.chapters[i]
                                    summaries.append(f"Chapitre {prev['number']}: {prev['summary']}")
                                cumulative_context = " ".join(summaries)

                            # Générer le chapitre
                            chapter_text = run_async(llm.generate_chapter(
                                plan,
                                chapter_num=chapter_num,
                                cumulative_context=cumulative_context,
                                min_words=min_words,
                                max_words=max_words
                            ))

                            generation_time = time.time() - start_time

                            if chapter_text:
                                # Stocker
                                if 'chapters_generated' not in st.session_state:
                                    st.session_state['chapters_generated'] = {}

                                st.session_state['chapters_generated'][chapter_num] = {
                                    'text': chapter_text,
                                    'time': generation_time
                                }

                                word_count = len(chapter_text.split())

                                # Métriques
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Mots", word_count)
                                with col2:
                                    st.metric("Temps", f"{generation_time:.1f}s")
                                with col3:
                                    st.metric("Mots/sec", f"{word_count/generation_time:.0f}")

                                # Afficher le chapitre
                                st.success(f"✅ Chapitre {chapter_num} généré")
                                st.markdown(f"### Chapitre {chapter_num}: {chapter_info['title']}")
                                st.markdown(chapter_text)
                            else:
                                st.error("❌ Échec de la génération")

                        except Exception as e:
                            st.error(f"❌ Erreur: {e}")
                            st.exception(e)

            # Afficher les chapitres déjà générés
            if st.session_state.get('chapters_generated'):
                st.divider()
                st.subheader("📚 Chapitres générés")

                for ch_num in sorted(st.session_state['chapters_generated'].keys()):
                    ch_data = st.session_state['chapters_generated'][ch_num]
                    ch_info = plan.chapters[ch_num - 1]

                    with st.expander(f"✅ Chapitre {ch_num}: {ch_info['title']}"):
                        word_count = len(ch_data['text'].split())
                        st.caption(f"⏱️ Généré en {ch_data['time']:.1f}s | 📝 {word_count} mots")
                        st.markdown(ch_data['text'])

    # Tab 3: Complete Story
    with tab3:
        st.header("Histoire Complète")

        if 'story_plan' not in st.session_state:
            st.info("👈 Générez d'abord un plan dans l'onglet 'Prompt & Plan'")
        else:
            plan = st.session_state['story_plan']
            chapters_gen = st.session_state.get('chapters_generated', {})

            total_chapters = len(plan.chapters)
            generated_count = len(chapters_gen)

            # Progression
            progress = generated_count / total_chapters
            st.progress(progress, text=f"Progression: {generated_count}/{total_chapters} chapitres générés")

            st.divider()

            # Bouton génération automatique
            if generated_count < total_chapters:
                if st.button("🚀 Générer tous les chapitres restants", type="primary"):
                    llm = get_llm()
                    if llm:
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        for ch_num in range(1, total_chapters + 1):
                            if ch_num not in chapters_gen:
                                status_text.text(f"Génération du chapitre {ch_num}/{total_chapters}...")

                                try:
                                    # Construire contexte
                                    cumulative_context = ""
                                    if ch_num > 1:
                                        summaries = []
                                        for i in range(ch_num - 1):
                                            prev = plan.chapters[i]
                                            summaries.append(f"Chapitre {prev['number']}: {prev['summary']}")
                                        cumulative_context = " ".join(summaries)

                                    # Générer
                                    start_time = time.time()
                                    chapter_text = run_async(llm.generate_chapter(
                                        plan,
                                        chapter_num=ch_num,
                                        cumulative_context=cumulative_context,
                                        min_words=min_words,
                                        max_words=max_words
                                    ))
                                    generation_time = time.time() - start_time

                                    if chapter_text:
                                        if 'chapters_generated' not in st.session_state:
                                            st.session_state['chapters_generated'] = {}

                                        st.session_state['chapters_generated'][ch_num] = {
                                            'text': chapter_text,
                                            'time': generation_time
                                        }

                                    # Update progress
                                    progress_bar.progress(ch_num / total_chapters)

                                except Exception as e:
                                    st.error(f"❌ Erreur chapitre {ch_num}: {e}")
                                    break

                        status_text.text("✅ Génération terminée!")
                        progress_bar.progress(1.0)
                        st.rerun()

            st.divider()

            # Afficher l'histoire complète
            if generated_count > 0:
                st.subheader(f"📖 {plan.theme}")

                for ch_num in range(1, total_chapters + 1):
                    ch_info = plan.chapters[ch_num - 1]

                    st.markdown(f"### Chapitre {ch_num}: {ch_info['title']}")

                    if ch_num in chapters_gen:
                        ch_data = chapters_gen[ch_num]
                        st.markdown(ch_data['text'])
                    else:
                        st.info(f"_Chapitre non généré. Résumé: {ch_info['summary']}_")

                    st.divider()

                # Export option
                if generated_count == total_chapters:
                    st.success("✅ Histoire complète générée!")

                    # Créer texte complet
                    full_story = f"# {plan.theme}\n\n"
                    for ch_num in range(1, total_chapters + 1):
                        ch_info = plan.chapters[ch_num - 1]
                        ch_data = chapters_gen[ch_num]
                        full_story += f"## Chapitre {ch_num}: {ch_info['title']}\n\n"
                        full_story += ch_data['text'] + "\n\n"

                    # Bouton download
                    st.download_button(
                        label="📥 Télécharger l'histoire (Markdown)",
                        data=full_story,
                        file_name=f"histoire_{int(time.time())}.md",
                        mime="text/markdown"
                    )


if __name__ == "__main__":
    main()
