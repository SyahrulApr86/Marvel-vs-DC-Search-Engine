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

## 🐳 Menjalankan dengan Docker

### Prasyarat
- Docker
- Docker Compose

### Quick Start dengan Docker

1. **Jalankan hanya Blazegraph:**
   ```shell
   docker-compose up blazegraph -d
   ```

2. **Jalankan semua services (Blazegraph + Web App):**
   ```shell
   docker-compose up -d
   ```

3. **Akses aplikasi:**
   - Web Application: http://localhost:8000
   - Blazegraph Admin: http://localhost:9999/blazegraph

### Setup Namespace Blazegraph

1. Buka http://localhost:9999/blazegraph
2. Pergi ke tab "Namespaces"
3. Buat namespace baru dengan nama `kb`
4. Import data RDF/TTL melalui tab "Update"

Untuk dokumentasi lengkap Docker setup, lihat [DOCKER.md](DOCKER.md)

## ⚙️ Konfigurasi

### Environment Variables

| Variable | Default | Deskripsi |
|----------|---------|-----------|
| `BLAZEGRAPH_HOST` | `http://34.124.187.20:8889/` | URL Blazegraph server |
| `DJANGO_DEBUG` | `True` | Mode debug Django |

### Mode Development vs Production

**Development (lokal):**
```shell
export BLAZEGRAPH_HOST=http://localhost:9999/
python manage.py runserver
```

**Production (Docker):**
```shell
export BLAZEGRAPH_HOST=http://blazegraph:9999/
docker-compose up -d
```
