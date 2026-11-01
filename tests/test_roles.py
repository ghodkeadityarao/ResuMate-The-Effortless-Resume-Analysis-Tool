import pytest

from resumate import roles


@pytest.fixture(scope="module")
def model():
    return roles.model()


def test_the_model_trains_on_unique_resumes_only(model):
    import pandas as pd
    raw = pd.read_csv(roles.DATA)
    assert len(raw) == 962 and model.training_size < raw.Resume.nunique() + 1 and model.training_size <= 167
    assert len(model.roles) == 25


def test_prediction_returns_three_roles_with_probabilities(model):
    ranked, confident = model.predict("Python developer with Django, Flask, pandas, numpy and REST API experience. Built backend services.")
    assert len(ranked) == 3 and ranked[0][1] >= ranked[1][1] >= ranked[2][1] and sum(p for _, p in ranked) <= 1.0001
    assert all(isinstance(name, str) for name, _ in ranked)


def test_a_data_science_resume_is_recognised(model):
    text = ("Data scientist skilled in machine learning, regression, random forest, scikit-learn, pandas, tensorflow, "
            "natural language processing, statistics, Tableau and SQL. Built classification models and forecasting dashboards.")
    ranked, confident = model.predict(text)
    assert ranked[0][0] == "Data Science" and confident


def test_text_with_no_signal_is_not_confident(model):
    ranked, confident = model.predict("lorem ipsum dolor sit amet consectetur adipiscing elit " * 5)
    assert not confident


def test_missing_skills_lists_common_skills_the_resume_lacks(model):
    missing = [s for s, _ in model.missing_skills("Data Science", "I know Excel only.")]
    assert missing and all(isinstance(s, str) for s in missing)
    have = [s for s, _ in model.missing_skills("Data Science", "machine learning " + " ".join(missing[:3]))]
    assert not set(missing[:3]) & set(have)
