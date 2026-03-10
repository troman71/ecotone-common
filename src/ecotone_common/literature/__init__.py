"""
ecotone_common.literature — Academic literature search clients.

Provides unified access to PubMed, Semantic Scholar, and (optionally)
Google Scholar via SerpAPI.
"""

from .pubmed_client import PubMedClient
from .semantic_scholar_client import SemanticScholarClient
from .unified_search import UnifiedLiteratureSearch

__all__ = ["PubMedClient", "SemanticScholarClient", "UnifiedLiteratureSearch"]
