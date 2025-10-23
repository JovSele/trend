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
