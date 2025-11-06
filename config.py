"""
Centralizovaná konfigurácia pre Unlocked Patents
Verzia 3.0 - S Percentilovým Scoringom
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
        'jurisdictions': 'Simple Family Member Jurisdictions',  # NOVÉ!
        'legal_status': 'Legal Status',
        'title': 'Title',
        'abstract': 'Abstract',
        'pub_year': 'Publication Year',
        'url': 'URL',
    }
    
    # === FILTER NASTAVENIA ===
    FILTERS = {
        'legal_status': 'EXPIRED',
        'min_citations_total': 0,  # Znížené na 0 (tvrdý filter v scoringu)
    }
    
    # === SCORING WEIGHTS (v2.0) ===
    WEIGHTS = {
        'citations_patent': 0.50,  # Technický dopad (50%)
        'family_size': 0.35,       # Komerčný dopad (35%)
        'jurisdictions': 0.15,     # Pokrytie trhu (15%)
        'google_trends': 0.00,     # Google Trends (vypnuté)
    }
    
    # === SCORING NASTAVENIA (v2.0) ===
    SCORING = {
        'min_score_percentile': 0.99,  # TOP 1% patentov
    }
    
    # === EXPORT NASTAVENIA ===
    TOP_N_PATENTS = 5  # Po scoringu a AI enrichmente
    
    # === GOOGLE TRENDS NASTAVENIA ===
    GOOGLE_TRENDS = {
        'timeframe': 'today 12-m',
        'batch_size': 5,
        'delay_between_batches': 30,
    }
    
    # === API KEYS ===
    GOOGLE_TRENDS_API_KEY = None
    CLAUDE_API_KEY = None


class ConfigDevelopment(Config):
    """Konfigurácia pre rýchle testovanie"""
    TOP_N_PATENTS = 5
    
    SCORING = {
        'min_score_percentile': 0.95,  # TOP 5% pre dev
    }
    
    GOOGLE_TRENDS = {
        'timeframe': 'today 12-m',
        'batch_size': 3,
        'delay_between_batches': 10,
    }


class ConfigWithTrends(Config):
    """Konfigurácia s povoleným Google Trends"""
    
    WEIGHTS = {
        'citations_patent': 0.40,  # 40%
        'family_size': 0.25,       # 25%
        'jurisdictions': 0.15,     # 15%
        'google_trends': 0.20,     # 20%
    }
    
    SCORING = {
        'min_score_percentile': 0.90,  # TOP 10% s Trends
    }


class ConfigProduction(ConfigWithTrends):
    """Produkčná konfigurácia"""
    TOP_N_PATENTS = 10
    
    SCORING = {
        'min_score_percentile': 0.95,  # TOP 5%
    }
    
    GOOGLE_TRENDS = {
        'timeframe': 'today 12-m',
        'batch_size': 1,
        'delay_between_batches': 90,
    }