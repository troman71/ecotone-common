"""
Semantic Scholar API Client

Free API access to Semantic Scholar academic graph.
- Unauthenticated: ~5,000 requests per 5 minutes (shared pool)
- With API key: 1 request/second (dedicated)

Documentation: https://www.semanticscholar.org/product/api
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class SemanticScholarClient:
    """
    Client for searching Semantic Scholar.

    Provides access to broad academic literature with excellent
    citation graph data and AI/CS coverage.

    NOTE: Without an API key, requests share a pool with all unauthenticated
    users and may be rate-limited. Get a free API key at:
    https://www.semanticscholar.org/product/api#api-key
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    RATE_LIMIT_WITH_KEY = 1.0  # 1 req/sec with key
    RATE_LIMIT_WITHOUT_KEY = 2.0  # More conservative for shared pool

    # Fields to request from API
    PAPER_FIELDS = [
        "paperId",
        "title",
        "abstract",
        "year",
        "authors",
        "citationCount",
        "referenceCount",
        "influentialCitationCount",
        "isOpenAccess",
        "openAccessPdf",
        "fieldsOfStudy",
        "publicationTypes",
        "journal",
        "externalIds",
        "url",
    ]

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Semantic Scholar client.

        Args:
            api_key: Optional API key for dedicated rate limit.
                     Request at: https://www.semanticscholar.org/product/api#api-key
        """
        self.api_key = api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
        self.rate_limit = self.RATE_LIMIT_WITH_KEY if self.api_key else self.RATE_LIMIT_WITHOUT_KEY
        self._last_request_time = 0
        self._requests_made = 0
        self._consecutive_rate_limits = 0
        self._temporarily_disabled = False
        self._disabled_until = 0

        if not self.api_key:
            logger.info(
                "Semantic Scholar client initialized without API key (shared pool). "
                "Get free API key at: https://www.semanticscholar.org/product/api#api-key"
            )

    def _apply_rate_limit(self):
        """Apply rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request_time = time.time()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    def search(
        self,
        query: str,
        max_results: int = 20,
        min_year: Optional[int] = None,
        fields_of_study: Optional[List[str]] = None,
        publication_types: Optional[List[str]] = None,
        open_access_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Search Semantic Scholar for papers.

        Args:
            query: Search query
            max_results: Maximum results to return (max 100 per request)
            min_year: Minimum publication year
            fields_of_study: Filter by fields (e.g., ["Psychology", "Education"])
            publication_types: Filter by types (e.g., ["Review", "ClinicalTrial"])
            open_access_only: Only return open access papers

        Returns:
            list: Paper metadata dicts
        """
        self._apply_rate_limit()

        params = {
            "query": query,
            "limit": min(max_results, 100),
            "fields": ",".join(self.PAPER_FIELDS),
        }

        if min_year:
            params["year"] = f"{min_year}-"

        if fields_of_study:
            params["fieldsOfStudy"] = ",".join(fields_of_study)

        if publication_types:
            params["publicationTypes"] = ",".join(publication_types)

        if open_access_only:
            params["openAccessPdf"] = ""

        # Check if temporarily disabled due to rate limits
        if self._temporarily_disabled:
            if time.time() < self._disabled_until:
                logger.info(
                    f"Semantic Scholar temporarily disabled (rate limited). "
                    f"Resuming in {int(self._disabled_until - time.time())}s"
                )
                return []
            else:
                self._temporarily_disabled = False
                self._consecutive_rate_limits = 0

        # Retry with exponential backoff for rate limits
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait_time = 2 ** (attempt + 1)  # 4, 8 seconds
                    logger.info(f"Semantic Scholar retry {attempt + 1}/{max_retries} after {wait_time}s")
                    time.sleep(wait_time)

                # Use precision search endpoint (better relevance ranking than /bulk)
                response = requests.get(
                    f"{self.BASE_URL}/paper/search",
                    params=params,
                    headers=self._get_headers(),
                    timeout=30,
                )

                if response.status_code == 429:
                    self._consecutive_rate_limits += 1
                    logger.warning(
                        f"Semantic Scholar rate limit (attempt {attempt + 1}, "
                        f"consecutive: {self._consecutive_rate_limits})"
                    )

                    # If we've hit too many rate limits, disable temporarily
                    if self._consecutive_rate_limits >= 5:
                        self._temporarily_disabled = True
                        self._disabled_until = time.time() + 60  # 1 minute cooldown
                        logger.warning(
                            "Semantic Scholar disabled for 60s due to persistent rate limits. "
                            "Consider getting an API key: https://www.semanticscholar.org/product/api#api-key"
                        )
                        return []

                    if attempt < max_retries - 1:
                        continue
                    return []

                response.raise_for_status()
                self._requests_made += 1
                self._consecutive_rate_limits = 0  # Reset on success

                data = response.json()
                papers = data.get("data", [])

                # Normalize and filter out non-paper records
                normalized = [self._normalize_paper(p) for p in papers]
                normalized = [p for p in normalized if self._is_valid_paper(p)]

                logger.info(f"Semantic Scholar: Retrieved {len(normalized)} papers")
                return normalized

            except requests.exceptions.HTTPError as e:
                if hasattr(e, "response") and e.response.status_code == 429:
                    self._consecutive_rate_limits += 1
                    if attempt < max_retries - 1:
                        continue
                logger.error(f"Semantic Scholar search failed: {e}")
                return []
            except Exception as e:
                logger.error(f"Semantic Scholar search failed: {e}")
                return []

        return []

    def _is_valid_paper(self, paper: Dict) -> bool:
        """
        Reject non-paper records that the API sometimes returns.

        Filters out geographic data records, stub entries, and other
        noise that appear as single-word or no-author titles.
        """
        title = (paper.get("title") or "").strip()
        if not title:
            return False
        # Single-word titles (e.g. "Monaco", "Oman") are almost never real papers
        if len(title.split()) < 2:
            return False
        # No authors AND no abstract is a strong signal of a stub/data record
        if not paper.get("authors") and not paper.get("abstract"):
            return False
        return True

    def _normalize_paper(self, paper: Dict) -> Dict[str, Any]:
        """
        Normalize Semantic Scholar paper to common format.

        Args:
            paper: Raw paper data from API

        Returns:
            dict: Normalized paper metadata
        """
        # Extract authors
        authors = []
        for author in paper.get("authors", []):
            name = author.get("name", "")
            if name:
                authors.append(name)

        # Extract open access PDF
        pdf_link = ""
        oa_pdf = paper.get("openAccessPdf")
        if oa_pdf and isinstance(oa_pdf, dict):
            pdf_link = oa_pdf.get("url", "")

        # Extract external IDs
        external_ids = paper.get("externalIds", {}) or {}
        doi = external_ids.get("DOI", "")
        pmid = external_ids.get("PubMed", "")
        arxiv_id = external_ids.get("ArXiv", "")

        # Extract journal info
        journal = ""
        journal_info = paper.get("journal")
        if journal_info and isinstance(journal_info, dict):
            journal = journal_info.get("name", "")

        return {
            "paper_id": paper.get("paperId", ""),
            "title": paper.get("title", ""),
            "authors": authors,
            "year": paper.get("year"),
            "abstract": paper.get("abstract", "") or "",
            "citation_count": paper.get("citationCount", 0) or 0,
            "reference_count": paper.get("referenceCount", 0) or 0,
            "influential_citations": paper.get("influentialCitationCount", 0) or 0,
            "is_open_access": paper.get("isOpenAccess", False),
            "pdf_link": pdf_link,
            "fields_of_study": paper.get("fieldsOfStudy", []) or [],
            "publication_types": paper.get("publicationTypes", []) or [],
            "journal": journal,
            "doi": doi,
            "pmid": pmid,
            "arxiv_id": arxiv_id,
            "link": paper.get("url", ""),
            "source": "semantic_scholar",
        }

    def get_paper_by_id(self, paper_id: str, id_type: str = "paperId") -> Optional[Dict[str, Any]]:
        """
        Get paper details by ID.

        Args:
            paper_id: Paper identifier
            id_type: Type of ID ("paperId", "DOI", "PMID", "ArXiv")

        Returns:
            dict: Paper metadata or None
        """
        self._apply_rate_limit()

        # Format ID based on type
        if id_type == "DOI":
            paper_id = f"DOI:{paper_id}"
        elif id_type == "PMID":
            paper_id = f"PMID:{paper_id}"
        elif id_type == "ArXiv":
            paper_id = f"ArXiv:{paper_id}"

        try:
            response = requests.get(
                f"{self.BASE_URL}/paper/{paper_id}",
                params={"fields": ",".join(self.PAPER_FIELDS)},
                headers=self._get_headers(),
                timeout=30,
            )
            response.raise_for_status()
            self._requests_made += 1

            paper = response.json()
            return self._normalize_paper(paper)

        except Exception as e:
            logger.error(f"Semantic Scholar paper lookup failed: {e}")
            return None

    def get_citations(self, paper_id: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Get papers that cite a given paper.

        Args:
            paper_id: Semantic Scholar paper ID
            max_results: Maximum results

        Returns:
            list: Citing papers
        """
        self._apply_rate_limit()

        try:
            response = requests.get(
                f"{self.BASE_URL}/paper/{paper_id}/citations",
                params={
                    "fields": ",".join(self.PAPER_FIELDS),
                    "limit": min(max_results, 100),
                },
                headers=self._get_headers(),
                timeout=30,
            )
            response.raise_for_status()
            self._requests_made += 1

            data = response.json()
            citations = data.get("data", [])

            # Extract the citing paper from each citation
            papers = []
            for citation in citations:
                citing_paper = citation.get("citingPaper", {})
                if citing_paper:
                    papers.append(self._normalize_paper(citing_paper))

            logger.info(f"Semantic Scholar: Found {len(papers)} citations")
            return papers

        except Exception as e:
            logger.error(f"Semantic Scholar citations failed: {e}")
            return []

    def get_references(self, paper_id: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Get papers referenced by a given paper.

        Args:
            paper_id: Semantic Scholar paper ID
            max_results: Maximum results

        Returns:
            list: Referenced papers
        """
        self._apply_rate_limit()

        try:
            response = requests.get(
                f"{self.BASE_URL}/paper/{paper_id}/references",
                params={
                    "fields": ",".join(self.PAPER_FIELDS),
                    "limit": min(max_results, 100),
                },
                headers=self._get_headers(),
                timeout=30,
            )
            response.raise_for_status()
            self._requests_made += 1

            data = response.json()
            references = data.get("data", [])

            # Extract the cited paper from each reference
            papers = []
            for ref in references:
                cited_paper = ref.get("citedPaper", {})
                if cited_paper:
                    papers.append(self._normalize_paper(cited_paper))

            logger.info(f"Semantic Scholar: Found {len(papers)} references")
            return papers

        except Exception as e:
            logger.error(f"Semantic Scholar references failed: {e}")
            return []

    def search_reviews(self, topic: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search for review papers.

        Args:
            topic: Research topic
            max_results: Maximum results

        Returns:
            list: Review papers
        """
        return self.search(
            query=topic,
            max_results=max_results,
            publication_types=["Review"],
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        stats = {
            "requests_made": self._requests_made,
            "has_api_key": bool(self.api_key),
            "rate_limit": f"{1/self.rate_limit:.1f} req/sec",
            "consecutive_rate_limits": self._consecutive_rate_limits,
            "temporarily_disabled": self._temporarily_disabled,
        }
        if self._temporarily_disabled:
            stats["disabled_seconds_remaining"] = max(0, int(self._disabled_until - time.time()))
        return stats
