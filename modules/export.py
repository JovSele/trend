import numpy as np
import os

class DataExporter:
    def __init__(self, config):
        self.config = config
        
    def export_top_n(self, df, n=None, filename=None):
        """Exportuje TOP N patentov s AI a Trends dátami"""
        if n is None:
            n = self.config.TOP_N_PATENTS
        
        if filename is None:
            filename = f'top_{n}_patents_for_curation.csv'
        
        import os
        os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(self.config.OUTPUT_DIR, filename)
        
        top_df = df.head(n).copy()
        
        # Základné stĺpce
        output_cols = [
            'Final_Score',
            self.config.COLUMNS['title'],
            self.config.COLUMNS['pub_year'],
            self.config.COLUMNS['citations_patent'],
            self.config.COLUMNS['citations_npl'],
            self.config.COLUMNS['family_size'],
        ]
        
        # AI stĺpce (ak existujú)
        ai_cols = ['AI_Human_Abstract', 'AI_Keywords', 'AI_Use_Cases', 'AI_Market_Potential']
        for col in ai_cols:
            if col in top_df.columns:
                output_cols.append(col)
        
        # Google Trends stĺpce - AGREGOVANÉ
        agg_trends_cols = [
            'Google_Trends_Average_Score',
            'Google_Trends_Best_Keyword', 
            'Google_Trends_Consensus'
        ]
        for col in agg_trends_cols:
            if col in top_df.columns:
                output_cols.append(col)
        
        # Google Trends - INDIVIDUÁLNE KEYWORDS (až 3)
        for i in range(1, 4):
            individual_cols = [
                f'Google_Trends_Keyword_{i}',
                f'Google_Trends_Score_{i}',
                f'Google_Trends_Direction_{i}',
                f'Google_Trends_Interest_{i}'
            ]
            for col in individual_cols:
                if col in top_df.columns:
                    output_cols.append(col)
        
        # Manuálne stĺpce
        top_df['Unlocked_Comment'] = ""
        output_cols.append('Unlocked_Comment')
        
        # Abstract a URL na koniec
        output_cols.extend([
            self.config.COLUMNS['abstract'],
            self.config.COLUMNS['url']
        ])
        
        # Export
        top_df[output_cols].to_csv(filepath, index=False, encoding='utf-8')
        
        print(f"\n💾 EXPORT DOKONČENÝ:")
        print(f"   Súbor: {filepath}")
        print(f"   Počet záznamov: {len(top_df)}")
        
        return filepath