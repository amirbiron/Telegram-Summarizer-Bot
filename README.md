# 🤖 Telegram Summarizer Bot

> **בוט טלגרם חכם לסיכום שיחות בקבוצות באמצעות Claude AI**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-green.svg)](https://www.mongodb.com/)
[![Claude AI](https://img.shields.io/badge/Claude-Sonnet%204.5-purple.svg)](https://www.anthropic.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 תוכן עניינים

- [תיאור](#-תיאור)
- [תכונות](#-תכונות)
- [דרישות מקדימות](#-דרישות-מקדימות)
- [התקנה](#-התקנה)
  - [התקנה מקומית](#1-התקנה-מקומית-ללא-docker)
  - [התקנה עם Docker](#2-התקנה-עם-docker-מומלץ)
- [שימוש](#-שימוש)
- [פקודות זמינות](#-פקודות-זמינות)
- [הגדרות](#-הגדרות)
- [מבנה הפרויקט](#-מבנה-הפרויקט)
- [פריסה לענן](#-פריסה-לענן)
- [פתרון בעיות](#-פתרון-בעיות)
- [תרומה לפרויקט](#-תרומה-לפרויקט)
- [רישיון](#-רישיון)

---

## 🎯 תיאור

בוט טלגרם מתקדם שמסכם שיחות בקבוצות באמצעות מודל **Claude Sonnet 4.5** של Anthropic. הבוט שומר חלון נע של 50 הודעות אחרונות, יוצר סיכומים חכמים, ושומר עד 5 סיכומים אחרונים לכל משתמש.

### 🌟 למה להשתמש בבוט הזה?

- 📱 **קבוצות פעילות** - סיכום מהיר של מאות הודעות
- ⏰ **חיסכון בזמן** - קרא את העיקר במקום כל ההודעות
- 🎯 **סיכומים ממוקדים** - סוגי סיכום שונים לפי צורך
- 💾 **שמירה אוטומטית** - הסיכומים נשמרים בצ'אט הפרטי שלך
- 🔍 **חיפוש** - מצא סיכומים ישנים בקלות

---

## ✨ תכונות

### 🎨 סוגי סיכום

| סוג | תיאור | דוגמה |
|-----|--------|--------|
| **📌 Standard** | 5-6 נקודות מרכזיות עם emoji | `/summarize` |
| **⚡ Quick** | 2-3 נקודות מהירות | `/summarize quick` |
| **📋 Detailed** | 8-10 נקודות מפורטות | `/summarize detailed` |
| **✅ Decisions** | רק החלטות שהתקבלו | `/summarize decisions` |
| **❓ Questions** | שאלות שנשארו פתוחות | `/summarize questions` |

### 🔧 יכולות נוספות

- 📊 **Buffer נע** - שומר 50 הודעות אחרונות אוטומטית
- 🎛️ **גמישות** - סכם בין 10 ל-200 הודעות
- 💾 **שמירה חכמה** - עד 5 סיכומים אחרונים למשתמש
- 🔍 **חיפוש** - חפש בסיכומים שמורים
- 🌐 **רב-לשוני** - תמיכה בעברית ואנגלית
- 🔄 **ניקוי אוטומטי** - מחיקת סיכומים ישנים

---

## 📦 דרישות מקדימות

### 1️⃣ **Python**
```bash
Python 3.12 ומעלה
```

### 2️⃣ **MongoDB**
```bash
MongoDB 7.0 ומעלה
```

### 3️⃣ **API Keys**

#### Telegram Bot Token
1. פתח שיחה עם [@BotFather](https://t.me/BotFather) בטלגרם
2. שלח `/newbot` ועקוב אחר ההוראות
3. שמור את ה-token שתקבל

#### Claude API Key
1. היכנס ל-[Anthropic Console](https://console.anthropic.com/)
2. צור API key חדש
3. שמור את המפתח (מתחיל ב-`sk-ant-`)

---

## 🚀 התקנה

### 1. התקנה מקומית (ללא Docker)

#### שלב 1: Clone הפרויקט

```bash
git clone https://github.com/yourusername/telegram-summarizer-bot.git
cd telegram-summarizer-bot
```

#### שלב 2: צור סביבה וירטואלית

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### שלב 3: התקן תלויות

```bash
pip install -r requirements.txt
```

#### שלב 4: הגדר משתני סביבה

```bash
# העתק את קובץ הדוגמה
cp .env.example .env

# ערוך את .env וצור בו:
# - TELEGRAM_BOT_TOKEN=your_token_here
# - ANTHROPIC_API_KEY=your_key_here
# - MONGODB_URL=mongodb://localhost:27017
```

#### שלב 5: הרץ MongoDB

```bash
# אופציה א': Docker
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# אופציה ב': MongoDB מותקן מקומית
mongod
```

#### שלב 6: הרץ את הבוט

```bash
python main.py
```

🎉 **הבוט רץ!** תראה הודעה:
```
✅ Bot is now running! Press Ctrl+C to stop.
```

---

### 2. התקנה עם Docker (מומלץ!)

#### שלב 1: Clone הפרויקט

```bash
git clone https://github.com/yourusername/telegram-summarizer-bot.git
cd telegram-summarizer-bot
```

#### שלב 2: הגדר משתני סביבה

```bash
# העתק את קובץ הדוגמה
cp .env.example .env

# ערוך את .env וצור בו:
# - TELEGRAM_BOT_TOKEN=your_token_here
# - ANTHROPIC_API_KEY=your_key_here
```

#### שלב 3: הרץ עם Docker Compose

```bash
# בנה והרץ (MongoDB + Bot)
docker-compose up -d

# צפה בלוגים
docker-compose logs -f bot

# עצור הכל
docker-compose down

# עצור ומחק נתונים
docker-compose down -v
```

🎉 **הבוט רץ ב-Docker!**

---

## 📖 שימוש

### הוספת הבוט לקבוצה

1. פתח את הקבוצה בטלגרם
2. לחץ על שם הקבוצה → **Add Members**
3. חפש את הבוט שלך (לפי username)
4. הוסף אותו לקבוצה
5. תן לו הרשאות **Admin** (אופציונלי - לקריאת הודעות)

### סיכום שיחה

#### בקבוצה:
```
/summarize
```

#### בצ'אט פרטי עם הבוט:
```
/start          - התחל שיחה
/mysummaries    - הצג סיכומים שמורים
/search פגישה  - חפש בסיכומים
```

---

## 📋 פקודות זמינות

### פקודות בסיסיות

| פקודה | תיאור | דוגמה |
|-------|--------|--------|
| `/start` | הודעת פתיחה והסבר | `/start` |
| `/help` | מדריך שימוש מלא | `/help` |

### פקודות סיכום (בקבוצות)

| פקודה | תיאור |
|-------|--------|
| `/summarize` | סיכום 50 ההודעות האחרונות |
| `/summarize 30` | סיכום 30 הודעות אחרונות |
| `/summarize 100` | סיכום 100 הודעות אחרונות |
| `/summarize quick` | סיכום מהיר (2-3 נקודות) |
| `/summarize detailed` | סיכום מפורט (8-10 נקודות) |
| `/summarize decisions` | רק החלטות |
| `/summarize questions` | שאלות פתוחות |
| `/summarize 50 detailed` | 50 הודעות, מפורט |

### פקודות ניהול (בפרטי)

| פקודה | תיאור |
|-------|--------|
| `/mysummaries` | הצג 5 סיכומים אחרונים |
| `/search <מילה>` | חפש בסיכומים |

### כפתורים אינטראקטיביים

- **📌 שמור סיכום** - שולח סיכום לצ'אט הפרטי
- **הצג סיכום** - מציג סיכום מלא

---

## ⚙️ הגדרות

כל ההגדרות נמצאות בקובץ `.env`:

### הגדרות חובה

```bash
# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Claude AI
ANTHROPIC_API_KEY=sk-ant-api03-...

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=telegram_summarizer
```

### הגדרות אופציונליות

```bash
# Claude Settings
CLAUDE_MODEL=claude-sonnet-4-5-20250929
CLAUDE_MAX_TOKENS=2048
CLAUDE_TIMEOUT=120

# Bot Behavior
MAX_MESSAGE_BUFFER=50           # מספר הודעות בבאפר
MAX_SUMMARIES_PER_USER=5        # סיכומים מקסימליים למשתמש
DEFAULT_SUMMARY_COUNT=50        # ברירת מחדל לסיכום

# Application
APP_ENV=development             # development/production
LOG_LEVEL=INFO                  # DEBUG/INFO/WARNING/ERROR
```

---

## 🗂️ מבנה הפרויקט

```
telegram-summarizer-bot/
│
├── database/              # מודלים ו-DB
│   ├── __init__.py
│   ├── db.py             # חיבור MongoDB
│   └── models.py         # Beanie models
│
├── handlers/             # טיפול באירועים
│   ├── __init__.py
│   ├── message_handler.py    # הודעות בקבוצות
│   └── command_handler.py    # פקודות בוט
│
├── services/             # לוגיקה עסקית
│   ├── __init__.py
│   ├── ai_service.py         # Claude API
│   └── summarizer.py         # יצירת סיכומים
│
├── utils/                # כלי עזר
│   ├── __init__.py
│   └── logger.py             # Logging
│
├── .env.example          # דוגמת הגדרות
├── .gitignore           # Git ignore
├── config.py            # ניהול הגדרות
├── docker-compose.yml   # Docker Compose
├── Dockerfile           # Docker image
├── main.py              # נקודת כניסה
├── README.md            # תיעוד (קובץ זה)
└── requirements.txt     # תלויות Python
```

---

## ☁️ פריסה לענן

### Render.com (מומלץ!)

1. **צור חשבון ב-[Render](https://render.com/)**

2. **צור MongoDB Atlas** (חינם):
   - היכנס ל-[MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - צור Cluster חינמי
   - קבל את connection string

3. **צור Web Service חדש ב-Render**:
   - Connect GitHub repository
   - בחר Docker deployment
   - הגדר Environment Variables:
     ```
     TELEGRAM_BOT_TOKEN=...
     ANTHROPIC_API_KEY=...
     MONGODB_URL=mongodb+srv://...
     ```

4. **Deploy!** 🚀

### Heroku

```bash
# התקן Heroku CLI
heroku login

# צור אפליקציה
heroku create telegram-summarizer-bot

# הוסף MongoDB addon
heroku addons:create mongolab:sandbox

# הגדר environment variables
heroku config:set TELEGRAM_BOT_TOKEN=...
heroku config:set ANTHROPIC_API_KEY=...

# Deploy
git push heroku main
```

### Railway.app

1. Connect GitHub repository
2. Add MongoDB service
3. Configure environment variables
4. Deploy automatically

---

## 🔧 פתרון בעיות

### הבוט לא מגיב

✅ **בדוק:**
- הבוט רץ? `docker-compose ps` או `ps aux | grep python`
- הטוקן נכון? בדוק `.env`
- יש אינטרנט?
- MongoDB רץ? `docker ps` או `mongod`

### שגיאת חיבור למונגו

```bash
# בדוק אם MongoDB רץ
docker ps | grep mongo

# אם לא, הרץ:
docker-compose up -d mongodb

# בדוק את ה-URL בקובץ .env
```

### שגיאת Claude API

```bash
# בדוק את ה-API key
echo $ANTHROPIC_API_KEY

# בדוק שהמפתח תקין והתחיל ב-sk-ant-
```

### הבוט לא רואה הודעות בקבוצה

✅ **פתרון:**
- תן לבוט הרשאות **Admin** בקבוצה
- או: כבה "Privacy Mode" ב-@BotFather:
  ```
  /mybots → בחר בוט → Bot Settings → Group Privacy → Turn off
  ```

### לוגים

```bash
# Docker
docker-compose logs -f bot

# מקומי
# לוגים מופיעים בקונסול
```

---

## 🤝 תרומה לפרויקט

אנחנו שמחים לקבל תרומות! 

### איך לתרום?

1. **Fork** את הפרויקט
2. צור **branch** חדש (`git checkout -b feature/AmazingFeature`)
3. **Commit** את השינויים (`git commit -m 'Add some AmazingFeature'`)
4. **Push** ל-branch (`git push origin feature/AmazingFeature`)
5. פתח **Pull Request**

### רעיונות לתרומה

- 🌍 תרגום לשפות נוספות
- 🎨 עיצובים חדשים לסיכומים
- 📊 ויזואליזציות של נתונים
- 🧪 טסטים נוספים
- 📝 שיפור תיעוד

---

## 📄 רישיון

פרויקט זה מופץ תחת רישיון MIT. ראה קובץ `LICENSE` לפרטים.

---

## 💡 תמיכה

יש שאלות? צור קשר:

- 📧 Email: your-email@example.com
- 💬 Telegram: [@yourusername](https://t.me/yourusername)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/telegram-summarizer-bot/issues)

---

## 🙏 תודות

פרויקט זה נבנה בעזרת:

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot framework
- [Anthropic Claude](https://www.anthropic.com/) - AI summarization
- [MongoDB](https://www.mongodb.com/) - Database
- [Beanie ODM](https://github.com/roman-right/beanie) - MongoDB ODM

---

## 📊 סטטיסטיקות

- ⭐ **Star** את הפרויקט אם אהבת!
- 🐛 מצאת באג? [פתח Issue](https://github.com/yourusername/telegram-summarizer-bot/issues)
- 💡 רעיון לפיצ'ר? [פתח Discussion](https://github.com/yourusername/telegram-summarizer-bot/discussions)

---

<div align="center">

**עשוי באהבה בישראל 🇮🇱**

Made with ❤️ by [Your Name](https://github.com/yourusername)

</div>
