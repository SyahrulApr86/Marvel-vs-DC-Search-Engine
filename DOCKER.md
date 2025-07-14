# Docker Setup untuk Marvel vs DC Search Engine dengan GraphDB

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

**Hanya GraphDB:**
```bash
# Jalankan hanya service GraphDB
docker-compose up graphdb -d
```

**Full Stack (GraphDB + Web App):**
```bash
# Jalankan semua services
docker-compose up -d
```

### 3. Akses Aplikasi

- **Web Application**: http://localhost:8000
- **GraphDB Workbench**: http://localhost:7200

## Environment Variables

Anda bisa mengatur environment variables berikut:

| Variable | Default | Deskripsi |
|----------|---------|-----------|
| `GRAPHDB_HOST` | `http://localhost:7200/` | URL GraphDB server |
| `DJANGO_DEBUG` | `True` | Mode debug Django |

## Konfigurasi GraphDB

### Repository Setup

1. Akses GraphDB Workbench di http://localhost:7200
2. Buat repository baru dengan nama `kb`:
   - Pergi ke "Setup" > "Repositories"
   - Klik "Create new repository"
   - Pilih "GraphDB Repository"
   - Masukkan Repository ID: `kb`
   - Masukkan Repository title: `Marvel DC Knowledge Base`
   - Klik "Create"

### Import Data

Untuk mengimpor data RDF/TTL ke GraphDB:

1. Pergi ke "Import" > "RDF"
2. Pilih repository `kb`
3. Upload file data atau paste RDF content
4. Klik "Import"

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
docker-compose logs -f graphdb
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

# GraphDB
docker-compose exec graphdb bash
```

## Production Setup

### 1. Ubah Environment Variables
```bash
# Set untuk production
export GRAPHDB_HOST=http://graphdb:7200/
export DJANGO_DEBUG=False
```

### 2. Build dan Deploy
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Troubleshooting

### GraphDB tidak bisa diakses
- Periksa apakah container berjalan: `docker-compose ps`
- Cek logs: `docker-compose logs graphdb`
- Pastikan port 7200 tidak digunakan aplikasi lain

### Web app tidak bisa connect ke GraphDB
- Pastikan `GRAPHDB_HOST` environment variable sudah benar
- Dalam Docker network, gunakan `http://graphdb:7200/`
- Untuk akses lokal, gunakan `http://localhost:7200/`

### Performance Issues
- Sesuaikan memory allocation di `graphdb.properties`
- Tingkatkan `GDB_HEAP_SIZE` di docker-compose.yml
- Monitor resource usage: `docker stats`

## Backup dan Restore

### Backup Data
```bash
# Backup GraphDB data
docker-compose exec graphdb tar -czf /tmp/backup.tar.gz /opt/graphdb/home
docker cp $(docker-compose ps -q graphdb):/tmp/backup.tar.gz ./graphdb-backup.tar.gz
```

### Restore Data
```bash
# Restore GraphDB data
docker cp ./graphdb-backup.tar.gz $(docker-compose ps -q graphdb):/tmp/backup.tar.gz
docker-compose exec graphdb tar -xzf /tmp/backup.tar.gz -C /
docker-compose restart graphdb
``` 