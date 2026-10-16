
"""
Lightweight portfolio retrieval for Render free tier.
No FAISS, PyTorch, or Sentence Transformers required.
Supports dynamic project names, section aliases, and global fallback.
"""

import json
import re
from pathlib import Path


# ============================================================
# LOAD PORTFOLIO DATA
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PORTFOLIO_PATH = BASE_DIR / "data" / "portfolio.json"

with open(PORTFOLIO_PATH, "r", encoding="utf-8") as file:
    portfolio = json.load(file)


# ============================================================
# FORMAT PORTFOLIO DATA
# ============================================================

def format_value(value):
    """Convert nested dictionaries and lists into readable text."""
    if isinstance(value, dict):
        lines = []

        for key, item in value.items():
            label = key.replace("_", " ").replace("-", " ").title()
            formatted = format_value(item)

            if formatted:
                lines.append(f"{label}: {formatted}")

        return "\n".join(lines)

    if isinstance(value, list):
        return "\n".join(
            f"- {format_value(item)}"
            for item in value
            if item is not None
        )

    return str(value).strip() if value is not None else ""


def create_project_document(project):
    """Create a readable document for an individual project."""
    if not isinstance(project, dict):
        return str(project)

    name = (
        project.get("name")
        or project.get("title")
        or project.get("project")
        or "Unnamed Project"
    )

    details = {
        key: value
        for key, value in project.items()
        if key not in ("name", "title", "project")
    }

    return f"Project: {name}\n{format_value(details)}"


# ============================================================
# CREATE SEARCHABLE DOCUMENTS
# ============================================================

all_chunks = []


def add_chunk(text, section, project_name=None):
    """Add a document with consistent metadata."""
    text = text.strip()

    if not text:
        return

    metadata = {
        "source": "portfolio",
        "section": section,
    }

    if project_name:
        metadata["project"] = project_name

    all_chunks.append({
        "text": text,
        "metadata": metadata,
    })


for section, content in portfolio.items():
    if section == "projects":
        continue

    add_chunk(
        text=format_value(content),
        section=section,
    )


projects = portfolio.get("projects", [])

if isinstance(projects, list):
    for project in projects:
        if isinstance(project, dict):
            project_name = (
                project.get("name")
                or project.get("title")
                or project.get("project")
                or "Unnamed Project"
            )
        else:
            project_name = "Unnamed Project"

        add_chunk(
            text=create_project_document(project),
            section="projects",
            project_name=project_name,
        )

elif isinstance(projects, dict):
    for project_name, details in projects.items():
        if isinstance(details, dict):
            project_data = dict(details)
            project_data.setdefault("name", project_name)
        else:
            project_data = {
                "name": project_name,
                "details": details,
            }

        add_chunk(
            text=create_project_document(project_data),
            section="projects",
            project_name=project_name,
        )


# ============================================================
# TEXT NORMALIZATION AND TOKENIZATION
# ============================================================

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "am",
    "what", "who", "where", "when", "why", "how", "which",
    "tell", "me", "about", "please", "can", "you", "your",
    "his", "her", "he", "she", "i", "and", "or", "of",
    "to", "in", "on", "for", "with", "do", "does", "did",
    "has", "have", "had", "my", "he's", "it's", "their",
    "this", "that", "these", "those", "would", "could",
    "should", "explain", "describe", "give", "show",
    "list", "me", "know", "much", "many", "some",
    "please", "farhan", "shaik",
}


def normalize_text(text):
    """Normalize punctuation and spacing for matching."""
    text = str(text).lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[-_/]+", " ", text)
    text = re.sub(r"[^a-z0-9+#.\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text):
    """Return meaningful words for keyword matching."""
    words = re.findall(r"[a-zA-Z0-9+#.]+", text.lower())

    return {
        word
        for word in words
        if word not in STOPWORDS and len(word) > 1
    }


# ============================================================
# SECTION ALIASES
# ============================================================

SECTION_ALIASES = {
    "about": [
        "about farhan",
        "about shaik farhan",
        "who is farhan",
        "who is shaik farhan",
        "introduce farhan",
        "tell me about yourself",
        "tell me about farhan",
        "professional summary",
        "profile summary",
        "personal introduction",
        "biography",
    ],
    "personal": [
        "full name",
        "your name",
        "his name",
        "where is farhan from",
        "where does farhan come from",
        "hometown",
        "location",
        "personal details",
    ],
    "education": [
        "education",
        "educational background",
        "academic background",
        "degree",
        "college",
        "university",
        "school",
        "qualification",
        "qualifications",
        "where did farhan study",
        "what did farhan study",
        "cgpa",
        "marks",
        "percentage",
    ],
    "skills": [
        "skills",
        "technical skills",
        "soft skills",
        "technical knowledge",
        "technologies",
        "technology stack",
        "tech stack",
        "programming languages",
        "frameworks",
        "libraries",
        "tools",
        "what can farhan do",
        "what technologies does he know",
        "areas of expertise",
    ],
    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "job experience",
        "work history",
        "employment history",
        "internship",
        "internships",
        "previous jobs",
        "where did farhan work",
        "where has farhan worked",
        "kodnest",
    ],
    "projects": [
        "project",
        "projects",
        "portfolio projects",
        "projects built",
        "projects developed",
        "projects created",
        "what has farhan built",
        "what did farhan build",
        "list all projects",
    ],
    "achievements": [
        "achievements",
        "achievement",
        "awards",
        "award",
        "accomplishments",
        "hackathon",
        "funding",
        "nain",
        "what has farhan won",
    ],
    "certifications": [
        "certifications",
        "certification",
        "certificates",
        "certificate",
        "credentials",
        "training",
        "professional badges",
    ],
    "contact": [
        "contact",
        "contact details",
        "contact information",
        "email address",
        "email",
        "phone number",
        "mobile number",
        "how can i contact farhan",
        "how do i reach farhan",
    ],
    "career": [
        "career",
        "career goals",
        "career objective",
        "career aspirations",
        "target role",
        "target job",
        "job opportunities",
        "looking for a job",
        "what role is farhan looking for",
    ],
}


def detect_section(query):
    """Identify the portfolio section using aliases and keywords."""
    q = normalize_text(query)

    # Exact aliases and phrases take priority.
    for section, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            if normalize_text(alias) in q:
                return section

    # Match actual section names from portfolio.json dynamically.
    for section in portfolio:
        normalized_section = normalize_text(section)
        if normalized_section and normalized_section in q:
            return section

    # General keyword fallback for common variations.
    section_keywords = {
        "about": {"introduce", "introduction", "biography", "profile"},
        "personal": {"name", "hometown", "location"},
        "education": {
            "studied", "study", "degree", "college", "university",
            "cgpa", "qualification", "academic",
        },
        "skills": {
            "skill", "skills", "technology", "technologies",
            "programming", "framework", "library", "libraries",
        },
        "experience": {
            "intern", "internship", "employment", "experience",
        },
        "projects": {
            "project", "projects", "built", "developed", "created",
        },
        "achievements": {
            "achievement", "achievements", "award", "awards",
            "hackathon", "funding",
        },
        "certifications": {
            "certificate", "certification", "certifications", "badge",
        },
        "contact": {"email", "phone", "contact", "mobile"},
        "career": {"career", "job", "jobs", "role", "opportunities"},
    }

    query_words = set(q.split())

    for section, keywords in section_keywords.items():
        if query_words & keywords:
            return section

    return None


# ============================================================
# DYNAMIC PROJECT ALIASES
# ============================================================

# These are optional extra aliases for project names that might
# be described differently in a visitor's question.
EXTRA_PROJECT_ALIASES = {
    "airpulse": [
        "air pulse",
        "cardiac sense",
        "wireless stethoscope",
        "digital stethoscope",
        "smart stethoscope",
        "heart sound project",
    ],
    "spam text detector": [
        "spam detector",
        "spam message classifier",
        "spam detection",
    ],
    "ux review tool": [
        "ux reviewer",
        "ui ux review",
        "website design review",
        "design feedback tool",
    ],
    "anime and movie recommendation system": [
        "anime recommendation",
        "movie recommendation",
        "recommendation system",
        "recommendation engine",
    ],
    "ai portfolio assistant": [
        "portfolio chatbot",
        "portfolio assistant",
        "portfolio ai chatbot",
    ],
}


def detect_project(query):
    """Find projects using names from JSON and optional aliases."""
    q = normalize_text(query)

    # First use project names loaded dynamically from JSON.
    project_chunks = [
        chunk for chunk in all_chunks
        if chunk["metadata"].get("section") == "projects"
    ]

    for chunk in project_chunks:
        project_name = chunk["metadata"].get("project", "")
        normalized_name = normalize_text(project_name)

        if normalized_name and normalized_name in q:
            return project_name

    # Then check additional names and descriptions.
    for alias_group, aliases in EXTRA_PROJECT_ALIASES.items():
        candidates = [alias_group] + aliases

        if any(normalize_text(alias) in q for alias in candidates):
            # Resolve the alias group against actual project names.
            for chunk in project_chunks:
                project_name = chunk["metadata"].get("project", "")
                name = normalize_text(project_name)

                if (
                    normalize_text(alias_group) in name
                    or name in normalize_text(alias_group)
                ):
                    return project_name

                if any(
                    normalize_text(alias) in name
                    or name in normalize_text(alias)
                    for alias in aliases
                ):
                    return project_name

            # Use a partial project-name match as a final fallback.
            alias_words = tokenize(alias_group)

            for chunk in project_chunks:
                project_name = chunk["metadata"].get("project", "")
                if alias_words & tokenize(project_name):
                    return project_name

    return None


# ============================================================
# SEARCH AND RANK DOCUMENTS
# ============================================================

def search_portfolio(
    query,
    top_k=5,
    section_filter=None,
    project_filter=None,
):
    """Rank documents by keyword overlap."""
    query_words = tokenize(query)

    if not query_words:
        return []

    scored = []

    for chunk in all_chunks:
        metadata = chunk["metadata"]

        if (
            section_filter is not None
            and metadata.get("section") != section_filter
        ):
            continue

        if project_filter is not None:
            actual_project = normalize_text(
                metadata.get("project", "")
            )
            wanted_project = normalize_text(project_filter)

            if (
                wanted_project not in actual_project
                and actual_project not in wanted_project
            ):
                continue

        searchable_text = (
            metadata.get("section", "")
            + " "
            + metadata.get("project", "")
            + " "
            + chunk["text"]
        )

        document_words = tokenize(searchable_text)
        overlap = query_words & document_words

        if not overlap:
            continue

        # Prefer documents matching more of the question.
        score = len(overlap) / (len(query_words) ** 0.5)

        # Give a small boost when the query contains the project name.
        project_name = normalize_text(metadata.get("project", ""))
        normalized_query = normalize_text(query)

        if project_name and project_name in normalized_query:
            score += 2.0

        scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)

    results = []
    for score, chunk in scored[:top_k]:
        results.append({
            "score": float(score),
            "text": chunk["text"],
            "metadata": chunk["metadata"],
        })

    return results


def get_all_projects():
    """Return every project document."""
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
    """Return experience documents."""
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
# PROFILE QUESTION HANDLING
# ============================================================

def is_general_profile_question(query):
    """Recognize broad questions about Farhan."""
    q = normalize_text(query)

    phrases = [
        "tell me about farhan",
        "tell me about shaik farhan",
        "about farhan",
        "who is farhan",
        "who is shaik farhan",
        "introduce farhan",
        "tell me about yourself",
        "describe farhan",
        "give me an introduction",
        "professional introduction",
    ]

    return any(normalize_text(phrase) in q for phrase in phrases)


def retrieve_profile_context(top_k=7):
    """Retrieve profile information from relevant sections."""
    preferred_sections = ["about", "personal", "education", "skills"]

    results = []

    for section in preferred_sections:
        for chunk in all_chunks:
            if chunk["metadata"].get("section") == section:
                results.append({
                    "score": 1.0,
                    "text": chunk["text"],
                    "metadata": chunk["metadata"],
                })

                if len(results) >= top_k:
                    return results

    # If section names differ from expected names, search broadly.
    return [
        {
            "score": 1.0,
            "text": chunk["text"],
            "metadata": chunk["metadata"],
        }
        for chunk in all_chunks[:top_k]
    ]


# ============================================================
# MAIN RETRIEVAL FUNCTION
# ============================================================

def retrieve_context(query, top_k=7):
    """Retrieve relevant facts for the existing RAG pipeline."""
    q = query.strip()

    if not q:
        return []

    # Broad profile questions should not depend on keyword overlap.
    if is_general_profile_question(q):
        return retrieve_profile_context(top_k=top_k)

    # Find an explicitly mentioned project.
    project = detect_project(q)

    if project:
        results = search_portfolio(
            q,
            top_k=top_k,
            section_filter="projects",
            project_filter=project,
        )

        if results:
            return results

        # Try the whole project section if the exact name differs.
        results = search_portfolio(
            q,
            top_k=top_k,
            section_filter="projects",
        )

        if results:
            return results

    # Requests for every project should return all project documents.
    project_list_phrases = [
        "what projects",
        "which projects",
        "list projects",
        "all projects",
        "projects has farhan",
        "what has farhan built",
        "what did farhan build",
        "projects did farhan",
    ]

    if any(
        normalize_text(phrase) in normalize_text(q)
        for phrase in project_list_phrases
    ):
        return get_all_projects()

    # Requests for a list of experience entries.
    experience_list_phrases = [
        "work experience",
        "professional experience",
        "work history",
        "list internships",
        "all internships",
    ]

    if any(
        normalize_text(phrase) in normalize_text(q)
        for phrase in experience_list_phrases
    ):
        results = get_all_experience()
        if results:
            return results

    # Search the detected section first.
    section = detect_section(q)

    if section:
        results = search_portfolio(
            q,
            top_k=top_k,
            section_filter=section,
        )

        if results:
            return results

    # Important: if routing fails, search every section.
    results = search_portfolio(q, top_k=top_k)

    if results:
        return results

    # Last-resort fallback for very broad questions.
    # This helps avoid an empty context when portfolio data exists.
    return [
        {
            "score": 0.0,
            "text": chunk["text"],
            "metadata": chunk["metadata"],
        }
        for chunk in all_chunks[:min(top_k, len(all_chunks))]
    ]
