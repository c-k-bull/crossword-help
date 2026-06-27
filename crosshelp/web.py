from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

from .patterns import find_matches
from .clue import solve_clue
from .synonyms import find_by_meaning
from .db.queries import log_search, record_correction, recent_searches, accuracy_stats
app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    """Serve the main page."""
    return render_template("index.html")


@app.route("/api/pattern", methods=["POST"])
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
        results = find_matches(pattern, min_score=min_score, limit=10)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    top_result = results[0][0] if results else None
    search_id = None
    try:
        search_id = log_search(
            mode="pattern",
            pattern=pattern,
            result_count=len(results),
            top_result=top_result,
        )
    except Exception as e:
        print(f"Failed to log search: {e}")

    return jsonify({
        "search_id": search_id,
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

    raw_results = solve_clue(clue, pattern=pattern or None)    # Dedup while preserving order
    seen = set()
    results = []
    for word in raw_results:
        if word not in seen:
            seen.add(word)
            results.append(word)
        if len(results) >= 10:
            break
    top_result = results[0] if results else None
    search_id = None
    try:
        search_id = log_search(
            mode="clue",
            clue=clue,
            pattern=pattern,
            result_count=len(results),
            top_result=top_result,
        )
    except Exception as e:
        print(f"Failed to log search: {e}")

    return jsonify({
        "search_id": search_id,
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
    
    results = find_by_meaning(meaning, pattern=pattern or None)[:10]
    top_result = results[0]["word"] if results else None
    try:
        search_id = log_search(
            mode="synonym",
            meaning=meaning,
            pattern=pattern,
            result_count=len(results),
            top_result=top_result,
        )
    except Exception as e:
        print(f"Failted to log search: {e}")

    return jsonify({
        "search_id": search_id,
        "results": results
    })

@app.route("/api/history", methods=["GET"])
def api_history():
    """Return recent searches"""
    mode = request.args.get("mode")
    limit = int(request.args.get("limit", 20)),
    try:
        rows = recent_searches(limit=limit, mode=mode)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    #Serialize datetime to ISO string for JSON output
    for row in rows:
        if row.get("created_at"):
            row["created_at"] = row["created_at"].isoformat()
    
    return jsonify({"history": rows})

@app.route("/api/feedback", methods=["POST"])
def api_feedback():
    """Record a user correction on a previous search."""
    data = request.get_json()
    search_id = data.get("search_id")
    corrected_answer = (data.get("corrected_answer") or "").strip()

    if not search_id:
        return jsonify({"error": "search_id is required"}), 400
    if not corrected_answer:
        return jsonify({"error": "corrected_answer is required"}), 400

    try:
        ok = record_correction(int(search_id), corrected_answer)
    except (ValueError, TypeError):
        return jsonify({"error": "search_id must be an integer"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if not ok:
        return jsonify({"error": "Search not found"}), 404

    return jsonify({"status": "recorded"})

@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Return reported accuracy stats."""
    mode = request.args.get("mode")
    try:
        stats = accuracy_stats(mode=mode)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify(stats)

def main():
    """Entry point: start the dev server."""
    import os

    # Render sets PORT; default to 5001 for local dev.
    port = int(os.environ.get("PORT", 5001))

    # Detect environment.
    in_container = os.path.exists("/.dockerenv")
    in_render = bool(os.environ.get("RENDER"))
    in_production = in_container or in_render

    if not in_production:
        import webbrowser
        import threading
        url = f"http://127.0.0.1:{port}"
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    host = "0.0.0.0" if in_production else "127.0.0.1"
    app.run(debug=False, host=host, port=port)


if __name__ == "__main__":
    main()