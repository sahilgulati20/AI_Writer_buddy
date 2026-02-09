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
    
    speak("Hi! I'm your AI Writer Buddy. I'm ready to write.")
    speak("I am currently in Single Line mode.")

    # Generator for voice input
    voice_stream = listener.listen()

    while True:
        # --- WAIT FOR INPUT ---
        listener.reset_grammar() # Ensure we are in free-text mode
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
            speak("I can switch modes. Say Single for single line, or Multi for multi line.")
            
            # Restrict grammar for accuracy
            listener.set_grammar(["single", "multi"])

            # Wait for selection
            while True:
                try:
                    selection = next(voice_stream).lower()
                    print(f"SELECTION HEARD: {selection}")
                    
                    if "single" in selection:
                        current_mode = MODE_SINGLE_LINE
                        speak("Got it. I've switched to Single Line mode.")
                        break
                    elif "multi" in selection:
                        current_mode = MODE_MULTI_LINE
                        speak("Understood. Multi Line mode active.")
                        break
                    else:
                        speak("Sorry, please just say Single or Multi.")
                except StopIteration:
                    break
            
            listener.reset_grammar()
            continue

        # 2. Sleep / Stop
        if "sleep" in text or "stop" in text:
            speak("Okay, taking a nap. Restart me when you need me.")
            break

        # --- CONFIRMATION LOOP ---
        # If we are here, 'text' is something the user might want to write.
        
        # Restrict grammar for confirmation
        listener.set_grammar(["yes", "no", "sleep"])
        
        while True:
            speak(f"I heard: {text}. Should I write that?")
            
            try:
                confirmation = next(voice_stream).lower()
            except StopIteration:
                break
                
            print(f"CONFIRM HEARD: {confirmation}")

            if "yes" in confirmation:
                speak("Writing it now.")
                
                # Plot logic
                lines = split_to_lines(text)
                cleaned_svgout.text_to_svg(lines, OUTPUT_FILE)
                
                # speak("Sending to plotter...")
                try:
                    plot(OUTPUT_FILE)
                except Exception as e:
                    print(f"Plot error: {e}")
                    speak("Oops, I had trouble sending that to the plotter.")
                
                speak("All done.")
                
                if current_mode == MODE_MULTI_LINE:
                    speak("What's the next line?")
                else:
                    speak("I'm listening.")
                break

            elif "no" in confirmation:
                speak("My apologies. Please tell me again.")
                break
            
            elif "sleep" in confirmation:
                speak("Goodnight.")
                return 

            else:
                speak("Please say Yes or No.")
                # Loop continues
        
        listener.reset_grammar()


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

