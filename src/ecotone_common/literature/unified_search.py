"""
Unified Literature Search

Combines multiple academic search sources:
- Google Scholar (via SerpAPI)
- PubMed (via E-utilities)
- Semantic Scholar

Provides deduplication, source attribution, and merged results.
"""

import hashlib
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Set

import requests

from ecotone_common.literature.pubmed_client import PubMedClient
from ecotone_common.literature.semantic_scholar_client import SemanticScholarClient

logger = logging.getLogger(__name__)


class UnifiedLiteratureSearch:
    """
    Unified search across multiple academic literature sources.

    Searches Google Scholar, PubMed, and Semantic Scholar in parallel,
    deduplicates results, and provides source attribution.
    """

    def __init__(
        self,
        enable_google_scholar: bool = True,
        enable_pubmed: bool = True,
        enable_semantic_scholar: bool = True,
        serpapi_key: Optional[str] = None,
        ncbi_api_key: Optional[str] = None,
        semantic_scholar_key: Optional[str] = None,
    ):
        """
        Initialize unified search.

        Args:
            enable_google_scholar: Enable Google Scholar via SerpAPI
            enable_pubmed: Enable PubMed via E-utilities
            enable_semantic_scholar: Enable Semantic Scholar
            serpapi_key: SerpAPI key for Google Scholar
            ncbi_api_key: NCBI API key for PubMed
            semantic_scholar_key: Semantic Scholar API key
        """
        self.enable_google_scholar = enable_google_scholar
        self.enable_pubmed = enable_pubmed
        self.enable_semantic_scholar = enable_semantic_scholar

        # API keys
        self.serpapi_key = serpapi_key or os.getenv("SERPAPI_API_KEY", "")
        self.ncbi_api_key = ncbi_api_key or os.getenv("NCBI_API_KEY", "")
        self.semantic_scholar_key = semantic_scholar_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")

        # Initialize clients
        if enable_pubmed:
            self.pubmed_client = PubMedClient(api_key=self.ncbi_api_key)
        else:
            self.pubmed_client = None

        if enable_semantic_scholar:
            self.semantic_scholar_client = SemanticScholarClient(api_key=self.semantic_scholar_key)
        else:
            self.semantic_scholar_client = None

        # Stats tracking
        self._total_requests = 0
        self._papers_by_source = {
            "google_scholar": 0,
            "pubmed": 0,
            "semantic_scholar": 0,
        }

        # Log enabled sources
        sources = []
        if enable_google_scholar and self.serpapi_key:
            sources.append("Google Scholar")
        if enable_pubmed:
            sources.append("PubMed")
        if enable_semantic_scholar:
            sources.append("Semantic Scholar")
        logger.info(f"UnifiedLiteratureSearch initialized with: {', '.join(sources)}")

    def search(
        self,
        query: str,
        max_results_per_source: int = 20,
        min_year: Optional[int] = None,
        parallel: bool = True,
    ) -> Dict[str, Any]:
        """
        Search all enabled sources.

        Args:
            query: Search query
            max_results_per_source: Max results from each source
            min_year: Minimum publication year filter
            parallel: Run searches in parallel (faster but uses more resources)

        Returns:
            dict: {
                "papers": [...],  # Deduplicated merged results
                "by_source": {...},  # Results grouped by source
                "stats": {...}  # Search statistics
            }
        """
        start_time = time.time()

        if parallel:
            results = self._search_parallel(query, max_results_per_source, min_year)
        else:
            results = self._search_sequential(query, max_results_per_source, min_year)

        # Merge and deduplicate
        all_papers = []
        for source, papers in results.items():
            all_papers.extend(papers)
            self._papers_by_source[source] = len(papers)

        deduplicated = self._deduplicate_papers(all_papers)

        elapsed = time.time() - start_time

        return {
            "papers": deduplicated,
            "by_source": results,
            "stats": {
                "total_raw": len(all_papers),
                "total_deduplicated": len(deduplicated),
                "sources_searched": len(results),
                "elapsed_seconds": round(elapsed, 2),
                "papers_per_source": {source: len(papers) for source, papers in results.items()},
            },
        }

    def _search_parallel(self, query: str, max_results: int, min_year: Optional[int]) -> Dict[str, List[Dict]]:
        """Run searches in parallel using threads."""
        results = {}

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}

            # Submit search tasks
            if self.enable_google_scholar and self.serpapi_key:
                futures[executor.submit(self._search_google_scholar, query, max_results, min_year)] = "google_scholar"

            if self.enable_pubmed and self.pubmed_client:
                futures[executor.submit(self._search_pubmed, query, max_results, min_year)] = "pubmed"

            if self.enable_semantic_scholar and self.semantic_scholar_client:
                futures[executor.submit(self._search_semantic_scholar, query, max_results, min_year)] = (
                    "semantic_scholar"
                )

            # Collect results
            for future in as_completed(futures):
                source = futures[future]
                try:
                    papers = future.result()
                    results[source] = papers
                except Exception as e:
                    logger.error(f"Search failed for {source}: {e}")
                    results[source] = []

        return results

    def _search_sequential(self, query: str, max_results: int, min_year: Optional[int]) -> Dict[str, List[Dict]]:
        """Run searches sequentially."""
        results = {}

        if self.enable_google_scholar and self.serpapi_key:
            results["google_scholar"] = self._search_google_scholar(query, max_results, min_year)

        if self.enable_pubmed and self.pubmed_client:
            results["pubmed"] = self._search_pubmed(query, max_results, min_year)

        if self.enable_semantic_scholar and self.semantic_scholar_client:
            results["semantic_scholar"] = self._search_semantic_scholar(query, max_results, min_year)

        return results

    def _search_google_scholar(self, query: str, max_results: int, min_year: Optional[int]) -> List[Dict[str, Any]]:
        """Search Google Scholar via SerpAPI."""
        try:
            params = {
                "engine": "google_scholar",
                "q": query,
                "api_key": self.serpapi_key,
                "num": min(max_results, 20),
                "hl": "en",
            }

            if min_year:
                params["as_ylo"] = min_year

            response = requests.get(
                "https://serpapi.com/search.json",
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            self._total_requests += 1

            results = response.json()
            organic = results.get("organic_results", [])

            papers = []
            for result in organic:
                # Extract resources
                resources = result.get("resources", [])
                pdf_link = resources[0].get("link", "") if resources else ""

                # Extract citation info
                inline_links = result.get("inline_links", {})
                cited_by = inline_links.get("cited_by", {})

                paper = {
                    "title": result.get("title", ""),
                    "authors": self._extract_gs_authors(result),
                    "year": self._extract_gs_year(result),
                    "abstract": result.get("snippet", ""),
                    "link": result.get("link", ""),
                    "pdf_link": pdf_link,
                    "citation_count": cited_by.get("total", 0),
                    "cites_id": cited_by.get("cites_id", ""),
                    "source": "google_scholar",
                    "result_id": result.get("result_id", ""),
                }
                papers.append(paper)

            logger.info(f"Google Scholar: Retrieved {len(papers)} papers")
            return papers

        except Exception as e:
            logger.error(f"Google Scholar search failed: {e}")
            return []

    def _extract_gs_authors(self, result: Dict) -> List[str]:
        """Extract authors from Google Scholar result."""
        pub_info = result.get("publication_info", {})
        authors = pub_info.get("authors", [])
        if isinstance(authors, list):
            return [a.get("name", "") for a in authors]
        return []

    def _extract_gs_year(self, result: Dict) -> Optional[int]:
        """Extract year from Google Scholar result."""
        import re

        pub_info = result.get("publication_info", {})
        summary = pub_info.get("summary", "")
        years = re.findall(r"20[0-2]\d", summary)
        if years:
            return int(years[0])
        return None

    def _search_pubmed(self, query: str, max_results: int, min_year: Optional[int]) -> List[Dict[str, Any]]:
        """Search PubMed via E-utilities."""
        try:
            papers = self.pubmed_client.search(
                query=query,
                max_results=max_results,
                min_year=min_year,
            )
            return papers
        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            return []

    def _search_semantic_scholar(self, query: str, max_results: int, min_year: Optional[int]) -> List[Dict[str, Any]]:
        """Search Semantic Scholar."""
        try:
            # Small delay to avoid hitting rate limits when running in parallel
            # with other sources
            time.sleep(0.5)

            papers = self.semantic_scholar_client.search(
                query=query,
                max_results=max_results,
                min_year=min_year,
            )
            return papers
        except Exception as e:
            logger.error(f"Semantic Scholar search failed: {e}")
            return []

    def _deduplicate_papers(self, papers: List[Dict]) -> List[Dict]:
        """
        Deduplicate papers across sources.

        Uses title similarity and DOI matching.
        When duplicates found, merges metadata from all sources.
        """
        seen_titles: Set[str] = set()
        seen_dois: Set[str] = set()
        unique_papers = []

        for paper in papers:
            # Normalize title for comparison
            title = paper.get("title", "").lower().strip()
            title_key = "".join(c for c in title if c.isalnum())[:60]

            # Check DOI
            doi = paper.get("doi", "").lower().strip()

            is_duplicate = False

            # Check by DOI first (most reliable)
            if doi and doi in seen_dois:
                is_duplicate = True
            elif title_key and title_key in seen_titles:
                is_duplicate = True

            if not is_duplicate:
                if title_key:
                    seen_titles.add(title_key)
                if doi:
                    seen_dois.add(doi)
                unique_papers.append(paper)

        # Sort by citation count (highest first)
        unique_papers.sort(key=lambda x: x.get("citation_count", 0) or 0, reverse=True)

        return unique_papers

    def search_for_evidence(
        self,
        topic: str,
        max_results_per_source: int = 15,
        min_year: int = 2010,
    ) -> Dict[str, Any]:
        """
        Specialized search for evidence synthesis.

        Searches for systematic reviews, meta-analyses, and RCTs.

        Args:
            topic: Research topic
            max_results_per_source: Max results per source
            min_year: Minimum year (default 2010)

        Returns:
            dict: Search results with evidence-focused papers
        """
        # Build evidence-focused queries for each source
        gs_query = f'{topic} ("systematic review" OR "meta-analysis" OR "randomized controlled trial")'
        pubmed_query = f"{topic}"  # PubMed client adds its own filters
        ss_query = topic

        results = {}

        # Google Scholar with evidence keywords
        if self.enable_google_scholar and self.serpapi_key:
            results["google_scholar"] = self._search_google_scholar(gs_query, max_results_per_source, min_year)

        # PubMed with systematic review filter
        if self.enable_pubmed and self.pubmed_client:
            results["pubmed"] = self.pubmed_client.search_systematic_reviews(topic, max_results_per_source)
            results["pubmed"].extend(self.pubmed_client.search_clinical_trials(topic, max_results_per_source))

        # Semantic Scholar with review filter
        if self.enable_semantic_scholar and self.semantic_scholar_client:
            results["semantic_scholar"] = self.semantic_scholar_client.search_reviews(ss_query, max_results_per_source)

        # Merge and deduplicate
        all_papers = []
        for source, papers in results.items():
            all_papers.extend(papers)

        deduplicated = self._deduplicate_papers(all_papers)

        return {
            "papers": deduplicated,
            "by_source": results,
            "stats": {
                "total_raw": len(all_papers),
                "total_deduplicated": len(deduplicated),
                "sources_searched": len(results),
                "focus": "evidence_synthesis",
            },
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get search statistics."""
        stats = {
            "total_requests": self._total_requests,
            "papers_by_source": self._papers_by_source.copy(),
            "sources_enabled": {
                "google_scholar": self.enable_google_scholar and bool(self.serpapi_key),
                "pubmed": self.enable_pubmed,
                "semantic_scholar": self.enable_semantic_scholar,
            },
        }

        if self.pubmed_client:
            stats["pubmed_stats"] = self.pubmed_client.get_stats()

        if self.semantic_scholar_client:
            stats["semantic_scholar_stats"] = self.semantic_scholar_client.get_stats()

        return stats
