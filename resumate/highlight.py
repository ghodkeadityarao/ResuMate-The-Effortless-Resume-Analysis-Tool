"""Turn the resume text into display lines with the flagged lines and words marked.

Each output line is a dict with html, flags, heading and blank: `html` is safe to insert in a page (everything from the resume is escaped)
and `flags` are the checks that flagged the line, so the page can light up the lines of one finding.
"""
import re

from markupsafe import Markup, escape

from .textutils import is_heading


def render(text, findings):
    out = []
    for line in text.split("\n"):
        keys = [f.key for f in findings if any(s and s in line for s in f.lines)]
        spans = []
        for f in findings:
            for word in f.words:
                for m in re.finditer(r"(?<!\w)" + re.escape(word) + r"(?!\w)", line, re.IGNORECASE):
                    spans.append((m.start(), m.end(), f.key))
        spans.sort()
        parts, position = [], 0
        for start, end, key in spans:
            if start < position:                                  # overlaps one already marked
                continue
            parts.append(escape(line[position:start]))
            parts.append(Markup('<mark data-f="{}">{}</mark>').format(key, line[start:end]))
            position = end
            if key not in keys:
                keys.append(key)
        parts.append(escape(line[position:]))
        out.append({"html": Markup("").join(parts), "flags": " ".join(keys), "heading": is_heading(line) and len(line.split()) <= 6,
                    "blank": not line.strip()})
    return out
