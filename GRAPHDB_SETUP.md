# GraphDB Manual Setup Guide

Jika auto-initialization GraphDB gagal, ikuti langkah manual berikut:

## Langkah 1: Akses GraphDB Workbench

1. Pastikan GraphDB sudah berjalan: `./docker-manage.sh start-graphdb`
2. Buka browser dan akses: http://localhost:7200
3. Anda akan melihat antarmuka GraphDB Workbench

## Langkah 2: Buat Repository

1. Di Workbench, klik **Setup** di menu atas
2. Pilih **Repositories** dari sidebar
3. Klik tombol **Create new repository**
4. Isi form dengan detail berikut:
   - **Repository ID**: `kb`
   - **Repository title**: `Marvel DC Knowledge Base`
   - **Repository type**: Pilih **GraphDB Free**
5. Klik **Create** untuk membuat repository

## Langkah 3: Import Data Marvel DC

1. Setelah repository berhasil dibuat, klik **Import** di menu atas
2. Pilih **RDF** dari sidebar
3. Pilih tab **Upload RDF files**
4. Upload file data: `/data/mdc_processed_csv_csv.ttl`
   - File ini ada di container GraphDB
   - Atau gunakan file `mdc_processed_csv_csv.ttl` dari project
5. Pilih **Named graph**: biarkan kosong (default graph)
6. Klik **Import** untuk mulai import data

## Langkah 4: Verifikasi Setup

1. Setelah import selesai, klik **SPARQL** di menu atas
2. Jalankan query test:
   ```sparql
   SELECT (COUNT(*) as ?count) WHERE {
     ?s ?p ?o
   }
   ```
3. Jika berhasil, Anda akan melihat jumlah triples yang telah diimport

## Langkah 5: Jalankan Aplikasi Web

1. Setelah repository dan data siap, jalankan aplikasi:
   ```bash
   ./docker-manage.sh start
   ```
2. Akses aplikasi di: http://localhost:8000

## Troubleshooting

### Repository Creation Failed
- Pastikan menggunakan **GraphDB Free** sebagai repository type
- Jika masih error, coba restart GraphDB container: `./docker-manage.sh stop && ./docker-manage.sh start-graphdb`

### Data Import Failed
- Pastikan repository sudah dibuat terlebih dahulu
- Check format data file (harus valid Turtle/TTL format)
- Periksa log di GraphDB Workbench untuk detail error

### Application Connection Error
- Pastikan repository ID adalah `kb` (case-sensitive)
- Pastikan GraphDB berjalan di port 7200
- Check environment variable `GRAPHDB_HOST` di aplikasi

## Environment Variables

Jika perlu customize setup, edit file `.env`:
```bash
GRAPHDB_HOST=http://localhost:7200/
GRAPHDB_REPOSITORY=kb
```

## Status Check

Untuk mengecek status setup:
```bash
# Check repository exists
curl -s http://localhost:7200/rest/repositories

# Check data count
curl -s "http://localhost:7200/repositories/kb?query=SELECT%20(COUNT(*)%20as%20?count)%20WHERE%20{%20?s%20?p%20?o%20}"
```

## Notes

- Setup manual ini hanya perlu dilakukan sekali
- Data akan persist selama GraphDB volume tidak dihapus
- Untuk production, pertimbangkan menggunakan GraphDB Enterprise untuk fitur lebih lengkap 