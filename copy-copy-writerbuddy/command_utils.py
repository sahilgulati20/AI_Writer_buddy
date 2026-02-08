import re

def normalize(text: str) -> str:
    return re.sub(r"[^a-zA-Z\s]", " ", text.lower())

def has_double_word(text: str, word: str) -> bool:
    norm = normalize(text).split()
    count = sum(1 for w in norm if w == word)
    return count >= 2
