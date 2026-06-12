import os
import re
from anthropic import Anthropic

from .patterns import pattern_to_regex, load_words

SYSTEM_PROMPT = """You are an expert crossword solver with deep knowledge of NYT-style puzzles.

Given a clue and a letter pattern, suggest possible answers. The pattern uses ? for unknown letters and capital letters for known letters.

Crossword answers follow specific conventions you must respect:

1. Crossword clues often use SLANG, IDIOMATIC, or SECONDARY meanings rather than literal ones.

2. Prefer COMMON crossword-frequency answers over rare ones. Think about what answer would actually appear in a published puzzle.

3. ROMAN NUMERALS are common for clues involving clock positions, centuries, popes, or "old" numbers. 

4. WORDPLAY clues use puns, double meanings, or hidden references. A question mark at the end of the clue (not in a quotation) is almost ALWAYS an indication of wordplay

5. PHRASES are common and written as single uppercase strings with no spaces.

6. If a word in a clue is in a specific language, the answer will often be in the same language

7. Generate 5-10 candidates. ORDER MATTERS: list the most likely crossword answer first, even if a more literal answer comes to mind.

OUTPUT FORMAT (strict):
- One answer per line
- Uppercase, no punctuation, no spaces, no explanation
- Every answer MUST exactly match the pattern length
- Every answer MUST match the fixed letters in the pattern
- If you have no good candidates, return nothing

Examples:

Clue: Big Apple, briefly
Pattern: ???
Answer:
NYC

Clue: Dodos
Pattern: ?????
Answer:
ASSES
GEESE
DUNCE
BOZOS
IDIOT

Clue: Seven on a grandfather clock
Pattern: ???
Answer:
VII
"""

def solve_clue(clue, pattern, model="claude-haiku-4-5", max_candidates=8):
    """
    Use an LLM to suggest crossword answers for a clue + pattern.

    Parameters:
        clue: the crossword clue text, e.g. "Capital of France"
        pattern: pattern string, e.g. "?????" or "P????"
        model: which Claude model to use
        max_candidates: how many candidates to ask the LLM for

    Returns a list of candidate answers (strings, uppercase) that match the pattern.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY enviornment variable is not set.")
        return []
    
    client = Anthropic()
    user_message = f"Clue: {clue}\nPattern: {pattern.upper()}\nReturn up to {max_candidates} answers."

    try:
        response = client.messages.create(
            model=model,
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
    except Exception as e:
        print(f"LLM API error: {e}")
        return[]
    
    raw_text = response.content[0].text
    candidates = _parse_candidates(raw_text)
    valid = _filter_by_pattern(candidates, pattern)
    return valid

def _parse_candidates(raw_text):
    """Extract candidate answers from the LLM raw response"""
    lines = raw_text.strip().split("\n")
    candidates = []
    for line in lines:
        cleaned = re.sub(r"[^A-Za-z]", "", line).upper()
        if cleaned:
            candidates.append(cleaned)
    return candidates

def _filter_by_pattern(candidates, pattern):
    """Keep only candidates that match the given pattern."""
    regex = pattern_to_regex(pattern)
    return [c for c in candidates if regex.match(c)]

def solve_clue_with_wordlist_check(clue, pattern, model="claude-haiku-4-5", max_candidates=5):
    """
    Like solve_clue, but also flags candidates that don't appear in the wordlist.

    Returns a list of (word, in_wordlist) tuples.
    """
    valid = solve_clue(clue, pattern, model=model, max_candidates=max_candidates)
    words_in_list = {word for word, score in load_words()}
    return [(word, word in words_in_list) for word in valid]