# Docker Setup untuk Marvel vs DC Search Engine

## Prasyarat

- Docker
- Docker Compose

## Quick Start

### 1. Clone Repository
```bash
git clone <repository-url>
cd Marvel-vs-DC-Search-Engine
```

### 2. Menjalankan dengan Docker Compose

**Hanya Blazegraph:**
```bash
# Jalankan hanya service Blazegraph
docker-compose up blazegraph -d
```

**Full Stack (Blazegraph + Web App):**
```bash
# Jalankan semua services
docker-compose up -d
```

### 3. Akses Aplikasi

- **Web Application**: http://localhost:8000
- **Blazegraph Admin**: http://localhost:9999/blazegraph

## Environment Variables

Anda bisa mengatur environment variables berikut:

| Variable | Default | Deskripsi |
|----------|---------|-----------|
| `BLAZEGRAPH_HOST` | `http://34.124.187.20:8889/` | URL Blazegraph server |
| `DJANGO_DEBUG` | `True` | Mode debug Django |

## Konfigurasi Blazegraph

### Namespace Setup

1. Akses Blazegraph admin di http://localhost:9999/blazegraph
2. Buat namespace baru dengan nama `kb`:
   - Pergi ke tab "Namespaces"
   - Klik "Create Namespace"
   - Masukkan nama: `kb`
   - Pilih mode: `triples`
   - Klik "Create"

### Import Data

Untuk mengimpor data RDF/TTL ke Blazegraph:

1. Pergi ke tab "Update"
2. Pilih namespace `kb`
3. Upload file data atau paste RDF content
4. Klik "Update"

## Docker Commands

### Membangun ulang images
```bash
docker-compose build
```

### Melihat logs
```bash
# Semua services
docker-compose logs -f

# Service tertentu
docker-compose logs -f blazegraph
docker-compose logs -f web
```

### Menghentikan services
```bash
docker-compose down
```

### Menghapus volumes (hapus data)
```bash
docker-compose down -v
```

## Development dengan Docker

### Mode Development
```bash
# Jalankan dengan hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Akses shell container
```bash
# Web application
docker-compose exec web bash

# Blazegraph
docker-compose exec blazegraph bash
```

## Production Setup

### 1. Ubah Environment Variables
```bash
# Set untuk production
export BLAZEGRAPH_HOST=http://blazegraph:9999/
export DJANGO_DEBUG=False
```

### 2. Build dan Deploy
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Blazegraph tidak bisa diakses
- Periksa apakah container berjalan: `docker-compose ps`
- Cek logs: `docker-compose logs blazegraph`
- Pastikan port 9999 tidak digunakan aplikasi lain

### Web app tidak bisa connect ke Blazegraph
- Pastikan `BLAZEGRAPH_HOST` environment variable sudah benar
- Dalam Docker network, gunakan `http://blazegraph:9999/`
- Untuk akses lokal, gunakan `http://localhost:9999/`

### Performance Issues
- Sesuaikan memory allocation di `blazegraph.properties`
- Tingkatkan `JAVA_OPTS` di docker-compose.yml
- Monitor resource usage: `docker stats`

## Backup dan Restore

### Backup Data
```bash
# Backup Blazegraph data
docker-compose exec blazegraph tar -czf /tmp/backup.tar.gz /var/lib/blazegraph/data
docker cp $(docker-compose ps -q blazegraph):/tmp/backup.tar.gz ./blazegraph-backup.tar.gz
```

### Restore Data
```bash
# Restore Blazegraph data
docker cp ./blazegraph-backup.tar.gz $(docker-compose ps -q blazegraph):/tmp/backup.tar.gz
docker-compose exec blazegraph tar -xzf /tmp/backup.tar.gz -C /
docker-compose restart blazegraph
``` 