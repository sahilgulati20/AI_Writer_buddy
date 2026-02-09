import json
import queue
import sys
import sounddevice as sd
from vosk import Model, KaldiRecognizer

SAMPLE_RATE = 16000

class VoskListener:
    def __init__(self, model_path, device=None):
        self.model = Model(model_path)
        self.rec = KaldiRecognizer(self.model, SAMPLE_RATE)
        self.q = queue.Queue()
        self.device = device

    def _callback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        self.q.put(bytes(indata))

    def listen(self):
        """Generator yielding FINAL recognized text only"""
        stream = sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=self._callback,
            device=self.device,
        )

        with stream:
            while True:
                data = self.q.get()
                if self.rec.AcceptWaveform(data):
                    res = json.loads(self.rec.Result())
                    text = res.get("text", "").strip()
                    if text:
                        yield text

    def set_grammar(self, words):
        """Restricts recognition to a specific list of words/phrases."""
        # Convert list of words to JSON string format required by Vosk
        # Example: '["yes", "no", "[unk]"]'
        grammar = json.dumps(words + ["[unk]"])
        self.rec = KaldiRecognizer(self.model, SAMPLE_RATE, grammar)

    def reset_grammar(self):
        """Resets recognition to full vocabulary."""
        self.rec = KaldiRecognizer(self.model, SAMPLE_RATE)
