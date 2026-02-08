#realtime_vosk.py
#!/usr/bin/env python3
"""Realtime microphone recognition using Vosk.

Usage:
  python3 realtime_vosk.py --model ./model/en_in --duration 10

If model path is missing, the script will print instructions to download a Vosk Indian English model.
"""
import argparse
import json
import os
import queue
import sys
import subprocess

try:
    import sounddevice as sd
    import numpy as np
    from vosk import Model, KaldiRecognizer
except Exception as e:
    print("Missing dependencies. Run: python3 -m pip install -r requirements.txt")
    raise


SAMPLE_RATE = 16000


def int16_to_bytes(data: np.ndarray) -> bytes:
    return data.tobytes()


def main():
    parser = argparse.ArgumentParser()
    default_model = './model/en_in'
    parser.add_argument("--model", default=default_model, help="Path to Vosk model directory (default: ./model/en_in)")
    parser.add_argument("--device", default=None, help="Input device (index or name). If omitted, auto-select first USB input device")
    parser.add_argument("--duration", type=int, default=0, help="Seconds to run (0 = until Ctrl+C)")
    args = parser.parse_args()

    model_path = args.model
    if not os.path.isdir(model_path):
        print("Model not found at:", model_path)
        print("Download an Indian English model (small) from:")
        print("https://alphacephei.com/vosk/models — look for 'vosk-model-small-en-in-*'")
        print("After download, extract and pass the extracted folder with --model")
        sys.exit(1)

    print("Loading model from", model_path)
    model = Model(model_path)
    rec = KaldiRecognizer(model, SAMPLE_RATE)

    q = queue.Queue()

    def find_first_usb_input_device():
        try:
            devs = sd.query_devices()
        except Exception:
            return None

        if isinstance(devs, dict):
            devs = [devs]

        for idx, d in enumerate(devs):
            try:
                name = d.get('name', '') if isinstance(d, dict) else ''
                max_in = d.get('max_input_channels', 0) if isinstance(d, dict) else 0
            except Exception:
                name = str(d)
                max_in = 1
            if max_in and any(k in name.lower() for k in ('usb', 'webcam', 'c270', 'microphone')):
                return idx
        return None

    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        q.put(bytes(indata))

    # Determine audio input device: CLI override -> auto-detect USB -> default
    selected_device = None
    if args.device:
        selected_device = args.device
    else:
        sel = find_first_usb_input_device()
        if sel is not None:
            selected_device = sel

    try:
        if selected_device is not None:
            print(f"Using audio device: {selected_device}")
            stream_ctx = sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000, dtype='int16', channels=1, callback=callback, device=selected_device)
        else:
            print("Using default audio input device")
            stream_ctx = sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000, dtype='int16', channels=1, callback=callback)

        with stream_ctx:
            print("Started listening (press Ctrl+C to stop)...")
            if args.duration and args.duration > 0:
                remaining_ms = args.duration * 1000
                import time as _time
                start = _time.time()
            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    text = res.get("text", "")
                    if text:
                        print("FINAL:", text)
                else:
                    partial = json.loads(rec.PartialResult()).get("partial", "")
                    if partial:
                        print("PARTIAL:", partial)
                if args.duration and ( _time.time() - start )*1000 >= remaining_ms:
                    break
    except KeyboardInterrupt:
        print("\nStopped by user")


if __name__ == '__main__':
    main()
