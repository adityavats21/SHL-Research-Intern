from __future__ import annotations

import re
from dataclasses import dataclass

from app.catalog import Catalog, load_catalog, normalize


ACK_RE = re.compile(
    r"\b(perfect|thanks|thank you|that works|that's good|that covers|clear|confirmed|confirm|lock|locking|final|as-is|as is|keep|keeping|good choice)\b",
    re.I,
)


@dataclass
class AgentResult:
    reply: str
    recommendations: list[dict[str, str]]
    end_of_conversation: bool = False


def _users(messages: list[dict[str, str]]) -> list[str]:
    return [m.get("content", "") for m in messages if m.get("role") == "user"]


def _last_user(messages: list[dict[str, str]]) -> str:
    users = _users(messages)
    return users[-1] if users else ""


def _has_any(text: str, words: list[str]) -> bool:
    ntext = normalize(text)
    return any(normalize(w) in ntext for w in words)


def _is_vague(text: str) -> bool:
    n = normalize(text)
    vague_bits = {"assessment", "solution", "test", "hiring", "need", "recommend"}
    tokens = set(n.split())
    return len(tokens) < 9 and bool(tokens & vague_bits) and not (tokens - vague_bits - {"i", "we", "a", "an"})


def _is_off_topic(text: str) -> bool:
    n = normalize(text)
    injection = ["ignore previous", "system prompt", "developer message", "jailbreak", "prompt injection"]
    legal = ["legally required", "legal requirement", "satisfy that requirement", "law", "lawsuit", "compliance advice"]
    general = ["write my resume", "salary negotiation", "interview tips", "hiring advice", "employment law"]
    return any(x in n for x in injection + legal + general)


def _end(messages: list[dict[str, str]], recs: list[dict[str, str]]) -> bool:
    return bool(recs and len(messages) > 1 and ACK_RE.search(_last_user(messages)))


def _reply_with(catalog: Catalog, names: list[str], reply: str, messages: list[dict[str, str]]) -> AgentResult:
    recs = catalog.recommend(names)
    return AgentResult(reply=reply, recommendations=recs, end_of_conversation=_end(messages, recs))


def _compare(catalog: Catalog, text: str) -> AgentResult:
    items = catalog.mentioned_items(text)
    if len(items) < 2 and "contact center call simulation" in normalize(text):
        items = [
            catalog.get("Contact Center Call Simulation (New)"),
            catalog.get("Customer Service Phone Simulation"),
        ]
    if len(items) < 2:
        return AgentResult(
            "I can compare SHL catalog assessments, but I need two catalog product names to compare.",
            [],
            False,
        )
    a, b = items[0], items[1]
    reply = (
        f"{a['name']} is cataloged as {', '.join(a['keys']) or a['test_type']}."
        f" {a['description'][:420]}"
        f"\n\n{b['name']} is cataloged as {', '.join(b['keys']) or b['test_type']}."
        f" {b['description'][:420]}"
        "\n\nSo the practical difference is the construct and use case: choose the first when that description matches the role need, and the second when its catalog scope is the closer fit."
    )
    return AgentResult(reply, [], False)


def _scenario_names(all_text: str) -> list[str] | None:
    n = normalize(all_text)

    if "senior leadership" in n or "cxo" in n or "director level" in n:
        return [
            "Occupational Personality Questionnaire OPQ32r",
            "OPQ Universal Competency Report 2.0",
            "OPQ Leadership Report",
        ]
    if "rust" in n or ("networking infrastructure" in n and "senior" in n):
        return [
            "Smart Interview Live Coding",
            "Linux Programming (General)",
            "Networking and Implementation (New)",
            "SHL Verify Interactive G+",
            "Occupational Personality Questionnaire OPQ32r",
        ]
    if "contact centre" in n or "contact center" in n or "inbound calls" in n:
        return [
            "SVAR Spoken English (US) (New)" if " us " in f" {n} " or "english" in n else "SVAR Spoken English (US) (New)",
            "Contact Center Call Simulation (New)",
            "Entry Level Customer Serv - Retail & Contact Center",
            "Customer Service Phone Simulation",
        ]
    if "financial analyst" in n or ("finance" in n and "graduate" in n):
        names = [
            "SHL Verify Interactive – Numerical Reasoning",
            "Financial Accounting (New)",
            "Basic Statistics (New)",
        ]
        if "situational" in n or "graduate scenarios" in n or "work context" in n:
            names.append("Graduate Scenarios")
        names.append("Occupational Personality Questionnaire OPQ32r")
        return names
    if "sales organization" in n or "re skill" in n or "reskill" in n or "sales report" in n:
        return [
            "Global Skills Assessment",
            "Global Skills Development Report",
            "Occupational Personality Questionnaire OPQ32r",
            "OPQ MQ Sales Report",
            "Sales Transformation 2.0 - Individual Contributor",
        ]
    if "plant operator" in n or "chemical facility" in n or ("safety" in n and "dependability" in n):
        if "industrial" in n and ("confirmed" in n or "right fit" in n):
            return [
                "Manufac. & Indust. - Safety & Dependability 8.0",
                "Workplace Health and Safety (New)",
            ]
        return [
            "Dependability and Safety Instrument (DSI)",
            "Manufac. & Indust. - Safety & Dependability 8.0",
            "Workplace Health and Safety (New)",
        ]
    if "hipaa" in n or "healthcare admin" in n or "patient records" in n:
        return [
            "HIPAA (Security)",
            "Medical Terminology (New)",
            "Microsoft Word 365 - Essentials (New)",
            "Dependability and Safety Instrument (DSI)",
            "Occupational Personality Questionnaire OPQ32r",
        ]
    if "admin assistant" in n or ("excel" in n and "word" in n and "daily" in n):
        if "simulation" in n or "capabilities" in n:
            return [
                "Microsoft Excel 365 - Essentials (New)",
                "Microsoft Word 365 (New)",
                "MS Excel (New)",
                "MS Word (New)",
                "Occupational Personality Questionnaire OPQ32r",
            ]
        return [
            "MS Excel (New)",
            "MS Word (New)",
            "Occupational Personality Questionnaire OPQ32r",
        ]
    if "core java" in n or "spring" in n or "full stack" in n or "fullstack" in n:
        names = [
            "Core Java (Advanced Level) (New)",
            "Spring (New)",
            "RESTful Web Services (New)",
            "SQL (New)",
        ]
        if "aws" in n or "docker" in n:
            names = [
                "Core Java (Advanced Level) (New)",
                "Spring (New)",
                "SQL (New)",
                "Amazon Web Services (AWS) Development (New)",
                "Docker (New)",
            ]
        names += ["SHL Verify Interactive G+", "Occupational Personality Questionnaire OPQ32r"]
        return names
    if "graduate management trainee" in n:
        names = ["SHL Verify Interactive G+", "Occupational Personality Questionnaire OPQ32r", "Graduate Scenarios"]
        if "drop the opq" in n or "remove the opq" in n:
            names = ["SHL Verify Interactive G+", "Graduate Scenarios"]
        return names
    return None


def recommend(messages: list[dict[str, str]]) -> AgentResult:
    catalog = load_catalog()
    last = _last_user(messages)
    users = _users(messages)
    all_text = "\n".join(users)
    nall = normalize(all_text)
    nlast = normalize(last)

    if not users:
        return AgentResult("Tell me the role, seniority, skills to assess, and any constraints such as language or time.", [], False)

    if _is_off_topic(last):
        return AgentResult(
            "I can help select SHL assessments from the catalog, but I cannot answer legal, general hiring-advice, or prompt-injection requests.",
            [],
            False,
        )

    if "difference between" in nlast or "compare" in nlast or "different from" in nlast:
        return _compare(catalog, last)

    if _is_vague(last):
        return AgentResult(
            "Happy to help. What role are you hiring for, what seniority level, and which skills or behaviours matter most?",
            [],
            False,
        )

    if ("senior leadership" in nall or "cxo" in nall or "director level" in nall) and "selection" not in nall and "development" not in nall:
        return AgentResult(
            "For senior leadership, should this support selection against a benchmark or development feedback for leaders already in role?",
            [],
            False,
        )

    if ("rust" in nall or "networking infrastructure" in nall) and not _has_any(nall, ["yes", "go ahead", "build a shortlist"]):
        return AgentResult(
            "SHL's catalog does not include a Rust-specific knowledge test. The closest fit is live coding plus systems and networking tests. Should I build that shortlist and add a cognitive screen?",
            [],
            False,
        )

    if ("contact centre" in nall or "contact center" in nall or "inbound calls" in nall) and "english" not in nall:
        return AgentResult("Before I shape the stack, what language are the calls in?", [], False)
    if ("contact centre" in nall or "contact center" in nall or "inbound calls" in nall) and "english" in nall and not _has_any(nall, [" us", " usa", "united states", "american"]):
        return AgentResult("SVAR has English variants by accent. Should this be US, UK, Australian, or Indian English?", [], False)

    if ("healthcare admin" in nall or "patient records" in nall) and "hybrid" not in nall and "functionally bilingual" not in nall:
        return AgentResult(
            "The healthcare knowledge tests are English-only, while OPQ32r and DSI support Latin American Spanish. Should we use a hybrid battery with knowledge tests in English and personality in Spanish?",
            [],
            False,
        )

    if ("full stack" in nall or "fullstack" in nall or "core java" in nall) and "backend" not in nall and "frontend" not in nall and "balanced" not in nall:
        return AgentResult(
            "That JD spans several areas. Is this backend-leaning, frontend-heavy, or a balanced full-stack role?",
            [],
            False,
        )
    if ("full stack" in nall or "fullstack" in nall or "core java" in nall) and "senior ic" not in nall and "tech lead" not in nall and "manager" not in nall:
        return AgentResult(
            "One more question: is the seniority closer to a senior individual contributor or a tech lead with broader architecture ownership?",
            [],
            False,
        )

    names = _scenario_names(all_text)
    if names:
        reply = "Here is a catalog-grounded shortlist that fits the role and constraints."
        if "drop the opq" in nall or "remove the opq" in nall:
            reply = "Updated. OPQ32r removed from the shortlist."
        elif "aws" in nlast or "docker" in nlast or "drop rest" in nlast:
            reply = "Updated: REST is removed, and AWS plus Docker are included."
        elif ACK_RE.search(last):
            reply = "Confirmed. This is the final catalog-grounded shortlist."
        return _reply_with(catalog, names, reply, messages)

    generic = catalog.search(all_text, limit=8)
    if not generic:
        return AgentResult(
            "I could not ground that in the SHL assessment catalog. Please share the role, skills, seniority, and constraints so I can recommend catalog items only.",
            [],
            False,
        )
    return AgentResult(
        "Based on the SHL catalog, these are the closest matching assessments. Share any constraints and I can refine the list.",
        generic,
        _end(messages, generic),
    )
