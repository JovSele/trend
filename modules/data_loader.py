import pandas as pd
import os

class DataLoader:
    def __init__(self, config):
        self.config = config
        self.df = None
        
    def load_csv(self, filepath=None):
        if filepath is None:
            filepath = self.config.INPUT_CSV
            
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Súbor '{filepath}' sa nenašiel")
            
        print(f"📂 Načítavam: {filepath}")
        self.df = pd.read_csv(filepath, low_memory=False)
        print(f"✓ Načítaných {len(self.df)} záznamov")
        
        self._validate_columns()
        self._clean_data()
        
        return self.df
    
    def _validate_columns(self):
        required = list(self.config.COLUMNS.values())
        missing = [col for col in required if col not in self.df.columns]
        
        if missing:
            raise KeyError(f"Chýbajúce stĺpce: {missing}")
        
        print(f"✓ Všetky požadované stĺpce prítomné")
    
    def _clean_data(self):
        numeric_cols = [
            self.config.COLUMNS['citations_patent'],
            self.config.COLUMNS['citations_npl'],
            self.config.COLUMNS['family_size']
        ]
        
        for col in numeric_cols:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
        
        legal_col = self.config.COLUMNS['legal_status']
        self.df[legal_col] = self.df[legal_col].astype(str).str.upper().str.strip()
        
        print(f"✓ Dáta vyčistené")