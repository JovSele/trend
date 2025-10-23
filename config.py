"""
Centralizovaná konfigurácia pre Unlocked Patents
Verzia 2.0 - S Google Trends podporou
"""

class Config:
    """Hlavná konfigurácia"""
    
    # === CESTY K SÚBOROM ===
    INPUT_CSV = 'data/vystup_lens_org.csv'
    OUTPUT_DIR = 'output'
    
    # === LENS.ORG COLUMN MAPPINGS ===
    COLUMNS = {
        'citations_patent': 'Cited by Patent Count',
        'citations_npl': 'NPL Citation Count',
        'family_size': 'Simple Family Size',
        'legal_status': 'Legal Status',
        'title': 'Title',
        'abstract': 'Abstract',
        'pub_year': 'Publication Year',
        'url': 'URL',
    }
    
    # === FILTER NASTAVENIA ===
    FILTERS = {
        'legal_status': 'EXPIRED',
        'min_citations_total': 5,
    }
    
    # === SCORING WEIGHTS ===
    # VARIANT A: Bez Google Trends (pôvodné váhy)
    WEIGHTS = {
        'citations_patent': 0.40,  # Forward Citations (40%)
        'citations_npl': 0.35,     # NPL Citations (35%)
        'family_size': 0.25,       # Family Size (25%)
        'google_trends': 0.00,     # Google Trends (0% = vypnuté)
    }
    
    # VARIANT B: S Google Trends (odkomentujte ak chcete)
    # WEIGHTS = {
    #     'citations_patent': 0.30,  # Forward Citations (30%)
    #     'citations_npl': 0.25,     # NPL Citations (25%)
    #     'family_size': 0.20,       # Family Size (20%)
    #     'google_trends': 0.25,     # Google Trends (25%)
    # }
    
    # === EXPORT NASTAVENIA ===
    TOP_N_PATENTS = 5
    
    # === GOOGLE TRENDS NASTAVENIA ===
    GOOGLE_TRENDS = {
        'timeframe': 'today 12-m',      # Posledných 5 rokov
        'batch_size': 5,               # Patentov na batch
        'delay_between_batches': 30,    # Sekúnd medzi batchmi (rate limiting)
    }
    
    # === API KEYS (Pre budúce moduly) ===
    GOOGLE_TRENDS_API_KEY = None  # pytrends nepotrebuje API key
    CLAUDE_API_KEY = None          # Pre AI enrichment


class ConfigDevelopment(Config):
    """Konfigurácia pre rýchle testovanie"""
    TOP_N_PATENTS = 5
    
    # Pre testovanie - kratšie časy
    GOOGLE_TRENDS = {
        'timeframe': 'today 12-m',      # Len posledný rok
        'batch_size': 5,                # Menšie batche
        'delay_between_batches': 60,    # Kratšia pauza
    }


class ConfigWithTrends(Config):
    """Konfigurácia s povoleným Google Trends"""
    
    # Prerozdelenie váh s Google Trends
    WEIGHTS = {
        'citations_patent': 0.30,  # 30%
        'citations_npl': 0.25,     # 25%
        'family_size': 0.20,       # 20%
        'google_trends': 0.25,     # 25%
    }


class ConfigProduction(ConfigWithTrends):
    """Produkčná konfigurácia"""
    TOP_N_PATENTS = 5
    
    GOOGLE_TRENDS = {
        'timeframe': 'today 12-m',
        'batch_size': 1,               # Väčšie batche
        'delay_between_batches': 90,   # Dlhšia pauza (bezpečnejšie)
    }