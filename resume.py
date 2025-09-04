import pdfplumber # type: ignore
import re
import json

# -----------------------------
# 1. Extract text from PDF
# -----------------------------
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"

    # Clean up symbols and formatting
    repls = {
        "\uf0d8": " ",
        "•": " ",
        "": " ",
        "": " ",
        "–": "-",
        "—": "-",
        "\xa0": " ",
        "\u200b": "",
    }
    for k, v in repls.items():
        text = text.replace(k, v)

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def get_lines(text):
    return [ln.strip() for ln in text.splitlines() if ln.strip()]

# -----------------------------
# 2. Personal details
# -----------------------------
def extract_personal_details(text):
    # Email
    email = None
    m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    if m: email = m.group(0)

    # Phone
    phone = None
    pm = re.search(r"(?:\+\d{1,3}\s*)?(?:\d[\s-]?){9,12}", text)
    if pm: phone = pm.group(0).strip()

    # Name = top candidate near top
    lines = get_lines(text)
    name = None
    for ln in lines[:10]:
        if len(ln) < 40 and re.search(r"[A-Za-z]", ln) and not re.search(r"@|www|http", ln):
            name = ln
            break

    # Links
    linkedin = None
    behance = None
    lm = re.search(r"(https?://[^\s]+linkedin[^\s]+)", text, re.I)
    if lm: linkedin = lm.group(1)
    bm = re.search(r"(https?://[^\s]*behance[^\s]+)", text, re.I)
    if bm: behance = bm.group(1)

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "links": {
            "linkedin": linkedin,
            "behance": behance
        }
    }

# -----------------------------
# 3. Education parser
# -----------------------------
def parse_education(text):
    lines = get_lines(text)
    edu = []
    capture = False
    for ln in lines:
        if re.search(r"education", ln, re.I):
            capture = True
            continue
        if capture:
            if re.search(r"(work experience|skills|objective|references)", ln, re.I):
                break
            if re.search(r"(Diploma|Degree|Course|Certificate|SSLC|PUC|B\.|M\.)", ln, re.I) or re.search(r"\b(20\d{2}|19\d{2})\b", ln):
                years = re.findall(r"\b(?:19|20)\d{2}\b", ln)
                start_y, end_y = None, None
                if len(years) >= 2:
                    start_y, end_y = years[0], years[1]
                elif len(years) == 1:
                    end_y = years[0]
                edu.append({
                    "details": ln.strip(),
                    "start_year": start_y,
                    "end_year": end_y
                })
    return edu

# -----------------------------
# 4. Work experience parser
# -----------------------------
import re

MONTHS = r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"

def find_date_range(s: str):
    s = s.replace("–","-").replace("—","-")
    m = re.search(fr"{MONTHS}\s+\d{{4}}\s*[-to]+\s*(?:{MONTHS}\s+\d{{4}}|Present)", s, re.I)
    if m:
        parts = re.split(r"[-to]+", m.group(0))
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
    all_my = re.findall(fr"{MONTHS}\s+\d{{4}}|Present", s, re.I)
    if len(all_my) >= 2:
        return all_my[0], all_my[1]
    if len(all_my) == 1:
        return all_my[0], None
    return None, None

def extract_project_details(block, company):
    title_match = re.search(r"Title\s*:\s*(.+)", block)
    title = title_match.group(1).strip() if title_match else None

    duration_match = re.search(
        r"Duration\s*:\s*([A-Za-z]+\s*\d{4})\s*[-–]\s*([A-Za-z]+\s*\d{4}|Present)",
        block
    )
    start_date, end_date = None, None
    if duration_match:
        start_date = duration_match.group(1)
        end_date = duration_match.group(2)

    role_match = re.search(
        r"(Technical Lead|Team Lead|Senior Engineer|Engineer|Developer|Manager|Designer|UI/UX Designer|Graphic Designer)",
        block, re.IGNORECASE
    )
    role = role_match.group(1) if role_match else None

    return {
        "company": company,
        "project_title": title,
        "role": role,
        "start_date": start_date,
        "end_date": end_date,
        "details": block.strip()
    }

import re

MONTHS = r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"

def find_date_range(s: str):
    """Extract start and end date (month year - month year / Present)."""
    s = s.replace("–", "-").replace("—", "-")
    m = re.search(fr"{MONTHS}\s+\d{{4}}\s*[-to]+\s*(?:{MONTHS}\s+\d{{4}}|Present)", s, re.I)
    if m:
        parts = re.split(r"[-to]+", m.group(0))
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
    all_my = re.findall(fr"{MONTHS}\s+\d{{4}}|Present", s, re.I)
    if len(all_my) >= 2:
        return all_my[0], all_my[1]
    if len(all_my) == 1:
        return all_my[0], None
    return None, None

def parse_experience(text):
    """Parse work experience from resumes with 'Professional Experience' or 'Work Experience'."""
    lines = text.split("\n")
    experiences = []
    capture = False
    block = []

    # --- Step 1: Capture the Experience Section ---
    for ln in lines:
        if re.search(r"(work experience|professional experience)", ln, re.I):
            capture = True
            continue
        if capture:
            if re.search(r"(education|skills|objective|references)", ln, re.I):
                break
            if ln.strip():
                block.append(ln.strip())

    if not block:
        return []

    # --- Step 2: Join the section into text ---
    section_text = " ".join(block)

    # --- Step 3: Split by company keywords or role patterns ---
    jobs = re.split(r"(?=Stress Engineer|Design Engineer|Software Engineer|UI/UX Designer|Developer|Manager)", section_text, flags=re.I)

    for job in jobs:
        job = job.strip()
        if not job:
            continue
        start, end = find_date_range(job)

        # Role
        role = None
        m = re.search(r"(Stress Engineer|Design Engineer|UI/UX Designer|Graphic Designer|Developer|Manager)", job, re.I)
        if m: role = m.group(1)

        # Company
        company = None
        m = re.search(r"(Capgemini|Quest Global|TCS|Infosys|Wipro|Accenture|Cognizant)", job, re.I)
        if m: company = m.group(1)

        experiences.append({
            "company": company,
            "role": role,
            "start_date": start,
            "end_date": end,
            "details": job
        })

    return experiences


def parse_skills(text):
    lines = text.split("\n")
    skills = []
    capture = False
    for ln in lines:
        if re.search(r"(skills|toolkit|languages)", ln, re.I):
            capture = True
            continue
        if capture and re.search(r"(experience|education|objective|references)", ln, re.I):
            break
        if capture:
            parts = re.split(r"[,/|;•\-]", ln)
            for p in parts:
                if p.strip():
                    skills.append(p.strip())
    return list(dict.fromkeys(skills))  # deduplicate

# -----------------------------
# 6. Build JSON
# -----------------------------
def build_resume_json(text):
    return {
        "personal_details": extract_personal_details(text),
        "education": parse_education(text),
        "work_experience": parse_experience_blocks(text), # type: ignore
        "skills": parse_skills(text)
    }

# -----------------------------
# 7. Main
# -----------------------------
if __name__ == "__main__":
    pdf_path = "/content/ex1 resume.pdf"  # replace with your file path
    text = extract_text_from_pdf(pdf_path)
    resume_json = build_resume_json(text)

    print(json.dumps(resume_json, indent=2, ensure_ascii=False))

    with open("resume_output.json", "w", encoding="utf-8") as f:
        json.dump(resume_json, f, indent=2, ensure_ascii=False)
