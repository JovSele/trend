import numpy as np

class CommercialScoring:
    def __init__(self, config):
        self.config = config
        
    def calculate_scores(self, df):
        print("\n📊 VÝPOČET SKÓRE:")
        
        df = df.copy()
        
        metrics_keys = ['citations_patent', 'citations_npl', 'family_size']
        metrics = [self.config.COLUMNS[k] for k in metrics_keys]
        
        for metric in metrics:
            df[f'log_{metric}'] = np.log1p(df[metric].fillna(0))
            
            min_val = df[f'log_{metric}'].min()
            max_val = df[f'log_{metric}'].max()
            
            if max_val > min_val:
                df[f'score_{metric}'] = (df[f'log_{metric}'] - min_val) / (max_val - min_val)
            else:
                df[f'score_{metric}'] = 0
        
        col_patent = self.config.COLUMNS['citations_patent']
        col_npl = self.config.COLUMNS['citations_npl']
        col_family = self.config.COLUMNS['family_size']
        
        df['Final_Score'] = (
            df[f'score_{col_patent}'] * self.config.WEIGHTS['citations_patent'] +
            df[f'score_{col_npl}'] * self.config.WEIGHTS['citations_npl'] +
            df[f'score_{col_family}'] * self.config.WEIGHTS['family_size']
        )
        
        df = df.sort_values(by='Final_Score', ascending=False)
        
        print(f"✓ Skóre vypočítané pre {len(df)} patentov")
        if len(df) > 0:
            print(f"   Max: {df['Final_Score'].max():.4f}")
            print(f"   Avg: {df['Final_Score'].mean():.4f}")
        
        return df