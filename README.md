# Binance AutoInvest Bot

## Overview

Automated trading bot for Binance with DCA (Dollar Cost Averaging) strategies.

## How to Run

```bash
# go to project folder
cd /path/to/your/project

# activate virtual environment
source venv/bin/activate

# run your script
python your_script.py
```

## Oracle Cloud Deployment

This document explains how to connect to your Oracle Cloud server, run and maintain your Binance DCA bot (Python), and update or reconfigure it as needed.

### 1. Connect to the server (Ubuntu on Oracle)

**Find the Public IP**

1. Go to Oracle Cloud Console
2. Navigate to Compute → Instances
3. Select your instance (e.g., binance-autoinvest-bot)
4. Copy the Public IP Address

**Connect from your PC (Windows + Git Bash)**

```bash
ssh -i ~/.ssh/oracle_vm ubuntu@YOUR_PUBLIC_IP
```

- Replace YOUR_PUBLIC_IP with the IP you copied
- Default username is ubuntu
- Use the same private key file you downloaded/generated during VM setup

### 2. Project location

Your project is located at:

```
/home/ubuntu/dev/binance-autoinvest-test
```

Inside you will find:

- `.venv/` → Python virtual environment
- `.env` → Binance and Telegram credentials
- `src/` → bot code
- `requirements.txt` → dependencies

### 3. Environment variables (.env)

The .env file contains your credentials:

```
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
USE_TESTNET=false
```

**Never push .env to GitHub.**

To edit:

```bash
nano /home/ubuntu/dev/binance-autoinvest-test/.env
```

(Ctrl+O = save, Ctrl+X = exit)

### 4. Run the bot manually

```bash
cd ~/dev/binance-autoinvest-test
source .venv/bin/activate
python src/strategies/simple_dca.py
```

### 5. Automation with systemd timer

The bot runs automatically via systemd.

**Config files**

- Service: `/etc/systemd/system/dca-bot.service`
- Timer: `/etc/systemd/system/dca-bot.timer`

**Useful commands**

Check next run:

```bash
systemctl list-timers | grep dca-bot
```

Watch logs:

```bash
journalctl -u dca-bot.service -f
```

Run immediately:

```bash
sudo systemctl start dca-bot.service
```

### 6. Change the schedule

Edit the timer:

```bash
sudo nano /etc/systemd/system/dca-bot.timer
```

**Examples of OnCalendar:**

Every hour:
```
OnCalendar=hourly
```

Every 30 minutes:
```
OnCalendar=*:0/30
```

Every day at 09:00:
```
OnCalendar=*-*-* 09:00:00
```

Every Monday at 09:00:
```
OnCalendar=Mon *-*-* 09:00:00
```

After editing:

```bash
sudo systemctl daemon-reload
sudo systemctl restart dca-bot.timer
```

### 7. Update the code

To pull the latest version from GitHub:

```bash
cd ~/dev/binance-autoinvest-test
git pull origin main
```

If dependencies changed:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 8. Maintenance commands

Restart the bot manually:

```bash
sudo systemctl restart dca-bot.service
```

Stop the timer:

```bash
sudo systemctl stop dca-bot.timer
```

Status of the timer:

```bash
systemctl status dca-bot.timer
```

Status of the service:

```bash
systemctl status dca-bot.service
```

### 9. Test Telegram

To test Telegram credentials:

```bash
curl -s -X POST https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage \
 -d chat_id=$TELEGRAM_CHAT_ID \
 -d text="Test message from my Oracle Cloud server"
```

If the message arrives, your .env is correct.

### Summary

- The Oracle Cloud VM (Frankfurt) runs 24/7 on Always Free
- Connect with: `ssh -i ~/.ssh/oracle_vm ubuntu@YOUR_PUBLIC_IP`
- The bot runs automatically according to the systemd timer (every hour by default)
- Update code with `git pull origin main`
- Check logs with `journalctl -u dca-bot.service -f`
