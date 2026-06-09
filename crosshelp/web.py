from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

from .patterns import find_matches
from .clue import solve_clue
from .synonyms import find_by_meaning

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    """Serve the main page."""
    return render_template("index.html")


@app.route("/api/pattern", methods=["POST"])
def api_pattern():
    """Pattern match search."""
    data = request.get_json()
    pattern = data.get("pattern", "").strip()
    min_score = int(data.get("min_score", 0))
    limit = int(data.get("limit", 30))

    if not pattern:
        return jsonify({"error": "Pattern is required"}), 400
    
    try:
        results = find_matches(pattern, min_score=min_score, limit=limit)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
    return jsonify({
        "results": [{"word": word, "score": score} for word, score in results]
    })

@app.route("/api/clue", methods=["POST"])
def api_clue():
    """LLM-powered clue solver."""
    data = request.get_json()
    clue = data.get("clue", "").strip()
    pattern = data.get("pattern", "").strip()

    if not clue or not pattern:
        return jsonify({"error": "Both clue and pattern are required"}), 400
    
    results = solve_clue(clue, pattern)

    return jsonify({
        "results": [{"word": word, "score": None} for word in results]
    })

@app.route("/api/synonym", methods=["POST"])
def api_synonym():
    """Datamuse meaning-based search."""
    data = request.get_json()
    meaning = data.get("meaning", "").strip()
    pattern = data.get("pattern", "").strip() or None
    limit = int(data.get("limit", 20))

    if not meaning:
        return jsonify({"error": "Meaning is required"}), 400
    
    results = find_by_meaning(meaning, pattern=pattern, limit=limit)

    return jsonify({
        "results": results
    })

def main():
    """Entry point: start the dev server."""
    import webbrowser
    import threading

    url = "http://127.0.0.1:5050"
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(debug=False, port=5050)


if __name__ == "__main__":
    main()