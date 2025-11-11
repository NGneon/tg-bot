# Поезд Чудес - Telegram Bot

## Overview
A Telegram bot for the "Train of Wonders" (Поезд Чудес) charity event. Users can select wish envelopes by number and provide their contact information to participate in granting children's wishes.

## Bot Description

### Short Description (для BotFather - /setdescription)
```
Бот благотворительной акции "Поезд Чудес" 🚂🎄🎁

Выберите номер конверта с желанием ребёнка, оставьте свой контакт — и подарите праздник!
```

### Full Description (для BotFather - /setabouttext)
```
🚂🎄🎁 Поезд Чудес

Добро пожаловать в благотворительную акцию "Поезд Чудес"!

Здесь вы можете выбрать желание ребёнка и подарить ему настоящий праздник.

Как это работает:
1️⃣ Нажмите /start для начала
2️⃣ Введите номер конверта, который выбрали
3️⃣ Оставьте ваш номер телефона для обратной связи
4️⃣ Получите подтверждение бронирования

По всем вопросам: @poyezd_chudes

Давайте дарить чудеса вместе! ✨
```

## Current State
- Python Telegram bot using pyTelegramBotAPI
- In-memory data storage for envelope selections
- Russian language interface
- Basic phone number validation

## Features
- `/start` command with welcome message
- Envelope number selection with numeric validation
- Phone number collection with format validation
- Custom keyboard with greeting button
- Confirmation message after registration

## Recent Changes
- Initial project setup (November 11, 2025)
- Core bot functionality implemented
- Environment variable management for secure token storage

## Project Structure
```
bot.py              # Main bot file with all handlers
.env                # Environment variables (not in git)
.env.example        # Example environment file
requirements.txt    # Python dependencies
.gitignore          # Git ignore rules
```

## Setup Instructions
1. Get your Telegram bot token from @BotFather
2. Add the token to Replit Secrets as `TELEGRAM_BOT_TOKEN`
3. Run the bot using the configured workflow

## Dependencies
- pyTelegramBotAPI: Telegram Bot API wrapper
- python-dotenv: Environment variable management

## Future Enhancements
- PostgreSQL database for persistent storage
- Envelope availability tracking
- Admin commands for viewing registrations
- Data export functionality (CSV/Excel)
- Enhanced phone number validation with international formats
