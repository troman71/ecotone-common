"""
PubMed E-utilities Client

Free API access to PubMed/MEDLINE database via NCBI E-utilities.
- 3 requests/second without API key
- 10 requests/second with API key

Documentation: https://www.ncbi.nlm.nih.gov/books/NBK25497/
"""

import logging
import os
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class PubMedClient:
    """
    Client for searching PubMed via NCBI E-utilities.

    Provides access to biomedical literature, clinical studies,
    and health sciences research.
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    RATE_LIMIT_WITH_KEY = 0.1  # 10 req/sec
    RATE_LIMIT_WITHOUT_KEY = 0.34  # 3 req/sec

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize PubMed client.

        Args:
            api_key: Optional NCBI API key for higher rate limits.
                     Get one free at: https://www.ncbi.nlm.nih.gov/account/
        """
        self.api_key = api_key or os.getenv("NCBI_API_KEY", "")
        self.rate_limit = self.RATE_LIMIT_WITH_KEY if self.api_key else self.RATE_LIMIT_WITHOUT_KEY
        self._last_request_time = 0
        self._requests_made = 0

        if not self.api_key:
            logger.info(
                "PubMed client initialized without API key (3 req/sec limit). "
                "Set NCBI_API_KEY for 10 req/sec."
            )

    def _apply_rate_limit(self):
        """Apply rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request_time = time.time()

    def search(
        self,
        query: str,
        max_results: int = 20,
        min_year: Optional[int] = None,
        article_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search PubMed and return paper metadata.

        Args:
            query: Search query (supports PubMed query syntax)
            max_results: Maximum results to return
            min_year: Minimum publication year filter
            article_types: Filter by article types (e.g., ["Review", "Clinical Trial"])

        Returns:
            list: Paper metadata dicts
        """
        # Build query with filters
        full_query = query

        if min_year:
            full_query += f" AND {min_year}:3000[pdat]"

        if article_types:
            type_filter = " OR ".join(f'"{t}"[pt]' for t in article_types)
            full_query += f" AND ({type_filter})"

        # Step 1: Search for PMIDs
        pmids = self._esearch(full_query, max_results)

        if not pmids:
            logger.info(f"PubMed: No results for query: {query[:50]}...")
            return []

        # Step 2: Fetch article details
        papers = self._efetch(pmids)

        logger.info(f"PubMed: Retrieved {len(papers)} papers")
        return papers

    def _esearch(self, query: str, max_results: int) -> List[str]:
        """
        Execute ESearch to get PMIDs.

        Args:
            query: Search query
            max_results: Maximum results

        Returns:
            list: PubMed IDs (PMIDs)
        """
        self._apply_rate_limit()

        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance",
        }

        if self.api_key:
            params["api_key"] = self.api_key

        max_retries = 3
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait_time = 2 ** (attempt + 1)  # 4, 8 seconds
                    logger.info(
                        f"PubMed ESearch retry {attempt + 1}/{max_retries} after {wait_time}s"
                    )
                    time.sleep(wait_time)
                    self._apply_rate_limit()

                response = requests.get(
                    f"{self.BASE_URL}/esearch.fcgi",
                    params=params,
                    timeout=30,
                )

                if response.status_code == 429:
                    logger.warning(f"PubMed rate limited (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        continue
                    return []

                response.raise_for_status()
                self._requests_made += 1

                data = response.json()
                pmids = data.get("esearchresult", {}).get("idlist", [])
                return pmids

            except Exception as e:
                logger.error(f"PubMed ESearch failed: {e}")
                if attempt < max_retries - 1:
                    continue
                return []

        return []

    def _efetch(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch article details for PMIDs.

        Args:
            pmids: List of PubMed IDs

        Returns:
            list: Paper metadata dicts
        """
        if not pmids:
            return []

        self._apply_rate_limit()

        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
        }

        if self.api_key:
            params["api_key"] = self.api_key

        max_retries = 3
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait_time = 2 ** (attempt + 1)  # 4, 8 seconds
                    logger.info(
                        f"PubMed EFetch retry {attempt + 1}/{max_retries} after {wait_time}s"
                    )
                    time.sleep(wait_time)
                    self._apply_rate_limit()

                response = requests.get(
                    f"{self.BASE_URL}/efetch.fcgi",
                    params=params,
                    timeout=60,
                )

                if response.status_code == 429:
                    logger.warning(
                        f"PubMed rate limited on EFetch (attempt {attempt + 1}/{max_retries})"
                    )
                    if attempt < max_retries - 1:
                        continue
                    return []

                response.raise_for_status()
                self._requests_made += 1

                papers = self._parse_pubmed_xml(response.text)
                return papers

            except Exception as e:
                logger.error(f"PubMed EFetch failed: {e}")
                if attempt < max_retries - 1:
                    continue
                return []

        return []

    def _parse_pubmed_xml(self, xml_text: str) -> List[Dict[str, Any]]:
        """
        Parse PubMed XML response into paper dicts.

        Args:
            xml_text: XML response from EFetch

        Returns:
            list: Parsed paper metadata
        """
        papers = []

        try:
            root = ET.fromstring(xml_text)

            for article in root.findall(".//PubmedArticle"):
                paper = self._parse_article(article)
                if paper:
                    papers.append(paper)

        except ET.ParseError as e:
            logger.error(f"XML parsing failed: {e}")

        return papers

    def _parse_article(self, article: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse a single PubmedArticle element."""
        try:
            medline = article.find(".//MedlineCitation")
            if medline is None:
                return None

            pmid_elem = medline.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else ""

            # Article info
            article_elem = medline.find(".//Article")
            if article_elem is None:
                return None

            # Title
            title_elem = article_elem.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else ""

            # Abstract
            abstract_parts = []
            for abs_text in article_elem.findall(".//AbstractText"):
                if abs_text.text:
                    label = abs_text.get("Label", "")
                    if label:
                        abstract_parts.append(f"{label}: {abs_text.text}")
                    else:
                        abstract_parts.append(abs_text.text)
            abstract = " ".join(abstract_parts)

            # Authors
            authors = []
            for author in article_elem.findall(".//Author"):
                lastname = author.find("LastName")
                forename = author.find("ForeName")
                if lastname is not None:
                    name = lastname.text
                    if forename is not None:
                        name = f"{lastname.text}, {forename.text[0]}."
                    authors.append(name)

            # Journal
            journal_elem = article_elem.find(".//Journal")
            journal = ""
            if journal_elem is not None:
                title_elem = journal_elem.find(".//Title")
                if title_elem is not None:
                    journal = title_elem.text

            # Year
            year = None
            pub_date = article_elem.find(".//PubDate")
            if pub_date is not None:
                year_elem = pub_date.find("Year")
                if year_elem is not None:
                    year = int(year_elem.text)

            # Article types
            article_types = []
            for pub_type in article_elem.findall(".//PublicationType"):
                if pub_type.text:
                    article_types.append(pub_type.text)

            # DOI
            doi = ""
            for article_id in article.findall(".//ArticleId"):
                if article_id.get("IdType") == "doi":
                    doi = article_id.text
                    break

            # PMC ID (for free full text)
            pmc_id = ""
            for article_id in article.findall(".//ArticleId"):
                if article_id.get("IdType") == "pmc":
                    pmc_id = article_id.text
                    break

            return {
                "pmid": pmid,
                "title": title,
                "authors": authors,
                "year": year,
                "abstract": abstract,
                "journal": journal,
                "article_types": article_types,
                "doi": doi,
                "pmc_id": pmc_id,
                "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "pdf_link": (
                    f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/" if pmc_id else ""
                ),
                "source": "pubmed",
            }

        except Exception as e:
            logger.error(f"Article parsing failed: {e}")
            return None

    def search_systematic_reviews(self, topic: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search specifically for systematic reviews and meta-analyses.

        Args:
            topic: Research topic
            max_results: Maximum results

        Returns:
            list: Systematic review papers
        """
        query = f"{topic} AND (systematic review[pt] OR meta-analysis[pt])"
        return self.search(query, max_results)

    def search_clinical_trials(self, topic: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search specifically for clinical trials.

        Args:
            topic: Research topic
            max_results: Maximum results

        Returns:
            list: Clinical trial papers
        """
        query = f"{topic} AND (randomized controlled trial[pt] OR clinical trial[pt])"
        return self.search(query, max_results)

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            "requests_made": self._requests_made,
            "has_api_key": bool(self.api_key),
            "rate_limit": f"{1 / self.rate_limit:.1f} req/sec",
        }
