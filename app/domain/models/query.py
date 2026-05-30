import uuid
from dataclasses import dataclass


@dataclass
class RawQuery:
    text: str


@dataclass
class SimilarTask:
    task_id: uuid.UUID
    title: str
    task_text: str
    solution: str


@dataclass
class IntermediateQuery:
    original_text: str
    enriched_text: str


@dataclass
class PreparedQuery:
    text: str


@dataclass
class QueryResponse:
    text: str
