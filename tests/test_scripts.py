import json
import os
import subprocess
import sys

BASE_ENV = {**os.environ, "MOCK_MODE": "1"}
PYTHON = sys.executable
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_script(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, env=BASE_ENV, cwd=ROOT)


def assert_valid_output(stdout, expected_source, expected_guid):
    data = json.loads(stdout)
    assert data["user_guid"] == expected_guid
    assert data["source"] == expected_source
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0
    for item in data["items"]:
        for field in ("title", "body", "published_at", "source_url"):
            assert field in item, f"Campo '{field}' ausente no item: {item}"


def test_linkedin_mock():
    r = run_script([PYTHON, "scrapingdog-linkedIn.py", "--user-guid", "guid-teste", "--profile-url", "https://linkedin.com/in/test"])
    assert r.returncode == 0, f"stderr: {r.stderr}"
    assert_valid_output(r.stdout, "linkedin", "guid-teste")


def test_scholar_mock():
    r = run_script([PYTHON, "scrapingdog-academico.py", "--user-guid", "guid-teste", "--author", "Autor Teste"])
    assert r.returncode == 0, f"stderr: {r.stderr}"
    assert_valid_output(r.stdout, "google_scholar", "guid-teste")


def test_lattes_mock():
    r = run_script([PYTHON, "lattes.py", "--user-guid", "guid-teste", "--url", "https://lattes.cnpq.br/mock"])
    assert r.returncode == 0, f"stderr: {r.stderr}"
    assert_valid_output(r.stdout, "lattes", "guid-teste")
