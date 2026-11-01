"""Measure the role model, the scoring checks and the job-post match.

    python evaluation/evaluate.py

Writes results.json, role_confusions.csv, damage_tests.csv, threshold_table.csv and results.png to evaluation/results/.

  1. Role model: how much testing on repeated resumes inflates accuracy, and the honest accuracy on resumes
     the model has not seen (cross-validation over unique resumes only).
  2. Scoring: robustness on every dataset resume, scores of a strong and a weak sample resume, and how the score
     falls when a strong resume is deliberately damaged.
  3. Original checks: how often three of the original checks gave a degenerate answer on the dataset.
  4. Job match: does a resume match the job post of its own role better than posts of other roles?
"""
import json
import re
import statistics
import sys
import time
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedShuffleSplit
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "tests"))
sys.path.insert(0, str(HERE))
import legacy_checks  # noqa: E402
import samples  # noqa: E402
from resumate import jobmatch, roles, skills  # noqa: E402
from resumate.extract import Document, clean, read_document  # noqa: E402
from resumate.scoring import analyze  # noqa: E402

RESULTS = HERE / "results"
SEED = 0
FOLDS, REPEATS = 3, 5                      # the smallest role has only 3 unique resumes
warnings.filterwarnings("ignore")


def pct(x, digits=1):
    return round(100 * float(x), digits)


def knn_pipeline():
    """The kind of model the project started with: TF-IDF (1,500 words) and k-nearest neighbours."""
    return make_pipeline(TfidfVectorizer(sublinear_tf=True, stop_words="english", max_features=1500), KNeighborsClassifier())


# --- 1. role model -----------------------------------------------------------------------------

def role_results():
    raw = pd.read_csv(roles.DATA).dropna()
    raw["clean"] = raw.Resume.map(roles.tidy)
    texts, labels, _ = roles.load_unique()
    texts, labels = np.array(texts, dtype=object), np.array(labels)

    # a) random split of the file as it is: the same resume lands on both sides of the split
    split = StratifiedShuffleSplit(1, test_size=0.2, random_state=SEED)
    tr, te = next(split.split(raw.clean, raw.Category))
    leaky = {}
    for name, make in [("knn", knn_pipeline), ("logistic", roles.new_pipeline)]:
        model = make().fit(raw.clean.iloc[tr], raw.Category.iloc[tr])
        leaky[name] = pct((model.predict(raw.clean.iloc[te]) == raw.Category.iloc[te]).mean())
    seen = set(raw.clean.iloc[tr])
    shared = pct(np.mean([t in seen for t in raw.clean.iloc[te]]))

    # b) honest: unique resumes only, repeated stratified cross-validation
    cv = RepeatedStratifiedKFold(n_splits=FOLDS, n_repeats=REPEATS, random_state=SEED)
    out = {"knn": [], "logistic": []}
    top3, probs_all, truth_all, pred_all = [], [], [], []
    for tr, te in cv.split(texts, labels):
        for name, make in [("knn", knn_pipeline), ("logistic", roles.new_pipeline)]:
            model = make().fit(texts[tr], labels[tr])
            pred = model.predict(texts[te])
            out[name].append((np.mean(pred == labels[te]), f1_score(labels[te], pred, average="macro")))
            if name == "logistic":
                p = model.predict_proba(texts[te])
                order = np.argsort(-p, axis=1)[:, :3]
                top3.extend(labels[te][i] in model.classes_[order[i]] for i in range(len(te)))
                probs_all.extend(p.max(axis=1))
                truth_all.extend(labels[te])
                pred_all.extend(pred)
    honest = {name: {"accuracy": pct(np.mean([a for a, _ in v])), "macro_f1": pct(np.mean([f for _, f in v]))} for name, v in out.items()}
    honest["logistic"]["top3_accuracy"] = pct(np.mean(top3))
    spread = pct(np.std([a for a, _ in out["logistic"]]))

    probs, correct = np.array(probs_all), np.array(truth_all) == np.array(pred_all)
    table = []
    for threshold in (0.0, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6):
        answered = probs >= threshold
        table.append({"min_confidence": threshold, "answered_pct": pct(answered.mean()),
                      "accuracy_when_answered_pct": pct(correct[answered].mean()) if answered.any() else None})
    pd.DataFrame(table).to_csv(RESULTS / "threshold_table.csv", index=False)

    confusions = pd.Series([f"{t} -> {p}" for t, p, ok in zip(truth_all, pred_all, correct) if not ok]).value_counts().head(10)
    confusions.rename_axis("true -> predicted").rename("times").reset_index().to_csv(RESULTS / "role_confusions.csv", index=False)
    return {"rows_in_file": len(raw), "unique_resumes": int(raw.clean.nunique()), "after_removing_near_duplicates": len(texts),
            "roles": len(set(labels)), "smallest_role_size": int(pd.Series(labels).value_counts().min()),
            "random_split_of_the_file": {**leaky, "test_resumes_also_in_training_pct": shared},
            "unseen_resume_cross_validation": {"folds": FOLDS, "repeats": REPEATS, **honest, "logistic_accuracy_std": spread},
            "chosen_min_confidence": roles.MIN_CONFIDENCE,
            "at_chosen_threshold": next(r for r in table if r["min_confidence"] == roles.MIN_CONFIDENCE),
            "most_common_mistakes": confusions.head(5).to_dict()}


# --- 2. scoring ----------------------------------------------------------------------------------

DAMAGE = {
    "contact details removed": lambda t: t.replace("asha.verma@example.com | +91 98765 43210 | linkedin.com/in/ashaverma | github.com/ashaverma", ""),
    "all numbers removed": lambda t: re.sub(r"\d[\d,.]*%?", "", t),
    "section headings removed": lambda t: re.sub(r"^(SUMMARY|EXPERIENCE|PROJECTS|EDUCATION|SKILLS|ACHIEVEMENTS)$", "", t, flags=re.M),
    "vague wording": lambda t: t.replace("Built", "Responsible for building").replace("Led", "Worked on leading").replace("Reduced", "Helped with reducing"),
    "stock phrases added": lambda t: t + "\nHard-working team player and self-starter, highly motivated and passionate. References available upon request.",
    "first person ('I', 'my')": lambda t: t.replace("• Built", "• I built my").replace("• Led", "• I led my").replace("• Won", "• I won my"),
    "cut to the first 12 lines": lambda t: "\n".join(t.split("\n")[:12]),
}


def scoring_results():
    unique = pd.read_csv(roles.DATA).dropna().drop_duplicates("Resume").Resume.tolist()
    totals, started, failures = [], time.perf_counter(), 0
    for text in unique:
        doc = Document(clean(text), 0, "text")
        doc.pages = max(1, -(-len(doc.text.split()) // 500))
        try:
            totals.append(analyze(doc).total)
        except Exception:
            failures += 1
    seconds = (time.perf_counter() - started) / len(unique)

    def score(text):
        return analyze(read_document("r.txt", text.encode())).total

    strong, weak = score(samples.GOOD), score(samples.WEAK)
    rows = [{"change": name, "score": score(fn(samples.GOOD)), "drop": round(strong - score(fn(samples.GOOD)), 1)} for name, fn in DAMAGE.items()]
    pd.DataFrame(rows).to_csv(RESULTS / "damage_tests.csv", index=False)
    formats = {kind: analyze(read_document("r", fn())).total for kind, fn in
               [("text", samples.text_bytes), ("docx", samples.docx_bytes), ("pdf", samples.pdf_bytes)]}
    return {"dataset_resumes_scored": len(totals), "failures": failures, "ms_per_resume": round(1000 * seconds, 1),
            "dataset_score_mean": round(statistics.mean(totals), 1), "dataset_score_min": min(totals), "dataset_score_max": max(totals),
            "strong_sample": strong, "weak_sample": weak, "same_score_in_text_docx_pdf": len(set(formats.values())) == 1,
            "damage_tests": {r["change"]: r["drop"] for r in rows}, "damage_tests_all_lower_pct": pct(np.mean([r["drop"] > 0 for r in rows]))}


# --- 3. original checks ---------------------------------------------------------------------------

def original_checks():
    unique = pd.read_csv(roles.DATA).dropna().drop_duplicates("Resume").Resume.tolist()
    buzz = [legacy_checks.buzzwords(t) for t in unique]
    length = [legacy_checks.resume_length(t) for t in unique]
    impact = [legacy_checks.quantify_impact(t) for t in unique]
    return {"resumes": len(unique), "buzzword_check_scored_zero_pct": pct(np.mean([b == 0 for b in buzz])),
            "length_check_scored_zero_pct": pct(np.mean([x == 0 for x in length])),
            "numbers_check_scored_zero_pct": pct(np.mean([x == 0 for x in impact])),
            "note": "the original skills check returned 5 for every resume"}


# --- 4. job match ----------------------------------------------------------------------------------

def job_match_results(top_skills=25, sample=100):
    texts, labels, originals = roles.load_unique()
    labels = np.array(labels)
    per_resume = [{n for n, _ in skills.extract_skills(t)} for t in originals]
    own, other = [], []
    chosen = np.random.default_rng(SEED).choice(len(labels), size=min(sample, len(labels)), replace=False)
    for i in sorted(chosen):
        role = labels[i]
        posts = {}
        for r in set(labels):
            counts = {}
            for j, names in enumerate(per_resume):
                if j != i and labels[j] == r:
                    for n in names:
                        counts[n] = counts.get(n, 0) + 1
            best = [n for n, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top_skills]]
            posts[r] = "Requirements: " + ", ".join(best) + ". Experience with these tools is required for this role."
        scores = {r: jobmatch.match(originals[i], post)["match_percent"] for r, post in posts.items()}
        own.append(scores[role])
        other.extend(v for r, v in scores.items() if r != role)
    others_by_resume = np.array(other).reshape(len(own), -1)
    wins = np.mean([[o > x for x in row] for o, row in zip(own, others_by_resume)])
    ties = np.mean([[o == x for x in row] for o, row in zip(own, others_by_resume)])
    ranked_first = np.mean([o > row.max() for o, row in zip(own, others_by_resume)])
    return {"resumes": len(own), "posts_per_resume": others_by_resume.shape[1] + 1, "mean_match_own_role_pct": round(float(np.mean(own)), 1),
            "mean_match_other_roles_pct": round(float(others_by_resume.mean()), 1),
            "own_role_post_scores_higher_pct": pct(wins), "tied_pct": pct(ties), "own_role_post_ranked_first_pct": pct(ranked_first),
            "note": "posts are synthetic: the 25 skills most common in the other resumes of each role"}


def figure(results):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    ax = axes[0]
    r = results["roles"]
    labels = ["random split\nof the file", "unseen resumes\n(cross-validation)"]
    ax.bar(np.arange(2) - 0.18, [r["random_split_of_the_file"]["knn"], r["unseen_resume_cross_validation"]["knn"]["accuracy"]], 0.36, label="TF-IDF + k-nearest neighbours", color="#888")
    ax.bar(np.arange(2) + 0.18, [r["random_split_of_the_file"]["logistic"], r["unseen_resume_cross_validation"]["logistic"]["accuracy"]], 0.36, label="TF-IDF + logistic regression", color="#1b5fd1")
    ax.set_xticks(range(2))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Role accuracy (%)")
    ax.set_title("Role prediction")
    ax.legend(fontsize=7, loc="lower left")
    ax = axes[1]
    d = pd.read_csv(RESULTS / "damage_tests.csv")
    ax.barh(d.change, d["drop"], color="#c0392b")
    ax.invert_yaxis()
    ax.set_xlabel("Points lost (strong sample resume)")
    ax.set_title("Damaging a resume lowers its score")
    ax = axes[2]
    t = pd.read_csv(RESULTS / "threshold_table.csv")
    ax.plot(t.min_confidence, t.accuracy_when_answered_pct, marker="o", label="accuracy when it answers")
    ax.plot(t.min_confidence, t.answered_pct, marker="s", label="share of resumes it answers")
    ax.axvline(roles.MIN_CONFIDENCE, color="gray", ls="--", lw=1)
    ax.set_xlabel("Minimum confidence")
    ax.set_ylim(0, 105)
    ax.set_title("'Not sure' threshold")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(RESULTS / "results.png", dpi=150)


def main():
    RESULTS.mkdir(exist_ok=True)
    results = {"seed": SEED}
    for name, fn in [("roles", role_results), ("scoring", scoring_results), ("original_checks", original_checks), ("job_match", job_match_results)]:
        results[name] = fn()
        print(name, json.dumps(results[name], default=float)[:1500], flush=True)
    (RESULTS / "results.json").write_text(json.dumps(results, indent=2, default=float))
    figure(results)


if __name__ == "__main__":
    main()
