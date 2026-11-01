import io

import pytest

import samples
from app import create_app


@pytest.fixture(scope="module")
def client():
    return create_app().test_client()


def upload(client, data, name="resume.pdf", job="", path="/analyze"):
    return client.post(path, data={"resume": (io.BytesIO(data), name), "job": job}, content_type="multipart/form-data")


def test_the_home_page_loads(client):
    html = client.get("/").get_data(as_text=True)
    assert "Upload a resume" in html and 'name="resume"' in html


@pytest.mark.parametrize("make,name", [(samples.pdf_bytes, "r.pdf"), (samples.docx_bytes, "r.docx"), (samples.text_bytes, "r.txt")])
def test_every_format_gives_a_report_with_a_score_and_roles(client, make, name):
    r = upload(client, make(), name)
    html = r.get_data(as_text=True)
    assert r.status_code == 200 and "/ 100" in html and "Roles this resume fits" in html and "Contact details" in html


def test_a_job_description_adds_a_match_section(client):
    html = upload(client, samples.pdf_bytes(), job="We need a Python and Flask engineer who knows Docker, AWS and PostgreSQL for backend services.").get_data(as_text=True)
    assert "Match with the job post" in html
    assert "Match with the job post" not in upload(client, samples.pdf_bytes()).get_data(as_text=True)


@pytest.mark.parametrize("data,name,message", [(b"", "a.pdf", "empty"), (b"\x00\x01" * 500, "a.bin", "not supported"),
                                               (b"hello world", "a.txt", "30 words")])
def test_bad_uploads_show_a_message_not_an_error(client, data, name, message):
    r = upload(client, data, name)
    assert r.status_code == 400 and message in r.get_data(as_text=True)


def test_no_file_is_a_clear_error(client):
    r = client.post("/analyze", data={})
    assert r.status_code == 400 and "Choose a resume" in r.get_data(as_text=True)


def test_a_too_short_job_description_is_a_clear_error(client):
    r = upload(client, samples.pdf_bytes(), job="python")
    assert r.status_code == 400 and "job description" in r.get_data(as_text=True)


def test_the_json_api_returns_score_findings_and_roles(client):
    r = upload(client, samples.docx_bytes(), "r.docx", path="/api/analyze")
    data = r.get_json()
    assert r.status_code == 200 and 85 <= data["score"] <= 100 and len(data["findings"]) == 18
    assert sum(c["max"] for c in data["categories"].values()) == 100 and len(data["roles"]) == 3
    assert "Python" in data["skills"]


def test_api_errors_are_json(client):
    r = upload(client, b"", "a.pdf", path="/api/analyze")
    assert r.status_code == 400 and r.get_json()["error"]


def test_nothing_is_shared_between_requests(client):
    a = upload(client, samples.pdf_bytes(), path="/api/analyze").get_json()
    upload(client, samples.text_bytes(samples.GOOD.replace("Python", "Welding")), "x.txt", path="/api/analyze")
    assert upload(client, samples.pdf_bytes(), path="/api/analyze").get_json() == a


def test_text_from_the_resume_is_escaped_in_the_report(client):
    evil = samples.GOOD.replace("Built a REST API", "Built a <script>alert(1)</script> API")
    html = upload(client, evil.encode(), "evil.txt").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html


def test_an_oversize_upload_is_refused(client):
    r = upload(client, b"a " * (6 * 1024 * 1024), "big.txt")
    assert r.status_code == 413 and "larger than" in r.get_data(as_text=True)


def test_nothing_is_written_to_disk(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    upload(client, samples.pdf_bytes())
    assert list(tmp_path.iterdir()) == []
