# ToDo Bot

## Overview

ToDo Bot is a Telegram bot designed for task and reminder management. It helps you organize your day by allowing you to create, edit, and delete tasks, set reminders, and interact with an AI assistant for time management tips. Key features include:

- 📋 Create and manage tasks
- ⏰ Set and edit reminders
- 🤖 Interactive AI assistant for planning and productivity
- 📢 Admin newsletter for user notifications
- 🗑 Delete all user data with a single command

The bot is written in Python using the `aiogram` library and SQLite via SQLAlchemy.

## Requirements

To run the bot, you need the following:

- Python 3.10 or higher
- Dependencies listed in `requirements.txt`:
  - `aiogram`
  - `sqlalchemy`
  - `aiosqlite`
  - and others (see `requirements.txt`)

You also need a Telegram bot token, which can be obtained from [BotFather](https://t.me/BotFather).

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/dashkared/ToDoBot.git
   cd todo-bot
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the project root and add your bot token:
   ```plaintext
   BOT_TOKEN=your_bot_token_here
   ```

5. **Initialize the database**:
   The SQLite database (`db.sqlite3`) is created automatically on the first run. Ensure the application has write permissions in the directory.

6. **Run the bot**:
   ```bash
   python main.py
   ```

## Usage

Once the bot is running in Telegram:

1. Find the bot by its name (e.g., `@YourToDoBot`) and start a conversation.
2. Use the `/start` command to register and view the welcome message.
3. Available commands:
   - `/menu` — open the main menu
   - `/tasks` — view the task list
   - `/del` — delete all your data
4. Admins (listed in `ADMIN_IDS` in `admin.py`) can send newsletters using the `/newsletter` command.

The bot supports inline buttons for managing tasks, reminders, and interacting with the AI assistant.

## Cloning the Repository

To clone the repository to your local machine:

```bash
git clone https://github.com/dashkared/ToDoBot.git
```

## Contact

For questions or suggestions, reach out to the developers via Telegram:
- [Roman](https://t.me/sadmenus)
- [Michael](https://t.me/michaelj_ordan)
- [Dmitry](https://t.me/sziixubs)
- [Mikhail](https://t.me/just_m1chael)
