from app.domain.models.query import RawQuery
from app.domain.services.llm_client import LLMClient
from app.domain.services.query_enricher import QueryEnricher

_SYSTEM_PROMPT = """You are a preprocessor for an algorithmic problem search engine.

Your task: rewrite the given competitive programming problem statement into a **canonical, story-free form**.

Rules:
- Remove all narrative, fictional context, character names, and thematic decoration.
- Keep only: the computational goal, input/output format, and constraints.
- Express the problem in abstract, neutral terms (e.g. "given an array of integers" not "Vasya has a sequence of coins").
- Use standard algorithmic vocabulary: array, graph, tree, integer, string, sequence, query, etc.
- Preserve all numeric constraints exactly (e.g. "1 ≤ n ≤ 10^5").
- Output only the rewritten problem statement — no explanations, no commentary, no preamble.

Example:
  Input:  "Alice wants to impress Bob at a party. She has N balloons numbered 1..N. She can pop any balloon and the adjacent ones merge. Find the minimum number of pops to make all balloons the same color."
  Output: "Given an array of N integers, each pop operation removes one element and merges its neighbors. Find the minimum number of operations to make all elements equal."
"""


class LLMQueryEnricher(QueryEnricher):
    def __init__(self, llm_client: LLMClient) -> None:
        self._llm = llm_client

    async def enrich(self, raw_query: RawQuery) -> str:
        prompt = f"{_SYSTEM_PROMPT}\n\nProblem statement:\n{raw_query.text}"
        return await self._llm.generate(prompt)