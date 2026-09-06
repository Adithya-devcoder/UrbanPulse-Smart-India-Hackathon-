from typing import List, Optional
from pydantic import BaseModel


class SearchResultItem(BaseModel):
    category: str  # "incident", "road", "vehicle", "camera"
    id: int
    title: str
    subtitle: str
    url_target: str
    metadata: Optional[dict] = None


class UnifiedSearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResultItem]
