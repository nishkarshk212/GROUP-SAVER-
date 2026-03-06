#!/usr/bin/env python3
"""Test script to debug NSFW word detection"""

import os
import sys

# Load environment variables
from bot import (
    text_has_nsfw, 
    _load_bad_words, 
    _bad_loaded, 
    _bad_word_re, 
    _bad_phrases, 
    _bad_langs
)

print("=" * 60)
print("NSFW Word Detection Debug Test")
print("=" * 60)

# Force load bad words
print("\n1. Loading bad words...")
_load_bad_words()

print(f"   - Bad words loaded: {_bad_loaded}")
print(f"   - Languages: {_bad_langs}")
print(f"   - Regex pattern compiled: {_bad_word_re is not None}")
print(f"   - Number of phrases: {len(_bad_phrases)}")

if _bad_word_re:
    print(f"   - Regex pattern: {_bad_word_re.pattern[:100]}...")

# Test cases
test_cases = [
    "This is porn",
    "Hello world",
    "Fuck you",
    "Nice weather today",
    "Sex content",
    "Clean message"
]

print("\n2. Testing word detection:")
for test in test_cases:
    result = text_has_nsfw(test)
    print(f"   '{test}' -> {'NSFW DETECTED' if result else 'Clean'}")

print("\n3. Testing with obfuscated words:")
obfuscated_tests = [
    "p0rn",
    "s3x",
    "f**k",
    "pr0n"
]

for test in obfuscated_tests:
    result = text_has_nsfw(test)
    print(f"   '{test}' -> {'NSFW DETECTED' if result else 'Clean'}")

print("=" * 60)

# Additional debug: Check if files exist
print("\n4. Checking naughty words files:")
import os
naughty_dir = os.path.join(os.path.dirname(__file__), "data", "naughty-words")
print(f"   Directory: {naughty_dir}")
print(f"   Exists: {os.path.exists(naughty_dir)}")
if os.path.exists(naughty_dir):
    files = os.listdir(naughty_dir)
    print(f"   Files found: {len(files)}")
    for f in files[:5]:
        filepath = os.path.join(naughty_dir, f)
        size = os.path.getsize(filepath)
        print(f"      - {f}: {size} bytes")

# Manual test of loading
print("\n5. Manual loading test for en.json:")
import json
en_path = os.path.join(naughty_dir, "en.json")
if os.path.isfile(en_path):
    with open(en_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"   Loaded {len(data)} English words")
    print(f"   Sample: {data[:3]}")
    
print("=" * 60)
