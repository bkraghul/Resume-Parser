# Resume Parser

**Resume Parser** is a Python-based project designed to automatically extract structured information from resumes in PDF format. It leverages **regular expressions**, **natural language processing**, and **date parsing** techniques to identify key candidate details such as contact information, education, work experience, skills, and more.  

This project is particularly useful for **HR teams, recruiters, and job portal platforms** to streamline the candidate screening process by converting unstructured resume data into a structured, machine-readable format.

## Features
- Extracts **Name, Email, Phone Number** from resumes.
- Detects **educational qualifications** and **experience durations**.
- Handles **PDF resumes** using `pdfplumber`.
- Supports **date parsing** for experience timelines.
- Outputs parsed data in **JSON format** for easy integration with databases or other applications.

## Technologies Used
- Python 3.x
- `pdfplumber` (PDF text extraction)
- `re` (regular expressions for pattern matching)
- `dateparser` (parsing dates from text)
- `json` (structured output)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/bkraghul/Resume-Parser.git
cd Resume-Parser

## 
