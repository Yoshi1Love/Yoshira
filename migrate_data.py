import os
import json
import shutil
from pathlib import Path

def migrate_data():
    """Переносит данные из старого места в новое"""
    
    print("🔍 Поиск файлов с данными...")
    
    # Где ищем
    search_paths = [
        '.',
        '..',
        os.path.expanduser('~'),
        os.path.expanduser('~/Desktop'),
        os.path.expanduser('~/Downloads'),
    ]
    
    found_files = []
    
    for path in search_paths:
        if not os.path.exists(path):
            continue
        
        for file in os.listdir(path):
            if file in ['casino_data.json', 'bot_status.json', 'blackjack_games.json']:
                full_path = os.path.join(path, file)
                found_files.append(full_path)
                print(f"📄 Найден файл: {full_path}")
    
    if not found_files:
        print("❌ Файлы не найдены")
        return
    
    # Создаем папку для данных
    data_folder = os.path.join(os.path.dirname(__file__), 'bot_data')
    os.makedirs(data_folder, exist_ok=True)
    
    # Копируем файлы
    for file_path in found_files:
        filename = os.path.basename(file_path)
        dest_path = os.path.join(data_folder, filename)
        
        try:
            shutil.copy2(file_path, dest_path)
            print(f"✅ Скопирован {filename} -> {dest_path}")
        except Exception as e:
            print(f"❌ Ошибка копирования {filename}: {e}")
    
    print(f"\n📁 Все файлы скопированы в: {data_folder}")

if __name__ == "__main__":
    migrate_data()