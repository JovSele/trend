"""
Social Proof Module
===================
Lightweight module for tracking keyword mentions using Google Custom Search API.
Easy integration into existing projects.
"""

import requests
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class SocialProofResult:
    """Result from social proof check"""
    keyword: str
    platform: str
    mentions: int
    timestamp: str
    
    def to_dict(self):
        return asdict(self)


class SocialProof:
    """
    Main class for social proof tracking.
    
    Usage:
        sp = SocialProof(api_key="xxx", search_engine_id="yyy")
        result = sp.check("bitcoin", "reddit")
        print(f"Mentions: {result.mentions}")
    """
    
    PLATFORMS = {
        'reddit': 'reddit.com',
        'twitter': 'twitter.com',
        'x': 'x.com',
        'hackernews': 'news.ycombinator.com',
        'stackoverflow': 'stackoverflow.com',
        'github': 'github.com',
        'medium': 'medium.com',
        'youtube': 'youtube.com',
        'linkedin': 'linkedin.com',
        'facebook': 'facebook.com',
    }
    
    def __init__(self, api_key: str, search_engine_id: str, delay: float = 1.0):
        self.api_key = api_key
        self.cx = search_engine_id
        self.delay = delay
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self._last_request = None
    
    def _rate_limit(self):
        """Apply rate limiting"""
        if self._last_request:
            elapsed = time.time() - self._last_request
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
        self._last_request = time.time()
    
    def _get_domain(self, platform: str) -> str:
        """Get domain from platform name"""
        return self.PLATFORMS.get(platform.lower(), platform)
    
    def check(self, keyword: str, platform: str) -> SocialProofResult:
        """
        Check mentions of keyword on platform.
        
        Args:
            keyword: Search keyword
            platform: Platform name (e.g., 'reddit') or domain
            
        Returns:
            SocialProofResult with mention count
        """
        self._rate_limit()
        
        site = self._get_domain(platform)
        
        params = {
            'key': self.api_key,
            'cx': self.cx,
            'q': f'site:{site} {keyword}',
            'num': 1
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            mentions = 0
            if 'searchInformation' in data:
                mentions = int(data['searchInformation'].get('totalResults', 0))
            
            return SocialProofResult(
                keyword=keyword,
                platform=platform,
                mentions=mentions,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            print(f"Error checking {keyword} on {platform}: {e}")
            return SocialProofResult(
                keyword=keyword,
                platform=platform,
                mentions=0,
                timestamp=datetime.now().isoformat()
            )
    
    def check_multiple(self, keyword: str, platforms: List[str]) -> List[SocialProofResult]:
        """
        Check keyword on multiple platforms.
        
        Args:
            keyword: Search keyword
            platforms: List of platform names
            
        Returns:
            List of SocialProofResult objects
        """
        results = []
        for platform in platforms:
            result = self.check(keyword, platform)
            results.append(result)
        return results
    
    def compare(self, keywords: List[str], platform: str) -> List[SocialProofResult]:
        """
        Compare multiple keywords on single platform.
        
        Args:
            keywords: List of keywords to compare
            platform: Platform name
            
        Returns:
            List of SocialProofResult objects sorted by mentions
        """
        results = []
        for keyword in keywords:
            result = self.check(keyword, platform)
            results.append(result)
        
        results.sort(key=lambda x: x.mentions, reverse=True)
        return results


def quick_check(keyword: str, platform: str, api_key: str, search_engine_id: str) -> int:
    """
    Quick check without creating instance.
    
    Returns:
        Number of mentions
    """
    sp = SocialProof(api_key, search_engine_id)
    result = sp.check(keyword, platform)
    return result.mentions


if __name__ == "__main__":
    print("""
Social Proof Module
===================

Usage:
    from modules.social_proof import SocialProof
    
    sp = SocialProof(
        api_key="YOUR_API_KEY",
        search_engine_id="YOUR_CX_ID"
    )
    
    # Single check
    result = sp.check("bitcoin", "reddit")
    print(f"Mentions: {result.mentions}")
    
    # Multiple platforms
    results = sp.check_multiple("bitcoin", ["reddit", "twitter"])
    for r in results:
        print(f"{r.platform}: {r.mentions}")
    
    # Compare keywords
    results = sp.compare(["Python", "JavaScript"], "stackoverflow")
    for r in results:
        print(f"{r.keyword}: {r.mentions}")
    """)
