"""Word lists the checks use."""

# Verbs that make a strong opening for an achievement line.
STRONG_VERBS = set("""
achieved accelerated acquired adapted administered advised aligned analyzed architected assembled assessed audited
authored automated boosted built calculated centralized championed clarified coached collaborated compiled completed
composed conducted configured consolidated constructed consulted converted coordinated created customized debugged
decreased defined delivered deployed derived designed detected developed devised diagnosed directed discovered
documented doubled drove earned edited eliminated enabled encouraged engineered enhanced established estimated
evaluated examined exceeded executed expanded facilitated forecasted formulated founded generated guided identified
implemented improved increased initiated innovated inspected installed integrated interpreted introduced invented
investigated launched led leveraged maintained managed mapped maximized measured mentored merged migrated minimized
modeled modernized monitored motivated negotiated operated optimized orchestrated organized outperformed overhauled
oversaw partnered performed pioneered planned presented prioritized processed produced programmed promoted proposed
prototyped published reduced redesigned refactored refined rehabilitated released remodeled replaced reported
researched resolved restructured retrieved reviewed revised saved scaled scheduled secured selected shipped simplified
solved spearheaded standardized streamlined strengthened supervised supported surpassed synthesized tailored taught
tested trained transformed translated troubleshot unified updated upgraded validated visualized won wrote
""".split())

# Openings and phrases that say little about what the person actually did.
WEAK_PHRASES = [
    "responsible for", "worked on", "work on", "helped with", "helped to", "helped in", "assisted with", "assisted in",
    "involved in", "participated in", "duties included", "tasked with", "in charge of", "was part of", "was a part of",
    "handled", "dealt with", "exposure to", "familiar with", "knowledge of", "tried to",
]

# Stock phrases that do not set one resume apart from another.
CLICHES = [
    "team player", "hard-working", "hardworking", "hard working", "results-driven", "results driven", "self-starter",
    "self starter", "detail-oriented", "detail oriented", "highly motivated", "dynamic", "proactive", "go-getter",
    "think outside the box", "outside-the-box", "passionate", "excellent communication skills", "good communication skills",
    "creative problem solver", "ability to work under pressure", "works well under pressure", "fast learner",
    "quick learner", "references available upon request", "references available on request", "synergy",
    "i am writing to apply", "seeking a challenging", "challenging position", "dedicated professional",
]

IRREGULAR_PARTICIPLES = (
    "built|made|done|given|taken|written|known|seen|shown|chosen|driven|run|held|led|sent|set|put|found|kept|"
    "begun|broken|brought|bought|caught|drawn|eaten|fallen|felt|gone|grown|heard|hidden|left|lost|met|paid|read|"
    "sold|spoken|spent|stolen|taught|told|thought|understood|won|worn"
)

# Heading text (lower case) that opens each kind of section.
HEADINGS = {
    "summary": ["summary", "professional summary", "career summary", "executive summary", "objective",
                "career objective", "professional objective", "profile", "professional profile", "about me", "about"],
    "education": ["education", "education details", "educational qualification", "educational qualifications",
                  "academic background", "academics", "academic qualifications", "qualifications", "education and training"],
    "experience": ["experience", "work experience", "professional experience", "employment", "employment history",
                   "work history", "internship", "internships", "internship experience", "experience details",
                   "relevant experience", "career history", "company details"],
    "projects": ["projects", "academic projects", "personal projects", "key projects", "project details",
                 "projects undertaken", "major projects"],
    "skills": ["skills", "technical skills", "key skills", "core skills", "core competencies", "skill set",
               "technical expertise", "skills details", "areas of expertise", "technologies", "technical proficiency",
               "skills and abilities"],
    "achievements": ["achievements", "accomplishments", "awards", "honors", "certifications", "certificates",
                     "extracurricular activities", "activities", "publications"],
}
