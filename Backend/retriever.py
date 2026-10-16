"""
Portfolio RAG retrieval module.

This module follows the logic from the Jupyter notebooks:
- Load portfolio.json
- Format portfolio sections into readable documents
- Keep each project as a separate document
- Create normalized embeddings and a FAISS inner-product index
- Detect sections/projects and retrieve relevant context
"""
import os

# Limit CPU thread usage to reduce overhead
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# ============================================================
# PATHS AND PORTFOLIO DATA
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PORTFOLIO_PATH = BASE_DIR / "data" / "portfolio.json"

with open(PORTFOLIO_PATH, "r", encoding="utf-8") as file:
    portfolio = json.load(file)


# ============================================================
# FORMAT PORTFOLIO DATA
# ============================================================

def format_value(value, indent=0):
    """Convert dictionaries and lists into readable text."""

    if isinstance(value, dict):
        lines = []

        for key, val in value.items():
            formatted_key = key.replace("_", " ").title()

            if isinstance(val, (dict, list)):
                lines.append(f"{formatted_key}:")
                nested = format_value(val, indent + 1)
                if nested:
                    lines.append(nested)
            else:
                lines.append(f"{formatted_key}: {val}")

        return "\n".join(lines)

    if isinstance(value, list):
        lines = []

        for item in value:
            if isinstance(item, dict):
                lines.append(format_value(item, indent + 1))
            else:
                lines.append(f"- {item}")

        return "\n".join(lines)

    return str(value)


def create_project_document(project):
    """Convert one project record into one self-contained document."""

    if not isinstance(project, dict):
        return str(project)

    project_name = (
        project.get("name")
        or project.get("title")
        or project.get("project")
        or "Unnamed Project"
    )

    lines = [f"Project: {project_name}", ""]

    for key, value in project.items():
        if key in ("name", "title", "project"):
            continue

        formatted_key = key.replace("_", " ").title()
        lines.append(f"{formatted_key}:")
        formatted_value = format_value(value)

        if formatted_value:
            lines.append(formatted_value)

        lines.append("")

    return "\n".join(lines).strip()


# ============================================================
# CREATE CHUNKS: ONE DOCUMENT PER SECTION, ONE PER PROJECT
# ============================================================

all_chunks = []

for section, content in portfolio.items():
    if section == "projects":
        continue

    text = format_value(content)

    if text.strip():
        all_chunks.append({
            "text": text,
            "metadata": {
                "source": "portfolio",
                "section": section,
            },
        })


projects = portfolio.get("projects", [])

if isinstance(projects, list):
    for project in projects:
        project_text = create_project_document(project)

        if isinstance(project, dict):
            project_name = (
                project.get("name")
                or project.get("title")
                or project.get("project")
                or "Unnamed Project"
            )
        else:
            project_name = "Unnamed Project"

        all_chunks.append({
            "text": project_text,
            "metadata": {
                "source": "portfolio",
                "section": "projects",
                "project": project_name,
            },
        })

elif isinstance(projects, dict):
    for project_name, project_data in projects.items():
        if isinstance(project_data, dict):
            project_copy = project_data.copy()
            project_copy.setdefault("name", project_name)
            project_text = create_project_document(project_copy)
        else:
            project_text = (
                f"Project: {project_name}\n\n{format_value(project_data)}"
            )

        all_chunks.append({
            "text": project_text,
            "metadata": {
                "source": "portfolio",
                "section": "projects",
                "project": project_name,
            },
        })


# ============================================================
# EMBEDDINGS AND FAISS INDEX
# ============================================================

embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2",
    device="cpu"
)
chunk_texts = [chunk["text"] for chunk in all_chunks]

if not chunk_texts:
    raise ValueError(
        f"No portfolio chunks were created from {PORTFOLIO_PATH}"
    )

embeddings = embedding_model.encode(
    chunk_texts,
    convert_to_numpy=True,
    normalize_embeddings=True,
).astype("float32")

index = faiss.IndexFlatIP(embeddings.shape[1])
index.add(embeddings)


# ============================================================
# PROJECT DETECTION
# ============================================================

def detect_project(query):

    q = query.lower()

    project_mapping = {
        "ux review tool": "UX Review Tool",

        "anime & movie recommendation system":
            "Anime & Movie Recommendation System",

        "anime recommendation system":
            "Anime & Movie Recommendation System",

        "movie recommendation system":
            "Anime & Movie Recommendation System",

        "spam text detector":
            "Spam Text Detector",

        "airpulse":
            "AirPulse Wireless Stethoscope - Cardiac Sense",

        "air pulse":
            "AirPulse Wireless Stethoscope - Cardiac Sense",

        "cardiac sense":
            "AirPulse Wireless Stethoscope - Cardiac Sense",

        "ai portfolio assistant":
            "AI Portfolio Assistant"
    }

    for keyword, project_name in project_mapping.items():

        if keyword in q:
            return project_name

    return None


# ============================================================
# SECTION DETECTION
# ============================================================

def detect_section(query):

    q = query.lower().strip()

    # ==================================================
    # PROJECT NAME DETECTION
    # ==================================================

    project_names = [
        "ux review tool",
        "anime & movie recommendation system",
        "anime recommendation system",
        "movie recommendation system",
        "spam text detector",
        "airpulse",
        "air pulse",
        "cardiac sense",
        "ai portfolio assistant"
    ]

    if any(project in q for project in project_names):
        return "projects"


    # ==================================================
    # PROJECTS
    # ==================================================

    project_keywords = [
        "project",
        "projects",
        "portfolio project",
        "portfolio projects",
        "what projects",
        "projects worked on",
        "projects built",
        "what did farhan build",
        "what has farhan built",
        "what did he build",
        "what has he built"
    ]

    if any(keyword in q for keyword in project_keywords):
        return "projects"


    # ==================================================
    # EXPERIENCE
    # ==================================================

    experience_keywords = [
        "experience",
        "work experience",
        "professional experience",
        "internship",
        "internships",
        "intern",
        "job experience",
        "work history",
        "where did farhan work",
        "where has farhan worked",
        "where did he work",
        "where has he worked",
        "worked at",
        "worked for",
        "employment",
        "company did farhan work",
        "kodnest"
    ]

    if any(keyword in q for keyword in experience_keywords):
        return "experience"


    # ==================================================
    # SKILLS
    # ==================================================

    skill_keywords = [
        "skills",
        "technical skills",
        "technologies",
        "technology",
        "tech stack",
        "programming languages",
        "frameworks",
        "libraries",
        "tools",
        "what can farhan do"
    ]

    if any(keyword in q for keyword in skill_keywords):
        return "skills"


    # ==================================================
    # EDUCATION
    # ==================================================

    education_keywords = [
        "education",
        "educational background",
        "degree",
        "college",
        "university",
        "school",
        "studied",
        "study",
        "cgpa",
        "academic background"
    ]

    if any(keyword in q for keyword in education_keywords):
        return "education"


    # ==================================================
    # ACHIEVEMENTS
    # ==================================================

    achievement_keywords = [
        "achievement",
        "achievements",
        "award",
        "awards",
        "won",
        "winner",
        "accomplishment",
        "accomplishments",
        "hackathon",
        "nain"
    ]

    if any(keyword in q for keyword in achievement_keywords):
        return "achievements"


    # ==================================================
    # CERTIFICATIONS
    # ==================================================

    certification_keywords = [
        "certification",
        "certifications",
        "certificate",
        "certificates",
        "workshop",
        "training",
        "credentials"
    ]

    if any(keyword in q for keyword in certification_keywords):
        return "certifications"


    # ==================================================
    # CONTACT
    # ==================================================

    contact_keywords = [
        "contact",
        "contact information",
        "email",
        "email address",
        "phone",
        "phone number",
        "mobile",
        "reach farhan",
        "how can i contact",
        "how to contact"
    ]

    if any(keyword in q for keyword in contact_keywords):
        return "contact"


    # ==================================================
    # CAREER
    # ==================================================

    career_keywords = [
        "career",
        "career goals",
        "career objective",
        "target role",
        "target roles",
        "job",
        "jobs",
        "job opportunities",
        "looking for",
        "open to",
        "what role",
        "which role"
    ]

    if any(keyword in q for keyword in career_keywords):
        return "career"


    # ==================================================
    # ABOUT
    # ==================================================

    about_keywords = [
        "about farhan",
        "about shaik farhan",
        "who is farhan",
        "who is shaik farhan",
        "introduce farhan",
        "tell me about farhan",
        "professional summary",
        "background"
    ]

    if any(keyword in q for keyword in about_keywords):
        return "about"


    # ==================================================
    # PERSONAL
    # ==================================================

    personal_keywords = [
        "name",
        "location",
        "where is farhan from",
        "where is farhan located",
        "who are you"
    ]

    if any(keyword in q for keyword in personal_keywords):
        return "personal"


    return None


# ============================================================
# SEARCH PORTFOLIO
# ============================================================

def search_portfolio(
    query,
    top_k=5,
    section_filter=None,
    project_filter=None,
):
    """Search FAISS, then apply metadata filters before returning results."""

    if not all_chunks:
        return []

    query_embedding = embedding_model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype("float32")

    # Search more candidates because metadata filtering may discard matches.
    search_k = min(max(top_k * 10, top_k), len(all_chunks))

    scores, indices = index.search(query_embedding, search_k)

    results = []

    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue

        chunk = all_chunks[int(idx)]
        metadata = chunk["metadata"]

        if (
            section_filter is not None
            and metadata.get("section") != section_filter
        ):
            continue

        if (
            project_filter is not None
            and metadata.get("project") != project_filter
        ):
            continue

        results.append({
            "score": float(score),
            "text": chunk["text"],
            "metadata": metadata,
        })

        if len(results) >= top_k:
            break

    return results


# ============================================================
# RETURN ALL PROJECTS / EXPERIENCE WHEN ASKED FOR A LIST
# ============================================================

def get_all_projects():
    """Return every project document without similarity filtering."""

    return [
        {
            "score": 1.0,
            "text": chunk["text"],
            "metadata": chunk["metadata"],
        }
        for chunk in all_chunks
        if chunk["metadata"].get("section") == "projects"
    ]


def get_all_experience():
    """Return every experience document without similarity filtering."""

    return [
        {
            "score": 1.0,
            "text": chunk["text"],
            "metadata": chunk["metadata"],
        }
        for chunk in all_chunks
        if chunk["metadata"].get("section") == "experience"
    ]


# ============================================================
# RETRIEVE CONTEXT
# ============================================================

def retrieve_context(query, top_k=7):
    """Route the query, then retrieve only relevant portfolio documents."""

    section = detect_section(query)
    project = detect_project(query)
    q = query.lower()

    project_list_patterns = [
        "what projects",
        "which projects",
        "list projects",
        "projects has farhan",
        "projects did farhan",
        "projects has he",
        "projects did he",
        "what has farhan built",
        "what did farhan build",
    ]

    if (
        section == "projects"
        and any(pattern in q for pattern in project_list_patterns)
    ):
        return get_all_projects()

    if project is not None:
        # Do not return unrelated chunks if this project cannot be found.
        return search_portfolio(
            query=query,
            top_k=top_k,
            section_filter="projects",
            project_filter=project,
        )

    experience_list_patterns = [
        "what experience",
        "work experience",
        "professional experience",
        "where did farhan work",
        "where has farhan worked",
        "where did he work",
        "where has he worked",
        "work history",
        "internships",
    ]

    if (
        section == "experience"
        and any(pattern in q for pattern in experience_list_patterns)
    ):
        return get_all_experience()

    if section is not None:
        # Keep the search inside the detected section.
        return search_portfolio(
            query=query,
            top_k=top_k,
            section_filter=section,
        )

    # For general questions without a detected section, search all sections.
    return search_portfolio(query=query, top_k=top_k)
