"""
Resume Parser (ML/NLP based, local only)
---------------------------------------
- Uses spaCy for NER (names, orgs, locations, dates)
- Uses regex + heuristics for emails, phones, skills
- Supports PDF, DOCX, TXT
- Outputs structured JSON
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional

import pdfplumber
import docx
import spacy

# -----------------------------
# Load spaCy NLP model
# -----------------------------
# Load the spaCy model, handling potential errors if not installed
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Please install spaCy English model: python -m spacy download en_core_web_sm")
    nlp = None


# -----------------------------
# Regex patterns
# -----------------------------
EMAIL_RX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RX = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")
LINKEDIN_RX = re.compile(r"(https?://)?(www\.)?linkedin\.com/in/[A-Za-z0-9\-_%]+")
YEAR_RX = re.compile(r"(19|20)\d{2}")

COMMON_SKILLS = {
    "python","java","c++","c#","javascript","typescript","react","angular","vue",
    "node","sql","mysql","postgresql","mongodb",
    "aws","azure","gcp","docker","kubernetes","linux","git",
    "django","flask","spring","fastapi","pandas","numpy","matplotlib","seaborn",
    "tensorflow","pytorch","nlp","machine learning","deep learning","html","css"
}

# -----------------------------
# Data classes
# -----------------------------
@dataclass
class Contact:
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    location: Optional[str] = None

@dataclass
class Education:
    degree: Optional[str] = None
    institution: Optional[str] = None
    years: Optional[str] = None

@dataclass
class Experience:
    title: Optional[str] = None
    company: Optional[str] = None
    years: Optional[str] = None
    description: Optional[str] = None

@dataclass
class Resume:
    contact: Contact
    education: List[Education]
    experience: List[Experience]
    skills: List[str]

# -----------------------------
# Text Extraction
# -----------------------------
def extract_text_from_pdf(path: str) -> str:
    try:
        text_parts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                txt = page.extract_text()
                if txt:
                    text_parts.append(txt)
        return "\n".join(text_parts).strip()
    except ImportError:
        print("pdfplumber not installed. Please install it using: !pip install pdfplumber")
        return ""
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""


def extract_text_from_docx(path: str) -> str:
    try:
        doc = docx.Document(path)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except ImportError:
        print("python-docx not installed. Please install it using: !pip install python-docx")
        return ""
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return ""


def extract_text(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(path)
    elif ext == ".docx":
        return extract_text_from_docx(path)
    elif ext == ".txt":
        try:
            return Path(path).read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"Error reading text file: {e}")
            return ""
    else:
        print(f"Unsupported file type: {ext}")
        return ""

# -----------------------------
# Extraction Functions
# -----------------------------
def extract_contact(text: str) -> Contact:
    email_match = EMAIL_RX.search(text)
    phone_match = PHONE_RX.search(text)
    linkedin_match = LINKEDIN_RX.search(text)

    doc = nlp(text[:1000])  # only first part for speed
    name = None
    location = None
    for ent in doc.ents:
        if not name and ent.label_ == "PERSON":
            name = ent.text
        if not location and ent.label_ in ("GPE","LOC"):
            location = ent.text

    return Contact(
        name=name,
        email=email_match.group(0) if email_match else None,
        phone=phone_match.group(0) if phone_match else None,
        linkedin=linkedin_match.group(0) if linkedin_match else None,
        location=location
    )

def extract_education(text: str) -> List[Education]:
    lines = text.splitlines()
    education = []
    for line in lines:
        if any(word in line.lower() for word in ["university","college","institute","school","bachelor","master","phd","mba"]):
            years = " - ".join(YEAR_RX.findall(line)) if YEAR_RX.findall(line) else None
            degree = None
            for keyword in ["bachelor","master","phd","mba","b.sc","m.sc","b.tech","m.tech"]:
                if keyword in line.lower():
                    degree = keyword.upper()
                    break
            education.append(Education(degree=degree, institution=line.strip(), years=years))
    return education

def extract_experience(text: str) -> List[Experience]:
    lines = text.splitlines()
    experience = []
    for line in lines:
        if any(word in line.lower() for word in ["intern","engineer","developer","manager","consultant","analyst","lead"]):
            years = " - ".join(YEAR_RX.findall(line)) if YEAR_RX.findall(line) else None
            experience.append(Experience(title=line.strip(), company=None, years=years, description=line.strip()))
    return experience

def extract_skills(text: str) -> List[str]:
    text_lower = text.lower()
    found = set()
    for skill in COMMON_SKILLS:
        if re.search(r"\b" + re.escape(skill.lower()) + r"\b", text_lower):
            found.add(skill)
    return sorted(found)

# -----------------------------
# Main parse function
# -----------------------------
def parse_resume(path: str) -> dict:
    text = extract_text(path)
    if not text:
        return {}
    contact = extract_contact(text)
    education = extract_education(text)
    experience = extract_experience(text)
    skills = extract_skills(text)

    resume = Resume(contact=contact, education=education, experience=experience, skills=skills)
    return {
        "contact": asdict(resume.contact),
        "education": [asdict(e) for e in resume.education],
        "experience": [asdict(e) for e in resume.experience],
        "skills": resume.skills
    }

# -----------------------------
# Main execution block for Colab
# -----------------------------

# Replace with your PDF path
# Use different resume files to test robustness
resume_file_path = '/content/Naukri_YogeshPopatChungde[2y_10m].pdf'



if __name__ == "__main__":
    # This block is intended for standalone script execution.
    # When running in Colab, the code outside this block will be executed directly.
    # We will move the execution logic outside this block for Colab compatibility.
    pass # Keep the __main__ block empty or remove it if preferred.

# --- Move execution logic here for Colab ---
# Check if nlp model was loaded successfully
if nlp:
    result = parse_resume(resume_file_path)
    print(json.dumps(result, indent=2))
else:
    print("spaCy NLP model not loaded. Please address the loading issue.")
