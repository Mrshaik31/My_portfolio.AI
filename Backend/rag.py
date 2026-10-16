"""
RAG orchestration and local LLM answer generation.

This module reuses retrieval from retriever.py and the functions
developed in the Context Builder and LLM Jupyter notebooks.
"""

import os
import requests

from retriever import retrieve_context


def build_context(results):
    """Format retrieved portfolio results into a context string."""
    context_parts = []

    for i, result in enumerate(results, start=1):
        metadata = result["metadata"]

        section = metadata.get("section", "")
        project = metadata.get("project", "")

        header = f"Source {i}\n"
        header += f"Section: {section}\n"

        if project:
            header += f"Project: {project}\n"

        header += "\n"
        context_parts.append(header + result["text"])

    return "\n\n" + "\n\n".join(context_parts)



def build_prompt(question, context):
    prompt = f"""
You are Farhan's portfolio assistant. Help visitors understand
Farhan's background, skills, and projects.

Use ONLY the facts provided in the context below.

CONTEXT:
{context}

VISITOR QUESTION:
{question}

IMPORTANT ANSWERING RULES:

1. Write like a real person speaking naturally, not like a resume,
   database, or technical report.
2. For questions about a project, explain it in a short paragraph:
   what the project does, how it works, and its main achievement.
3. For questions about skills, summarize the most relevant skills
   instead of listing every skill in the context.
4. Use simple, professional English that a fresher can comfortably
   speak during an interview.
5. When the visitor asks for an interview answer or asks how Farhan
   would explain something, write in first person using "I".
6. For ordinary portfolio questions, use natural wording and refer
   to Farhan by name when appropriate.
7. Do not copy headings such as "Key Features", "Technologies Used",
   or "Category" from the context.
8. Do not use bullet points, numbered lists, Markdown formatting,
   or labels unless the visitor explicitly requests a list.
9. Aim for 3-5 sentences. Include relevant technical details and
   important achievements without explaining everything.
10. Never invent experience, results, or achievements.
11. If the context does not contain the answer, say so honestly.

Write ONLY the final answer. Do not explain these instructions.

ANSWER:
"""
    return prompt

# response_style = """
# RESPONSE STYLE RULES:
# - Speak in a natural, friendly, professional, conversational tone.
# - Keep the default answer to 2-4 short sentences.
# - Explain the most important points instead of listing every item.
# - Use simple English that a fresher can comfortably speak in an interview.
# - Avoid long lists, nested bullets, and unnecessary technical jargon.
# - Do not output Markdown symbols such as *, **, or +.
# - Use first person ("I") when the visitor asks for an interview-style
#   answer that Farhan can speak aloud.
# - Otherwise, describe Farhan in the third person.
# - Use only information supported by the retrieved context.
# - If asked for all skills or a complete list, provide a structured list.
# """


def rag_pipeline(query, top_k=5):
    """
    Run retrieval, context construction, and prompt construction.
    Returns the intermediate results for debugging and testing.
    """
    results = retrieve_context(query, top_k=top_k)
    context = build_context(results)
    prompt = build_prompt(query, context)

    return {
        "query": query,
        "results": results,
        "context": context,
        "prompt": prompt,
    }



def generate_answer(query, top_k=5):
    """Generate an answer using OpenRouter and retrieved portfolio context."""

    rag_result = rag_pipeline(query, top_k=top_k)

    # Do not ask the AI to answer without relevant portfolio evidence.
    if not rag_result["results"]:
        return (
            "I couldn't find relevant information in Farhan's "
            "portfolio to answer that question."
        )

    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL")

    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured.")

    if not model:
        raise RuntimeError("OPENROUTER_MODEL is not configured.")

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Title": "Farhan Portfolio Assistant",
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": rag_result["prompt"],
            }
        ],
        "temperature": 0.2,
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=60,
    )

    # Raise an error if OpenRouter returns an HTTP error.
    response.raise_for_status()

    result = response.json()

    answer = result["choices"][0]["message"]["content"]

    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("OpenRouter returned an empty answer.")

    return answer.strip()

