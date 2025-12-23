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
from app.tts.celeste_tts import CelesteTTS
from app.utils.config import get_config
from webapp.utils.prompt_editor import load_prompts, save_prompts


def load_llm_config():
    """Load LLM configuration including pricing"""
    try:
        import json
        config_path = Path(__file__).parent.parent / "configs" / "llm_config.json"
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.warning(f"Could not load LLM config: {e}")
        return {}


def estimate_tokens(text: str) -> int:
    """Estimate token count from text (rough: 1 token ≈ 4 chars)"""
    return len(text) // 4


def calculate_cost(input_tokens: int, output_tokens: int, model_id: str) -> float:
    """
    Calculate estimated cost in USD

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model_id: Model identifier

    Returns:
        Estimated cost in USD
    """
    llm_config = load_llm_config()

    if 'pricing' not in llm_config:
        return 0.0

    pricing = llm_config['pricing'].get(model_id)
    if not pricing:
        return 0.0

    input_cost = (input_tokens / 1_000_000) * pricing.get('input_per_1m', 0)
    output_cost = (output_tokens / 1_000_000) * pricing.get('output_per_1m', 0)

    return input_cost + output_cost


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


@st.cache_resource
def get_tts():
    """Initialiser et cacher Celeste TTS"""
    try:
        config = get_config()
        tts = CelesteTTS(config)
        return tts
    except Exception as e:
        st.error(f"❌ Erreur initialisation TTS: {e}")
        st.info("""
        **Vérifiez votre configuration:**
        1. Celeste 0.3.5+ installé avec support Gradium
        2. GRADIUM_API_KEY dans .env (si nécessaire)
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

        st.divider()

        # Configuration TTS
        st.subheader("🔊 Paramètres TTS (Narration)")

        enable_tts = st.checkbox(
            "Activer la narration audio",
            value=False,
            help="Permet de générer et écouter l'audio des chapitres"
        )

        voice_id = None
        tts_speed = 1.0

        if enable_tts:
            voice_id = st.text_input(
                "Voice ID Gradium",
                value="",
                placeholder="Entrez votre voice ID Gradium",
                help="ID de la voix Gradium à utiliser pour la narration (optionnel, utilise la voix par défaut si vide)"
            )

            tts_speed = st.slider(
                "Vitesse de lecture",
                min_value=0.5,
                max_value=2.0,
                value=1.0,
                step=0.1,
                help="Vitesse de narration (1.0 = normale)"
            )

        # Mapper la longueur
        length_map = {
            "Court (100-150 mots)": (100, 150),
            "Moyen (150-250 mots)": (150, 250),
            "Long (250-400 mots)": (250, 400)
        }
        min_words, max_words = length_map[chapter_length]

        st.divider()

        # Afficher les erreurs si présentes
        if 'errors' in st.session_state and st.session_state['errors']:
            st.error(f"⚠️ {len(st.session_state['errors'])} erreur(s)")
            with st.expander("Voir les erreurs"):
                for i, error in enumerate(st.session_state['errors'][-5:], 1):  # Dernières 5 erreurs
                    st.text(f"{i}. {error['type']}: {error['message']}")
                    st.caption(f"Heure: {error.get('time', 'N/A')}")
                if st.button("Effacer les erreurs"):
                    st.session_state['errors'] = []
                    st.rerun()

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
    tab1, tab2, tab3, tab4 = st.tabs(["🎤 Prompt & Plan", "✍️ Génération Chapitres", "📚 Histoire Complète", "⚙️ Prompts"])

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
                        plan = run_async(llm.generate_story_plan(user_prompt, num_chapters=num_chapters, temperature=temperature))

                        generation_time = time.time() - start_time

                        if plan:
                            # Stocker dans session state
                            st.session_state['story_plan'] = plan
                            st.session_state['user_prompt'] = user_prompt
                            st.session_state['chapters_generated'] = {}

                            # Calculer métriques
                            # Estimation des tokens (input = prompt, output = plan JSON)
                            plan_json = str(plan.to_dict())
                            input_tokens = estimate_tokens(user_prompt)
                            output_tokens = estimate_tokens(plan_json)
                            total_tokens = input_tokens + output_tokens

                            # Calculer coût
                            cost = calculate_cost(input_tokens, output_tokens, config.llm.model_path)

                            # Afficher succès
                            st.success(f"✅ Plan généré en {generation_time:.1f}s")

                            # Métriques détaillées
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Chapitres", len(plan.chapters))
                            with col2:
                                st.metric("Temps", f"{generation_time:.1f}s")
                            with col3:
                                st.metric("Tokens", f"~{total_tokens:,}", delta=f"in:{input_tokens} out:{output_tokens}")
                            with col4:
                                if cost > 0:
                                    st.metric("Coût", f"${cost:.6f}", help="Estimation basée sur les tarifs du modèle")
                                else:
                                    st.metric("Coût", "N/A", help="Tarif non disponible pour ce modèle")

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
                        # Stocker l'erreur
                        if 'errors' not in st.session_state:
                            st.session_state['errors'] = []
                        st.session_state['errors'].append({
                            'type': 'Plan Generation Error',
                            'message': str(e),
                            'time': time.strftime('%H:%M:%S')
                        })

                        st.error(f"❌ Erreur lors de la génération du plan: {e}")
                        with st.expander("Détails de l'erreur"):
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
                                max_words=max_words,
                                temperature=temperature
                            ))

                            generation_time = time.time() - start_time

                            if chapter_text:
                                # Calculer métriques
                                word_count = len(chapter_text.split())

                                # Estimation des tokens
                                # Input = prompt complet (template + context + plan)
                                input_estimate = cumulative_context + str(plan.to_dict()) + chapter_info['title']
                                input_tokens = estimate_tokens(input_estimate)
                                output_tokens = estimate_tokens(chapter_text)
                                total_tokens = input_tokens + output_tokens

                                # Calculer coût
                                cost = calculate_cost(input_tokens, output_tokens, config.llm.model_path)

                                # Stocker avec métriques
                                if 'chapters_generated' not in st.session_state:
                                    st.session_state['chapters_generated'] = {}

                                st.session_state['chapters_generated'][chapter_num] = {
                                    'text': chapter_text,
                                    'time': generation_time,
                                    'tokens': total_tokens,
                                    'cost': cost,
                                    'word_count': word_count
                                }

                                # Métriques détaillées
                                col1, col2, col3, col4, col5 = st.columns(5)
                                with col1:
                                    st.metric("Mots", word_count)
                                with col2:
                                    st.metric("Temps", f"{generation_time:.1f}s")
                                with col3:
                                    st.metric("Mots/sec", f"{word_count/generation_time:.0f}")
                                with col4:
                                    st.metric("Tokens", f"~{total_tokens:,}", delta=f"in:{input_tokens} out:{output_tokens}")
                                with col5:
                                    if cost > 0:
                                        st.metric("Coût", f"${cost:.6f}")
                                    else:
                                        st.metric("Coût", "N/A")

                                # Afficher le chapitre
                                st.success(f"✅ Chapitre {chapter_num} généré")
                                st.markdown(f"### Chapitre {chapter_num}: {chapter_info['title']}")
                                st.markdown(chapter_text)

                                # Bouton TTS pour écouter le chapitre
                                if enable_tts:
                                    col_tts1, col_tts2 = st.columns([1, 4])
                                    with col_tts1:
                                        if st.button(f"🔊 Écouter le chapitre {chapter_num}", key=f"tts_new_{chapter_num}"):
                                            tts = get_tts()
                                            if tts:
                                                with st.spinner("Génération audio en cours..."):
                                                    audio_bytes = run_async(tts.generate_speech(
                                                        chapter_text,
                                                        voice_id=voice_id if voice_id else None,
                                                        speed=tts_speed
                                                    ))

                                                    if audio_bytes:
                                                        st.audio(audio_bytes, format='audio/mp3')
                                                        st.success("✅ Audio généré!")
                                                    else:
                                                        st.error("❌ Échec de la génération audio")
                            else:
                                st.error("❌ Échec de la génération")

                        except Exception as e:
                            # Stocker l'erreur
                            if 'errors' not in st.session_state:
                                st.session_state['errors'] = []
                            st.session_state['errors'].append({
                                'type': f'Chapter {chapter_num} Generation Error',
                                'message': str(e),
                                'time': time.strftime('%H:%M:%S')
                            })

                            st.error(f"❌ Erreur lors de la génération du chapitre {chapter_num}: {e}")
                            with st.expander("Détails de l'erreur"):
                                st.exception(e)

            # Afficher les chapitres déjà générés
            if st.session_state.get('chapters_generated'):
                st.divider()
                st.subheader("📚 Chapitres générés")

                for ch_num in sorted(st.session_state['chapters_generated'].keys()):
                    ch_data = st.session_state['chapters_generated'][ch_num]
                    ch_info = plan.chapters[ch_num - 1]

                    with st.expander(f"✅ Chapitre {ch_num}: {ch_info['title']}"):
                        # Afficher métriques si disponibles
                        if 'tokens' in ch_data and 'cost' in ch_data:
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.caption(f"📝 {ch_data.get('word_count', len(ch_data['text'].split()))} mots")
                            with col2:
                                st.caption(f"⏱️ {ch_data['time']:.1f}s")
                            with col3:
                                st.caption(f"🎯 ~{ch_data['tokens']:,} tokens")
                            with col4:
                                if ch_data['cost'] > 0:
                                    st.caption(f"💰 ${ch_data['cost']:.6f}")
                                else:
                                    st.caption("💰 N/A")
                        else:
                            # Ancien format sans métriques détaillées
                            word_count = len(ch_data['text'].split())
                            st.caption(f"⏱️ Généré en {ch_data['time']:.1f}s | 📝 {word_count} mots")

                        st.markdown(ch_data['text'])

                        # Bouton TTS pour écouter le chapitre
                        if enable_tts:
                            if st.button(f"🔊 Écouter", key=f"tts_prev_{ch_num}"):
                                tts = get_tts()
                                if tts:
                                    with st.spinner("Génération audio en cours..."):
                                        audio_bytes = run_async(tts.generate_speech(
                                            ch_data['text'],
                                            voice_id=voice_id if voice_id else None,
                                            speed=tts_speed
                                        ))

                                        if audio_bytes:
                                            st.audio(audio_bytes, format='audio/mp3')
                                            st.success("✅ Audio généré!")
                                        else:
                                            st.error("❌ Échec de la génération audio")

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

            # Dashboard de métriques globales si au moins un chapitre généré
            if generated_count > 0:
                st.divider()
                st.subheader("📊 Métriques de Performance Globales")

                # Calculer totaux
                total_time = sum(ch.get('time', 0) for ch in chapters_gen.values())
                total_words = sum(ch.get('word_count', len(ch['text'].split())) for ch in chapters_gen.values())
                total_tokens = sum(ch.get('tokens', 0) for ch in chapters_gen.values())
                total_cost = sum(ch.get('cost', 0) for ch in chapters_gen.values())

                # Afficher métriques
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Chapitres générés", generated_count, delta=f"sur {total_chapters}")
                with col2:
                    st.metric("Temps total", f"{total_time:.1f}s", delta=f"{total_time/60:.1f} min")
                with col3:
                    st.metric("Mots totaux", f"{total_words:,}", delta=f"~{total_words/generated_count:.0f}/ch" if generated_count > 0 else None)
                with col4:
                    if total_tokens > 0:
                        st.metric("Tokens totaux", f"~{total_tokens:,}", delta=f"~{total_tokens/generated_count:.0f}/ch" if generated_count > 0 else None)
                    else:
                        st.metric("Tokens totaux", "N/A")
                with col5:
                    if total_cost > 0:
                        st.metric("Coût total", f"${total_cost:.6f}", delta=f"${total_cost/generated_count:.6f}/ch" if generated_count > 0 else None)
                    else:
                        st.metric("Coût total", "N/A")

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
                                        max_words=max_words,
                                        temperature=temperature
                                    ))
                                    generation_time = time.time() - start_time

                                    if chapter_text:
                                        # Calculer métriques
                                        word_count = len(chapter_text.split())
                                        input_estimate = cumulative_context + str(plan.to_dict()) + plan.chapters[ch_num - 1]['title']
                                        input_tokens = estimate_tokens(input_estimate)
                                        output_tokens = estimate_tokens(chapter_text)
                                        total_tokens = input_tokens + output_tokens
                                        cost = calculate_cost(input_tokens, output_tokens, config.llm.model_path)

                                        if 'chapters_generated' not in st.session_state:
                                            st.session_state['chapters_generated'] = {}

                                        st.session_state['chapters_generated'][ch_num] = {
                                            'text': chapter_text,
                                            'time': generation_time,
                                            'tokens': total_tokens,
                                            'cost': cost,
                                            'word_count': word_count
                                        }

                                    # Update progress
                                    progress_bar.progress(ch_num / total_chapters)

                                except Exception as e:
                                    # Stocker l'erreur
                                    if 'errors' not in st.session_state:
                                        st.session_state['errors'] = []
                                    st.session_state['errors'].append({
                                        'type': f'Auto-gen Chapter {ch_num} Error',
                                        'message': str(e),
                                        'time': time.strftime('%H:%M:%S')
                                    })

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
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📥 Télécharger l'histoire (Markdown)",
                            data=full_story,
                            file_name=f"histoire_{int(time.time())}.md",
                            mime="text/markdown"
                        )

                    # Bouton TTS pour écouter toute l'histoire
                    if enable_tts:
                        with col2:
                            if st.button("🔊 Écouter toute l'histoire", type="secondary"):
                                tts = get_tts()
                                if tts:
                                    # Combiner tout le texte des chapitres
                                    story_text = ""
                                    for ch_num in range(1, total_chapters + 1):
                                        ch_info = plan.chapters[ch_num - 1]
                                        ch_data = chapters_gen[ch_num]
                                        story_text += f"Chapitre {ch_num}: {ch_info['title']}. "
                                        story_text += ch_data['text'] + " "

                                    with st.spinner("Génération audio de l'histoire complète en cours... (cela peut prendre du temps)"):
                                        audio_bytes = run_async(tts.generate_speech(
                                            story_text,
                                            voice_id=voice_id if voice_id else None,
                                            speed=tts_speed
                                        ))

                                        if audio_bytes:
                                            st.audio(audio_bytes, format='audio/mp3')
                                            st.success("✅ Audio de l'histoire complète généré!")
                                        else:
                                            st.error("❌ Échec de la génération audio")

    # Tab 4: Prompt Editor
    with tab4:
        st.header("⚙️ Éditeur de Prompts")

        st.info("Modifiez les prompts utilisés pour la génération. Les changements sont sauvegardés dans `configs/prompts.json`.")

        # Charger les prompts
        try:
            prompts = load_prompts()
        except Exception as e:
            st.error(f"❌ Erreur chargement prompts: {e}")
            st.stop()

        # Section Plan
        st.subheader("📖 Génération du Plan")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**System Prompt**")
            plan_system = st.text_area(
                "Instructions système pour le plan",
                value=prompts['plan']['system_prompt'],
                height=200,
                key="plan_system",
                help="Définit le rôle et le comportement de l'IA pour la génération du plan"
            )

        with col2:
            st.markdown("**User Template**")
            plan_template = st.text_area(
                "Template du prompt utilisateur",
                value=prompts['plan']['user_template'],
                height=200,
                key="plan_template",
                help="Variables disponibles: {theme}, {num_chapters}"
            )

        # Preview du plan avec variables
        with st.expander("👁️ Preview du prompt plan (avec variables remplies)"):
            preview_theme = st.text_input("Thème de test", "un robot qui découvre les émotions", key="preview_theme_plan")
            preview_chapters = st.number_input("Nombre de chapitres", 3, 10, 5, key="preview_chapters_plan")

            try:
                filled_plan = plan_template.format(
                    theme=preview_theme,
                    num_chapters=preview_chapters
                )
                st.code(filled_plan, language="markdown")
            except Exception as e:
                st.error(f"Erreur de formatage: {e}")

        st.divider()

        # Section Chapter
        st.subheader("✍️ Génération des Chapitres")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**System Prompt**")
            chapter_system = st.text_area(
                "Instructions système pour les chapitres",
                value=prompts['chapter']['system_prompt'],
                height=200,
                key="chapter_system",
                help="Définit le rôle et le comportement de l'IA pour la génération des chapitres"
            )

        with col2:
            st.markdown("**User Template**")
            chapter_template = st.text_area(
                "Template du prompt utilisateur",
                value=prompts['chapter']['user_template'],
                height=200,
                key="chapter_template",
                help="Variables: {chapter_num}, {chapter_title}, {cumulative_context}, {story_plan}, {min_words}, {max_words}"
            )

        # Preview du chapitre avec variables
        with st.expander("👁️ Preview du prompt chapitre (avec variables remplies)"):
            preview_ch_num = st.number_input("Numéro chapitre", 1, 10, 1, key="preview_ch_num")
            preview_ch_title = st.text_input("Titre du chapitre", "Le Réveil du Robot", key="preview_ch_title")

            try:
                filled_chapter = chapter_template.format(
                    chapter_num=preview_ch_num,
                    chapter_title=preview_ch_title,
                    cumulative_context="C'est le début de l'histoire.",
                    story_plan="1. Le Réveil du Robot: Un petit robot s'active pour la première fois.\n2. La Découverte: Il explore son environnement.",
                    min_words=150,
                    max_words=300
                )
                st.code(filled_chapter, language="markdown")
            except Exception as e:
                st.error(f"Erreur de formatage: {e}")

        st.divider()

        # Boutons d'action
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
                try:
                    if save_prompts(new_prompts):
                        st.success("✅ Prompts sauvegardés dans configs/prompts.json")
                        st.info("ℹ️ Les changements prendront effet lors de la prochaine génération. Rechargez le LLM pour appliquer immédiatement.")
                    else:
                        st.error("❌ Erreur lors de la sauvegarde")
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")

        with col2:
            if st.button("🔄 Recharger LLM"):
                st.cache_resource.clear()
                st.success("✅ Cache LLM effacé")
                st.info("ℹ️ Rechargez la page pour réinitialiser complètement")
                st.rerun()


if __name__ == "__main__":
    main()
