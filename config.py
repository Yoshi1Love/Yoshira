# config.py
import os
import sys
from pathlib import Path

def get_base_path():
    """Возвращает базовый путь для сохранения файлов"""
    
    # Если запущено как exe (pyinstaller)
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    
    # Если запущено из VS Code или другого IDE
    # Проверяем наличие файла .vscode или конкретных файлов проекта
    current_dir = os.getcwd()
    
    # Проверяем, есть ли в текущей директории файлы бота
    if os.path.exists(os.path.join(current_dir, 'bot.py')) or \
       os.path.exists(os.path.join(current_dir, 'main.py')):
        return current_dir
    
    # Если запущено из терминала, но файлы в текущей папке
    if os.path.exists('casino_data.json') or os.path.exists('bot.py'):
        return os.getcwd()
    
    # Иначе используем домашнюю директорию пользователя
    return os.path.expanduser('~')

def get_data_folder():
    """Создает и возвращает путь к папке с данными"""
    base_path = get_base_path()
    
    # Пробуем разные варианты папок
    possible_folders = [
        os.path.join(base_path, 'bot_data'),
        os.path.join(base_path, 'data'),
        os.path.join(base_path, 'discord_bot_data'),
        os.path.join(os.path.expanduser('~'), '.discord_bot'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot_data'),  # Папка со скриптом
    ]
    
    # Ищем существующую папку с данными
    for folder in possible_folders:
        if os.path.exists(folder) and os.path.isdir(folder):
            print(f"📁 Найдена существующая папка: {folder}")
            return folder
    
    # Если не нашли, создаем в папке со скриптом
    script_folder = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.join(script_folder, 'bot_data')
    
    try:
        os.makedirs(data_folder, exist_ok=True)
        print(f"📁 Создана папка для данных: {data_folder}")
        return data_folder
    except:
        # Если не получается, используем домашнюю директорию
        home_folder = os.path.join(os.path.expanduser('~'), '.discord_bot')
        os.makedirs(home_folder, exist_ok=True)
        print(f"📁 Используем домашнюю папку: {home_folder}")
        return home_folder

# Определяем пути
DATA_FOLDER = get_data_folder()
STATUS_FILE = os.path.join(DATA_FOLDER, 'bot_status.json')
CASINO_DATA_FILE = os.path.join(DATA_FOLDER, 'casino_data.json')
BLACKJACK_GAMES_FILE = os.path.join(DATA_FOLDER, 'blackjack_games.json')

print(f"📁 Директория для данных: {DATA_FOLDER}")
print(f"📄 Файл казино: {CASINO_DATA_FILE}")