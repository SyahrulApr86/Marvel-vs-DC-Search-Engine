# Marvel vs DC Film Search App

Jejaring Semantik (CSCE604131) - Gasal 2023/2024

## Tim Pengembang

- Dianisa Wulandari - 2106702150
- Muhammad Rizqy Ramadhan - 2106632182
- Sasha Nabila Fortuna - 2106632226
- Syahrul Apriansyah - 2106708311

---
Cara menjalankan aplikasi:
1. Masuk ke dalam repositori yang sudah di-_clone_ dan jalankan perintah berikut
   untuk menyalakan _virtual environment_:

   ```shell
   python -m venv env
   ```
2. Nyalakan environment dengan perintah berikut:

   ```shell
   # Windows
   .\env\Scripts\activate
   ```
   ```
   # Linux/Unix, e.g. Ubuntu, MacOS
   source env/bin/activate
   ```
3. Install dependencies yang dibutuhkan untuk menjalankan aplikasi dengan perintah berikut:

   ```shell
   pip install -r requirements.txt
   ```

4. Jalankan aplikasi Django menggunakan server pengembangan yang berjalan secara
   lokal:

   ```shell
   python manage.py runserver
   ```

5. Bukalah `http://localhost:8000` pada browser favoritmu untuk melihat apakah aplikasi sudah berjalan dengan benar.

## Menjalankan dengan Docker

### Prasyarat
- Docker
- Docker Compose

### Quick Start dengan Docker

1. **Jalankan hanya GraphDB:**
   ```shell
   docker compose up graphdb -d
   ```

2. **Jalankan GraphDB + Redis (untuk caching):**
   ```shell
   docker compose up graphdb redis -d
   ```

3. **Jalankan semua services (GraphDB + Redis + Web App):**
   ```shell
   docker compose up -d
   ```

4. **Akses aplikasi:**
   - Web Application: http://localhost:8000
   - GraphDB Workbench: http://localhost:7200
   - Redis Cache Stats: http://localhost:8000/api/cache-stats/

### Setup Otomatis

GraphDB akan setup secara **otomatis** ketika pertama kali dijalankan:
- Repository `kb` dibuat otomatis
- Data Marvel DC di-import otomatis dari `data/mdc_processed_csv_csv.ttl` 
- Siap langsung digunakan!

**Manual Setup (jika diperlukan):**
1. `./docker-manage.sh setup-repository` - Run setup script manual
2. Atau buka http://localhost:7200 > "Setup" > "Repositories" > Create `kb`

Untuk dokumentasi lengkap Docker setup, lihat [DOCKER.md](DOCKER.md)

## Konfigurasi

### Environment Variables

| Variable | Default | Deskripsi |
|----------|---------|-----------|
| `GRAPHDB_HOST` | `http://localhost:7200/` | URL GraphDB server |
| `DJANGO_DEBUG` | `True` | Mode debug Django |

### Mode Development vs Production

**Development (lokal):**
```shell
export GRAPHDB_HOST=http://localhost:7200/
python manage.py runserver
```

**Production (Docker):**
```shell
export GRAPHDB_HOST=http://graphdb:7200/
export REDIS_HOST=redis
docker compose up -d
```

## Redis Image Caching

Aplikasi ini menggunakan Redis untuk caching gambar dari Wikidata:

### Fitur Caching:
- **Film posters** - Cache poster film dari Wikidata
- **Person photos** - Cache foto profil orang dari Wikidata
- **Lazy loading** - Gambar dimuat secara bertahap saat diperlukan
- **Automatic fallback** - Jika Redis tidak tersedia, aplikasi tetap berjalan tanpa cache

### Setup Redis:
```shell
# Jalankan setup script
./scripts/setup-redis.sh

# Atau manual dengan Docker Compose
docker compose up redis -d
```

### Cache Management:
```shell
# Lihat statistik cache
curl http://localhost:8000/api/cache-stats/

# Clear semua cache
curl -X POST -H "Content-Type: application/json" \
  -d '{"action":"clear"}' \
  http://localhost:8000/api/cache-stats/

# Clear hanya cache film
curl -X POST -H "Content-Type: application/json" \
  -d '{"action":"clear","image_type":"film"}' \
  http://localhost:8000/api/cache-stats/
```
