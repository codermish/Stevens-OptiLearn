# import os
# import fitz  # PyMuPDF
# import openai
# import json
# from dotenv import load_dotenv
# from datetime import datetime
# from tqdm import tqdm

# # Load OpenAI API key
# load_dotenv()
# openai.api_key = os.getenv("OPENAI_API_KEY")

# # Paths
# PDF_DIR = "../StevensCourses"
# OUT_DIR = "./CoursesJSON"
# os.makedirs(OUT_DIR, exist_ok=True)

# def build_prompt(text: str, file_path: str) -> str:
#     return f"""
# You are an expert AI assistant that parses university course syllabi.

# Here is the course content:
# {text.strip()[:1500]}

# Strictly return ONLY a valid JSON object with this **exact structure**. DO NOT omit fields. If a field is not found, leave it blank or as an empty list.

# Use this format:
# {{
#   "textbooks": [],
#   "course_schedule": {{
#     "week1": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
#     "week2": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
#     "week3": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
#     "week4": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
#     "week5": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
#     "week6": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
#     "week7": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
#     "week8": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
#     "week9": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
#     "week10": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
#     "week11": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
#     "week12": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
#     "week13": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}}
#   }},
#   "grading": {{
#     "breakdown": {{
#       "participation": "",
#       "assignments": "",
#       "exams": "",
#       "projects": "",
#       "quizzes": "",
#       "final": ""
#     }},
#     "scale": "",
#     "policies": ""
#   }},
#   "assignments": [],
#   "policies": {{
#     "attendance": "",
#     "late_work": "",
#     "academic_integrity": "",
#     "accommodations": ""
#   }},
#   "important_dates": [],
#   "additional_info": {{
#     "course_format": "",
#     "technology_requirements": "",
#     "support_resources": ""
#   }},
#   "_metadata": {{
#     "extraction_date": "{datetime.now().isoformat()}",
#     "pdf_source": "{file_path}",
#     "source_type": "file",
#     "text_length": {len(text)},
#     "model_used": "gpt-4o-mini",
#     "course_info": {{
#       "title": "",
#       "code": "",
#       "credits": "",
#       "semester": "",
#       "year": "",
#       "instructor": {{
#         "name": "",
#         "email": "",
#         "office_hours": "",
#         "contact_info": ""
#       }}
#     }},
#     "course_description": "",
#     "learning_outcomes": [],
#     "learning_outcomes_count": 0,
#     "prerequisites": [],
#     "prerequisites_count": 0,
#     "corequisites": [],
#     "corequisites_count": 0
#   }}
# }}

# Only return the JSON. No explanations. No markdown. Format must be parseable.
# """


# def process_pdf(pdf_path):
#     try:
#         doc = fitz.open(pdf_path)
#         text = "\n".join([page.get_text() for page in doc])
#         doc.close()

#         if len(text.strip()) < 100:
#             return None, "Empty or unreadable content"

#         prompt = build_prompt(text, pdf_path)  # ✅ FIXED: added 2nd argument
#         response = openai.chat.completions.create(
#             model="gpt-4o",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.3,
#             max_tokens=4096
#         )
#         reply = response.choices[0].message.content.strip()

#         return reply, None
#     except Exception as e:
#         return None, str(e)


# # Process each PDF
# results = []
# pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]

# for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
#     full_path = os.path.join(PDF_DIR, pdf_file)
#     output_path = os.path.join(OUT_DIR, os.path.splitext(pdf_file)[0] + ".json")

#     if os.path.exists(output_path):
#         continue  # Skip if already processed

#     result, error = process_pdf(full_path)

#     if result:
#         with open(output_path, "w", encoding="utf-8") as f:
#             f.write(result)
#     else:
#         results.append({"file": pdf_file, "error": error})

# results[:5]  # Show sample failed files/errors if any

import os
import fitz  # PyMuPDF
import openai
import json
from dotenv import load_dotenv
from datetime import datetime
from tqdm import tqdm

# Load OpenAI API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Paths
PDF_DIR = "../StevensCourses"
OUT_DIR = "./CoursesJSON"
os.makedirs(OUT_DIR, exist_ok=True)

def build_prompt(text: str, file_path: str) -> str:
    return f"""
You are an expert AI assistant that parses university course syllabi. Your task is to extract ALL available information from the syllabus text and populate a comprehensive JSON structure.

IMPORTANT INSTRUCTIONS:
- Read through the ENTIRE syllabus text carefully
- Extract ALL available information, even if it appears in different sections
- For dates, preserve the original format but also note semester/year context
- For grading breakdowns, extract exact percentages or weights
- For course schedules, map content to weeks even if not explicitly numbered
- If information exists but is unclear, make your best interpretation
- Only leave fields empty if the information is genuinely not present in the text

Here is the complete course syllabus content:
{text.strip()}

Strictly return ONLY a valid JSON object with this **exact structure**. Fill in ALL fields that have corresponding information in the text above:

{{
  "textbooks": [],
  "course_schedule": {{
    "week1": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
    "week2": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
    "week3": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
    "week4": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
    "week5": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
    "week6": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
    "week7": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
    "week8": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
    "week9": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
    "week10": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
    "week11": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
    "week12": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}},
    "week13": {{"topics": [], "readings": [], "assignments": [], "due_dates": []}}
  }},
  "grading": {{
    "breakdown": {{
      "participation": "",
      "assignments": "",
      "exams": "",
      "projects": "",
      "quizzes": "",
      "final": ""
    }},
    "scale": "",
    "policies": ""
  }},
  "assignments": [],
  "policies": {{
    "attendance": "",
    "late_work": "",
    "academic_integrity": "",
    "accommodations": ""
  }},
  "important_dates": [],
  "additional_info": {{
    "course_format": "",
    "technology_requirements": "",
    "support_resources": ""
  }},
  "_metadata": {{
    "extraction_date": "{datetime.now().isoformat()}",
    "pdf_source": "{file_path}",
    "source_type": "file",
    "text_length": {len(text)},
    "model_used": "gpt-4o",
    "course_info": {{
      "title": "",
      "code": "",
      "credits": "",
      "semester": "",
      "year": "",
      "instructor": {{
        "name": "",
        "email": "",
        "office_hours": "",
        "contact_info": ""
      }}
    }},
    "course_description": "",
    "learning_outcomes": [],
    "learning_outcomes_count": 0,
    "prerequisites": [],
    "prerequisites_count": 0,
    "corequisites": [],
    "corequisites_count": 0
  }}
}}

EXTRACTION GUIDELINES:
- textbooks: Include title, author, edition, ISBN if available
- course_schedule: Map all topics, readings, assignments to appropriate weeks
- grading.breakdown: Extract exact percentages (e.g., "20%", "300 points")
- grading.scale: Include letter grade ranges (e.g., "A: 90-100%")
- assignments: List all homework, projects, papers, etc. with descriptions
- policies: Extract attendance, late work, academic integrity, accommodation policies
- important_dates: Include exam dates, project due dates, holidays, etc.
- course_info: Extract course title, code (e.g., "CS 101"), credits, semester, year
- instructor: Name, email, office hours, phone number if provided
- learning_outcomes: Extract all course objectives/learning goals
- prerequisites/corequisites: List required prior courses

Only return the JSON. No explanations. No markdown. Format must be parseable by json.loads().
"""


def process_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = "\n".join([page.get_text() for page in doc])
        doc.close()

        if len(text.strip()) < 100:
            return None, "Empty or unreadable content"

        prompt = build_prompt(text, pdf_path)
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # Lower temperature for more consistent extraction
            max_tokens=4096
        )
        reply = response.choices[0].message.content.strip()

        # Validate JSON before returning
        try:
            json.loads(reply)
            return reply, None
        except json.JSONDecodeError as e:
            return None, f"Invalid JSON generated: {str(e)}"

    except Exception as e:
        return None, str(e)


# Process each PDF
results = []
pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]

for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
    full_path = os.path.join(PDF_DIR, pdf_file)
    output_path = os.path.join(OUT_DIR, os.path.splitext(pdf_file)[0] + ".json")

    if os.path.exists(output_path):
        continue  # Skip if already processed

    result, error = process_pdf(full_path)

    if result:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result)
    else:
        results.append({"file": pdf_file, "error": error})

results[:5]  # Show sample failed files/errors if any