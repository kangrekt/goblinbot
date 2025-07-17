# 🐲 Goblin Meme Box Tool

**Goblin Meme Box Tool** adalah script otomatis berbasis Python untuk mengelola *mining box* di [Goblin Meme](https://www.goblin.meme/). Tool ini membantu menyelesaikan misi, klaim hadiah, dan memulai mining box baru secara otomatis untuk banyak akun.

> **Belum punya akun?** Silakan daftar terlebih dahulu melalui tautan berikut: **[👉 LINK DAFTAR GOBLIN MEME](https://goblin.meme?referral_code=O2MZEV)**

---

## ✨ Fitur Utama

* 🔄 **Multi Akun** – Mendukung banyak akun melalui `cookies.txt`
* 🎯 **Auto Mission** – Selesaikan misi otomatis
* 🎁 **Auto Claim Prize** – Klaim hadiah secara otomatis
* 🪙 **Auto Start Mining** – Mulai box mining baru setelah klaim
* ⏳ **Countdown Timer** – Hitung mundur hingga box siap
* 🖥️ **Tampilan Cantik** – Menggunakan [rich](https://github.com/Textualize/rich) untuk antarmuka terminal

---

## 📂 Struktur File Pendukung

| File          | Fungsi                                            |
| ------------- | ------------------------------------------------- |
| `cookies.txt` | Daftar session token akun (setiap baris = 1 akun) |
| `goblin.py`   | Script utama untuk menjalankan bot Goblin Meme    |

---

## 🔧 Instalasi

### 1. Wajib Mengaktifkan Screen

```bash
apt install screen
screen -S goblinbot
```

### 2. Clone Repo

```bash
git clone https://github.com/kangrekt/goblinbot.git
cd goblinbot
```

### 3. Install Dependensi (Virtual Environment Disarankan)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Jika belum ada `requirements.txt`, install manual:

```bash
pip install requests rich
```

---

## 🚀 Cara Menjalankan

```bash
python goblin.py
```

Pastikan file `cookies.txt` telah diisi dengan session token:

```text
eyJhbGciOi... (token akun 1)
eyJhbGciOi... (token akun 2)
```

### Alur Kerja Otomatis

1. Mengecek status box setiap akun
2. Menunggu hingga box siap (dengan countdown otomatis)
3. Menyelesaikan misi
4. Klaim hadiah
5. Memulai box mining baru
6. Mengulang setelah 24 jam

---

## 📝 Contoh Output Terminal

```
=== ✓ HADIAH BERHASIL DIKLAIM ===
• Message: Box completed successfully
• Prize Amount: 2,000 points
• New Balance: 50,000 points
• Promo Applied: ✓ Yes
```

---

## ⚠️ Catatan Penting

* Gunakan session token aktif dari akun Goblin Meme
* Jika token tidak valid, proses untuk akun tersebut akan dilewati
* Jangan gunakan akun secara berlebihan agar tidak terkena pembatasan

---

## 📜 Lisensi

MIT License © 2025 [@kangrekt](https://github.com/kangrekt)

---

## ☕ Dukungan

Jika bot ini membantumu, bantu dengan:

* ⭐ Memberi bintang di GitHub
* 🏱 Kontribusi pull request / ide baru
* 📣 Share ke komunitas lain

---
