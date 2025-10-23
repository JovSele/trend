"""
AI Enrichment Module - Claude API Integration
==============================================

Používa Claude na:
1. Prepis abstraktu do ľudskej reči
2. Extrakcia lepších kľúčových slov pre Google Trends
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
    """Claude AI enrichment pre patenty"""
    
    def __init__(self, model="claude-sonnet-4-20250514"):
        """
        Args:
            model: Claude model (claude-sonnet-4-20250514 odporúčaný)
        """
        api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY nie je nastavený v .env")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        print(f"🤖 Claude API AKTIVOVANÉ (model: {model})")
    
    def enrich_patent(self, title: str, abstract: str) -> Dict:
        """
        Analyzuje patent pomocou Claude AI
        
        Args:
            title: Názov patentu
            abstract: Abstrakt patentu
            
        Returns:
            {
                'human_abstract': str,  # Zrozumiteľný opis
                'keywords': list,       # Kľúčové slová pre Google Trends
                'use_cases': list,      # Praktické použitia
                'market_potential': str # Komerčný potenciál
            }
        """
        
        # Príprava promptu
        prompt = self._create_prompt(title, abstract)
        
        try:
            # Claude API call
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,  # Nižšia = konzistentnejšie výsledky
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parsovanie odpovede
            response_text = message.content[0].text
            result = self._parse_response(response_text)
            
            return result
            
        except Exception as e:
            print(f"   ⚠️  AI chyba: {str(e)[:100]}")
            return self._empty_result()
    
    def _create_prompt(self, title: str, abstract: str) -> str:
        """Vytvorí prompt pre Claude"""
        
        prompt = f"""Analyzuj tento expirovaný patent a pomôž mi posúdiť jeho komerčný potenciál.

PATENT TITLE: {title}

PATENT ABSTRACT: {abstract}

Potrebujem od teba:

1. HUMAN ABSTRACT (2-3 vety):
   Prepíš technický abstrakt do jednoduchej, zrozumiteľnej reči. Vysvetli ČO táto technológia robí a PREČO by mohla byť užitočná.

2. GOOGLE TRENDS KEYWORDS (3-5 slov):
   Navrhni kľúčové slová, ktoré by ľudia hľadali na Google, ak by túto technológiu potrebovali. 
   Používaj bežné, populárne termíny, NIE technický žargón.
   Príklad: namiesto "thermal cycler" použi "PCR machine" alebo "DNA testing equipment"

3. USE CASES (3 konkrétne príklady):
   Kde by sa toto dalo prakticky použiť? Reálne aplikácie v konkrétnych odvetviach.

4. MARKET POTENTIAL (1-2 vety):
   Krátke zhodnotenie: Je to stále relevantné? Rastúci alebo klesajúci trh? Veľký alebo niche?

FORMÁT ODPOVEDE (presne takto):
```json
{{
  "human_abstract": "...",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "use_cases": ["use case 1", "use case 2", "use case 3"],
  "market_potential": "..."
}}
```

Odpovedaj VÝHRADNE JSON, nič pred ani za ním."""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict:
        """Parsuje Claude odpoveď"""
        
        try:
            # Odstránenie markdown ```json blokov ak existujú
            text = response_text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            
            # Parse JSON
            data = json.loads(text.strip())
            
            # Validácia
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
        """Prázdny výsledok pri chybe"""
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
        Analyzuje viacero patentov v dávke
        
        Args:
            patents_df: DataFrame s patentmi
            title_col: Názov stĺpca s titulkom
            abstract_col: Názov stĺpca s abstraktom
            delay: Pauza medzi requestmi (sekundy)
            
        Returns:
            DataFrame s pridanými AI stĺpcami
        """
        
        total = len(patents_df)
        
        print(f"\n🤖 AI ENRICHMENT (Claude):")
        print(f"   Patenty na spracovanie: {total}")
        print(f"   Delay medzi requestmi: {delay}s")
        print(f"   Odhadovaný čas: {(total * delay) / 60:.1f} min")
        print(f"   Odhadovaná cena: ${total * 0.006:.2f}\n")
        
        results = []
        
        for idx, row in patents_df.iterrows():
            print(f"   📄 Patent {idx + 1}/{total}...", end='')
            
            # AI analýza
            result = self.enrich_patent(
                row[title_col],
                row[abstract_col]
            )
            
            print(f" ✓")
            
            # Uloženie výsledkov
            results.append({
                'index': idx,
                'AI_Human_Abstract': result['human_abstract'],
                'AI_Keywords': ', '.join(result['keywords']),
                'AI_Use_Cases': ' | '.join(result['use_cases']),
                'AI_Market_Potential': result['market_potential'],
                'AI_Keywords_List': result['keywords']  # Pre Google Trends
            })
            
            # Delay
            if idx < total - 1:
                time.sleep(delay)
        
        print(f"\n✓ AI analýza dokončená!")
        
        # Merge výsledkov
        results_df = pd.DataFrame(results).set_index('index')
        return patents_df.join(results_df)


# =============================================================================
# TESTOVANIE
# =============================================================================

if __name__ == "__main__":
    """Test na jednom patente"""
    
    print("=" * 70)
    print("TEST: AI Enrichment Module")
    print("=" * 70)
    
    # Inicializácia
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
    
    # AI analýza
    print("\n🤖 Spúšťam Claude AI analýzu...\n")
    result = enricher.enrich_patent(test_title, test_abstract)
    
    # Výsledky
    print("\n" + "=" * 70)
    print("VÝSLEDKY:")
    print("=" * 70)
    
    print(f"\n📝 HUMAN ABSTRACT:")
    print(f"   {result['human_abstract']}")
    
    print(f"\n🔑 KEYWORDS (pre Google Trends):")
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