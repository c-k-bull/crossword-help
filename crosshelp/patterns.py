from pathlib import Path

_WORDS_CACHE = None

WORDLIST_PATH = Path(__file__).parent / "data" / "wordlist.txt"

def load_words() :
    """Read the worldlist file and return a list of (word, score) tuples.
    Score is an integer 0-100 indicating crossword likeliness.
    Cached after first call.
    """
    global _WORDS_CACHE
    if _WORDS_CACHE is not None:
        return _WORDS_CACHE
    words = []
    with open(WORDLIST_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if ";" in line:
                parts = line.split(";")
                word = parts[0].upper()
                try:
                    score = int(parts[1])
                except (ValueError, IndexError):
                    score = 50
            else:
                word = line.upper()
                score = 50
            if word.isalpha():
                words.append((word,score))
    _WORDS_CACHE = words
    return words

import re

def pattern_to_regex(pattern) :
    """
    Convert a word patter like 'C?UE' into a regex object.
    '?', '.', and '_' are all treated as single letter wildcards
    """
    pattern = pattern.upper()
    regex_parts = ["^"]
    for char in pattern:
        if char in "?._":
            regex_parts.append("[A-Z]")
        elif char.isalpha():
            regex_parts.append(char)
        else:
            raise ValueError(f"Invalud character")
    regex_parts.append("$")
    regex_str = "".join(regex_parts)
    return re.compile(regex_str)
        
def find_matches(pattern, min_score=0, limit=5):
    """
    Find all words in the wordlist that match the pattern.
    Returns at most 'limit' results with a minimum likeliness score of 'min_score'.
    Sorted by descending.
    """
    regex = pattern_to_regex(pattern)
    words = load_words()
    matches = []
    for word, score in words:
        if score < min_score:
            continue
        if regex.match(word):
            matches.append((word, score))
    matches.sort(key=lambda item: -item[1])
    return matches[:limit]