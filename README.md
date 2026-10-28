## Arsitektur Dasar

View $\rightarrow$ Service $\rightarrow$ Repository $\rightarrow$ Model

## Menjalankan Program

1.  Buat dan aktifkan virtual environment:

    ```html
    python -m venv venv
    ```

    - Windows:
      ```html
      venv\Scripts\activate
      ```
    - Linux/macOS:
      ```html
      source venv/bin/activate
      ```

2.  Install dependensi:
    ```html
    pip install -r requirements.txt
    ```
3.  Generate Secret Key:
    ```html
    python manage.py shell -c 'from django.core.management.utils import
    get_random_secret_key; print(get_random_secret_key())'
    ```
4.  Buat file .env baru berdasarkan .env.example pastikan semua data terisi termasuk secret key yang sudah di buat sebelumnya.
5.  Jalankan migrasi database:
    ```html
    python manage.py migrate
    ```
6.  Jalankan server pengembangan:
    ```html
    python manage.py runserver
    ```
7.  Buka http://127.0.0.1:8000/ di peramban Anda.

### Tambahan

- Buat Akun Superadmin

  ```html
  python manage.py createsuperuser
  ```

  atau:

  ```html
  docker exec -it [docker-id / container name] python manage.py createsuperuser
  ```

- List Command Penting Django
  1. Create Migration Model

  ```html
  python manage.py makemigrations
  ```

  2. Bikin apps Baru

  ```html
  cd apps && python ..\manage.py startapp [nama-app]
  ```
