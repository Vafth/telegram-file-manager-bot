# Telegram File Manager Bot

A Telegram bot that transforms your chats into an organized file management system with hierarchical folders and inline mode availability.

## Key Features

- **Hierarchical Folder Structure** - Organize files in nested folders like a traditional file system
- **File Storage** - Save any Telegram media (up to 50MB) with custom names
- **Inline Search** - Access your files from any chat using `@your_bot` queries
- **Smart Search** - Find files by folder path, extension, or combined filters
- **Auto Backup** - All files automatically backed up to your private group with organized topics
- **File Management** - Rename folders, move files, organize your media library

## Quick Start

1. [Create a Telegram Bot](#1-create-telegram-bot)
2. [Set up Backup Group](#2-create-backup-group)
3. [Configure Environment](#3-installation--configuration)
4. [Get Required IDs](#4-get-chat-and-group-ids)
5. [Start Using](#running-the-bot)

---

## Installation & Setup

### Prerequisites

- Python 3.11+
- Telegram account
- Basic command line knowledge

### 1. Create Telegram Bot

1. Open [@BotFather](https://t.me/botfather) in Telegram
2. Send `/newbot` and follow the prompts
3. Save the **API Token**
4. **Enable Inline Mode:**
   - Bot Settings → Inline Mode → Turn on
5. **Allow Groups:**
   - Bot Settings → Allow Groups? → Turn on

### 2. Create Backup Group

1. Create a new **private group** in Telegram
2. **Enable Topics:**
   - Group Settings → Manage Group → Topics → Enable
3. **Create 6 topics** for the following Telegram file types:
   - Photo
   - Video
   - Audio
   - Animation
   - Sticker
   - Document
4. **Add your bot** to this group

### 3. Installation & Configuration

**Clone the repository:**
```bash
git clone https://github.com/Vafth/telegram-file-manager-bot.git
cd telegram-file-manager-bot
```

**Set up environment:**

<details>
<summary><b>Using uv</b></summary>
```bash
# Install uv if you don't have it yet
pip install uv

# Sync dependencies
uv sync
```

</details>

<details>
<summary><b>Using pip</b></summary>
```bash
# Create virtual environment
python -m venv venv

# Activate environment
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

</details>

**Configure environment variables:**
```bash
# Copy example env file
cp .env.example .env
```

Edit `.env` and configure for **admin setup mode**:
```env
ADMIN_SETUP=true  # Enable admin mode for initial setup
BOT_TOKEN='your_bot_token_here'
# Leave other variables empty for now
```

### 4. Get Chat and Group IDs

**Run the bot in admin mode:**
```bash
# Using uv
uv run python main.py

# Using pip
python main.py
```

The bot will automatically run in **admin mode** when `ADMIN_SETUP=true`, giving you access to ID collection commands.

**Get your Chat ID:**
1. Send `/get_my_chat_id` to your bot in private chat
2. Copy the chat ID

**Get Group and Thread IDs:**
1. Go to your backup group
2. **In each of the 6 topics**, send `/get_group_and_thread_id`
3. Copy the group ID and thread ID for each topic

**Update `.env` file:**
```env
ADMIN_SETUP=false  # ← Disable admin mode after setup

# Telegram Bot section
BOT_TOKEN       = 'your_bot_token_here' 
...

# Telegram Users section
ADMIN_LIST      = '[your_chat_id_here]'

# Telegram Group section
GROUP_LIST      = '[your_group_id_here]'

# Thread IDs for each media type
THREAD_DOCUMENT = 1
THREAD_IMAGE    = 2
THREAD_VIDEO    = 3
THREAD_AUDIO    = 4
THREAD_STICKER  = 5
THREAD_GIF      = 6
```

**Restart the bot in normal mode:**
```bash
# Using uv
uv run python main.py

# Using pip
python main.py
```

---

## User Guide

### Basic Commands

- `/start` - Initialize your file system and get started
- `/fe` - Open File Explorer (main interface)
- `/rn` - Rename current folder
- `/mv` - Move files to another folder
- `/rm` - Delete folder (all files move to parent)
- `/help` - User Guide

### File Explorer (`/fe`)

The file explorer shows your current location and available actions:

- **../ button** - Go up one level to the parent folder
- **Folder buttons** - Navigate into subfolders
- **File buttons** - Click to get a specific file
- **Add Folder button** - Create a subfolder in current location

### Saving Files

1. Navigate to desired folder using `/fe`
2. Send any file to the bot
3. Bot asks for a name - reply with the filename
4. File is saved and automatically backed up file into your private group

### Inline Mode Search

Access your files from **any chat** by typing `@your_bot_username` followed by:

**Search by folder:**
```
@your_bot /music/
```
Shows all subfolders in `/music/`

**Search by file type:**
```
@your_bot .gif
```
Shows all `.gif` files you have ever saved

**Search in specific folder by type:**
```
@your_bot /memes/.gif
```
Shows all `.gif` files in `/memes/` folder

### File Search Tags

- **Animation:** `.gif`
- **Video:** `.mp4`
- **Photo:** `.png`
- **Audio:** `.mp3`
- **Sticker:** `.sti`
- **Document:** `.doc`

> **Note on File Tags:** These extensions are **internal search tags** used by the bot to categorize your media. They allow you to filter by type regardless of the actual file's name.

---

## Tech Stack

- **[aiogram 3.x](https://github.com/aiogram/aiogram)** - Telegram Bot framework
- **[SQLModel](https://github.com/fastapi/sqlmodel)** - Async ORM
- **SQLite** - As a default database
- **Python 3.11+** - Core language

Full dependencies in `requirements.txt` and `pyproject.toml`

---

## Roadmap

- [ ] **Bulk file operations**
- [ ] **Enhanced folder search** - Show available file types in folder suggestions during inline search
- [ ] **User space management** - Ability to view and permanently operate at all saved files globally (currently, files removed from folders remain in storage and are only accessible via inline **Search by file type**)
- [ ] **Advanced search filters:**
  - Search by file name
  - Recursive **Search by file type** within a folder and all its subfolders
- [ ] **Shared folders & access groups** - Create a `/Groups/` folder containing shared folders where:
  - Folder owners can invite specific users
  - Owners can set granular permissions (view, add, remove, move files)
  - Collaborative file management between users
- [ ] **External access tools**

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details
