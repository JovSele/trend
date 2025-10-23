# --- scoring_script.py ---

import pandas as pd
import numpy as np

# Uistite sa, že súbor je na rovnakej ceste, kde spúšťate skript, a je vo formáte CSV
CSV_FILE = 'vystup_lens_org.csv' 
TOP_N_PATENTS = 100 
MIN_CITATIONS_TOTAL = 5 # Minimálny súčet citácií, aby sa patent vôbec zvažoval

# Presné názvy stĺpcov z vášho súboru Lens.org
COL_CITATIONS_PATENT = 'Cited by Patent Count'
COL_CLAIMS = 'Simple Family Size'  # Použijeme Simple Family Size ako ZÁSTUPNÝ ukazovateľ pre rozsah
COL_CITATIONS_NPL = 'NPL Citation Count'
COL_LEGAL_STATUS = 'Legal Status'

# Definícia váh pre Skóre komerčného potenciálu
WEIGHTS = {
    COL_CITATIONS_PATENT: 0.40,  # Sila patentu (Forward Citations - Najdôležitejšie)
    COL_CITATIONS_NPL: 0.35,     # Súčasná odbornosť/záujem
    COL_CLAIMS: 0.25,            # Zástupný rozsah (Family Size)
}

# --- 2. FUNKCIA NA VÝPOČET SKÓRE ---
def calculate_commercial_score(df):
    
    # Krok 2.1: Normalizácia kľúčových metrík
    metrics = list(WEIGHTS.keys())
    
    for metric in metrics:
        # Aplikácia logaritmickej transformácie pre zníženie vplyvu extrémnych hodnôt
        # (patenty s 1000 citáciami by inak dominovali skóre)
        df[f'log_{metric}'] = np.log1p(df[metric].fillna(0))
        
        # Min-Max Normalizácia na škálu 0-1
        min_val = df[f'log_{metric}'].min()
        max_val = df[f'log_{metric}'].max()
        
        # Vytvorenie normalizovaného stĺpca pre bodovanie
        if max_val > min_val:
            df[f'score_{metric}'] = (df[f'log_{metric}'] - min_val) / (max_val - min_val)
        else:
            df[f'score_{metric}'] = 0
            
    # Krok 2.2: Výpočet finálneho váženého skóre
    df['Final_Score'] = (
        df[f'score_{COL_CITATIONS_PATENT}'] * WEIGHTS[COL_CITATIONS_PATENT] +
        df[f'score_{COL_CITATIONS_NPL}'] * WEIGHTS[COL_CITATIONS_NPL] +
        df[f'score_{COL_CLAIMS}'] * WEIGHTS[COL_CLAIMS]
    )
    
    return df.sort_values(by='Final_Score', ascending=False)

# --- 3. HLAVNÁ LOGIKA SKRIPTU ---
try:
    # Načítanie dát
    print(f"Načítavam dáta zo súboru: {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)
    print(f"Načítaných celkom: {len(df)} záznamov.")

    # 3.1: FILTROVANIE A ČISTENIE DÁT
    
    # a) Filter 1: Len expirované patenty
    # Predpokladá sa, že stĺpec Legal Status obsahuje text "EXPIRED" (môže byť case-sensitive!)
    df_filtered = df[df[COL_LEGAL_STATUS].str.upper() == 'EXPIRED'].copy()
    print(f"Po filtrácii expirovaných patentov zostalo: {len(df_filtered)} záznamov.")
    
    # b) Príprava numerických stĺpcov
    for col in [COL_CITATIONS_PATENT, COL_CITATIONS_NPL, COL_CLAIMS]:
        # Konverzia na čísla, chyby (ako prázdne bunky) sa menia na NaN a potom na 0
        df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce').fillna(0)
    
    # c) Filter 2: Priebežná redukcia - len patenty s minimálnym vplyvom
    df_filtered = df_filtered[
        (df_filtered[COL_CITATIONS_PATENT] + df_filtered[COL_CITATIONS_NPL]) >= MIN_CITATIONS_TOTAL
    ]
    print(f"Po filtrácii patentov s nízkym vplyvom zostalo: {len(df_filtered)} záznamov.")

    # 3.2: VÝPOČET SKÓRE
    print("Spúšťam výpočet komerčného skóre...")
    df_scored = calculate_commercial_score(df_filtered.copy())
    
    # 3.3: VÝBER TOP N PATENTOV
    top_patents = df_scored.head(TOP_N_PATENTS).copy()
    
    # 3.4: Pridanie stĺpcov pre manuálne vstupy
    top_patents['Google_Trends_Score'] = np.nan
    top_patents['Unlocked_Comment'] = ""
    top_patents['AI_Retranscription'] = ""
    
    # Uloženie TOP N patentov
    OUTPUT_FILE = f'top_{TOP_N_PATENTS}_patents_for_curation.csv'
    # Ponecháme len dôležité stĺpce pre kurátorstvo:
    output_cols = ['Final_Score', 'Title', 'Abstract', 'Publication Year', 
                   COL_CITATIONS_PATENT, COL_CITATIONS_NPL, COL_CLAIMS,
                   'Google_Trends_Score', 'Unlocked_Comment', 'AI_Retranscription', 'URL']
                   
    top_patents[output_cols].to_csv(OUTPUT_FILE, index=False)
    
    print("\n" + "=" * 60)
    print(f"✅ Hromadné spracovanie dokončené.")
    print(f"TOP {TOP_N_PATENTS} patentov pre manuálne kurátorstvo je uložených v: {OUTPUT_FILE}")
    print("Teraz môžete začať s manuálnym pridaním Google Trends a AI retranskripcií.")
    print("=" * 60)
    
except FileNotFoundError:
    print(f"❌ Chyba: Súbor '{CSV_FILE}' sa nenašiel. Uistite sa, že je správne umiestnený a má formát CSV.")
except KeyError as e:
    print(f"❌ Chyba: Chýba stĺpec {e} v súbore. Skontrolujte názvy stĺpcov.")
except Exception as e:
    print(f"❌ Nastala neočakávaná chyba: {e}")