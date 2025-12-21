#!/usr/bin/env python3
"""
Script de test audio + bouton GPIO pour débogage
Teste l'enregistrement avec le bouton sans passer par Vosk/Gemini
"""

import pyaudio
import wave
import time
from gpiozero import Button

# Configuration
BUTTON_PIN = 17
AUDIO_FILE = "/tmp/test_recording.wav"
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1

# Trouver le device USB et son sample rate natif
def find_usb_device():
    """Trouve le device USB audio et retourne (index, sample_rate)"""
    p = pyaudio.PyAudio()

    print("Devices audio disponibles:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(f"  [{i}] {info['name']} - Channels: {info['maxInputChannels']}")

        # Chercher le device USB
        if 'USB' in info['name'] and info['maxInputChannels'] > 0:
            # Essayer différents sample rates communs
            for rate in [48000, 44100, 32000, 16000, 8000]:
                try:
                    # Tester si ce sample rate fonctionne
                    if p.is_format_supported(
                        rate,
                        input_device=i,
                        input_channels=1,
                        input_format=pyaudio.paInt16
                    ):
                        print(f"\n✓ Device USB trouvé: {info['name']}")
                        print(f"  Index: {i}")
                        print(f"  Sample rate: {rate} Hz")
                        p.terminate()
                        return i, rate
                except:
                    continue

    p.terminate()
    return None, None


class AudioRecorder:
    """Enregistreur audio simplifié"""

    def __init__(self, device_index, sample_rate):
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.is_recording = False
        self.frames = []
        self.audio = None
        self.stream = None

    def start_recording(self):
        """Démarre l'enregistrement"""
        print("🔴 ENREGISTREMENT...")
        self.is_recording = True
        self.frames = []

        self.audio = pyaudio.PyAudio()

        try:
            self.stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=CHUNK
            )
            print(f"   Stream ouvert: {self.sample_rate} Hz")
        except Exception as e:
            print(f"❌ Erreur ouverture stream: {e}")
            self.is_recording = False
            if self.audio:
                self.audio.terminate()
            return

        # Enregistrer en boucle
        try:
            while self.is_recording:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                self.frames.append(data)
        except Exception as e:
            print(f"❌ Erreur lecture: {e}")

    def stop_recording(self):
        """Arrête et sauvegarde"""
        print("⏹️  Arrêt enregistrement...")
        self.is_recording = False
        time.sleep(0.1)  # Laisser le thread finir

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        if self.audio:
            self.audio.terminate()

        # Sauvegarder
        if self.frames:
            wf = wave.open(AUDIO_FILE, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(FORMAT))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.frames))
            wf.close()

            duration = len(self.frames) * CHUNK / self.sample_rate
            print(f"✓ Enregistré: {AUDIO_FILE} ({duration:.1f}s)")
            return True

        return False


def main():
    """Test du bouton + enregistrement"""

    print("=" * 70)
    print("🎤 TEST BOUTON GPIO + AUDIO")
    print("=" * 70)
    print()

    # Trouver le device USB
    device_idx, sample_rate = find_usb_device()

    if device_idx is None:
        print("❌ Aucun device USB trouvé")
        return

    print()
    print("─" * 70)
    print("📝 INSTRUCTIONS:")
    print("─" * 70)
    print("1. Appuyez sur le bouton (GPIO 17) pour commencer")
    print("2. Parlez pendant que le bouton est pressé")
    print("3. Relâchez le bouton pour arrêter")
    print("4. Le fichier sera sauvegardé dans /tmp/test_recording.wav")
    print()
    print("🔵 En attente du bouton...")
    print()

    # Créer le bouton
    button = Button(BUTTON_PIN, pull_up=True, bounce_time=0.1)
    recorder = AudioRecorder(device_idx, sample_rate)

    recording_started = False

    def on_press():
        nonlocal recording_started
        if not recording_started:
            recording_started = True
            # Démarrer dans un thread séparé
            import threading
            thread = threading.Thread(target=recorder.start_recording)
            thread.start()

    def on_release():
        if recording_started:
            recorder.stop_recording()
            print()
            print("✅ Test terminé!")
            print(f"   Fichier: {AUDIO_FILE}")
            print()
            print("Pour écouter:")
            print(f"   aplay {AUDIO_FILE}")
            print()

    button.when_pressed = on_press
    button.when_released = on_release

    try:
        # Attendre indéfiniment
        import signal
        signal.pause()
    except KeyboardInterrupt:
        print()
        print("🛑 Interrompu")
        button.close()


if __name__ == "__main__":
    main()
