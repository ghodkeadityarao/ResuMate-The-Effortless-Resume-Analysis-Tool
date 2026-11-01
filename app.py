"""ResuMate: upload a resume, get a score out of 100 with fixes, role suggestions and a job-post match.

    flask --app app run

Nothing is stored: an upload is read in memory, analysed and forgotten, and no state is shared between requests.
"""
from flask import Flask, jsonify, render_template, request

from resumate import highlight, jobmatch, roles
from resumate.checks import CATEGORIES
from resumate.extract import MAX_BYTES, UnreadableFile, read_document
from resumate.scoring import analyze

MAX_JOB_CHARS = 20000


def band(score):
    """(css class, label) for a score out of 100."""
    for floor, cls, label in ((85, "strong", "Strong"), (70, "good", "Good"), (50, "fair", "Getting there")):
        if score >= floor:
            return cls, label
    return "poor", "Needs work"


def run_analysis(upload, job_text):
    """Everything the report shows, for one uploaded file (a werkzeug FileStorage) and an optional job post."""
    if upload is None or not upload.filename:
        raise UnreadableFile("Choose a resume file to upload.")
    doc = read_document(upload.filename, upload.read(MAX_BYTES + 1))
    report = analyze(doc)
    ranked, confident = roles.model().predict(doc.text)
    band_class, band_label = band(report.total)
    result = {"report": report, "roles": ranked, "confident": confident, "filename": upload.filename,
              "lines": highlight.render(doc.text, report.findings), "band_class": band_class, "band_label": band_label,
              "missing_skills": roles.model().missing_skills(ranked[0][0], doc.text) if confident else [], "job": None}
    job_text = (job_text or "").strip()[:MAX_JOB_CHARS]
    if job_text:
        result["job"] = jobmatch.match(doc.text, job_text)
    return result


def as_json(result):
    r = result["report"]
    return {"score": r.total, "categories": {k: {"score": s, "max": m} for k, (s, m) in r.categories.items()},
            "words": r.words, "pages": r.pages, "sections_found": r.sections, "skills": [s for s, _ in r.skills],
            "findings": [{"key": f.key, "category": f.category, "title": f.title, "score": f.score, "max": f.max_points,
                          "summary": f.summary, "evidence": f.evidence, "tip": f.tip} for f in r.findings],
            "roles": [{"role": name, "probability": round(p, 3)} for name, p in result["roles"]],
            "role_confident": result["confident"], "skills_to_consider": [s for s, _ in result["missing_skills"]],
            "job_match": result["job"]}


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_BYTES + 200_000
    roles.model()                                                   # train once at start so the first request is fast

    @app.get("/")
    def index():
        return render_template("index.html", error=None)

    @app.post("/analyze")
    def analyze_page():
        wants_fragment = request.headers.get("X-Requested-With") == "fetch"      # sent by static/app.js
        try:
            result = run_analysis(request.files.get("resume"), request.form.get("job"))
        except (UnreadableFile, ValueError) as e:
            if wants_fragment:
                return jsonify(error=str(e)), 400
            return render_template("index.html", error=str(e), job_text=request.form.get("job")), 400
        page = "_report.html" if wants_fragment else "report.html"
        return render_template(page, categories=CATEGORIES, **result)

    @app.post("/api/analyze")
    def analyze_api():
        try:
            result = run_analysis(request.files.get("resume"), request.form.get("job"))
        except (UnreadableFile, ValueError) as e:
            return jsonify(error=str(e)), 400
        return jsonify(as_json(result))

    @app.errorhandler(413)
    def too_big(_):
        message = f"The upload is larger than {MAX_BYTES // 1024 // 1024} MB."
        if request.path.startswith("/api/"):
            return jsonify(error=message), 413
        return render_template("index.html", error=message), 413

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
