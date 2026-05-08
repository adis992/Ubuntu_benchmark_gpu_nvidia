# 📤 Kako Push-ovati na GitHub

## ✅ Kod je već commit-ovan!

Tvoj kod je spremam za push. Sve što ti treba je da:

### 1️⃣ Napravi GitHub Repository

Idi na: https://github.com/new

- **Repository name**: `nvidia-gpu-benchmark` (ili kako hoćeš)
- **Description**: Professional NVIDIA GPU Benchmark Tool with Web Dashboard
- **Public** ili **Private** (kako želiš)
- ❌ **NE** čekiraj "Initialize with README" (već imaš README)

Klikni **Create repository**

---

### 2️⃣ Dodaj Remote

GitHub će ti prikazati URL tvog repo-a. Kopiraj ga i pokreni:

**Za HTTPS (lakše):**
```bash
git remote add origin https://github.com/TVOJUsername/REPO_IME.git
```

**Za SSH (bezbednije, ako imaš SSH key):**
```bash
git remote add origin git@github.com:TVOJUsername/REPO_IME.git
```

---

### 3️⃣ Push!

```bash
./push_to_github.sh
```

Ili direktno:
```bash
git push -u origin main
```

---

## 🔐 Ako traži authentication:

### Za HTTPS:
GitHub više ne podržava password auth. Trebaće ti **Personal Access Token**:

1. Idi na: https://github.com/settings/tokens
2. Generate new token (classic)
3. Selektuj `repo` scope
4. Kopiraj token
5. Kad te pita za password, unesi **TOKEN** (ne password!)

### Za SSH:
Ako imaš SSH key:
```bash
ssh -T git@github.com
```

Ako nemaš, napravi ga:
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
cat ~/.ssh/id_ed25519.pub  # Kopiraj output
```

Dodaj na: https://github.com/settings/keys

---

## ⚡ Brze komande:

```bash
# Proveri status
git status

# Vidi commit history
git log --oneline

# Vidi remote URL
git remote -v

# Promeni remote URL
git remote set-url origin NOVI_URL

# Push
./push_to_github.sh
```

---

## 📊 Šta je commit-ovano?

**26 fajlova, 4237+ linija koda:**

✅ Web dashboard (Flask + SocketIO)  
✅ GPU monitoring (NVML)  
✅ Benchmark system  
✅ Safety controls (temp limits, auto-stop)  
✅ Fan control  
✅ Crash detection  
✅ systemd service  
✅ Management scripts (install, restart, check)  
✅ Kompletna dokumentacija  

---

## 💡 Tips:

**Nakon što push-uješ, možeš dodati GitHub Actions badge u README:**
```markdown
![GitHub Stars](https://img.shields.io/github/stars/USERNAME/REPO?style=social)
```

**Dodaj Topics na GitHub:**
- `nvidia`
- `gpu-benchmark`
- `rtx-3090`
- `monitoring`
- `flask`
- `python`

---

**Sve je spremno! Samo dodaj remote i puši! 🚀**
