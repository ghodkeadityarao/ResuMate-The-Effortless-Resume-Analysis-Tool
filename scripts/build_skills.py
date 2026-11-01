"""Build data/skills.txt from the skill lists the project started with.

    python scripts/build_skills.py

Both source lists keep their skills in the header row of a CSV. Entries are merged, de-duplicated
and cleaned: one-word entries that are everyday English ("training", "reports", "English") are
dropped because they are not informative as skills, apart from a short list of real skills that
are also ordinary words.
"""
import csv
import re
from pathlib import Path

from spellchecker import SpellChecker

ROOT = Path(__file__).resolve().parent.parent
SOURCES = [ROOT / "data" / "source" / "skills_list_1.csv", ROOT / "data" / "source" / "skills_list_2.csv"]
COMMON_WORDS = 5000
KEEP = {"excel", "java", "python", "spark", "hive", "oracle", "swift", "ruby", "rust", "react", "go", "r", "c",
        "sql", "git", "word", "design", "testing", "sales", "marketing", "finance", "accounting", "nursing",
        "teaching", "recruitment", "networking", "security", "analytics", "statistics", "leadership", "teamwork",
        "communication", "negotiation", "budgeting", "forecasting", "auditing", "payroll", "linux", "android",
        "cloud", "agile", "scrum", "ios", "bootstrap", "angular", "windows", "kubernetes", "docker", "tableau",
        "hadoop", "automation", "debugging", "programming", "algorithms", "databases", "mysql", "mongodb"}
# Common tools the source lists lack (they are dated); checked against the list before adding.
EXTRA = ["React", "TypeScript", "Kotlin", "Go", "Rust", "Vue.js", "Next.js", "Node.js", "REST API", "CI/CD", "Terraform",
         "Ansible", "Helm", "Prometheus", "Grafana", "FastAPI", "GraphQL", "PyTorch", "Tailwind CSS", "Redux",
         "Spring Boot", "Jenkins", "GitHub Actions", "Airflow", "dbt", "Snowflake", "BigQuery", "Redis", "Elasticsearch",
         "RabbitMQ", "gRPC", "Postman", "Figma", "Power BI", "Looker", "Databricks", "Kubernetes", "Docker", "Kafka"]
JUNK = {"unnamed: 0", "technical skills", "skills", "llp", "tar", "bot", "models", "processing", "survey"}


def main():
    common = {w for w, _ in sorted(SpellChecker().word_frequency.dictionary.items(), key=lambda kv: -kv[1])[:COMMON_WORDS]}
    seen, out = set(), []
    for path in SOURCES:
        with open(path, newline="", encoding="utf-8-sig") as f:
            for name in [*next(csv.reader(f)), *EXTRA]:
                name = re.sub(r"\s+", " ", name).strip()
                key = name.lower()
                if not name or key in JUNK or key in seen or len(name) > 60 or not name.isascii():
                    continue
                if " " not in key and key in common and key not in KEEP:
                    continue
                seen.add(key)
                out.append(name)
    (ROOT / "data" / "skills.txt").write_text("\n".join(sorted(out, key=str.lower)) + "\n", encoding="utf-8")
    print(f"{len(out)} skills written")


if __name__ == "__main__":
    main()
