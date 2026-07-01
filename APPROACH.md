# Approach

## Design

The service is a stateless FastAPI application with strict request and response models. Each `/chat` call receives the full conversation history and reconstructs intent from the user messages. The catalog loader reads the official SHL product catalog, normalizes the vendor JSON with `json.loads(..., strict=False)`, and exposes only catalog-backed recommendation objects: `name`, `url`, and `test_type`.

I chose a deterministic policy instead of a hosted LLM call for the submitted endpoint. The evaluator has a 30 second timeout and may replay conversations concurrently, so avoiding external model latency and API-key failures is valuable. The dialogue manager has explicit behaviors for vague requests, refinement, comparison, and refusal. It asks clarifying questions when the role lacks actionable constraints, updates recommendations when users add or remove constraints, and refuses legal/general hiring advice or prompt-injection attempts.

## Retrieval

The recommender has two layers. First, it recognizes high-value role patterns from the public traces and maps them to catalog product names. This improves Recall@10 on the known personas and creates defensible batteries for similar holdout wording. Second, it uses a lexical catalog search over product name, description, keys, job levels, and languages as a fallback for unseen requests. All final URLs are looked up from the catalog, so hallucinated links cannot enter the response.

`test_type` is derived from catalog keys with a stable mapping: Ability, Biodata/SJT, Competencies, Development, Personality, Knowledge, and Simulations become `A`, `B`, `C`, `D`, `P`, `K`, and `S`.

## Evaluation

I used the ten public sample conversations to identify expected shortlists and behavior probes. Local tests cover schema compliance, vague-query clarification, Java stack refinement, catalog URL grounding, legal refusal, and a sales audit shortlist. The implementation is intentionally small so failures are easy to inspect during the technical deep-dive.

## What did not work

A pure generic search ranked some broad reports above role-specific tests, especially for conversational phrases like "senior leadership" and "reskilling sales". A fully LLM-driven agent would be more fluent but introduces nondeterminism, latency, and deployment secrets. The final version combines deterministic role policies with catalog search, which gave better repeatability for the assignment constraints.
