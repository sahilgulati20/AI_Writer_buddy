#tts.py
import pyttsx3
import time

engine = pyttsx3.init("espeak")
engine.setProperty("rate", 150)
engine.setProperty("volume", 1.0)

def speak(text):
    engine.say(text)
    engine.runAndWait()
    engine.stop()   # forces release of audio device
    time.sleep(0.1) # tiny buffer drain
