import requests

DATAMUSE_URL = "https://api.datamuse.com/words"


def find_by_meaning(meaning, pattern=None, limit=20, strict=False):
    """
    Find words by meaning, optionally constrained by a crossword pattern.

    Parameters:
        meaning: a word or phrase describing the meaning (e.g. "fleeting")
        pattern: optional crossword pattern like 'E?H???R?L'
                 ('?' is a wildcard for any letter)
        limit: max results to return
        strict: if True, only return strict synonyms.
                if False (default), allow broader meaning matches.

    Returns a list of dicts: [{"word": "EPHEMERAL", "score": 12345}, ...]
    """
    params = {"max": limit}
    if strict:
        params["rel_syn"] = meaning
    else:
        params["ml"] = meaning
    if pattern:
        params["sp"] = pattern.lower()
    
    try:
        response = requests.get(DATAMUSE_URL, params=params, timeout=5)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Datamuse API error: {e}")
        return[]
    
    data = response.json()
    return [{"word": item["word"].upper(), "score": item.get("score", 0)} for item in data]

def get_definitions(word):
    """
    Get definitions for a single word.
    Returns a list of definition strings.
    """
    params = {"sp": word.lower(), "md": "d", "max": 1}

    try:
        response = requests.get(DATAMUSE_URL, params=params, timeout=5)
        response.raise_for_status
    except requests.RequestException as e:
        print(f"Datamuse API error: {e}")
        return []
    
    data = response.json()
    if not data:
        return []
    
    raw_defs = data[0].get("defs", [])
    return [d.split("\t", 1)[1] if "\t" in d else d for d in raw_defs]