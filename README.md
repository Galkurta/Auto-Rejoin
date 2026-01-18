# Auto Rejoin Roblox Private Server (Rooted Android)

Script Python ini akan otomatis memantau status bermain Anda dan melakukan rejoin ke Private Server jika terdeteksi pindah ke public server atau terputus.

## ✨ Fitur

- ✅ Deteksi otomatis perpindahan server (Private → Public) menggunakan Game ID tracking
- ✅ Auto rejoin ke Private Server dalam waktu 10-30 detik
- ✅ Monitoring real-time status in-game
- ✅ SELinux auto-configuration untuk kompatibilitas maksimal

## 📋 Syarat Wajib

1. **Rooted Android Device** (Wajib - Magisk/KernelSU)
2. **Termux** app terinstall
3. **Roblox** app terinstall
4. **Roblox Cookie** (.ROBLOSECURITY) untuk Game ID tracking

## 🔧 Cara Install

### 1. Setup Termux

Buka Termux dan jalankan:

```bash
pkg update && pkg upgrade
pkg install python
pip install requests
```

### 2. Setup Storage Permission

```bash
termux-setup-storage
```

Izinkan akses storage saat diminta.

### 3. Download/Copy Script

Simpan script di folder yang mudah diakses (misal `/sdcard`):

```bash
git clone https://github.com/Galkurta/AutoRejoin.git
cd AutoRejoin
```

## ⚙️ Konfigurasi (`config.json`)

### 1. Dapatkan Link Private Server

- Buka Private Server Roblox Anda
- Copy link share (contoh: `https://www.roblox.com/share?code=XXXXX&type=Server`)

### 2. Dapatkan User ID

- Buka profil Roblox Anda
- User ID ada di URL (contoh: `roblox.com/users/12345678/profile`)

### 3. Dapatkan Roblox Cookie (.ROBLOSECURITY)

**PENTING: Cookie ini sangat rahasia! Jangan share ke siapapun!**

#### Di Browser Desktop/Mobile:

1. Buka [roblox.com](https://www.roblox.com) dan login
2. Buka Developer Tools (F12)
3. Pilih tab **Application** (Chrome) atau **Storage** (Firefox)
4. Klik **Cookies** → `https://www.roblox.com`
5. Cari cookie bernama `.ROBLOSECURITY`
6. Copy seluruh nilai cookie (mulai dari `_|WARNING:...`)

#### Di Chrome Android:

1. Install ekstensi seperti "Cookie Editor" atau gunakan `chrome://inspect`
2. Buka roblox.com dan login
3. Buka Cookie Editor dan copy `.ROBLOSECURITY`

### 4. Edit config.json

```json
{
  "ps_link": "https://www.roblox.com/share?code=KODE_ANDA&type=Server",
  "user_id": 12345678,
  "check_interval": 10,
  "restart_delay": 30,
  "roblox_cookie": "_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items.|_COOKIE_ANDA_DISINI"
}
```

**Parameter:**

- `ps_link`: Link Private Server Anda
- `user_id`: User ID Roblox Anda
- `check_interval`: Interval pengecekan dalam detik (10 = cek setiap 10 detik)
- `restart_delay`: Waktu tunggu loading game dalam detik (30 = tunggu 30 detik)
- `roblox_cookie`: Cookie .ROBLOSECURITY untuk Game ID tracking

## 🚀 Cara Menjalankan

### Metode 1: Dengan su (Recommended)

```bash
cd /sdcard/AutoRejoin
su
python main.py
```

### Metode 2: Dengan tsu (alternatif)

```bash
cd /sdcard/AutoRejoin
tsu
python main.py
```

**Pastikan memberi izin Root saat popup Magisk/KernelSU muncul!**

## 📊 Output Normal

```
==================================================
  Auto Rejoin Roblox Script (Termux/Root)
==================================================
Checking SELinux status...
  ✓ SELinux set to Permissive (temporary)

📊 Configuration:
   User ID: 12345678
   Check Interval: 10s
   Restart Delay: 30s
   Cookie: Set ✓ (Game ID tracking enabled)

==================================================

Stopping Roblox...
  > Roblox stopped.
Opening Private Server Link...
  ✓ Roblox opened successfully!

⏳ Waiting 60s for game to load...

🔍 Getting private server game ID...
✅ Private server game ID: xxxx-xxxx-xxxx-xxxx-xxxx

[Check #1] 🟢 In-Game ✓ (ID: xxxx...)
[Check #2] 🟢 In-Game ✓ (ID: xxxx...)
[Check #3] 🔴 Server changed (Private→Public) - Rejoining...
   Game ID: xxxx... → xxxx...
✅ Rejoined with game ID: xxxx...
[Check #4] 🟢 In-Game ✓ (ID: xxxx...)
```

## 🔍 Cara Kerja

Script ini menggunakan **Game ID Tracking** untuk mendeteksi perpindahan server:

1. **Saat Start**: Script membuka Private Server dan mencatat Game ID-nya
2. **Monitoring**: Setiap X detik (sesuai `check_interval`), script:
   - Cek apakah Roblox masih berjalan
   - Cek Game ID saat ini melalui Roblox Presence API
   - Bandingkan dengan Game ID Private Server
3. **Auto Rejoin**: Jika Game ID berubah (pindah ke public server), script akan:
   - Force stop Roblox
   - Buka kembali Private Server link
   - Update Game ID yang diharapkan

## ❓ Troubleshooting

### SELinux Error

```bash
# Cek status
su -c "getenforce"

# Set manual ke Permissive
su -c "setenforce 0"
```

### Game ID Tidak Terdeteksi

- Pastikan `roblox_cookie` sudah diisi dengan benar di config.json
- Cookie harus lengkap dan valid (login di browser untuk verifikasi)
- Jangan ada spasi atau karakter tambahan saat copy-paste

### Roblox Tidak Terbuka

```bash
# Test manual
su -c "am start -a android.intent.action.VIEW -d 'LINK_PS_ANDA' -p com.roblox.client"

# Atau test dengan monkey
su -c "monkey -p com.roblox.client 1"
```

### Script Crash/Error

- Pastikan Python dan requests sudah terinstall: `pip install requests`
- Check permission root: `su -c "id"`
- Lihat log error untuk debugging

## ⚠️ Catatan Keamanan

1. **JANGAN SHARE** file `config.json` atau cookie `.ROBLOSECURITY` Anda!
2. Cookie ini setara dengan password - siapapun yang punya cookie bisa login sebagai Anda
3. Ganti password Roblox secara berkala untuk keamanan
4. Logout dari semua device akan mereset cookie (perlu setup ulang)

## 📱 Tips Penggunaan

- Set `check_interval` ke 10 untuk deteksi cepat (lebih banyak API calls)
- Set `check_interval` ke 30 untuk menghemat baterai (deteksi lebih lambat)
- `restart_delay` sebaiknya 30-60 detik tergantung kecepatan loading game Anda
- Script akan berjalan terus sampai di-stop manual (Ctrl+C)

## 🔄 Auto-Start Saat Boot (Opsional)

Untuk menjalankan script otomatis saat device boot, gunakan Termux:Boot atau Tasker dengan root.

## 📝 License

Free to use and modify.

## 🤝 Support

Jika ada masalah atau pertanyaan, buat issue di repository ini.

---

**Disclaimer**: Script ini untuk educational purposes. Gunakan dengan bijak dan ikuti Terms of Service Roblox.
