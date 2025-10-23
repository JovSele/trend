"""
Google Trends Modul - S Webshare.io Proxy Podporou
===================================================

Analyzuje trhový dopyt pomocou Google Trends API cez proxy.
"""

from pytrends.request import TrendReq
import time
import re
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

# Načítanie .env
load_dotenv()


class GoogleTrendsAnalyzer:
    """Analyzer pre Google Trends s proxy podporou"""
    
    def __init__(self, language='en-US', timezone=360, use_proxy=True):
        """
        Args:
            language: Jazyk (en-US, sk-SK, ...)
            timezone: Časová zóna (360 = GMT+6)
            use_proxy: Použiť Webshare.io proxy (True = odporúčané)
        """
        proxies = None
        
        # Konfigurácia proxy z .env
        if use_proxy:
            proxy_user = os.getenv('WEBSHARE_PROXY_USER')
            proxy_pass = os.getenv('WEBSHARE_PROXY_PASS')
            proxy_host = os.getenv('WEBSHARE_PROXY_HOST')
            proxy_port = os.getenv('WEBSHARE_PROXY_PORT')
            
            if all([proxy_user, proxy_pass, proxy_host, proxy_port]):
                # pytrends očakáva proxy ako LIST, nie dict!
                proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
                proxies = [proxy_url]  # ← ZMENA: list namiesto dict
                print("🔒 Proxy AKTIVOVANÉ (Webshare.io)")
                print(f"   Proxy: {proxy_host}:{proxy_port}")
            else:
                print("⚠️  Proxy credentials nenájdené v .env")
                print("   Pokračujem BEZ proxy (môže byť blokované)")
        
        # Inicializácia pytrends s proxy
        self.pytrends = TrendReq(
            hl=language, 
            tz=timezone, 
            timeout=(10, 25),
            proxies=proxies  # ← LIST formát
        )
        self.cache = {}
        self.use_proxy = use_proxy and proxies is not None
        
    def analyze_patent(self, title: str, abstract: str = None, 
                      timeframe: str = 'today 5-y') -> Dict:
        """
        Analyzuje jeden patent a vráti Trends score
        
        Args:
            title: Názov patentu
            abstract: Abstrakt (nepoužíva sa v jednoduchej verzii)
            timeframe: 'today 5-y', 'today 3-y', 'today 12-m'
            
        Returns:
            {
                'keyword': str,
                'avg_interest': float (0-100),
                'trend_direction': str ('rising', 'stable', 'falling'),
                'final_score': float (0-1) normalized
            }
        """
        # Extrakcia kľúčového slova z názvu
        keyword = self._extract_keyword(title)
        
        if not keyword:
            return self._empty_result()
        
        # Skúsime získať trend data
        trend_data = self._get_trends_data(keyword, timeframe)
        
        if trend_data is None or len(trend_data) == 0:
            return self._empty_result()
        
        # Výpočet metrík
        avg_interest = trend_data['interest'].mean()
        trend_direction = self._calculate_trend_direction(trend_data)
        
        # Normalizácia na 0-1
        final_score = self._normalize_score(avg_interest, trend_direction)
        
        return {
            'keyword': keyword,
            'avg_interest': avg_interest,
            'trend_direction': trend_direction,
            'final_score': final_score
        }
    
    def _extract_keyword(self, title: str) -> str:
        """
        Extrahuje hlavné kľúčové slovo z názvu patentu
        
        Stratégia:
        1. Odstráni špeciálne znaky
        2. Vezme prvé 3-5 slov (alebo celý názov ak je krátky)
        3. Vráti ako vyhľadávací term
        """
        if not title or pd.isna(title):
            return ""
        
        # Čistenie
        title = str(title)
        title = re.sub(r'[^\w\s-]', '', title)  # Odstráni špeciálne znaky
        
        # Stop words na odstránenie
        stop_words = {
            'method', 'system', 'apparatus', 'device', 'process',
            'means', 'assembly', 'composition', 'compound',
            'a', 'an', 'the', 'and', 'or', 'for', 'with', 'using'
        }
        
        words = title.lower().split()
        words = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Ak je názov veľmi krátky, použijeme ho celý
        if len(title.split()) <= 5:
            return title.strip()[:100]  # Max 100 znakov
        
        # Inak vezmeme prvé 3-4 relevantné slová
        keyword = ' '.join(words[:4])
        return keyword[:100] if keyword else title[:100]
    
    def _get_trends_data(self, keyword: str, timeframe: str) -> Optional[pd.DataFrame]:
        """
        Získa trend data z Google Trends s error handling a retry logikou
        
        Args:
            keyword: Vyhľadávací term
            timeframe: Časové obdobie
            
        Returns:
            DataFrame s interest_over_time alebo None
        """
        # Kontrola cache
        cache_key = f"{keyword}_{timeframe}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Skúsime 3 razy s rastúcou pauzou
        for attempt in range(3):
            try:
                # Kratšia pauza ak používame proxy (1-3s), dlhšia bez proxy (3-6s)
                import random
                wait_time = random.uniform(10, 20) if self.use_proxy else random.uniform(3, 6)
                
                if attempt > 0:
                    print(f"      Pokus {attempt + 1}/3...")
                time.sleep(wait_time)
                
                # Build payload pre Google Trends
                self.pytrends.build_payload(
                    [keyword],
                    cat=0,           # Všetky kategórie
                    timeframe=timeframe,
                    geo='',          # Worldwide
                    gprop=''         # Web search
                )
                
                # Získanie dát
                interest_df = self.pytrends.interest_over_time()
                
                if interest_df.empty:
                    print(f"   ⚠️  Žiadne data pre: '{keyword}'")
                    return None
                
                # Premenujeme stĺpec na 'interest'
                if keyword in interest_df.columns:
                    interest_df['interest'] = interest_df[keyword]
                else:
                    return None
                
                # Cache
                self.cache[cache_key] = interest_df
                
                return interest_df
                
            except Exception as e:
                error_msg = str(e)
                
                # Ak je to rate limit, počkáme dlhšie
                if '429' in error_msg or 'rate limit' in error_msg.lower():
                    wait = (attempt + 1) * 30  # 30s, 60s, 90s
                    print(f"   ⚠️  Rate limit! Čakám {wait}s...")
                    time.sleep(wait)
                    continue
                
                # Iné chyby
                if attempt == 2:  # Posledný pokus
                    print(f"   ⚠️  Zlyhalo pre '{keyword}': {error_msg[:60]}")
                    return None
        
        return None
    
    def _calculate_trend_direction(self, trend_data: pd.DataFrame) -> str:
        """
        Vypočíta smer trendu (rising/stable/falling)
        
        Porovnáva prvú a druhú polovicu časového obdobia
        """
        if trend_data is None or len(trend_data) < 10:
            return 'unknown'
        
        mid = len(trend_data) // 2
        first_half = trend_data['interest'].iloc[:mid].mean()
        second_half = trend_data['interest'].iloc[mid:].mean()
        
        if first_half == 0:
            return 'stable'
        
        change_pct = ((second_half - first_half) / first_half) * 100
        
        if change_pct > 25:
            return 'rising'
        elif change_pct < -25:
            return 'falling'
        else:
            return 'stable'
    
    def _normalize_score(self, avg_interest: float, trend_direction: str) -> float:
        """
        Normalizuje score na 0-1 s bonusom za rising trend
        
        Args:
            avg_interest: Priemerný záujem (0-100)
            trend_direction: 'rising', 'stable', 'falling'
            
        Returns:
            Normalized score (0-1)
        """
        # Base score
        base = avg_interest / 100.0
        
        # Bonus/penalizácia
        if trend_direction == 'rising':
            multiplier = 1.3  # +30% bonus
        elif trend_direction == 'falling':
            multiplier = 0.7  # -30% penalizácia
        else:
            multiplier = 1.0
        
        final = base * multiplier
        
        # Clamp 0-1
        return min(max(final, 0.0), 1.0)
    
    def _empty_result(self) -> Dict:
        """Prázdny výsledok ak zlyhá"""
        return {
            'keyword': '',
            'avg_interest': 0.0,
            'trend_direction': 'unknown',
            'final_score': 0.0
        }
    
    def batch_analyze(self, patents_df: pd.DataFrame, 
                     title_col: str, abstract_col: str = None,
                     batch_size: int = 10, delay_between_batches: int = 60) -> pd.DataFrame:
        """
        Analyzuje viacero patentov v dávkach
        
        Args:
            patents_df: DataFrame s patentmi
            title_col: Názov stĺpca s titulkom
            abstract_col: Názov stĺpca s abstraktom (nepoužíva sa)
            batch_size: Počet patentov v dávke
            delay_between_batches: Pauza medzi dávkami (sekundy)
            
        Returns:
            DataFrame s pridanými stĺpcami:
            - Google_Trends_Score (0-1 normalized)
            - Google_Trends_Keyword
            - Google_Trends_Direction
            - Google_Trends_Avg_Interest (0-100)
        """
        total = len(patents_df)
        
        print(f"\n🔍 GOOGLE TRENDS ANALÝZA:")
        print(f"   Patenty na spracovanie: {total}")
        print(f"   Batch size: {batch_size}")
        print(f"   Delay medzi dávkami: {delay_between_batches}s")
        print(f"   Odhadovaný čas: {(total / batch_size * delay_between_batches) / 60:.1f} min\n")
        
        results = []
        
        for i in range(0, total, batch_size):
            batch_num = i // batch_size + 1
            total_batches = (total - 1) // batch_size + 1
            
            batch = patents_df.iloc[i:i+batch_size]
            print(f"   📦 Batch {batch_num}/{total_batches} ({len(batch)} patentov)...")
            
            for idx, row in batch.iterrows():
                result = self.analyze_patent(row[title_col])
                
                results.append({
                    'index': idx,
                    'Google_Trends_Score': result['final_score'],
                    'Google_Trends_Keyword': result['keyword'],
                    'Google_Trends_Direction': result['trend_direction'],
                    'Google_Trends_Avg_Interest': result['avg_interest']
                })
            
            # Pauza medzi dávkami (okrem poslednej)
            if i + batch_size < total:
                print(f"   ⏳ Pauza {delay_between_batches}s (rate limiting)...")
                time.sleep(delay_between_batches)
        
        print(f"\n✓ Google Trends analýza dokončená!")
        
        # Merge výsledkov
        results_df = pd.DataFrame(results).set_index('index')
        return patents_df.join(results_df)


# =============================================================================
# TESTOVANIE
# =============================================================================

if __name__ == "__main__":
    """Jednoduchý test"""
    
    analyzer = GoogleTrendsAnalyzer()
    
    # Test 1: Jeden patent
    print("=" * 60)
    print("TEST: Analýza jedného patentu")
    print("=" * 60)
    
    result = analyzer.analyze_patent(
        title="Machine Learning Classification Method",
        abstract="A method for classifying data..."
    )
    
    print(f"Keyword: {result['keyword']}")
    print(f"Avg Interest: {result['avg_interest']:.2f}/100")
    print(f"Direction: {result['trend_direction']}")
    print(f"Final Score: {result['final_score']:.3f}")
    
    # Test 2: Batch
    print("\n" + "=" * 60)
    print("TEST: Batch analýza")
    print("=" * 60)
    
    test_df = pd.DataFrame({
        'Title': [
            'Artificial Intelligence System',
            'Solar Panel Efficiency',
            'Battery Storage Technology'
        ]
    })
    
    result_df = analyzer.batch_analyze(
        test_df, 
        title_col='Title',
        batch_size=2,
        delay_between_batches=5  # Krátka pauza pre test
    )
    
    print("\nVýsledky:")
    print(result_df[['Title', 'Google_Trends_Score', 'Google_Trends_Direction']])