"""
Unlocked Patents - Hlavný Orchestrátor v3.0
============================================

Pipeline:
1. Načítanie a filtrovanie
2. Base scoring
3. AI Enrichment (Human Abstract + Keywords)
4. Google Trends (použije AI keywords)
5. Final scoring
6. Export
"""

from config import Config, ConfigDevelopment
from modules import (DataLoader, PatentFilters, CommercialScoring, 
                     DataExporter, GoogleTrendsAnalyzer, AIEnrichment)


def main(use_dev_config=False, enable_ai=True, enable_google_trends=True):
    """
    Hlavná funkcia s AI a Google Trends
    
    Args:
        use_dev_config: Dev config (5 patentov)
        enable_ai: Claude AI enrichment
        enable_google_trends: Google Trends analýza
    """
    
    print("=" * 70)
    print("🔓 UNLOCKED PATENTS - Automated Patent Curation Pipeline v3.0")
    if enable_ai:
        print("   🤖 AI Enrichment: ENABLED")
    if enable_google_trends:
        print("   📈 Google Trends: ENABLED")
    print("=" * 70)
    
    config = ConfigDevelopment() if use_dev_config else Config()
    
    try:
        # === FÁZA 1: Základné Spracovanie ===
        print("\n📊 FÁZA 1: Základné Spracovanie")
        print("-" * 70)
        
        loader = DataLoader(config)
        df = loader.load_csv()
        
        filters = PatentFilters(config)
        df_filtered = filters.apply_all_filters(df)
        
        scoring = CommercialScoring(config)
        df_scored = scoring.calculate_scores(df_filtered)
        
        # TOP N patentov
        top_patents = df_scored.head(config.TOP_N_PATENTS).copy()
        
        # === FÁZA 2: AI Enrichment ===
        if enable_ai:
            print("\n🤖 FÁZA 2: AI Enrichment (Claude)")
            print("-" * 70)
            
            try:
                ai = AIEnrichment()
                top_patents = ai.batch_enrich(
                    top_patents,
                    title_col=config.COLUMNS['title'],
                    abstract_col=config.COLUMNS['abstract'],
                    delay=1.0
                )
                
                print(f"\n✓ AI enrichment dokončený!")
                
            except ValueError as e:
                print(f"\n⚠️  AI enrichment preskočený: {e}")
                enable_ai = False
        
        # === FÁZA 3: Google Trends (s AI keywords) ===
        if enable_google_trends:
            print("\n📈 FÁZA 3: Google Trends Analysis")
            print("-" * 70)
            
            trends = GoogleTrendsAnalyzer()
            
            # Ak máme AI keywords, použijeme ich
            if enable_ai and 'AI_Keywords_List' in top_patents.columns:
                print("   Používam AI-generované keywords...")
                top_patents = _trends_with_ai_keywords(top_patents, trends, config)
            else:
                print("   Používam automaticky extrahované keywords...")
                top_patents = trends.batch_analyze(
                    top_patents,
                    title_col=config.COLUMNS['title'],
                    batch_size=config.GOOGLE_TRENDS['batch_size'],
                    delay_between_batches=config.GOOGLE_TRENDS['delay_between_batches']
                )
            
            print(f"\n✓ Google Trends analýza dokončená!")
            
            # Prepočet Final Score s Google Trends
            if config.WEIGHTS.get('google_trends', 0) > 0:
                print("\n   Prepočítavam Final_Score s Google Trends...")
                top_patents = _recalculate_with_trends(top_patents, config)
        
        # === FÁZA 4: Export ===
        print("\n💾 FÁZA 4: Export")
        print("-" * 70)
        
        exporter = DataExporter(config)
        output_file = exporter.export_top_n(top_patents)
        
        # === ZÁVER ===
        print("\n" + "=" * 60)
        print(f"✅ Pipeline dokončený!")
        print(f"📄 Výstup: {output_file}")
        
        if enable_ai:
            print(f"🤖 AI Human Abstracts: ÁNO")
            print(f"🔑 AI Keywords: ÁNO")
        
        if enable_google_trends:
            avg_trends = top_patents['Google_Trends_Score'].mean()
            print(f"📈 Priemerné Trends Score: {avg_trends:.3f}")
        
        print("=" * 60)
        
        return top_patents
        
    except Exception as e:
        print(f"\n❌ Chyba: {e}")
        import traceback
        traceback.print_exc()
        return None


def _trends_with_ai_keywords(df, trends_analyzer, config):
    """
    Google Trends analýza použije AI-generované keywords
    """
    import pandas as pd
    import time
    
    results = []
    total = len(df)
    
    print(f"\n🔍 GOOGLE TRENDS (s AI keywords):")
    print(f"   Patenty: {total}")
    
    for idx, row in df.iterrows():
        print(f"   📄 Patent {idx + 1}/{total}...", end='')
        
        # AI keywords (už sú v DataFrame)
        keywords = row.get('AI_Keywords_List', [])
        
        if not keywords:
            print(" ⚠️  Žiadne keywords")
            results.append({
                'index': idx,
                'Google_Trends_Score': 0.0,
                'Google_Trends_Keyword': '',
                'Google_Trends_Direction': 'unknown',
                'Google_Trends_Avg_Interest': 0.0
            })
            continue
        
        # Použijeme LEN prvé keyword (nie všetky naraz)
        keyword = keywords[0] if keywords else ''
        
        print(f" [{keyword}]...", end='')  # ← NOVÝ RIADOK - vypíše keyword
        
        # Google Trends analýza
        result = trends_analyzer.analyze_patent(
            title=keyword,
            abstract=None
        )
        
        print(f" ✓ ({result['trend_direction']}, score: {result['final_score']:.3f})")  # ← ROZŠÍRENÝ výpis
        
        results.append({
            'index': idx,
            'Google_Trends_Score': result['final_score'],
            'Google_Trends_Keyword': keyword,
            'Google_Trends_Direction': result['trend_direction'],
            'Google_Trends_Avg_Interest': result['avg_interest']
        })
        
        time.sleep(2)  # Rate limiting
    
    # Merge výsledkov
    results_df = pd.DataFrame(results).set_index('index')
    return df.join(results_df)


def _recalculate_with_trends(df, config):
    """Prepočíta Final_Score s Google Trends"""
    import numpy as np
    
    df['score_google_trends'] = df['Google_Trends_Score'].fillna(0)
    
    w_patent = config.WEIGHTS.get('citations_patent', 0.30)
    w_npl = config.WEIGHTS.get('citations_npl', 0.30)
    w_family = config.WEIGHTS.get('family_size', 0.20)
    w_trends = config.WEIGHTS.get('google_trends', 0.20)
    
    total_weight = w_patent + w_npl + w_family + w_trends
    w_patent /= total_weight
    w_npl /= total_weight
    w_family /= total_weight
    w_trends /= total_weight
    
    col_patent = config.COLUMNS['citations_patent']
    col_npl = config.COLUMNS['citations_npl']
    col_family = config.COLUMNS['family_size']
    
    df['Final_Score'] = (
        df[f'score_{col_patent}'] * w_patent +
        df[f'score_{col_npl}'] * w_npl +
        df[f'score_{col_family}'] * w_family +
        df['score_google_trends'] * w_trends
    )
    
    df = df.sort_values(by='Final_Score', ascending=False)
    
    print(f"   ✓ Final_Score prepočítané (Trends váha: {w_trends:.1%})")
    
    return df


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Unlocked Patents Pipeline v3.0')
    parser.add_argument('--dev', action='store_true',
                       help='Dev config (5 patentov)')
    parser.add_argument('--no-ai', action='store_true',
                       help='Vypnúť AI enrichment')
    parser.add_argument('--no-trends', action='store_true',
                       help='Vypnúť Google Trends')
    
    args = parser.parse_args()
    
    main(
        use_dev_config=args.dev,
        enable_ai=not args.no_ai,
        enable_google_trends=not args.no_trends
    )