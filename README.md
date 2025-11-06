# krok 1
pip install -r requirements.txt --break-system-packages
# krok 2
python main.py --dev --trends
# Aktivujte venv - virtulane prostredie
source .venv/bin/activate



# Odstráňte .env z gitu (ale ponechajte lokálne)
git rm --cached .env
# Commitnite zmenu
git add .gitignore
git commit -m "Remove .env from git tracking"



# .env súbor
# Kľúče by mali byť v súlade s tými, ktoré očakáva funkcia os.getenv()
REDDIT_CLIENT_ID="_PR_IxAmI8IVtpEra3YH4g"
REDDIT_CLIENT_SECRET="t9UY7N7UE4S3l2lmVLtOJ2u1UevieA"
# Prípadne iné, ktoré potrebujete...

# Webshare.io credentials
WEBSHARE_PROXY_USER=twbcadjq
WEBSHARE_PROXY_PASS=gl6mb2qsr1sr
WEBSHARE_PROXY_HOST=64.137.96.74
WEBSHARE_PROXY_PORT=6641

# API Key Claude
# Nove API https://console.anthropic.com/dashboard


popis:
Programovací tip (Analýza pre databázu):
Pri tvorbe databázy by si mal primárne využívať klasifikáciu patentov, najmä Medzinárodné patentové triedenie (IPC) alebo Cooperative Patent Classification (CPC).

Pre oblasť IT/Počítačových technológií sa zameraj na:

IPC triedy:

G06F (Elektrické digitálne spracovanie dát).

H04L (Prenos digitálnych informácií, napr. v sieťach).

G06N (Počítačové systémy založené na špecifických výpočtových modeloch, napr. AI/ML).

++++++++++++
👏 Toto je vynikajúci a pragmatický prístup! Kurátorovaná databáza so zameraním na vysokohodnotné expirované patenty je oveľa užitočnejšia ako hromada neštruktúrovaných dát. Tým, že ideš z 50 000 na 100, vlastne hľadáš "ihlu v kope sena", ktorá má najväčší komerčný potenciál.Aby si úspešne zredukoval 50 000 patentov na 100 najlepších, musíš použiť viackrokové a prísne filtrovanie a bodovanie patentov.Tu je navrhovaný postup a kritériá, ktoré môžeš použiť vo svojom Pythone skripte:
⚙️ Krok 1: Predfiltrovanie (50 000 → ~5 000)Toto je prvé, tvrdé filtrovanie, ktoré eliminuje patenty bez reálneho komerčného využitia alebo tie, ktoré sú príliš staré/nové.
KritériáÚčelParametre na filtrovanie
1. Stav patentu a expiračná blízkosťZabezpečiť, že ide o expirované patenty (alebo blízko expirácii).Patent Status = Expired (Expirovaný) ALEBO Expected Expiration Date (Predpokladaný dátum exp.) je v rokoch 2023 - 2028.
2. Geografický dosah (Trh)Filtrovať patenty, ktoré boli dôležité na veľkých trhoch.Zahrnúť patenty podané v US (Spojené štáty), EP (Európsky patent), WO (WIPO - medzinárodné) a CN (Čína).
3. Vek patentu (Optimálna generácia)Vyhnúť sa príliš starým (nerelevantným) alebo príliš novým (príliš málo citácií) patentom.

Krok 2: 
Kvantitatívne skóre (Body) (5 000 → ~500)Po predfiltrovaní priradíš každému patentu numerické skóre, ktoré odráža jeho technickú dôležitosť.
Kvantitatívne kritériáVysvetlenie & Programovacie tipy
1. Skóre Citácií (Citation Score)Kľúčové kritérium. Patent, na ktorý sa odvoláva veľa neskorších patentov, bol technicky dôležitý a slúžil ako základ pre ďalší vývoj.Implementácia: Vytvor skóre na základe Number of Citations (Počet citácií). Napr., top 10% dostane 5 bodov, nasledujúcich 20% dostane 3 body.
2. Rodina patentov (Family Size)Čím viac verzií patentu bolo podaných v rôznych krajinách (patentová rodina), tým dôležitejší ho majiteľ považoval pre svoj globálny trh.Implementácia: Vytvor skóre na základe Patent Family Size (Veľkosť patentovej rodiny). Väčšia rodina = vyššie skóre.
3. Počet nárokov (Claims Count)Vyšší počet nárokov (Claims) často naznačuje, že vynález bol komplexnejší a má širší rozsah ochrany.Implementácia: Použi Claims Count. Patenty s nadpriemerným počtom nárokov získajú extra body.

Krok 3: 
Kurátorované Skóre a AI/Trendy (500 → 100)Tu začína skutočná kurácia, kde zapojíš externé dáta a tvoje nástroje. Toto bude pomalší, iteratívny proces.
KritériáPopis a Metodika
1. Google Trend Skóre (Pre CPC/Kľúčové Slovo)Analyzuj hlavné CPC (Cooperative Patent Classification) a kľúčové slová každého patentu.Implementácia: Pre 500 najlepších patentov automaticky alebo polo-automaticky získaj dáta z Google Trends pre ich hlavné kľúčové slová. Ak je trend rastúci alebo stabilne vysoký, skóre je vysoké.
2. AI Skóre (Tématická blízkosť k súčasným trendom)Použi NLP (Natural Language Processing) na analýzu Abstraktu a Popisu.Implementácia: Použi model (napr. na základe BERT alebo jednoduchšiu analýzu kľúčových slov) na porovnanie textu patentu s najnovšími „hype“ témami v tvojej oblasti (napr. pre IT: edge computing, GenAI, Web3; pre Energetiku: solid-state battery, smart grid). Čím bližšie, tým vyššie AI Skóre.
3. Inside Market Skóre (Trhové signály)Vyhľadaj, či spoločnosti v súčasnosti nakupujú alebo investujú do technológií súvisiacich s danou expirovanou technológiou.Implementácia: Toto je polo-manuálne. Skús automatizované Google vyhľadávanie pre Kľúčové slovo patentu + "investment" alebo "startup funding". Vysoký počet nájdených relevantných článkov = vyššie skóre trhového záujmu.

🐍 Programovanie: Stratégia redukcie 50 000 → 1 000Ak chceš znížiť objem dát 50-násobne, potrebuješ veľmi prísne a kombinované kritériá. Pre optimálne spracovanie v Pythone ti odporúčam zamerať sa na nasledujúce parametre, ktoré by mali byť ľahko dostupné v exporte z Lens.org.
1. Prvé, tvrdé filtre (Eliminácia irelevantných 50 000 → ~5 000)Tieto filtre sú binárne (áno/nie) a eliminujú drvivú väčšinu patentov.Parameter z CSVDôvod / Kritériá pre Python
A. Rok expiračnej udalostiHľadáme patenty, ktoré nedávno expirovali alebo exspirujú čoskoro. Novšie technológie sú relevantnejšie.Kritérium: Year of Expiration Event medzi 2010 a 2028. (Ak sú všetky už expirované, tak 2000-2025).
B. Typ expiračnej udalostiMnohé patenty expirovali pre nezaplatenie poplatkov. Je to signál, že majiteľ ich nepovažoval za dosť cenné.Kritérium: Vylúčiť patenty expirované z dôvodu Failure to Pay Maintenance Fee (nezaplatenie poplatkov). Hľadať skôr plne vyčerpanú 20-ročnú dobu.
C. Geografická JurisdikciaAk patent existoval len v jednej malej jurisdikcii, jeho trhový potenciál je malý.Kritérium: Zahrnúť patenty podané v US, EP, WO, CN, JP, KR. (Filter len na tieto top ekonomiky).

Kvantitatívne skóre (Bodovanie 5 000 → 1 000)Na zvyšných 5 000 patentov aplikuješ bodový systém, kde každý patent získa súčet bodov. Tvojich TOP 1 000 budú patenty s najvyšším skóre.Parameter z CSVHodnotenie a Váha (Príklad)
D. Počet citáciíNajvyššia váha (40-50% celkového skóre). Ukazuje, ako veľmi bol patent dôležitý pre následný technický rozvoj.Bodovanie: Top 1% citácií = 10 bodov, 1-5% = 7 bodov, 5-10% = 5 bodov, atď.
E. Veľkosť patentovej rodinyStredná váha (25-35%). Svedčí o globálnom komerčnom zámere pôvodného majiteľa.Bodovanie: Viac ako 5 členov rodiny = 5 bodov, 3-5 členov = 3 body.
F. Počet CPC triedPatent, ktorý má veľa rôznych klasifikácií, má tendenciu spájať rôzne technologické oblasti (interdisciplinarita).Bodovanie: Viac ako 5 rôznych CPC/IPC tried = 3 body.
G. Rok podania (Pre staré)Staré patenty (napr. pred 1990) už môžu mať iné (ne-patentové) prekážky pre komercializáciu.Bodovanie: Zníženie 2 bodov pre patenty staršie ako 30 rokov (podané pred 1995).