#tts.py
import os
import time
import sys

# Try importing gTTS (internet required)
try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False
    print("gTTS not found. Install with: pip install gTTS")

# Fallback engine
import pyttsx3
engine = pyttsx3.init("espeak")
engine.setProperty("rate", 150)
engine.setProperty("volume", 1.0)

def speak_fallback(text):
    """Uses the offline robotic voice."""
    engine.say(text)
    engine.runAndWait()
    engine.stop()

def speak(text):
    """Tries to speak with a human-like voice (online), falls back if fails."""
    if not HAS_GTTS:
        speak_fallback(text)
        return

    try:
        # Generate MP3
        tts = gTTS(text=text, lang='en', tld='co.in') # 'co.in' for Indian accent
        filename = "temp_voice.mp3"
        tts.save(filename)
        
        # Play MP3 (works on Linux/Pi with mpg123 or aplay)
        # On Windows, 'start' command works. On Pi, 'mpg123' is best.
        if sys.platform == "win32":
            os.system(f"start {filename}")
            # wait a bit for player to start (rough hack)
            time.sleep(1 + len(text)/10) 
        else:
            # Linux / Raspberry Pi
            exit_code = os.system(f"mpg123 -q {filename}")
            if exit_code != 0:
                # If mpg123 fails/missing, try aplay or fallback
                # aplay doesn't play mp3 directly usually
                raise Exception("Audio player failed")

        # Cleanup
        # os.remove(filename) # Keep file briefly or overwrite next time
        
    except Exception as e:
        print(f"TTS Error (switching to fallback): {e}")
        speak_fallback(text)
