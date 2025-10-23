"""
Example: Social Proof Module Integration
==========================================
Ukážka použitia social proof modulu pre analýzu patentových keywords.
"""

import os
from dotenv import load_dotenv
from modules import SocialProof

# Načítanie environment premenných
load_dotenv()


def example_basic_usage():
    """Základné použitie - kontrola jedného keyword na jednej platforme"""
    
    # Inicializácia (potrebné API keys z Google Custom Search)
    api_key = os.getenv('GOOGLE_CUSTOM_SEARCH_API_KEY')
    search_engine_id = os.getenv('GOOGLE_CUSTOM_SEARCH_ENGINE_ID')
    
    if not api_key or not search_engine_id:
        print("⚠️  Chýbajú API keys v .env súbore:")
        print("   GOOGLE_CUSTOM_SEARCH_API_KEY")
        print("   GOOGLE_CUSTOM_SEARCH_ENGINE_ID")
        return
    
    sp = SocialProof(api_key=api_key, search_engine_id=search_engine_id)
    
    # Kontrola jedného keyword
    result = sp.check("artificial intelligence", "reddit")
    print(f"\n📊 Výsledok:")
    print(f"   Keyword: {result.keyword}")
    print(f"   Platform: {result.platform}")
    print(f"   Mentions: {result.mentions:,}")
    print(f"   Timestamp: {result.timestamp}")


def example_multiple_platforms():
    """Kontrola jedného keyword na viacerých platformách"""
    
    api_key = os.getenv('GOOGLE_CUSTOM_SEARCH_API_KEY')
    search_engine_id = os.getenv('GOOGLE_CUSTOM_SEARCH_ENGINE_ID')
    
    if not api_key or not search_engine_id:
        print("⚠️  Chýbajú API keys")
        return
    
    sp = SocialProof(api_key=api_key, search_engine_id=search_engine_id, delay=2.0)
    
    keyword = "blockchain"
    platforms = ["reddit", "twitter", "hackernews", "github"]
    
    print(f"\n🔍 Analýza keyword: '{keyword}'")
    print(f"   Platformy: {', '.join(platforms)}\n")
    
    results = sp.check_multiple(keyword, platforms)
    
    print("📊 Výsledky:")
    for r in results:
        print(f"   {r.platform:15s}: {r.mentions:>8,} mentions")
    
    total = sum(r.mentions for r in results)
    print(f"\n   {'TOTAL':15s}: {total:>8,} mentions")


def example_compare_keywords():
    """Porovnanie viacerých keywords na jednej platforme"""
    
    api_key = os.getenv('GOOGLE_CUSTOM_SEARCH_API_KEY')
    search_engine_id = os.getenv('GOOGLE_CUSTOM_SEARCH_ENGINE_ID')
    
    if not api_key or not search_engine_id:
        print("⚠️  Chýbajú API keys")
        return
    
    sp = SocialProof(api_key=api_key, search_engine_id=search_engine_id, delay=2.0)
    
    keywords = ["machine learning", "deep learning", "neural networks"]
    platform = "stackoverflow"
    
    print(f"\n🔍 Porovnanie keywords na: {platform}")
    print(f"   Keywords: {', '.join(keywords)}\n")
    
    results = sp.compare(keywords, platform)
    
    print("📊 Výsledky (zoradené podľa popularity):")
    for i, r in enumerate(results, 1):
        print(f"   {i}. {r.keyword:20s}: {r.mentions:>8,} mentions")


def example_patent_keywords():
    """Príklad analýzy patentových keywords"""
    
    api_key = os.getenv('GOOGLE_CUSTOM_SEARCH_API_KEY')
    search_engine_id = os.getenv('GOOGLE_CUSTOM_SEARCH_ENGINE_ID')
    
    if not api_key or not search_engine_id:
        print("⚠️  Chýbajú API keys")
        return
    
    sp = SocialProof(api_key=api_key, search_engine_id=search_engine_id, delay=2.0)
    
    # Simulácia AI-generovaných keywords z patentu
    patent_keywords = [
        "quantum computing",
        "quantum algorithms",
        "quantum cryptography"
    ]
    
    platforms = ["reddit", "hackernews", "github"]
    
    print(f"\n🔬 Analýza patentových keywords")
    print(f"   Keywords: {len(patent_keywords)}")
    print(f"   Platforms: {len(platforms)}\n")
    
    # Analýza každého keyword na všetkých platformách
    for keyword in patent_keywords:
        print(f"📌 {keyword}:")
        results = sp.check_multiple(keyword, platforms)
        
        for r in results:
            print(f"   {r.platform:15s}: {r.mentions:>6,} mentions")
        
        total = sum(r.mentions for r in results)
        print(f"   {'TOTAL':15s}: {total:>6,} mentions\n")


if __name__ == "__main__":
    print("=" * 70)
    print("🔍 SOCIAL PROOF MODULE - Examples")
    print("=" * 70)
    
    # Vyber príklad na spustenie
    print("\nDostupné príklady:")
    print("1. Základné použitie (1 keyword, 1 platform)")
    print("2. Viacero platforiem (1 keyword, N platforms)")
    print("3. Porovnanie keywords (N keywords, 1 platform)")
    print("4. Patentové keywords (N keywords, N platforms)")
    
    choice = input("\nVyber príklad (1-4): ").strip()
    
    if choice == "1":
        example_basic_usage()
    elif choice == "2":
        example_multiple_platforms()
    elif choice == "3":
        example_compare_keywords()
    elif choice == "4":
        example_patent_keywords()
    else:
        print("\n⚠️  Neplatná voľba")
        print("\nSpusti jednotlivé príklady priamo:")
        print("  python example_social_proof.py")
