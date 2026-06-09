import os
import re
from anthropic import Anthropic

from .patterns import pattern_to_regex, load_words

SYSTEM_PROMPT = """You are an expert crossword solver, using the NYT crosswords as a baseline for trivia and wordplay. Given a clue and a letter pattern, suggest possible answers.

Rules:
- The pattern uses ? for unknown letters and capital letters for known letters.
- Every answer MUST be exactly the same length as the pattern.
- Every answer MUST match the fixed letters in the pattern.
- Return one answer per line, uppercase, no punctuation, no explanation.
- Return up to 8 answers, best first.
- If you have no good guesses, return nothing."""

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
        cleaned = re.sub(r"[^A-Za-z]", "". line).upper()
        if cleaned:
            candidates.append(cleaned)
    return candidates

def _filter_by_pattern(candidates, pattern):
    """Keep only candidates that match the given pattern."""
    regex = pattern_to_regex(pattern)
    return [c for c in candidates if regex.match(c)]