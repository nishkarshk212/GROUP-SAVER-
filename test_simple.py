#!/usr/bin/env python3
"""Simple test without Google Translate"""

import os
import re
import json

# Set environment before importing bot
os.environ['NSFW_WORD_LANGS'] = 'en'

_bad_word_re = None
_bad_phrases = []
_bad_loaded = False
_bad_local_dir = os.path.join(os.path.dirname(__file__), "data", "naughty-words")

def load_bad_words():
    global _bad_word_re, _bad_phrases, _bad_loaded
    if _bad_loaded:
        return
    
    langs = ['en']
    words = set()
    phrases = set()
    
    for lang in langs:
        local_path = os.path.join(_bad_local_dir, f"{lang}.json")
        print(f"Loading {lang} from {local_path}")
        
        if os.path.isfile(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"  Found {len(data)} items")
            
            for item in data:
                s = str(item).strip().lower()
                if not s:
                    continue
                if " " in s or "-" in s or "'" in s:
                    phrases.add(s)
                else:
                    words.add(s)
    
    if words:
        escaped = [re.escape(w) for w in sorted(words, key=len, reverse=True)]
        pattern = r"(?i)\b(?:" + "|".join(escaped) + r")\b"
        _bad_word_re = re.compile(pattern)
        print(f"Compiled regex with {len(words)} words")
    
    _bad_phrases = sorted(phrases, key=len, reverse=True)
    print(f"Loaded {len(words)} words and {len(phrases)} phrases")
    _bad_loaded = True

# Load the words
load_bad_words()

# Test
test_cases = [
    "This is porn",
    "Fuck you",
    "Hello world",
    "ass",
    "bitch",
    "2 girls 1 cup"
]

print("\nTesting detection:")
for test in test_cases:
    t = test.lower()
    detected = False
    
    if _bad_word_re and _bad_word_re.search(t):
        detected = True
        print(f"  '{test}' -> NSFW (regex match)")
    elif any(p in t for p in _bad_phrases):
        detected = True
        print(f"  '{test}' -> NSFW (phrase match)")
    else:
        print(f"  '{test}' -> Clean")
