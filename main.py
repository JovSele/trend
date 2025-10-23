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
    Google Trends analýza pre VŠETKY AI keywords (až 3)
    Vypočíta priemer + identifikuje best keyword
    """
    import pandas as pd
    import time
    
    results = []
    total = len(df)
    
    print(f"\n🔍 GOOGLE TRENDS (Multi-Keyword Analysis):")
    print(f"   Patenty: {total}")
    print(f"   Analyzujem až 3 keywords na patent\n")
    
    for idx, row in df.iterrows():
        print(f"   📄 Patent {idx + 1}/{total}:")
        
        # AI keywords (až 3)
        keywords_list = row.get('AI_Keywords_List', [])
        
        if not keywords_list:
            print("      ⚠️  Žiadne AI keywords")
            results.append(_empty_trends_result(idx))
            continue
        
        # Analyzujeme až 3 keywords
        keyword_results = []
        
        for i, keyword in enumerate(keywords_list[:3], 1):
            print(f"      KW{i}: [{keyword}]...", end='', flush=True)
            
            # Google Trends analýza
            result = trends_analyzer.analyze_patent(
                title=keyword,
                abstract=None
            )
            
            keyword_results.append({
                'keyword': keyword,
                'score': result['final_score'],
                'direction': result['trend_direction'],
                'avg_interest': result['avg_interest']
            })
            
            print(f" ✓ (score: {result['final_score']:.3f}, {result['trend_direction']})")
            
            # Delay medzi keywords
            if i < len(keywords_list[:3]):
                time.sleep(2)
        
        # Výpočet agregovaných metrík
        avg_score = sum(r['score'] for r in keyword_results) / len(keyword_results)
        best_keyword = max(keyword_results, key=lambda x: x['score'])
        
        # Trend consensus
        directions = [r['direction'] for r in keyword_results]
        if directions.count('rising') >= 2:
            consensus = 'Rising'
        elif directions.count('falling') >= 2:
            consensus = 'Falling'
        else:
            consensus = 'Mixed'
        
        print(f"      📊 AVG: {avg_score:.3f} | BEST: {best_keyword['keyword']} | CONSENSUS: {consensus}\n")
        
        # Uloženie výsledkov
        result_data = {
            'index': idx,
            'Google_Trends_Average_Score': avg_score,
            'Google_Trends_Best_Keyword': best_keyword['keyword'],
            'Google_Trends_Consensus': consensus,
        }
        
        # Individuálne keywords (až 3)
        for i, kr in enumerate(keyword_results, 1):
            result_data[f'Google_Trends_Keyword_{i}'] = kr['keyword']
            result_data[f'Google_Trends_Score_{i}'] = kr['score']
            result_data[f'Google_Trends_Direction_{i}'] = kr['direction']
            result_data[f'Google_Trends_Interest_{i}'] = kr['avg_interest']
        
        results.append(result_data)
        
        # Pauza medzi patentmi
        if idx < df.index[-1]:
            time.sleep(3)
    
    print(f"✓ Multi-Keyword Google Trends analýza dokončená!\n")
    
    # Merge výsledkov
    results_df = pd.DataFrame(results).set_index('index')
    return df.join(results_df)


def _empty_trends_result(idx):
    """Prázdny výsledok pre patent bez keywords"""
    return {
        'index': idx,
        'Google_Trends_Average_Score': 0.0,
        'Google_Trends_Best_Keyword': '',
        'Google_Trends_Consensus': 'Unknown',
        'Google_Trends_Keyword_1': '',
        'Google_Trends_Score_1': 0.0,
        'Google_Trends_Direction_1': 'unknown',
        'Google_Trends_Interest_1': 0.0
    }


def _recalculate_with_trends(df, config):
    """Prepočíta Final_Score s Google Trends"""
    import numpy as np
    
    # Použijeme AVERAGE score zo všetkých keywords
    if 'Google_Trends_Average_Score' in df.columns:
        df['score_google_trends'] = df['Google_Trends_Average_Score'].fillna(0)
    else:
        df['score_google_trends'] = 0
    
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