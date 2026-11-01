"""A realistic (fictional) resume and helpers that build it as text, PDF and Word files."""
import io

GOOD = """Asha Verma
asha.verma@example.com | +91 98765 43210 | linkedin.com/in/ashaverma | github.com/ashaverma

SUMMARY
Backend engineer with three years of experience building data services in Python. Focused on reliable APIs, clear code and measurable performance gains.

EXPERIENCE
Software Engineer, Northwind Labs, Pune
Jun 2022 - Present
• Built a REST API in Flask serving 120,000 requests a day, cutting average response time by 38%.
• Reduced monthly cloud cost by 22% by moving batch jobs to scheduled containers on AWS.
• Automated 14 manual reports with Python and pandas, saving the finance team 30 hours a month.
• Led a team of 4 engineers to migrate a MySQL database to PostgreSQL with zero downtime.
• Designed unit and integration tests with pytest, raising coverage from 48% to 91%.
• Mentored 3 interns who all received full-time offers.

Software Intern, Contoso Systems, Mumbai
Jan 2022 - May 2022
• Developed a Django dashboard used by 60 support agents to track open tickets.
• Optimized 9 slow SQL queries, reducing page load time from 4.2 seconds to 1.1 seconds.
• Documented 25 internal endpoints so new engineers could start without help.

PROJECTS
• Created a resume scoring tool in Python that analysed 500 resumes and flagged 12 common mistakes.
• Deployed a price tracker with Docker and Git workflows that checked 2,000 products every night.
• Implemented a recommender using scikit-learn that improved click-through by 15% in an A/B test.

EDUCATION
B.Tech in Computer Engineering, Savitribai Phule Pune University, 2018 - 2022, CGPA 8.9

SKILLS
Python, SQL, Flask, Django, pandas, numpy, scikit-learn, Docker, Git, AWS, PostgreSQL, MySQL, pytest, Linux, REST APIs

ACHIEVEMENTS
• Won first place among 40 teams at the Smart India Hackathon 2021.
• Published a 6 page guide on API testing read by 3,000 engineers.
"""


def text_bytes(text=GOOD):
    return text.encode("utf-8")


def docx_bytes(text=GOOD):
    import docx
    d = docx.Document()
    for line in text.split("\n"):
        d.add_paragraph(line)
    out = io.BytesIO()
    d.save(out)
    return out.getvalue()


def pdf_bytes(text=GOOD):
    from fpdf import FPDF
    pdf = FPDF()
    pdf.set_auto_page_break(True, 15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    for line in text.replace("•", "-").split("\n"):
        pdf.multi_cell(0, 5, line or " ", new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


WEAK = """John Smith
Objective
I am a hard-working team player looking for a challenging position where I can use my skills.

Experience
I was responsible for helping with the website. I worked on many tasks and assisted with reports.
The reports were written by me and the tasks were handled by the team.
Worked on the database. Responsible for testing.

Education
BSc Computer Science 2020

Skills
Computer, Internet, Microsoft word
"""
