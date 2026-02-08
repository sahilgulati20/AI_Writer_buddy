from realtime_vosk import VoskListener
from tts import speak
import cleaned_svgout
from plot import plot
import time

MODEL_PATH = "./model/en_in"
OUTPUT_FILE = "output_1a4.svg"

# Modes
MODE_SINGLE_LINE = "single"
MODE_MULTI_LINE = "multi"

def main():
    # 1. Reset state on startup
    cleaned_svgout.reset_state()
    
    # 2. Initialize Listener
    speak("System initializing...")
    listener = VoskListener(MODEL_PATH)
    
    # 3. Default Settings
    current_mode = MODE_SINGLE_LINE
    
    speak("Welcome to AI Writer Buddy.")
    speak("I am set to Single Line mode.")

    # Generator for voice input
    voice_stream = listener.listen()

    while True:
        # --- WAIT FOR INPUT ---
        print("\n[LISTENING]...")
        
        # Get next phrase
        try:
            text = next(voice_stream).lower()
        except StopIteration:
            break

        print(f"HEARD: {text}")

        # --- COMMANDS ---
        
        # 1. Buddy Line Options
        if "buddy line options" in text or "line options" in text:
            speak("You have two options. First, Single Line. Second, Multi Line.")
            speak("Which one do you want? Say Single or Multi.")
            
            # Wait for selection
            while True:
                try:
                    selection = next(voice_stream).lower()
                    print(f"SELECTION HEARD: {selection}")
                    
                    if "single" in selection:
                        current_mode = MODE_SINGLE_LINE
                        speak("Okay. Single Line mode selected.")
                        break
                    elif "multi" in selection:
                        current_mode = MODE_MULTI_LINE
                        speak("Okay. Multi Line mode selected.")
                        break
                    else:
                        speak("Please say Single, or Multi.")
                except StopIteration:
                    break
            continue

        # 2. Sleep / Stop
        if "sleep" in text or "stop" in text:
            speak("Going to sleep. Restart program to wake me up.")
            break

        # --- CONFIRMATION LOOP ---
        # If we are here, 'text' is something the user might want to write.
        
        while True:
            speak(f"You said: {text}. Do you want me to write this? Say Yes or No.")
            
            try:
                confirmation = next(voice_stream).lower()
            except StopIteration:
                break
                
            print(f"CONFIRM HEARD: {confirmation}")

            if "yes" in confirmation:
                speak("Okay, writing.")
                
                # Plot logic
                lines = split_to_lines(text)
                cleaned_svgout.text_to_svg(lines, OUTPUT_FILE)
                
                speak("Plotting now...")
                try:
                    plot(OUTPUT_FILE)
                except Exception as e:
                    print(f"Plot error: {e}")
                    speak("There was an error sending to the plotter.")
                
                # Note: plot() might block for a while.
                
                speak("Done.")
                
                if current_mode == MODE_MULTI_LINE:
                    speak("Ready for next line.")
                else:
                    speak("Waiting for next command.")
                break

            elif "no" in confirmation:
                speak("Okay, tell me again what you want to write.")
                # Break inner loop to go back to main listening loop
                break
            
            elif "sleep" in confirmation:
                speak("Going to sleep.")
                return 

            else:
                # If they said something else, ask again
                # Loop continues
                pass


def split_to_lines(text, max_words=8):
    """Simple line breaker for SVG"""
    words = text.split()
    lines, current = [], []

    for w in words:
        current.append(w)
        if len(current) >= max_words:
            lines.append(" ".join(current))
            current = []

    if current:
        lines.append(" ".join(current))

    return lines

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")

