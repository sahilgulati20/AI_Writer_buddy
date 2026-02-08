import speech_recognition as sr
import pyttsx3

# Initialize recognizer and TTS engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def listen():
    try:
        with sr.Microphone() as source:
            print("Listening... (speak now)")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio)
            print("You said:", text)
            return text
        except sr.UnknownValueError:
            print("Sorry, I didn't understand.")
            return ""
        except sr.RequestError:
            print("Speech service error.")
            return ""
    except OSError as e:
        # No audio input device available (e.g., running headless). Fall back to typed input.
        print("No microphone/input device available:", e)
        try:
            fallback = input("Type input to simulate speech (or leave empty to skip): ")
        except Exception:
            fallback = ""
        return fallback

# Main loop
while True:
    try:
        user_text = listen()
        if user_text:
            speak("You said " + user_text)
    except KeyboardInterrupt:
        print('\nExiting.')
        break
