class PatentFilters:
    def __init__(self, config):
        self.config = config
        
    def apply_all_filters(self, df):
        print("\n🔍 APLIKUJEM FILTRE:")
        print(f"   Počiatočný počet: {len(df)}")
        
        df = self.filter_legal_status(df)
        df = self.filter_min_citations(df)
        
        print(f"✓ Finálny počet: {len(df)}\n")
        return df
    
    def filter_legal_status(self, df):
        col = self.config.COLUMNS['legal_status']
        status = self.config.FILTERS['legal_status']
        
        df_filtered = df[df[col].str.upper() == status].copy()
        print(f"   → Legal Status = {status}: {len(df_filtered)}")
        return df_filtered
    
    def filter_min_citations(self, df):
        col_patent = self.config.COLUMNS['citations_patent']
        col_npl = self.config.COLUMNS['citations_npl']
        min_cit = self.config.FILTERS['min_citations_total']
        
        df_filtered = df[
            (df[col_patent] + df[col_npl]) >= min_cit
        ].copy()
        print(f"   → Min citácie >= {min_cit}: {len(df_filtered)}")
        return df_filtered