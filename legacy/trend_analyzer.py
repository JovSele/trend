# ---trend_analyzer.py -------------------------------------

import pandas as pd
import praw
import nltk
from nltk.corpus import stopwords
from gensim.models import LdaModel
from gensim.corpora import Dictionary
from gensim.utils import simple_preprocess
from pytrends.request import TrendReq
import matplotlib.pyplot as plt
import os
import spacy
from dotenv import load_dotenv # <-- PRIDANÉ: Pre načítanie .env

# ----------------------------------------------------------------------
# 1. KONFIGURÁCIA A NASTAVENIA
# ----------------------------------------------------------------------
load_dotenv() # <-- PRIDANÉ: Načíta premenné z .env súboru
# KĽÚČOVÉ INFORMÁCIE
CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
USER_AGENT = "PatentTrendAnalyzer v1.0 by /u/uwt101" # Zmeňte!

# Ciele zberu dát
TARGET_SUBREDDITS = ['Patents', 'IntellectualProperty', 'Law', 'Futurology', 'startups']
TIME_FILTER = 'year' # Zber dát za posledný rok
LIMIT = 1000         # Max. počet príspevkov na subreddit (pre demo, inak None)

# Čistenie textu
# Stiahnutie zoznamu stop words (ak ešte neboli stiahnuté v Gitpode)
try:
    nltk.data.find('corpora/stopwords')
except nltk.downloader.DownloadError:
    nltk.download('stopwords')
    
# Rozšírený zoznam STOP WORDS (angličtina je najbežnejšia pre technické fóra)
EN_STOP_WORDS = stopwords.words('english')

# Špecifické kľúčové slová IRELEVANTNÉ pre patenty (pridané do Stop Words)
IRRELEVANT_KEYWORDS = [
    # Geopolitika/Vojna
    'war', 'ukraine', 'russia', 'conflict', 'peace', 'sanction', 'nato', 'putin', 
    # Široká Ekonomika/Financie
    'crypto', 'bitcoin', 'stock', 'investment', 'mortgage', 'inflation', 'bank', 
    # Široká politika
    'election', 'president', 'politics', 'government', 
    # Osobné/Vzťahy
    'relationship', 'girlfriend', 'boyfriend', 'family', 'kids', 'dating', 
    # Gaming/Médiá
    'movie', 'series', 'game', 'netflix', 'meme', 'youtuber', 'bug', 'crash'
]

CUSTOM_STOP_WORDS = set(EN_STOP_WORDS + IRRELEVANT_KEYWORDS)

# ----------------------------------------------------------------------
# 2. POMOCNÉ FUNKCIE (ZBER & NLP)
# ----------------------------------------------------------------------

# Načítanie spaCy modelu len raz
# V Gitpode môže byť potrebné spustiť: python -m spacy download en_core_web_sm
try:
    nlp = spacy.load('en_core_web_sm', disable=['parser', 'ner'])
except OSError:
    print("Spacy model 'en_core_web_sm' nenájdený. Spustite: python -m spacy download en_core_web_sm")
    # Na účely demo to spustíme bez lemmatizácie, len s tokenizáciou
    nlp = None 
    print("Pokračuje sa bez lemmatizácie...")


def tokenize_a_cisti(text):
    """
    Tokenizuje, odstraňuje stop words a lemmatizuje text.
    """
    if pd.isna(text) or text is None:
        return []
    
    # Odstránenie interpunkcie a tokenizácia
    words = simple_preprocess(str(text), deacc=True) 
    
    # Aplikácia Spacy lemmatizácie a odstránenie rozšírených stop words
    if nlp:
        tokens = [
            token.lemma_.lower() 
            for token in nlp(" ".join(words)) 
            if token.lemma_.lower() not in CUSTOM_STOP_WORDS and token.is_alpha and len(token) > 2
        ]
    else: # Fallback bez Spacy (bez lemmatizácie)
        tokens = [
            word.lower()
            for word in words
            if word.lower() not in CUSTOM_STOP_WORDS and word.isalpha() and len(word) > 2
        ]
        
    return tokens


def get_reddit_data():
    """
    Zbiera dáta z Redditu a vytvára DataFrame.
    """
    print(f"Spúšťam zber dát z Reddit subreddits: {', '.join(TARGET_SUBREDDITS)} (filter: {TIME_FILTER})")
    
    reddit = praw.Reddit(client_id=CLIENT_ID,
                         client_secret=CLIENT_SECRET,
                         user_agent=USER_AGENT)
    
    data = []
    
    for subreddit_name in TARGET_SUBREDDITS:
        subreddit = reddit.subreddit(subreddit_name)
        
        # Získanie "Top" príspevkov, pretože sú relevantnejšie pre trendy
        for submission in subreddit.top(time_filter=TIME_FILTER, limit=LIMIT):
            data.append({
                'id': submission.id,
                'title': submission.title,
                'text': submission.selftext,
                'subreddit': subreddit_name,
                'score': submission.score,
                'num_comments': submission.num_comments
            })

    df = pd.DataFrame(data)
    # Kombinácia titulku a textu pre analýzu
    df['full_text'] = df['title'].fillna('') + ' ' + df['text'].fillna('')
    
    # Odstránenie duplikátov
    df = df.drop_duplicates(subset=['id']).reset_index(drop=True)
    
    print(f"Zozbieraných celkom {len(df)} príspevkov.")
    return df

# ----------------------------------------------------------------------
# 3. HLAVNÁ ANALÝZA TRENDOV
# ----------------------------------------------------------------------

def run_patent_trend_analysis():
    # Krok 1: Zber a Čistenie
    df = get_reddit_data()
    
    # Hrubé filtrovanie - príspevky, ktorých titulok alebo text obsahuje IRELEVANTNÉ KĽÚČOVÉ SLOVÁ
    pattern = '|'.join([term.lower() for term in IRRELEVANT_KEYWORDS])
    mask_irelevant = df['full_text'].str.contains(pattern, case=False, na=False)
    
    df_cisty = df[~mask_irelevant].copy()
    print(f"Po odstránení irelevantných tém (Geopolitika/Zábava): {len(df_cisty)} príspevkov zostalo.")
    
    # Aplikácia jemného čistenia a tokenizácie
    df_cisty['tokens'] = df_cisty['full_text'].apply(tokenize_a_cisti)
    
    # Filtrácia prázdnych príspevkov po čistená
    documents = df_cisty['tokens'].tolist()
    documents = [doc for doc in documents if doc] # Odstránenie prázdnych zoznamov
    
    if not documents:
        print("Chyba: Žiadne relevantné príspevky nezostali po čistení. Ukončujem analýzu.")
        return

    # Krok 2: Topic Modeling (LDA)
    print("\nSpúšťam Topic Modeling (LDA)...")
    dictionary = Dictionary(documents)
    corpus = [dictionary.doc2bow(doc) for doc in documents]
    
    # Trénovanie LDA modelu (5 hlavných patentových trendov)
    NUM_TOPICS = 5
    lda_model = LdaModel(corpus=corpus,
                         id2word=dictionary,
                         num_topics=NUM_TOPICS,
                         random_state=100,
                         chunksize=100,
                         passes=10,
                         per_word_topics=True)

    print("\n--- IDENTIFIKOVANÉ PATENTOVÉ TRENDY ---")
    trends = {}
    for i, topic in lda_model.show_topics(formatted=False, num_topics=NUM_TOPICS, num_words=5):
        keywords = [word for word, prob in topic]
        trend_name = f"Téma {i+1}"
        trends[trend_name] = keywords
        print(f"Trend {i+1}: {', '.join(keywords)}")

    # Krok 3: Validácia najsilnejšieho trendu v Google Trends
    
    # Zjednodušená metóda: zoberieme kľúčové slová z prvého (najsilnejšieho) trendu
    if trends:
        # Zoberieme len prvé 3 najsilnejšie slová pre Google Trends API
        main_keywords = trends["Téma 1"][:3] 
        print(f"\nValidujem najsilnejší Trend 1 ({main_keywords}) v Google Trends...")
        
        # Inicializácia pytrends
        pytrends = TrendReq(hl='en-US', tz=360) 
        
        try:
            pytrends.build_payload(main_keywords, cat=0, timeframe='today 12-m', geo='')
            df_pytrends = pytrends.interest_over_time()
            
            if df_pytrends.empty or 'isPartial' in df_pytrends.columns and df_pytrends['isPartial'].any():
                 print("Chyba: Google Trends nevrátili dáta. Možno sú kľúčové slová príliš špecifické/nezmyselné.")
                 return
                 
            # Krok 4: Vizualizácia
            plt.figure(figsize=(12, 6))
            df_pytrends.drop(columns=['isPartial'], errors='ignore').plot(ax=plt.gca())
            plt.title(f"Google Trend (Posledných 12m) pre Kľúčové Slová z Trendu: {', '.join(main_keywords)}")
            plt.ylabel("Index Hľadanosti (0-100)")
            plt.xlabel("Dátum")
            
            # Uloženie grafu, aby ho bolo možné zobraziť v Gitpode (alebo stiahnuť)
            output_file = "google_trend_validation.png"
            plt.savefig(output_file)
            print(f"\nAnalýza Dokončená. Graf uložený ako: {output_file}")
            print("Ak používate Gitpod, môžete graf otvoriť kliknutím na súbor.")
            
        except Exception as e:
            print(f"Chyba pri prístupe k Google Trends: {e}")
            print("Uistite sa, že kľúčové slová nie sú príliš široké.")
    else:
        print("Neboli identifikované žiadne témy na validáciu.")


if __name__ == "__main__":
    # Kontrola, či sú nastavené API kľúče
    if not CLIENT_ID or not CLIENT_SECRET:
        print("CHYBA: Nenastavili ste REDDIT_CLIENT_ID a REDDIT_CLIENT_SECRET ako environmentálne premenné!")
        print("Pre Gitpod, to môžete urobiť v Nastaveniach > Environment Variables.")
    else:
        run_patent_trend_analysis()