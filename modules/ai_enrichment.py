"""
AI Enrichment Module - Claude API Integration (English Output)
===============================================================

Uses Claude to:
1. Rewrite abstract in human-readable English
2. Extract better keywords for Google Trends in English
"""

import anthropic
import os
from dotenv import load_dotenv
import pandas as pd
import time
from typing import Dict, List
import json

load_dotenv()


class AIEnrichment:
    """Claude AI enrichment for patents - English output"""
    
    def __init__(self, model="claude-sonnet-4-20250514"):
        """
        Args:
            model: Claude model (claude-sonnet-4-20250514 recommended)
        """
        api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY nie je nastavený v .env")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        print(f"🤖 Claude API AKTIVOVANÉ (model: {model})")
    
    def enrich_patent(self, title: str, abstract: str) -> Dict:
        """
        Analyzes patent using Claude AI (English output)
        
        Args:
            title: Patent title
            abstract: Patent abstract
            
        Returns:
            {
                'human_abstract': str,  # English readable description
                'keywords': list,       # English keywords for Google Trends
                'use_cases': list,      # Practical applications in English
                'market_potential': str # Commercial potential in English
            }
        """
        
        # Prepare prompt (in English)
        prompt = self._create_prompt(title, abstract)
        
        try:
            # Claude API call
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,  # Lower = more consistent results
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse response
            response_text = message.content[0].text
            result = self._parse_response(response_text)
            
            return result
            
        except Exception as e:
            print(f"   ⚠️  AI chyba: {str(e)[:100]}")
            return self._empty_result()
    
    def _create_prompt(self, title: str, abstract: str) -> str:
        """Creates prompt for Claude - ENGLISH OUTPUT ONLY"""
        
        prompt = f"""Analyze this expired patent and help me assess its commercial potential.

PATENT TITLE: {title}

PATENT ABSTRACT: {abstract}

I need from you:

1. HUMAN ABSTRACT (2-3 sentences in ENGLISH):
   Rewrite the technical abstract into simple, understandable language. Explain WHAT this technology does and WHY it could be useful.
   IMPORTANT: Write in English only.

2. GOOGLE TRENDS KEYWORDS (3-5 keywords in ENGLISH):
   Suggest keywords that people would search on Google if they needed this technology.
   Use common, popular terms, NOT technical jargon.
   Example: instead of "thermal cycler" use "PCR machine" or "DNA testing equipment"
   IMPORTANT: All keywords must be in English.

3. USE CASES (3 specific examples in ENGLISH):
   Where could this be practically used? Real applications in specific industries.
   IMPORTANT: Write in English only.

4. MARKET POTENTIAL (1-2 sentences in ENGLISH):
   Brief assessment: Is this still relevant? Growing or declining market? Large or niche?
   IMPORTANT: Write in English only.

OUTPUT FORMAT (exactly like this):
```json
{{
  "human_abstract": "...",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "use_cases": ["use case 1", "use case 2", "use case 3"],
  "market_potential": "..."
}}
```

CRITICAL: All text in the JSON must be in ENGLISH. Do not use any other language.
Respond ONLY with JSON, nothing before or after it."""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict:
        """Parses Claude response"""
        
        try:
            # Remove markdown ```json blocks if exist
            text = response_text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            
            # Parse JSON
            data = json.loads(text.strip())
            
            # Validation
            return {
                'human_abstract': data.get('human_abstract', ''),
                'keywords': data.get('keywords', [])[:5],  # Max 5
                'use_cases': data.get('use_cases', [])[:3],  # Max 3
                'market_potential': data.get('market_potential', '')
            }
            
        except Exception as e:
            print(f"   ⚠️  Parse chyba: {e}")
            return self._empty_result()
    
    def _empty_result(self) -> Dict:
        """Empty result on error"""
        return {
            'human_abstract': '',
            'keywords': [],
            'use_cases': [],
            'market_potential': ''
        }
    
    def batch_enrich(self, patents_df: pd.DataFrame, 
                    title_col: str, abstract_col: str,
                    delay: float = 1.0) -> pd.DataFrame:
        """
        Analyzes multiple patents in batch
        
        Args:
            patents_df: DataFrame with patents
            title_col: Column name with title
            abstract_col: Column name with abstract
            delay: Pause between requests (seconds)
            
        Returns:
            DataFrame with added AI columns (in English)
        """
        
        total = len(patents_df)
        
        print(f"\n🤖 AI ENRICHMENT (Claude - English output):")
        print(f"   Patenty na spracovanie: {total}")
        print(f"   Delay medzi requestmi: {delay}s")
        print(f"   Odhadovaný čas: {(total * delay) / 60:.1f} min")
        print(f"   Odhadovaná cena: ${total * 0.006:.2f}\n")
        
        results = []
        
        for idx, row in patents_df.iterrows():
            print(f"   📄 Patent {idx + 1}/{total}...", end='')
            
            # AI analysis
            result = self.enrich_patent(
                row[title_col],
                row[abstract_col]
            )
            
            print(f" ✓")
            
            # Save results
            results.append({
                'index': idx,
                'AI_Human_Abstract': result['human_abstract'],
                'AI_Keywords': ', '.join(result['keywords']),
                'AI_Use_Cases': ' | '.join(result['use_cases']),
                'AI_Market_Potential': result['market_potential'],
                'AI_Keywords_List': result['keywords']  # For Google Trends
            })
            
            # Delay
            if idx < total - 1:
                time.sleep(delay)
        
        print(f"\n✓ AI analýza dokončená!")
        
        # Merge results
        results_df = pd.DataFrame(results).set_index('index')
        return patents_df.join(results_df)


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    """Test on one patent"""
    
    print("=" * 70)
    print("TEST: AI Enrichment Module (English output)")
    print("=" * 70)
    
    # Initialize
    try:
        enricher = AIEnrichment()
    except ValueError as e:
        print(f"❌ {e}")
        print("\nNastavte ANTHROPIC_API_KEY v .env súbore:")
        print("ANTHROPIC_API_KEY=sk-ant-api03-your-key-here")
        exit(1)
    
    # Test patent
    test_title = "Thermal Cycler with Automatic Performance Optimization"
    test_abstract = """
    A method and apparatus for thermal cycling of samples in a polymerase chain 
    reaction (PCR) process. The system includes a heating block with temperature 
    sensors and automated control mechanisms for optimizing cycle times and 
    temperature accuracy.
    """
    
    print("\n📄 TEST PATENT:")
    print(f"Title: {test_title}")
    print(f"Abstract: {test_abstract[:100]}...")
    
    # AI analysis
    print("\n🤖 Spúšťam Claude AI analýzu (English output)...\n")
    result = enricher.enrich_patent(test_title, test_abstract)
    
    # Results
    print("\n" + "=" * 70)
    print("RESULTS (in English):")
    print("=" * 70)
    
    print(f"\n📝 HUMAN ABSTRACT:")
    print(f"   {result['human_abstract']}")
    
    print(f"\n🔑 KEYWORDS (for Google Trends):")
    for kw in result['keywords']:
        print(f"   • {kw}")
    
    print(f"\n💡 USE CASES:")
    for uc in result['use_cases']:
        print(f"   • {uc}")
    
    print(f"\n📊 MARKET POTENTIAL:")
    print(f"   {result['market_potential']}")
    
    print("\n" + "=" * 70)
    
    # Batch test
    print("\nTEST: Batch processing")
    print("=" * 70)
    
    test_df = pd.DataFrame({
        'Title': [
            'Machine Learning Classification System',
            'Solar Panel Efficiency Enhancement'
        ],
        'Abstract': [
            'A neural network system for data classification...',
            'A method for improving solar panel energy conversion...'
        ]
    })
    
    result_df = enricher.batch_enrich(test_df, 'Title', 'Abstract', delay=1.0)
    
    print("\nVýsledky:")
    print(result_df[['Title', 'AI_Keywords', 'AI_Market_Potential']])