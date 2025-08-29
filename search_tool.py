import os
from tavily import TavilyClient
from typing import List, Dict, Any
from pydantic import BaseModel

# Fixed company configuration
COMPANY_NAME = "Apple Inc."

class SearchResult(BaseModel):
    title: str
    url: str
    content: str
    published_date: str = ""

class IndustryResearch(BaseModel):
    company_trends: List[SearchResult]
    product_trends: List[SearchResult] 
    industry_news: List[SearchResult]
    competitive_landscape: List[SearchResult]

class TavilySearchTool:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("Tavily API key is required. Set TAVILY_API_KEY environment variable.")
        self.client = TavilyClient(api_key=self.api_key)
    
    def search_company_trends(self, company_name: str = None, products: List[str] = None) -> IndustryResearch:
        """
        Comprehensive search for company and industry trends
        """
        if company_name is None:
            company_name = COMPANY_NAME
        if products is None:
            products = []
            
        try:
            # Search for company-specific trends
            company_query = f"{company_name} latest news trends 2024 2025 business strategy"
            company_results = self._perform_search(company_query, max_results=3)
            
            # Search for product trends
            product_queries = []
            for product in products[:3]:  # Limit to top 3 products
                product_queries.append(f"{product} market trends 2024 2025 industry analysis")
            
            product_results = []
            for query in product_queries:
                results = self._perform_search(query, max_results=2)
                product_results.extend(results)
            
            # Search for general industry news
            industry_query = f"{company_name} industry market analysis competitive landscape 2024"
            industry_results = self._perform_search(industry_query, max_results=3)
            
            # Search for competitive landscape
            competitive_query = f"{company_name} competitors market share analysis 2024"
            competitive_results = self._perform_search(competitive_query, max_results=3)
            
            return IndustryResearch(
                company_trends=company_results,
                product_trends=product_results,
                industry_news=industry_results,
                competitive_landscape=competitive_results
            )
            
        except Exception as e:
            raise Exception(f"Error performing industry research: {str(e)}")
    
    def _perform_search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Perform a single search query using Tavily"""
        try:
            response = self.client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_answer=True,
                include_raw_content=False
            )
            
            results = []
            for result in response.get('results', []):
                search_result = SearchResult(
                    title=result.get('title', ''),
                    url=result.get('url', ''),
                    content=result.get('content', ''),
                    published_date=result.get('published_date', '')
                )
                results.append(search_result)
            
            return results
            
        except Exception as e:
            print(f"Search error for query '{query}': {str(e)}")
            return []

def create_industry_research_prompt(research: IndustryResearch, company_name: str = None) -> str:
    """Create a formatted prompt with industry research findings"""
    if company_name is None:
        company_name = COMPANY_NAME
        
    prompt = f"""
Industry Research Summary for {company_name}:

COMPANY-SPECIFIC TRENDS:
"""
    
    for i, trend in enumerate(research.company_trends[:3], 1):
        prompt += f"{i}. {trend.title}\n   {trend.content[:300]}...\n   Source: {trend.url}\n\n"
    
    prompt += "PRODUCT MARKET TRENDS:\n"
    for i, trend in enumerate(research.product_trends[:4], 1):
        prompt += f"{i}. {trend.title}\n   {trend.content[:250]}...\n   Source: {trend.url}\n\n"
    
    prompt += "INDUSTRY NEWS & ANALYSIS:\n"
    for i, news in enumerate(research.industry_news[:3], 1):
        prompt += f"{i}. {news.title}\n   {news.content[:250]}...\n   Source: {news.url}\n\n"
    
    prompt += "COMPETITIVE LANDSCAPE:\n"
    for i, comp in enumerate(research.competitive_landscape[:3], 1):
        prompt += f"{i}. {comp.title}\n   {comp.content[:250]}...\n   Source: {comp.url}\n\n"
    
    return prompt