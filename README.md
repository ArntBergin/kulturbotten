# 🎬 Kulturbotten

**Kulturbotten** er en Python-basert scraper som henter kinoprogram fra Namsos Kulturhus. Den samler informasjon om kommende filmer, inkludert:

- 📅 Dato
- 🎞️ Tittel
- 🕒 Starttidspunkt
- ⏱️ Lengde
- 🏛️ Kinosal

Perfekt for deg som vil automatisere oversikten over lokale filmvisninger – enten til en nettside, app, eller bare for å holde deg oppdatert.

---

## 🚀 Kom i gang

### Installasjon

1. Klon repoet:
   ```bash
   git clone https://github.com/ArntBergin/kulturbotten.git
   cd kulturbotten
   
2. Installer avhengigheter:

   ```bash
   pip install -r requirements.txt

3. Hente ut filminfo
   ```bash
   kulturbotten.py

📌 TODO

[ ] API-endepunkt for å hente data

[ ] Integrasjon mot home-assistant



🚀 Installere Kulturbotten via Rancher
Kulturbotten er tilgjengelig som en Helm-app direkte fra GitHub-repoet ditt. Følg disse stegene for å installere den i K3s via Rancher:

🔹 Forutsetninger
Du har lagt til GitHub-repoet som Helm App Repository i Rancher:

https://github.com/ArntBergin/kulturbotten
Du har en aktiv Nginx Ingress Controller (f.eks. Nginx Proxy Manager)

🧭 Steg-for-steg installasjon
Gå til Rancher Dashboard

Naviger til Apps → Charts

Finn kulturbotten i listen

Klikk Install

Fyll inn:

Namespace: kulturbotten (opprettes automatisk hvis den ikke finnes)

Image tag: 0.3

Ingress host: kulturbot.bergin.no

Klikk Install

🌐 Resultat
Etter installasjon vil APIet være tilgjengelig på:

https://kulturbot.bergin.no
Nginx Proxy Manager håndterer SSL og routing automatisk.
