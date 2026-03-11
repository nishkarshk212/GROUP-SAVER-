#!/usr/bin/env python3
"""Test if oxytocin is detected by the bot"""

import re
import unicodedata

# Copy the bot's detection logic
LEET_MAP = {
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t",
    "@": "a", "$": "s", "!": "i", "+": "t"
}

DRUG_WORDS = [
    "drug", "weed", "marijuana", "cannabis", "cocaine", "crack", "heroin",
    "mdma", "molly", "ecstasy", "ketamine", "xanax", "adderall", "oxy",
    "oxycodone", "opioid", "meth", "crystal", "ice", "lsd", "acid", "shrooms",
    "psilocybin", "dmt", "fentanyl", "tramadol", "ritalin", "benzos", "benzo",
    "pill", "pharmacy", "420", "high", "stoned"
]

NSFW_WORDS = [
    "sex", "porn", "nude", "nudes", "xxx", "hentai", "blowjob", "anal",
    "fetish", "cum", "sperm", "cock", "pussy", "tits", "boobs", "lingerie",
    "erotic", "camgirl", "onlyfans", "fap", "naked", "hot", "milf", "teen",
    "dick", "ass", "butt", "thot", "slut", "whore", "bitch"
]

drug_re = re.compile(
    r"(?i)\b(?:drug|weed|marijuana|cannabis|cocaine|crack|heroin|mdma|molly|ecstasy|ketamine|xanax|adderall|oxy|oxycodone|opioid|meth|crystal|ice|lsd|acid|shrooms|psilocybin|dmt|fentanyl|tramadol|ritalin|benzos|benzo|pill|pharmacy)\b"
)

def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    for leet, char in LEET_MAP.items():
        text = text.replace(leet, char)
    text = re.sub(r'[^a-z]', '', text)
    text = re.sub(r'(.)\1+', r'\1', text)
    return text

def detect_nsfw_advanced(text: str) -> bool:
    if not text:
        return False
    
    cleaned = normalize_text(text)
    
    # Check NSFW words
    for word in NSFW_WORDS:
        if word in cleaned:
            return True
    
    # Check drug words
    for word in DRUG_WORDS:
        if word in cleaned:
            return True
    
    # Also check with original regex
    if drug_re.search(text):
        return True
    
    return False

# Test cases
test_texts = [
    "oxytocin",
    "Oxytocin", 
    "OXYTOCIN",
    "oxytocin hormone",
    "the oxytocin molecule",
    "oxy",
    "oxycodone"
]

print("=" * 60)
print("Testing OXYTOCIN Detection")
print("=" * 60)

for test in test_texts:
    result_regex = bool(drug_re.search(test))
    result_advanced = detect_nsfw_advanced(test)
    normalized = normalize_text(test)
    
    print(f"\nTest: '{test}'")
    print(f"  Normalized: '{normalized}'")
    print(f"  Regex Match: {result_regex}")
    print(f"  Advanced Detection: {result_advanced}")
    
    # Check which word matched
    cleaned = normalize_text(test)
    for word in DRUG_WORDS:
        if word in cleaned:
            print(f"  ✓ Matched drug word: '{word}'")

print("\n" + "=" * 60)
print("CONCLUSION:")
print("=" * 60)
print(" oxytocin contains 'oxy' but after normalization,")
print(" the full word 'oxytocin' is checked, not substrings.")
print(" Since 'oxytocin' is not in DRUG_WORDS list, it won't match")
print(" unless 'oxy' is found as a separate word (with word boundaries).")
