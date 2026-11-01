"""Suggest job roles from resume text with TF-IDF and logistic regression.

The model learns from data/resume_dataset.csv (25 roles). Duplicate and near-duplicate resumes are
removed first, because the file repeats the same resume many times and a model tested on resumes it has
already seen looks far better than it is. It is trained when first needed, so no saved model file can
go out of step with the installed library versions.
"""
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

from . import skills

DATA = Path(__file__).resolve().parent.parent / "data" / "resume_dataset.csv"
NEAR_DUPLICATE = 0.9              # cosine similarity above which two resumes of a role count as the same resume
MIN_CONFIDENCE = 0.15             # below this the model says it is not sure (chosen in evaluation/: the lowest value with 90%+ accuracy)


def tidy(text):
    text = re.sub(r"http\S+|\S+@\S+", " ", str(text))
    return re.sub(r"[^a-z0-9+#.\s]", " ", text.encode("ascii", "ignore").decode().lower())


def new_pipeline():
    return make_pipeline(TfidfVectorizer(sublinear_tf=True, stop_words="english", ngram_range=(1, 2), min_df=2, max_features=20000),
                         LogisticRegression(C=20, max_iter=3000))


def load_unique(path=DATA):
    """The dataset without repeated resumes: (cleaned texts, roles, original texts)."""
    df = pd.read_csv(path).dropna()
    df["clean"] = df["Resume"].map(tidy)
    df = df.drop_duplicates("clean").reset_index(drop=True)
    vectors = TfidfVectorizer(sublinear_tf=True, stop_words="english").fit_transform(df["clean"])
    similarity = (vectors @ vectors.T).toarray()
    keep = []
    for i in range(len(df)):
        if not any(similarity[i, j] >= NEAR_DUPLICATE and df.Category[i] == df.Category[j] for j in keep):
            keep.append(i)
    df = df.loc[keep].reset_index(drop=True)
    return df["clean"].tolist(), df["Category"].tolist(), df["Resume"].tolist()


class RoleModel:
    def __init__(self):
        texts, roles, originals = load_unique()
        self.pipeline = new_pipeline().fit(texts, roles)
        self.roles = [str(r) for r in self.pipeline.classes_]
        self.training_size = len(texts)
        self._common = self._common_skills(originals, roles)

    @staticmethod
    def _common_skills(originals, roles, share=0.3):
        """Skills that at least `share` of a role's resumes mention: {role: [(skill, share)]}."""
        per_role, size = {}, Counter(roles)
        for text, role in zip(originals, roles):
            per_role.setdefault(role, Counter()).update({name for name, _ in skills.extract_skills(text)})
        return {role: sorted(((s, n / size[role]) for s, n in counts.items() if n / size[role] >= share), key=lambda x: -x[1])
                for role, counts in per_role.items()}

    def predict(self, text, top=3):
        """([(role, probability)] best first, whether the model is confident in the first one)."""
        probs = self.pipeline.predict_proba([tidy(text)])[0]
        order = np.argsort(-probs)[:top]
        ranked = [(str(self.roles[i]), float(probs[i])) for i in order]
        return ranked, ranked[0][1] >= MIN_CONFIDENCE

    def missing_skills(self, role, text, n=10):
        have = {name.lower() for name, _ in skills.extract_skills(text)}
        return [(s, share) for s, share in self._common.get(role, []) if s.lower() not in have][:n]


@lru_cache(maxsize=1)
def model():
    return RoleModel()
