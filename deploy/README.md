# Deployment Django (Docker + Nginx + Gunicorn)

Panduan menjalankan aplikasi Django di server menggunakan Docker Compose,
dengan **Nginx** sebagai reverse proxy dan **Gunicorn** sebagai application server.

## Arsitektur

```
Browser ──► Nginx (port 8151) ──► Gunicorn (web:80) ──► Django
               │
               ├──► Static files (/app/staticfiles)
               └──► Media files (/app/media)
```

- **Nginx** : menerima request dari luar di port **8151**, meneruskannya ke Gunicorn.
- **Gunicorn** : menjalankan aplikasi Django di port **80** (internal antar-container).
- **Static files** : disajikan langsung oleh Nginx dari folder `staticfiles/` (hasil `collectstatic`).
- **Media files** : disajikan langsung oleh Nginx dari folder `media/` (hasil upload / `ImageField`). Jangan pernah menyajikan media lewat Django di production (WhiteNoise hanya menangani static, bukan media).

## Prasyarat

- Docker & Docker Compose terpasang di server.
- Folder `deploy/` berisi `docker-compose.yml` dan `nginx.conf.template`.
- Buat file `nginx.conf` dari template **sebelum** menjalankan compose:

  ```bash
  cd deploy
  cp nginx.conf.template nginx.conf
  ```

  > `docker-compose.yml` me-mount `./nginx.conf` ke container Nginx. Jika memakai
  > CI/CD, generate file ini (mis. via `envsubst`) di langkah deploy.

## Langkah 1 — Siapkan file `.env`

Buat file `.env` di **root proyek** (sejajar dengan `manage.py`) jika belum ada:

```bash
cp .env.example .env
```

Isi dengan nilai yang sesuai:

```env
PORT=8000
SECRET_KEY=<isi-dengan-secret-key-acak>
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,<ip-server-atau-domain>
```

> Generate secret key:
>
> ```bash
> python manage.py shell -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
> ```

## Langkah 2 — Build & jalankan

Dari folder `deploy/`:

```bash
cd deploy
docker compose up -d --build
```

Perintah ini akan:

1. Build image dari `DockerFile`.
2. Menjalankan migrasi database (`python manage.py migrate`).
3. Mengumpulkan file statis (`python manage.py collectstatic --noinput`).
4. Menjalankan Gunicorn dengan 3 worker.

## Langkah 3 — Akses aplikasi

- Melalui Nginx (publik): `http://<ip-server>:8151/`
- Langsung ke Gunicorn (debug lokal): `http://127.0.0.1:8000/`

## Langkah 4 — Buat superuser

```bash
docker compose exec web python manage.py createsuperuser
```

## Perintah berguna

```bash
# Lihat log
docker compose logs -f web
docker compose logs -f nginx

# Restart
docker compose restart web

# Stop (tanpa hapus container)
docker compose stop

# Stop + hapus container
docker compose down

# Stop + hapus container DAN volume
docker compose down -v
```

## Catatan produksi

- Pastikan `.env` berisi `SECRET_KEY` dan `ALLOWED_HOSTS` sebelum deploy.
- Data SQLite tersimpan di host lewat bind mount `../:/app`, sehingga tetap aman saat
  container dihapus.
- File media tersimpan di folder `media/` di root proyek (bind mount ke `/app/media`).
  Folder ini dibuat otomatis saat pertama upload; untuk data contoh jalankan
  `python manage.py seed_products`. Nginx membaca folder ini secara read-only,
  jadi pastikan `media/` ikut di-deploy/backup bersama kode & `db.sqlite3`.
- Untuk produksi yang lebih ketat, pertimbangkan:
  - Tidak me-mount seluruh kode (`../:/app`) agar build lebih terkontrol.
  - Mengarahkan port publik Nginx sesuai domain/firewall Anda (default **8151**).
- Kalau tidak pakai CI / CD Pastikan untuk menghapus folder `.github`

## Setting CI / CD Github | runs-on: ubuntu-latest

Catatan: Setelah di coba gagal `time out`, kemungkinan karena akses github nya terkunci karena beda jaringan atau server di setup khusus akses nya melalui jaringan atau internet perusahaan.

### 1. Konfigurasi GitHub Secrets

- `VPS_HOST`: IP Address VPS Anda.
- `VPS_USER`: Username SSH untuk deploy (direkomendasikan menggunakan `deploy`).
- `VPS_SSH_KEY`: Isi dengan Private Key SSH (biasanya diambil dari `~/.ssh/github_actions_deploy`).

### 2. Setup VPS

Pastikan sudah server dan folder tersimpan aman dan siap di jalankan. Lalu pastikan juga path untuk data project sudah benar. lalu ubah di .github\workflows\deploy.yml bagian path server nya.

Buat SSH KEY:

```html
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions_deploy
```

Daftarkan Public Key:

```html
cat ~/.ssh/github_actions_deploy.pub >> ~/.ssh/authorized_keys
```

Ambil VPS_SSH_KEY:

```html
cat ~/.ssh/github_actions_deploy
```

## Setting CI / CD Github Self Host

Lihat Tutorial Di Github Action sampai batas `# Last step, run it!`
Lalu lanjut setup agar runner bisa jalan otomatis ketika server di jalankan atau di restart.

- Jika awal mau clone project pastikan sudah membuat akses SSH dulu. dengan cara:
  ```html
  ssh-keygen -t ed25519 -C "email@gmail.com"
  ```
- Ambil Public Key yang untuk di daftarkan di akun github
  ```html
  cat ~/.ssh/id_ed25519.pub
  ```
- Pasang di Akun GitHub Anda
  - Buka GitHub SSH Keys Settings.
  - Klik New SSH Key.
  - Beri judul (contoh: VPS-Server).
  - Paste string yang tadi di-copy ke kolom Key, lalu klik Add SSH Key.
- Test Koneksi Github
  ```html
  ssh -T git@github.com
  ```
- Saat Mau clone project di server
  ```html
  git clone git@github.com:username-kamu/nama-repo.git
  ```
- Atur Identitas Commit di Repo Baru (Opsional ?)

  ```html
  cd /path/to/repo-baru git config user.name "Nama Kamu" git config user.email
  "email_github_kamu@example.com"
  ```

- Konfigurasi GitHub Secret:
  `VPS_USER` -> Username SSH untuk mengetahui nama folder home project yang digunakan (direkomendasikan di user `deploy`).
- Masuk ke folder runner yang telah di buat sebelumnya
- Ketik Perintah ini untuk install ke service:

  ```html
  sudo ./svc.sh install
  ```

- Lalu Jalankan Service nya:

  ```html
  sudo ./svc.sh start
  ```
