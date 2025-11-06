import pandas as pd
import numpy as np
import re

# --- KONFIGURÁCIA ---
FILE_PATH = 'data/vystup_lens_org.csv' 
OUTPUT_FILE_PATH = 'data/kuracia_patenty_nad_prahom.csv'

# Nastavenie váh pre kritériá skóre
WEIGHT_CITATIONS = 0.50     # Technický dopad
WEIGHT_FAMILY_SIZE = 0.35   # Komerčný dopad
WEIGHT_JURISDICTIONS = 0.15 # Pokrytie trhu

# Nastavenie Prahu Skóre (Threshold):
# Vyber len tie patenty, ktoré sú v TOP 10% všetkých skóre.
# (0.90 = 90. percentil)
MIN_SCORE_PERCENTILE = 0.90 
# --------------------

def count_top_jurisdictions(juris_list):
    """Pomocná funkcia na spočítanie, koľko TOP jurisdikcií je v rodine."""
    TOP_JURISDICTIONS = ['US', 'EP', 'WO', 'CN', 'JP', 'KR']
    if pd.isna(juris_list):
        return 0
    # Rozdelenie reťazca 'AU;;CA;;US' na jednotlivé jurisdikcie
    count = sum(1 for juris in str(juris_list).split(';;') if juris in TOP_JURISDICTIONS)
    return count

def calculate_patent_score_and_filter(file_path):
    """Načíta dáta, vypočíta vážené kvantitatívne skóre a filtruje nad prahom."""
    try:
        # Načítanie súboru
        df = pd.read_csv(file_path, low_memory=False)
    except FileNotFoundError:
        print(f"CHYBA: Súbor {file_path} nebol nájdený. Skontrolujte cestu.")
        return None
    
    print(f"Načítaných patentov z '{file_path}': {len(df)}")
    
    # 1. Čistenie a Príprava Dát
    
    # Konverzia na numerické hodnoty (ochrana pred chybami)
    df['Cited by Patent Count'] = pd.to_numeric(df['Cited by Patent Count'], errors='coerce').fillna(0)
    df['Simple Family Size'] = pd.to_numeric(df['Simple Family Size'], errors='coerce').fillna(0)
    
    # Vytvorenie pomocného stĺpca pre geografické pokrytie
    df['Top_Jurisdictions_Count'] = df['Simple Family Member Jurisdictions'].apply(count_top_jurisdictions)

    # 2. Aplikácia Tvrdého Filtra (Eliminácia Patentov s Nulovou Hodnotou)
    
    initial_count = len(df)
    
    # KĽÚČOVÁ ZMENA: Používame .copy() na vytvorenie skutočnej kópie a odstránenie varovaní!
    df_filtered = df[
        (df['Cited by Patent Count'] > 0) |    # Má aspoň 1 citáciu
        (df['Simple Family Size'] > 1) |       # ALEBO je v aspoň 2 krajinách
        (df['Top_Jurisdictions_Count'] > 0)    # ALEBO je v Top jurisdikcii
    ].copy() 
    
    print(f"Patentov po tvrdom filtri: {len(df_filtered)} (Eliminovaných: {initial_count - len(df_filtered)})")
    
    # 3. Normalizácia Dát (0 až 1)
    
    max_citations = df_filtered['Cited by Patent Count'].max()
    df_filtered['Norm_Citations'] = df_filtered['Cited by Patent Count'] / max_citations if max_citations else 0
    
    max_family = df_filtered['Simple Family Size'].max()
    df_filtered['Norm_Family'] = df_filtered['Simple Family Size'] / max_family if max_family else 0
    
    max_juris = df_filtered['Top_Jurisdictions_Count'].max()
    df_filtered['Norm_Juris'] = df_filtered['Top_Jurisdictions_Count'] / max_juris if max_juris else 0
    
    # 4. Výpočet Finálneho Kvantitatívneho Skóre
    df_filtered['Quantitative_Score'] = (
        df_filtered['Norm_Citations'] * WEIGHT_CITATIONS +
        df_filtered['Norm_Family'] * WEIGHT_FAMILY_SIZE +
        df_filtered['Norm_Juris'] * WEIGHT_JURISDICTIONS
    )

    # 5. Výber Hodnotných Patentov na základe Percentilového Prahu
    
    # Vypočítaj skóre na definovanom percentili (napr. 90. percentil)
    score_threshold = df_filtered['Quantitative_Score'].quantile(MIN_SCORE_PERCENTILE)
    
    # Aplikuj filter a vyber len patenty nad týmto prahom
    df_top_n = df_filtered[df_filtered['Quantitative_Score'] >= score_threshold].copy()
    
    df_top_n = df_top_n.sort_values(by='Quantitative_Score', ascending=False)

    print(f"\n--- Výber Hodnotných Patentov ---")
    print(f"Prah skóre (Percentil {int(MIN_SCORE_PERCENTILE*100)}%): {score_threshold:.4f}")
    print(f"Vybraných {len(df_top_n)} patentov s kvantitatívnym skóre nad prahom. Pripravené na kuráciu.")
    
    # Finalizácia a Uloženie
    score_column = df_top_n.pop('Quantitative_Score')
    df_top_n.insert(0, 'Quantitative_Score', score_column)
    
    df_top_n.to_csv(OUTPUT_FILE_PATH, index=False)
    
    print(f"\nSúbor s TOP patentmi ({len(df_top_n)} záznamov) bol uložený ako '{OUTPUT_FILE_PATH}'.")
    
    return df_top_n

# Spustenie skriptu
if __name__ == "__main__":
    calculate_patent_score_and_filter(FILE_PATH)