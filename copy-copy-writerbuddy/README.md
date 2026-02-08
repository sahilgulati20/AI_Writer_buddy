# Realtime Vosk recognition (Indian English)

Steps to use:

1. Install Python dependencies:

```bash
python3 -m pip install -r requirements.txt
```

2. Download a Vosk Indian English model (example):

Visit https://alphacephei.com/vosk/models and download a model named like `vosk-model-small-en-in-0.*`.

Extract it and provide the extracted folder path to `--model`.

3. Run (example for 10 seconds):

```bash
python3 realtime_vosk.py --model ./model/en_in --duration 10
```

Notes:
- If you want the assistant to try to download/extract the model automatically, ask and I can add that step.
- On Raspberry Pi you may need system-level audio setup (ALSA / PulseAudio) and PortAudio development headers for `sounddevice`.
