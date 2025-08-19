# 🎬 Kulturbotten

**Kulturbotten** er en Python-app som samler kinoprogrammer fra Namsos kino og filmdata fra IMDb. Den gjør det enkelt å:  

- 📅 Se hvilke filmer som går på kino i dag eller en spesifikk dato  
- ⭐ Hente IMDb-rating, originaltittel og IMDb-ID for filmene  
- 🖼️ Lagre filmplakater og lage thumbnails  
- 💾 Lagrer alt i en PostgreSQL-database  

Kort sagt: **den samler kinoprogrammet, bilder og IMDb-info på ett sted.**  

---

## ⚡ Funksjoner

- 🎞️ Hent filmer for i dag, en spesifikk dato eller et helt år  
- 🏷️ Sortering etter dato og starttid  
- 🖼️ Thumbnail-generering for plakater  


---

## 📂 Databasefelt

| Felt | Beskrivelse | Ikon |
|------|-------------|------|
| `guid` | Unik ID for filmen | 🆔 |
| `movie_date` | Dato filmen vises | 📅 |
| `start_time` | Starttid for filmen | ⏰ |
| `title` | Filmens tittel | 🎬 |
| `age` | Aldersgrense | 🔞 |
| `info` | Sjanger eller info | 🏷️ |
| `length` | Varighet på filmen | ⏳ |
| `screen` | Kino-/salerom | 🏛️ |
| `filename` | Lokal sti til plakatbildet | 🖼️ |
| `thumbnail` | Lokal sti til thumbnail | 🖼️ |
| `imdb_rating` | IMDb-rating | ⭐ |
| `imdb_orgtitle` | Original tittel | 📝 |
| `imdb_id` | IMDb-ID | 🔗 |

