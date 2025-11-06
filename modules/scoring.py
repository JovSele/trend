import numpy as np
import pandas as pd


class CommercialScoring:
    """
    Commercial Scoring v2.0 - Percentile-Based Filtering
    =====================================================
    
    Nová logika:
    1. Tvrdý filter (eliminuje "zombie" patenty s 0 hodnotou)
    2. Normalizácia na 0-1 (nie log transformácia)
    3. 3 váhy: Citations, Family Size, Top Jurisdictions
    4. Percentilové filtrovanie (TOP N%)
    """
    
    def __init__(self, config):
        self.config = config
        
    def calculate_scores(self, df):
        """
        Vypočíta kvantitatívne skóre a filtruje TOP N% patentov
        
        Returns:
            DataFrame s patentmi nad percentile threshold
        """
        print("\n📊 VÝPOČET KVANTITATÍVNEHO SKÓRE (v2.0):")
        print(f"   Vstupné patenty: {len(df)}")
        
        df = df.copy()
        
        # 1. PRÍPRAVA DÁT
        col_citations = self.config.COLUMNS['citations_patent']
        col_family = self.config.COLUMNS['family_size']
        col_jurisdictions = self.config.COLUMNS.get('jurisdictions', 'Simple Family Member Jurisdictions')
        
        # Konverzia na numerické
        df[col_citations] = pd.to_numeric(df[col_citations], errors='coerce').fillna(0)
        df[col_family] = pd.to_numeric(df[col_family], errors='coerce').fillna(0)
        
        # Počítanie TOP jurisdikcií
        df['Top_Jurisdictions_Count'] = df[col_jurisdictions].apply(self._count_top_jurisdictions)
        
        # 2. TVRDÝ FILTER (eliminuje zombie patenty)
        initial_count = len(df)
        
        df_filtered = df[
            (df[col_citations] > 0) |           # Má aspoň 1 citáciu
            (df[col_family] > 1) |              # ALEBO je v aspoň 2 krajinách
            (df['Top_Jurisdictions_Count'] > 0) # ALEBO je v TOP jurisdikcii
        ].copy()
        
        eliminated = initial_count - len(df_filtered)
        print(f"   → Tvrdý filter: {len(df_filtered)} zostalo (eliminovaných: {eliminated})")
        
        if len(df_filtered) == 0:
            print("   ⚠️  Po tvrdom filtri nezostali žiadne patenty!")
            return pd.DataFrame()
        
        # 3. NORMALIZÁCIA (0-1)
        max_citations = df_filtered[col_citations].max()
        df_filtered['Norm_Citations'] = df_filtered[col_citations] / max_citations if max_citations else 0
        
        max_family = df_filtered[col_family].max()
        df_filtered['Norm_Family'] = df_filtered[col_family] / max_family if max_family else 0
        
        max_juris = df_filtered['Top_Jurisdictions_Count'].max()
        df_filtered['Norm_Juris'] = df_filtered['Top_Jurisdictions_Count'] / max_juris if max_juris else 0
        
        # 4. VÝPOČET FINÁLNEHO SKÓRE
        df_filtered['Quantitative_Score'] = (
            df_filtered['Norm_Citations'] * self.config.WEIGHTS['citations_patent'] +
            df_filtered['Norm_Family'] * self.config.WEIGHTS['family_size'] +
            df_filtered['Norm_Juris'] * self.config.WEIGHTS['jurisdictions']
        )
        
        # 5. PERCENTILOVÉ FILTROVANIE
        percentile = self.config.SCORING.get('min_score_percentile', 0.90)
        score_threshold = df_filtered['Quantitative_Score'].quantile(percentile)
        
        df_top = df_filtered[df_filtered['Quantitative_Score'] >= score_threshold].copy()
        df_top = df_top.sort_values(by='Quantitative_Score', ascending=False)
        
        print(f"   → Percentilový filter ({int(percentile*100)}%): {len(df_top)} patentov")
        print(f"   → Score threshold: {score_threshold:.4f}")
        
        if len(df_top) > 0:
            print(f"   → Max skóre: {df_top['Quantitative_Score'].max():.4f}")
            print(f"   → Avg skóre: {df_top['Quantitative_Score'].mean():.4f}")
        
        # Premenovanie na Final_Score pre kompatibilitu
        df_top['Final_Score'] = df_top['Quantitative_Score']
        
        return df_top
    
    def _count_top_jurisdictions(self, juris_list):
        """Počíta top jurisdikcie v patent family"""
        TOP_JURISDICTIONS = ['US', 'EP', 'WO', 'CN', 'JP', 'KR']
        
        if pd.isna(juris_list):
            return 0
        
        # Rozdelenie reťazca 'AU;;CA;;US' na jednotlivé jurisdikcie
        count = sum(1 for juris in str(juris_list).split(';;') if juris in TOP_JURISDICTIONS)
        return count