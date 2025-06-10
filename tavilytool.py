#!/usr/bin/env python3
"""
Tavily API Script for AI Agents
Execute with: python tavily.py "your search query"
"""

import os
import sys
import json
import requests  # type: ignore
import argparse
from typing import Dict, List, Optional


class TavilyAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.tavily.com"

    def search(
        self,
        query: str,
        search_depth: str = "basic",
        include_answer: bool = True,
        include_images: bool = False,
        include_raw_content: bool = False,
        max_results: int = 5,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> Dict:
        """
        Perform a search using Tavily API

        Args:
            query: Search query string
            search_depth: "basic" or "advanced"
            include_answer: Include AI-generated answer
            include_images: Include images in results
            include_raw_content: Include raw HTML content
            max_results: Maximum number of results (1-20)
            include_domains: List of domains to include
            exclude_domains: List of domains to exclude

        Returns:
            Dictionary containing search results
        """
        url = f"{self.base_url}/search"

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "include_answer": include_answer,
            "include_images": include_images,
            "include_raw_content": include_raw_content,
            "max_results": max_results,
        }

        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response from API"}


def format_results(results: Dict) -> str:
    """Format search results for display"""
    if "error" in results:
        return f"❌ Error: {results['error']}"

    output = []

    # Add answer if available
    if results.get("answer"):
        output.append("🤖 AI Answer:")
        output.append(f"   {results['answer']}")
        output.append("")

    # Add search results
    if results.get("results"):
        output.append("🔍 Search Results:")
        for i, result in enumerate(results["results"], 1):
            output.append(f"   {i}. {result.get('title', 'No title')}")
            output.append(f"      URL: {result.get('url', 'No URL')}")
            if result.get("content"):
                # Truncate content to first 200 chars
                content = (
                    result["content"][:200] + "..."
                    if len(result["content"]) > 200
                    else result["content"]
                )
                output.append(f"      Content: {content}")
            output.append("")

    # Add images if available
    if results.get("images"):
        output.append("🖼️ Images:")
        for img in results["images"][:3]:  # Show first 3 images
            output.append(f"   {img}")
        output.append("")

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="Search using Tavily API")
    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "--depth",
        choices=["basic", "advanced"],
        default="basic",
        help="Search depth (default: basic)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="Maximum number of results (default: 5)",
    )
    parser.add_argument(
        "--include-images", action="store_true", help="Include images in results"
    )
    parser.add_argument(
        "--no-answer", action="store_true", help="Don't include AI-generated answer"
    )
    parser.add_argument(
        "--include-domains", nargs="+", help="Include only these domains"
    )
    parser.add_argument("--exclude-domains", nargs="+", help="Exclude these domains")
    parser.add_argument("--raw", action="store_true", help="Output raw JSON response")

    args = parser.parse_args()

    # Get API key from environment
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("❌ Error: TAVILY_API_KEY environment variable not set")
        print("Set it with: export TAVILY_API_KEY='your-api-key-here'")
        sys.exit(1)

    # Initialize Tavily API
    tavily = TavilyAPI(api_key)

    # Perform search
    results = tavily.search(
        query=args.query,
        search_depth=args.depth,
        include_answer=not args.no_answer,
        include_images=args.include_images,
        max_results=args.max_results,
        include_domains=args.include_domains,
        exclude_domains=args.exclude_domains,
    )

    # Output results
    if args.raw:
        print(json.dumps(results, indent=2))
    else:
        print(format_results(results))


if __name__ == "__main__":
    main()
