# Git Authentication Fix Guide

## Problem
GitHub no longer supports password authentication for HTTPS Git operations. You need to use either:
1. **SSH keys** (recommended)
2. **Personal Access Token (PAT)** with HTTPS
3. **Git Credential Manager** (Windows)

---

## Solution 1: Switch to SSH (Recommended)

### Step 1: Generate SSH Key (if you don't have one)
```powershell
# Generate a new SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Press Enter to accept default location
# Enter a passphrase (optional, but recommended)
```

### Step 2: Add SSH Key to SSH Agent
```powershell
# Start the ssh-agent service
Get-Service ssh-agent | Set-Service -StartupType Automatic
Start-Service ssh-agent

# Add your SSH key
ssh-add $env:USERPROFILE\.ssh\id_ed25519
```

### Step 3: Copy Your Public Key
```powershell
# Display your public key (copy the entire output)
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub
```

### Step 4: Add SSH Key to GitHub
1. Go to GitHub.com → Settings → SSH and GPG keys
2. Click "New SSH key"
3. Paste your public key
4. Click "Add SSH key"

### Step 5: Change Remote URL to SSH
```powershell
# Change from HTTPS to SSH
git remote set-url origin git@github.com:vineet-chelsea/clave-master.git

# Verify the change
git remote -v
```

### Step 6: Test Connection
```powershell
ssh -T git@github.com
```

---

## Solution 2: Use Personal Access Token (PAT) with HTTPS

### Step 1: Generate a Personal Access Token on GitHub
1. Go to GitHub.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name (e.g., "clave-master-repo")
4. Select scopes: Check **repo** (full control of private repositories)
5. Click "Generate token"
6. **COPY THE TOKEN IMMEDIATELY** (you won't see it again!)

### Step 2: Use Token When Pushing
When Git prompts for credentials:
- **Username**: Your GitHub username
- **Password**: Paste your Personal Access Token (NOT your GitHub password)

### Step 3: Configure Git Credential Manager (Windows)
```powershell
# Install/configure Git Credential Manager to store the token
git config --global credential.helper manager-core
```

Now when you push, it will prompt once and save your credentials securely.

---

## Solution 3: Update Remote URL with Token (Quick Fix)

You can embed the token directly in the remote URL (less secure, but works):
```powershell
# Replace YOUR_TOKEN with your actual Personal Access Token
git remote set-url origin https://YOUR_TOKEN@github.com/vineet-chelsea/clave-master.git

# Or with username:
git remote set-url origin https://YOUR_USERNAME:YOUR_TOKEN@github.com/vineet-chelsea/clave-master.git
```

⚠️ **Warning**: This stores the token in plain text in `.git/config`. Only use this temporarily.

---

## Verify Your Setup

After applying any solution:
```powershell
# Check remote URL
git remote -v

# Try pushing
git push origin main
```

---

## Recommended: Use SSH (Solution 1)
SSH is more secure and convenient once set up. You won't need to enter credentials repeatedly.

## Quick Fix: Use PAT (Solution 2)
If you need to push immediately, use a Personal Access Token with Git Credential Manager.


