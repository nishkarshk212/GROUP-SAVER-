#!/usr/bin/env python3
"""
Debug script to check if multilanguage NSFW detection is working properly
"""
import os
import sys
sys.path.insert(0, '/Users/nishkarshkr/Desktop/bot-app')

# Load env from .env file
try:
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"\'')
except FileNotFoundError:
    print("Warning: .env file not found")

from bot import _load_bad_words, _bad_loaded, _bad_word_re, _bad_phrases, _bad_langs

print("Current NSFW_WORD_LANGS setting:", os.environ.get("NSFW_WORD_LANGS", "en,ru"))

# Load bad words
_load_bad_words()

print("Languages loaded:", _bad_langs)
print("Bad word regex compiled:", _bad_word_re is not None)
print("Number of bad phrases:", len(_bad_phrases) if _bad_phrases else 0)

# Test some sample text in different languages
test_cases = [
    "hello world",  # Safe English
    "fuck you",     # NSFW English
    "puta",         # NSFW Spanish
    "merde",        # NSFW French
    "porca",        # NSFW Italian
    "блять",        # NSFW Russian (transliterated as 'blyat')
]

from bot import text_has_nsfw

print("\nTesting text_has_nsfw function:")
for test_text in test_cases:
    result = text_has_nsfw(test_text)
    print(f"'{test_text}' -> {'NSFW' if result else 'Safe'}")

# Also test the translation function if available
try:
    from bot import translate_text
    print(f"\nTesting translation: 'puta' -> '{translate_text('puta')}'")
except ImportError:
    print("\nTranslation function not available")