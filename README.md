# ResuMate: The Effortless Resume Analysis Tool

A resume analysis tool. Upload a resume and get a score out of 100 with the exact lines behind each point lost, the fixes that gain the most, the roles it fits, and, if you paste a job post, how well it matches. It uses rules, word lists and classic text statistics only: no language model and no neural network.

## What it has

- **A report you can read at a glance:** an animated score ring that counts up, a ring for each category, and a "quick wins" list ranked by points gained. Your resume sits on the right of the screen with every flagged line highlighted and the exact words underlined; opening a finding, or clicking a quick win, dims everything else and scrolls to its lines. A PDF can also be viewed as uploaded, from the browser's own copy of the file. Dark and light themes follow the device, and the layout adapts to phones.
- **Score out of 100 from 18 checks** in four categories: Impact 30, Brevity 20, Style 25, Sections 25. Every check returns its points, the evidence (the actual lines it flagged) and a fix tip. Points are earned in proportion, so a small improvement always moves the score.
  - Impact: numbers that show results, strong opening verbs, vague phrases, repetition.
  - Brevity: word count, pages, achievement line length, number of achievement lines.
  - Style: passive voice, first-person words, stock phrases, spelling, date consistency.
  - Sections: contact details, education, experience or projects, skills, summary.
- **Job-post match:** paste a job description to see a match percentage, the skills and keywords the resume covers and the ones it lacks.
- **Role suggestions:** the top three roles from 25, with a confidence, and the skills common in that role's resumes that yours does not mention. It says "not sure" when confidence is low.
- **Skill detection:** a vocabulary of about 37,000 skills, matched as exact phrases (including `C++`, `C#`, `Node.js`).
- **Formats:** PDF, Word (.docx) and plain text up to 5 MB, recognised by content. Scanned images, password-protected PDFs and old `.doc` files get a plain message saying what to do.
- **Private and stateless:** a file is read in memory, analysed and forgotten. Nothing is written to disk, nothing is shared between visitors, and there is no login or stored password.
- **Web page and JSON API** (`POST /api/analyze`).

## How it works

- **Checks:** regular expressions (numbers, dates, contact details), word lists (strong verbs, vague phrases, stock phrases), heading detection for sections, and a dictionary spell check that ignores tools and URLs. Passive voice is a rule: a form of "to be" followed by a past participle.
- **Job match:** TF-IDF weights, learnt from the resume dataset so everyday resume words count for little, pick the heaviest words and word pairs of the post. The match is a weighted share of the post's skills and keywords found in the resume.
- **Role model:** TF-IDF and logistic regression, trained at start-up on the unique resumes of `data/resume_dataset.csv`. Repeated and near-identical resumes are removed first.

## Results

All numbers come from `evaluation/`; the output is in `evaluation/results/`.

**Role model.** The dataset has 962 rows but only 167 unique resumes (166 after removing near-identical ones), over 25 roles.

| Test | TF-IDF + k-nearest neighbours | TF-IDF + logistic regression |
|---|---|---|
| Random split of the file as it is (98.4% of test resumes also appear in training) | 97.4% | 100% |
| Unseen resumes (3-fold cross-validation repeated 5 times, unique resumes only) | 80.8% | **83.6%** (±5.2 between folds) |

On unseen resumes the chosen model has 78.5% macro-F1, and the right role is among its top three 95.1% of the time. With the "not sure" threshold at 15% confidence it answers 67.6% of resumes and is right 92.7% of the time when it does. The commonest mistakes are Web Designing read as Java Developer, and DevOps Engineer read as Database or Java Developer. With 166 resumes and a smallest role of 3, these estimates are rough.

**Scoring.**

| Measure | Result |
|---|---|
| Robustness | All 167 unique dataset resumes scored with no failures, 117 ms each |
| Same resume, three formats | Identical score as text, Word and PDF |
| Deliberate damage to a strong sample resume (96.0) | Every one of 7 changes lowers the score: cut to 12 lines −25.5, section headings removed −17.2, numbers removed −16.9, contact details removed −8.3, stock phrases added −5.5, vague wording −4.3, first person −3.8 |
| Weak sample resume | 44.5 |

**Original checks.** On the 167 unique dataset resumes the original buzzword check scored zero for 43.1% (it penalised strong verbs and matched words like "a" and "on"), the length check scored zero for 71.3%, and the numbers check scored zero for 82.6%. The original skills check returned 5 for every resume.

**Job match.** For 100 resumes, each compared with 25 synthetic posts (the skills most common in each role's other resumes), the post of the resume's own role scored higher than another role's post in 89.4% of comparisons (5.6% ties) and ranked first among all 25 for 55% of resumes. Mean match was 33.2% for the own role against 11.2% for the others.

## Limits

- The score is built from widely used resume rules of thumb. It has not been validated against hiring decisions and does not model any particular applicant tracking system.
- The dataset resumes are anonymised (no names or contact details), so they score low on contact details and are used to test robustness, not to calibrate the score.
- The role model learned from 166 mostly technical resumes in 25 roles. It is English only, and other fields are not covered.
- The job match counts words and skills; it does not understand meaning. Its test uses synthetic posts, not real ones.
- The skill vocabulary comes from older lists plus a short list of added tools, so it is noisy for some terms.
- The spell check uses US English and flags British spellings. Resumes with columns or graphics may have text read in an odd order. Layout and design are not judged.

## Repository

| Path | Contents |
|---|---|
| `app.py`, `templates/`, `static/` | Flask app, pages, styles and the front-end script (upload without leaving the page, loading screen, score count-up, highlight focus) |
| `resumate/extract.py` | Reads PDF, Word and text from bytes |
| `resumate/checks.py`, `scoring.py` | The 18 checks and the score |
| `resumate/textutils.py`, `wordlists.py`, `highlight.py` | Sections, achievement lines, word lists, marking flagged lines and words for display |
| `resumate/skills.py`, `jobmatch.py`, `roles.py` | Skill detection, job match, role model |
| `data/` | Resume dataset, skill vocabulary and the two skill lists it is built from |
| `scripts/build_skills.py` | Builds the skill vocabulary |
| `evaluation/` | The evaluation, its results and figure, and three of the original checks it compares with |
| `tests/` | 75 tests: each check, file reading, scoring and damage, highlighting, job match, role model, and the app including errors, escaping and no stored files |
