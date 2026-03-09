import subprocess
import json
import os
import discord
from discord.ext import commands
from discord.ui import Button, View, Select, Modal, TextInput
import asyncio
import yt_dlp
from collections import deque
import time
import random
from datetime import datetime, timedelta
import atexit
import shutil
import glob
import sys

print("=" * 50)
print(f"🐍 Python interpreter: {sys.executable}")
print(f"📁 Current working directory: {os.getcwd()}")
print(f"📁 Script directory: {os.path.dirname(os.path.abspath(__file__))}")
print(f"📁 Sys path: {sys.path[0]}")
print("=" * 50)

def find_casino_data_files():
    """Ищет все возможные файлы с данными казино"""
    print("🔍 Поиск файлов с данными казино...")
    
    # Возможные имена файлов
    possible_names = [
        'casino_data.json',
        'casino_stats.json',
        'casino.json',
        'bot_data/casino_data.json',
        'data/casino_data.json',
        'casino_data_backup.json'
    ]
    
    # Текущая директория
    current_dir = os.getcwd()
    print(f"📁 Текущая директория: {current_dir}")
    
    # Список всех json файлов в текущей директории
    json_files = glob.glob("*.json")
    if json_files:
        print(f"📄 Найдены JSON файлы: {', '.join(json_files)}")
    
    # Проверяем возможные имена
    found_files = []
    for name in possible_names:
        if os.path.exists(name):
            size = os.path.getsize(name)
            found_files.append((name, size))
    
    if found_files:
        print("✅ Найдены файлы с данными:")
        for name, size in found_files:
            print(f"   - {name} ({size} байт)")
            try:
                with open(name, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"     Содержит данных для {len(data)} пользователей")
            except:
                print(f"     (не удалось прочитать)")
    else:
        print("❌ Файлы с данными не найдены")
    
    return found_files

find_casino_data_files()

DATA_FOLDER = 'bot_data'
STATUS_FILE = os.path.join(DATA_FOLDER, 'bot_status.json')
CASINO_DATA_FILE = os.path.join(DATA_FOLDER, 'casino_data.json')
BLACKJACK_GAMES_FILE = os.path.join(DATA_FOLDER, 'blackjack_games.json')

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER, exist_ok=True)

def install_requirements():
    """Автоматическая установка зависимостей при запуске"""
    required = {'yt-dlp', 'discord.py', 'PyNaCl'}
    installed = {pkg.split('==')[0] for pkg in 
                 subprocess.check_output([sys.executable, '-m', 'pip', 'freeze']).decode().splitlines()}
    
    missing = required - installed
    if missing:
        print(f"Установка недостающих пакетов: {missing}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])

def save_status(status_type, activity_type, activity_message):
    """Сохраняет текущий статус в файл"""
    data = {
        'status_type': status_type,
        'activity_type': activity_type,
        'activity_message': activity_message
    }
    with open(STATUS_FILE, 'w') as f:
        json.dump(data, f)

def load_status():
    """Загружает сохраненный статус из файла"""
    if not os.path.exists(STATUS_FILE):
        return None
    
    with open(STATUS_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return None

def save_casino_data():
    """Сохраняет данные казино в файл с созданием бэкапа"""
    try:
        os.makedirs(os.path.dirname(CASINO_DATA_FILE) or '.', exist_ok=True)
        
        if os.path.exists(CASINO_DATA_FILE):
            backup_name = CASINO_DATA_FILE.replace('.json', f'_backup_{int(time.time())}.json')
            try:
                import shutil
                shutil.copy2(CASINO_DATA_FILE, backup_name)
                backup_files = sorted(glob.glob(CASINO_DATA_FILE.replace('.json', '_backup_*.json')))
                for old_backup in backup_files[:-5]:
                    os.remove(old_backup)
            except Exception as e:
                print(f"⚠️ Не удалось создать бэкап: {e}")
        
        temp_file = CASINO_DATA_FILE + '.tmp'
        
        saved = False
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(casino_stats, f, ensure_ascii=False, indent=2)
            
            if os.name == 'nt' and os.path.exists(CASINO_DATA_FILE):
                os.remove(CASINO_DATA_FILE)
            
            os.rename(temp_file, CASINO_DATA_FILE)
            print(f"✅ Данные казино сохранены в {CASINO_DATA_FILE} ({len(casino_stats)} пользователей)")
            saved = True
            
        except Exception as e:
            print(f"⚠️ Метод 1 не сработал: {e}")
        
        if not saved:
            try:
                with open(CASINO_DATA_FILE, 'w', encoding='utf-8') as f:
                    json.dump(casino_stats, f, ensure_ascii=False, indent=2)
                print(f"✅ Данные сохранены напрямую в {CASINO_DATA_FILE}")
                saved = True
            except Exception as e:
                print(f"⚠️ Метод 2 не сработал: {e}")
        
        if not saved:
            try:
                local_file = 'casino_data.json'
                with open(local_file, 'w', encoding='utf-8') as f:
                    json.dump(casino_stats, f, ensure_ascii=False, indent=2)
                print(f"✅ Данные сохранены в локальный файл {local_file}")
                
                # Обновляем путь
                CASINO_DATA_FILE = os.path.abspath(local_file)
                saved = True
            except Exception as e:
                print(f"⚠️ Метод 3 не сработал: {e}")
        
        return saved
        
    except Exception as e:
        print(f"❌ Ошибка при сохранении: {e}")
        return False

def load_casino_data():
    """Загружает данные казино из файла с поиском по разным путям"""
    
    possible_paths = [
        'casino_data.json',  
        'bot_data/casino_data.json',
        'data/casino_data.json',
        os.path.join(os.path.dirname(__file__), 'casino_data.json'),  
        os.path.join(os.getcwd(), 'casino_data.json'),  
    ]
    
    if 'CASINO_DATA_PATH' in os.environ:
        possible_paths.append(os.environ['CASINO_DATA_PATH'])
    
    loaded_data = None
    loaded_path = None
    
    print("🔍 Поиск файла с данными казино...")
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict): 
                        print(f"✅ Найден файл: {path} ({len(data)} пользователей)")
                        loaded_data = data
                        loaded_path = path
                        break
                    else:
                        print(f"⚠️ Файл {path} имеет неверный формат")
            except json.JSONDecodeError as e:
                print(f"⚠️ Файл {path} поврежден: {e}")
            except Exception as e:
                print(f"⚠️ Ошибка при чтении {path}: {e}")
    
    if loaded_data is not None and loaded_path is not None:
        CASINO_DATA_FILE = loaded_path
        print(f"📁 Используем файл: {CASINO_DATA_FILE}")
        return loaded_data
    
    backup_files = glob.glob("*backup*.json") + glob.glob("bot_data/*backup*.json")
    if backup_files:
        print(f"🔍 Найдены бэкап файлы: {', '.join(backup_files)}")
        latest_backup = max(backup_files, key=os.path.getctime)
        try:
            with open(latest_backup, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"✅ Загружен бэкап: {latest_backup} ({len(data)} пользователей)")
                return data
        except:
            pass
    
    print("⚠️ Файл с данными не найден, создаем новый")
    return {}

def save_blackjack_games():
    """Сохраняет активные игры в блэкджек в файл"""
    try:
        games_data = {}
        for game_id, game in blackjack_games.items():
            games_data[game_id] = game.to_dict()
        
        with open(BLACKJACK_GAMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(games_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка при сохранении игр в блэкджек: {e}")

def load_blackjack_games():
    """Загружает активные игры в блэкджек из файла"""
    if not os.path.exists(BLACKJACK_GAMES_FILE):
        return {}
    
    try:
        with open(BLACKJACK_GAMES_FILE, 'r', encoding='utf-8') as f:
            games_data = json.load(f)
        
        # Восстанавливаем объекты игр
        games = {}
        for game_id, data in games_data.items():
            games[game_id] = BlackjackGame.from_dict(data)
        
        return games
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_casino_data_on_exit():
    """Сохраняет данные казино при завершении программы"""
    try:
        with open(CASINO_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(casino_stats, f, ensure_ascii=False, indent=2)
        print(f"Данные казино сохранены для {len(casino_stats)} пользователей")
    except Exception as e:
        print(f"Ошибка при сохранении данных казино при завершении: {e}")
        
TOKEN = 'OTA4NzUyNTM0MjIxNTEyNzA0.GYGFVr.kCh1lYrI3QG4IcfydVB8lxCGz7UIr0Clxfu2gA'
PREFIX = '!'

STATUS_TYPES = {
    "online": discord.Status.online,
    "idle": discord.Status.idle,
    "dnd": discord.Status.dnd,
    "offline": discord.Status.offline,
    "invisible": discord.Status.invisible
}

ACTIVITY_TYPES = {
    "playing": discord.ActivityType.playing,
    "streaming": discord.ActivityType.streaming,
    "listening": discord.ActivityType.listening,
    "watching": discord.ActivityType.watching,
    "competing": discord.ActivityType.competing
}

MUSIC_IMAGES = {
    'now_playing': 'https://i.pinimg.com/736x/6d/13/40/6d13409d4e86b5c24f10f7f6b6403cd3.jpg',
    'added_to_queue': 'https://i.pinimg.com/736x/1d/9b/97/1d9b979d82d4fbb36862d971f39d844f.jpg',
    'queue': 'https://i.pinimg.com/736x/75/82/df/7582dfc6dcf711e5a6d5a5e0072c4936.jpg',
    'search_results': 'https://i.pinimg.com/736x/59/74/5b/59745b6c6092fd4a949fe8c325f8f547.jpg',
    'error': 'https://i.pinimg.com/736x/a3/2e/bd/a32ebdb3a9c3adfb8d8f2302afdbcb31.jpg',
    'casino': 'https://i.pinimg.com/736x/8f/1e/9a/8f1e9a8b5d7c9a6b4d8f9a7b6c5d4e3f.jpg',
    'jackpot': 'https://i.pinimg.com/736x/9e/2d/89/9e2d89b8c9a8d5f7e4b9c7d3f8a2e5b7.jpg',
    'blackjack': 'https://i.pinimg.com/736x/8e/3d/7a/8e3d7a8b9c5d4f6e7a8b9c5d4f6e7a8b.jpg'
}

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch5',
    'source_address': '0.0.0.0',
    'extract_flat': 'in_playlist'
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

FFMPEG_OPTIONS_SEEK = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

COLORS = {
    'success': 0x2ecc71,
    'error': 0xe74c3c,
    'info': 0x3498db,
    'warning': 0xf39c12,
    'music': 0x9b59b6,
    'casino': 0xffd700,  
    'blackjack': 0x34495e  
}

bot = commands.Bot(command_prefix=PREFIX, intents=discord.Intents.all(), help_command=None)

current_song = None
loop_queue = False
loop_single = False
current_view = None
current_message = None 
song_queue = deque()
search_results = {}

casino_stats = load_casino_data()

blackjack_games = load_blackjack_games()

SLOT_EMOJIS = {
    '🍒': 1,   
    '🍋': 2,   
    '🍊': 3,  
    '🍇': 4,   
    '💎': 10,  
    '7️⃣': 20,  
}

SLOT_EMOJI_LIST = list(SLOT_EMOJIS.keys())

class BlackjackGame:
    """Класс для игры в блэкджек между игроками"""
    
    def __init__(self, game_id, channel_id, creator_id, bet_amount):
        self.game_id = game_id
        self.channel_id = channel_id
        self.creator_id = creator_id
        self.bet_amount = bet_amount
        self.players = {}  
        self.deck = self.create_deck()
        random.shuffle(self.deck)
        self.status = 'waiting' 
        self.current_turn_index = 0
        self.turn_order = []
        self.message_id = None
        self.created_at = time.time()
        
        self.add_player(creator_id, bet_amount)
    
    def to_dict(self):
        """Конвертирует объект игры в словарь для сохранения"""
        return {
            'game_id': self.game_id,
            'channel_id': self.channel_id,
            'creator_id': self.creator_id,
            'bet_amount': self.bet_amount,
            'players': self.players,
            'deck': self.deck,
            'status': self.status,
            'current_turn_index': self.current_turn_index,
            'turn_order': self.turn_order,
            'message_id': self.message_id,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """Восстанавливает объект игры из словаря"""
        game = cls(
            data['game_id'],
            data['channel_id'],
            data['creator_id'],
            data['bet_amount']
        )
        game.players = data['players']
        game.deck = data['deck']
        game.status = data['status']
        game.current_turn_index = data['current_turn_index']
        game.turn_order = data['turn_order']
        game.message_id = data['message_id']
        game.created_at = data['created_at']
        return game
    
    def create_deck(self):
        """Создает колоду карт для блэкджека"""
        suits = ['♠', '♥', '♦', '♣']
        values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = []
        for suit in suits:
            for value in values:
                deck.append(f"{value}{suit}")
        return deck
    
    def get_card_value(self, card):
        """Возвращает стоимость карты в очках"""
        value = card[:-1]  
        if value in ['J', 'Q', 'K']:
            return 10
        elif value == 'A':
            return 11
        else:
            return int(value)
    
    def calculate_hand_value(self, cards):
        """Вычисляет стоимость руки с учетом тузов"""
        value = 0
        aces = 0
        
        for card in cards:
            card_value = self.get_card_value(card)
            if card_value == 11:
                aces += 1
            value += card_value
        
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        
        return value
    
    def deal_card(self, user_id):
        """Выдает карту игроку"""
        if not self.deck:
            self.deck = self.create_deck()
            random.shuffle(self.deck)
        
        card = self.deck.pop()
        
        if user_id not in self.players:
            self.players[user_id] = {
                'cards': [],
                'value': 0,
                'status': 'playing',
                'bet': self.bet_amount
            }
        
        self.players[user_id]['cards'].append(card)
        self.players[user_id]['value'] = self.calculate_hand_value(self.players[user_id]['cards'])
        
        if len(self.players[user_id]['cards']) == 2 and self.players[user_id]['value'] == 21:
            self.players[user_id]['status'] = 'blackjack'
        
        elif self.players[user_id]['value'] > 21:
            self.players[user_id]['status'] = 'bust'
        
        return card
    
    def add_player(self, user_id, bet_amount):
        """Добавляет игрока в игру"""
        if user_id not in self.players:
            self.players[user_id] = {
                'cards': [],
                'value': 0,
                'status': 'waiting', 
                'bet': bet_amount
            }
            self.turn_order.append(user_id)
            return True
        return False
    
    def start_game(self):
        """Начинает игру"""
        if len(self.players) < 2:
            return False
        
        self.status = 'playing'
        
        for user_id in self.players:
            self.deal_card(user_id)
            self.deal_card(user_id)
            self.players[user_id]['status'] = 'playing'
        
        self.current_turn_index = 0
        return True
    
    def next_turn(self):
        """Переходит к следующему игроку"""
        self.current_turn_index += 1
        while self.current_turn_index < len(self.turn_order):
            current_player = self.turn_order[self.current_turn_index]
            if self.players[current_player]['status'] in ['playing', 'blackjack']:
                return current_player
            self.current_turn_index += 1
        
        self.status = 'finished'
        return None
    
    def get_current_player(self):
        """Возвращает текущего игрока"""
        if self.current_turn_index < len(self.turn_order):
            return self.turn_order[self.current_turn_index]
        return None
    
    def get_hand_display(self, cards, hide_first=False):
        """Возвращает отображение руки"""
        if hide_first:
            return '🂠 ' + ' '.join(cards[1:])
        else:
            return ' '.join(cards)
    
    def determine_winners(self):
        """Определяет победителей и возвращает словарь с выигрышами"""
        results = {}
        
        best_value = 0
        for user_id, player in self.players.items():
            if player['status'] != 'bust' and player['value'] > best_value:
                best_value = player['value']
        
        winners = []
        for user_id, player in self.players.items():
            if player['status'] != 'bust' and player['value'] == best_value:
                winners.append(user_id)
        
        total_pot = len(self.players) * self.bet_amount
        
        if len(winners) == 1:
            winner_id = winners[0]
            if self.players[winner_id]['status'] == 'blackjack':
                win_amount = int(self.bet_amount * 1.5)
                results[winner_id] = win_amount + self.bet_amount
            else:
                results[winner_id] = total_pot
        elif len(winners) > 1:
            split_amount = total_pot // len(winners)
            for winner_id in winners:
                if self.players[winner_id]['status'] == 'blackjack':
                    win_amount = int(self.bet_amount * 1.5)
                    results[winner_id] = win_amount
                else:
                    results[winner_id] = split_amount
        
        return results, winners

class BlackjackJoinView(View):
    """View для присоединения к игре в блэкджек"""
    
    def __init__(self, game_id, creator_id, bet_amount):
        super().__init__(timeout=300) 
        self.game_id = game_id
        self.creator_id = creator_id
        self.bet_amount = bet_amount
    
    @discord.ui.button(label="Присоединиться к игре", style=discord.ButtonStyle.green, emoji="🎲")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        game = blackjack_games.get(self.game_id)
        
        if not game:
            embed = discord.Embed(
                title="❌ Игра не найдена",
                description="Эта игра больше не существует",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if game.status != 'waiting':
            embed = discord.Embed(
                title="❌ Игра уже началась",
                description="Вы не можете присоединиться к уже начатой игре",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        user_id = str(interaction.user.id)
        
        if user_id in game.players:
            embed = discord.Embed(
                title="❌ Вы уже в игре",
                description="Вы уже присоединились к этой игре",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        stats = get_user_stats(user_id)
        if stats['balance'] < self.bet_amount:
            embed = discord.Embed(
                title="❌ Недостаточно средств",
                description=f"Для игры в блэкджек нужно **{self.bet_amount}** монет, а у вас только **{stats['balance']}**",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        stats['balance'] -= self.bet_amount
        save_casino_data()
        
        game.add_player(user_id, self.bet_amount)
        save_blackjack_games()
        
        embed = discord.Embed(
            title="✅ Вы присоединились к игре!",
            description=f"Ставка: **{self.bet_amount}** монет\nОжидаем других игроков...",
            color=COLORS['success']
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        channel = bot.get_channel(int(game.channel_id))
        if channel:
            try:
                msg = await channel.fetch_message(game.message_id)
                embed = create_game_lobby_embed(game)
                await msg.edit(embed=embed, view=self)
            except:
                pass
    
    @discord.ui.button(label="Начать игру", style=discord.ButtonStyle.blurple, emoji="▶️")
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.creator_id:
            embed = discord.Embed(
                title="❌ Недостаточно прав",
                description="Только создатель игры может начать её",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        game = blackjack_games.get(self.game_id)
        
        if not game:
            embed = discord.Embed(
                title="❌ Игра не найдена",
                description="Эта игра больше не существует",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if len(game.players) < 2:
            embed = discord.Embed(
                title="❌ Недостаточно игроков",
                description="Для начала игры нужно минимум 2 игрока",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not game.start_game():
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Не удалось начать игру",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        save_blackjack_games()
        
        await interaction.message.edit(view=None)
        
        await show_game_turn(interaction.channel, game)

class BlackjackGameView(View):
    """View для игрового процесса блэкджека"""
    
    def __init__(self, game_id, user_id):
        super().__init__(timeout=120) 
        self.game_id = game_id
        self.user_id = user_id
    
    @discord.ui.button(label="Взять карту", style=discord.ButtonStyle.green, emoji="🃏", row=0)
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            embed = discord.Embed(
                title="❌ Не ваш ход",
                description="Сейчас ход другого игрока",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        game = blackjack_games.get(self.game_id)
        
        if not game or game.status != 'playing':
            embed = discord.Embed(
                title="❌ Игра не активна",
                description="Эта игра больше не активна",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        current_player = game.get_current_player()
        if current_player != self.user_id:
            embed = discord.Embed(
                title="❌ Не ваш ход",
                description="Сейчас ход другого игрока",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        card = game.deal_card(self.user_id)
        
        player_status = game.players[self.user_id]['status']
        
        embed = discord.Embed(
            title=f"🃏 Вы взяли карту: {card}",
            description=f"**Ваши карты:** {game.get_hand_display(game.players[self.user_id]['cards'])}\n**Сумма:** {game.players[self.user_id]['value']}",
            color=COLORS['info']
        )
        
        if player_status == 'bust':
            embed.title = "💥 Перебор!"
            embed.description += "\n\nВы проиграли этот раунд."
            embed.color = COLORS['error']
            
            next_player = game.next_turn()
            
            if next_player:
                embed.add_field(name="Следующий ход", value=f"<@{next_player}>", inline=False)
            
            save_blackjack_games()
            await interaction.response.send_message(embed=embed)
            
            await show_game_turn(interaction.channel, game)
            return
        
        save_blackjack_games()
        await interaction.response.send_message(embed=embed)
        
        await show_game_turn(interaction.channel, game, update_only=True)
    
    @discord.ui.button(label="Хватит", style=discord.ButtonStyle.blurple, emoji="✋", row=0)
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            embed = discord.Embed(
                title="❌ Не ваш ход",
                description="Сейчас ход другого игрока",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        game = blackjack_games.get(self.game_id)
        
        if not game or game.status != 'playing':
            embed = discord.Embed(
                title="❌ Игра не активна",
                description="Эта игра больше не активна",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        current_player = game.get_current_player()
        if current_player != self.user_id:
            embed = discord.Embed(
                title="❌ Не ваш ход",
                description="Сейчас ход другого игрока",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        game.players[self.user_id]['status'] = 'stand'
        
        embed = discord.Embed(
            title="✋ Вы остановились",
            description=f"**Ваши карты:** {game.get_hand_display(game.players[self.user_id]['cards'])}\n**Сумма:** {game.players[self.user_id]['value']}",
            color=COLORS['info']
        )
        
        next_player = game.next_turn()
        
        if next_player:
            embed.add_field(name="Следующий ход", value=f"<@{next_player}>", inline=False)
        else:
            embed.add_field(name="Игра завершена", value="Определяем победителей...", inline=False)
        
        save_blackjack_games()
        await interaction.response.send_message(embed=embed)
        
        if game.status == 'finished':
            await finish_blackjack_game(interaction.channel, game)
        else:
            await show_game_turn(interaction.channel, game, update_only=True)
    
    @discord.ui.button(label="Удвоить ставку", style=discord.ButtonStyle.red, emoji="💰", row=1)
    async def double_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            embed = discord.Embed(
                title="❌ Не ваш ход",
                description="Сейчас ход другого игрока",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        game = blackjack_games.get(self.game_id)
        
        if not game or game.status != 'playing':
            embed = discord.Embed(
                title="❌ Игра не активна",
                description="Эта игра больше не активна",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        current_player = game.get_current_player()
        if current_player != self.user_id:
            embed = discord.Embed(
                title="❌ Не ваш ход",
                description="Сейчас ход другого игрока",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if len(game.players[self.user_id]['cards']) != 2:
            embed = discord.Embed(
                title="❌ Нельзя удвоить",
                description="Удвоить ставку можно только после получения первых двух карт",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        stats = get_user_stats(self.user_id)
        if stats['balance'] < game.players[self.user_id]['bet']:
            embed = discord.Embed(
                title="❌ Недостаточно средств",
                description="У вас недостаточно монет для удвоения ставки",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        stats['balance'] -= game.players[self.user_id]['bet']
        game.players[self.user_id]['bet'] *= 2
        save_casino_data()
        
        card = game.deal_card(self.user_id)
        
        embed = discord.Embed(
            title=f"💰 Ставка удвоена!",
            description=f"**Ставка:** {game.players[self.user_id]['bet']} монет\n**Вы взяли карту:** {card}",
            color=COLORS['success']
        )
        
        if game.players[self.user_id]['value'] <= 21:
            game.players[self.user_id]['status'] = 'stand'
            embed.add_field(name="Ваши карты", value=game.get_hand_display(game.players[self.user_id]['cards']), inline=False)
            embed.add_field(name="Сумма", value=game.players[self.user_id]['value'], inline=True)
        else:
            embed.title = "💥 Перебор!"
            embed.description += f"\n\n**Ваши карты:** {game.get_hand_display(game.players[self.user_id]['cards'])}\n**Сумма:** {game.players[self.user_id]['value']}"
            embed.color = COLORS['error']
        
        next_player = game.next_turn()
        
        if next_player:
            embed.add_field(name="Следующий ход", value=f"<@{next_player}>", inline=False)
        else:
            embed.add_field(name="Игра завершена", value="Определяем победителей...", inline=False)
        
        save_blackjack_games()
        await interaction.response.send_message(embed=embed)
        
        if game.status == 'finished':
            await finish_blackjack_game(interaction.channel, game)
        else:
            await show_game_turn(interaction.channel, game, update_only=True)

def create_game_lobby_embed(game):
    """Создает embed для лобби игры"""
    embed = discord.Embed(
        title="🃏 Блэкджек (21) - Лобби",
        description=f"**Ставка:** {game.bet_amount} монет\n"
                   f"**Создатель:** <@{game.creator_id}>\n"
                   f"**Игроков:** {len(game.players)}/∞",
        color=COLORS['blackjack']
    )
    
    if game.players:
        players_list = []
        for user_id in game.players:
            players_list.append(f"<@{user_id}>")
        
        embed.add_field(
            name="👥 Игроки в лобби",
            value="\n".join(players_list),
            inline=False
        )
    
    embed.add_field(
        name="⏰ Таймаут",
        value="Лобби закроется через 5 минут",
        inline=False
    )
    
    embed.set_thumbnail(url=MUSIC_IMAGES['blackjack'])
    embed.set_footer(text="Нажмите кнопку ниже, чтобы присоединиться")
    
    return embed

async def show_game_turn(channel, game, update_only=False):
    """Показывает текущий ход в игре"""
    current_player = game.get_current_player()
    
    if not current_player:
        await finish_blackjack_game(channel, game)
        return
    
    embed = discord.Embed(
        title="🃏 Блэкджек (21) - Ход игрока",
        description=f"**Ставка:** {game.bet_amount} монет",
        color=COLORS['blackjack']
    )
    
    for user_id in game.turn_order:
        player = game.players[user_id]
        status_emoji = {
            'playing': '▶️',
            'stand': '✋',
            'bust': '💥',
            'blackjack': '🃏'
        }.get(player['status'], '⏳')
        
        if user_id == current_player:

            hand_value = player['value']
            hand_display = player['cards']
        else:

            hand_display = player['cards'][:1] + ['🂠'] * (len(player['cards']) - 1)
            hand_value = "?"
        
        cards_text = ' '.join(hand_display)
        embed.add_field(
            name=f"{status_emoji} <@{user_id}>",
            value=f"Карты: {cards_text}\nСумма: {hand_value}",
            inline=False
        )
    
    embed.add_field(
        name="⏰ Ваш ход",
        value=f"<@{current_player}>, выберите действие:",
        inline=False
    )
    
    embed.set_thumbnail(url=MUSIC_IMAGES['blackjack'])
    
    if update_only and game.message_id:
        try:
            msg = await channel.fetch_message(game.message_id)
            await msg.edit(embed=embed, view=BlackjackGameView(game.game_id, current_player))
        except:
            msg = await channel.send(embed=embed, view=BlackjackGameView(game.game_id, current_player))
            game.message_id = msg.id
            save_blackjack_games()
    else:
        msg = await channel.send(embed=embed, view=BlackjackGameView(game.game_id, current_player))
        game.message_id = msg.id
        save_blackjack_games()

async def finish_blackjack_game(channel, game):
    """Завершает игру и определяет победителей"""
    results, winners = game.determine_winners()
    
    embed = discord.Embed(
        title="🃏 Игра завершена!",
        description="Результаты игры в блэкджек:",
        color=COLORS['blackjack']
    )
    
    for user_id in game.turn_order:
        player = game.players[user_id]
        status_text = {
            'stand': f"✋ Остановился",
            'bust': f"💥 Перебор ({player['value']})",
            'blackjack': f"🃏 Блэкджек! ({player['value']})"
        }.get(player['status'], f"📊 {player['value']} очков")
        
        cards_text = ' '.join(player['cards'])
        embed.add_field(
            name=f"<@{user_id}>",
            value=f"Карты: {cards_text}\n{status_text}",
            inline=False
        )
    
    if winners:
        winners_text = ""
        total_pot = len(game.players) * game.bet_amount
        
        for user_id in game.turn_order:
            if user_id in results:
                win_amount = results[user_id]
                winners_text += f"<@{user_id}>: +{win_amount} монет\n"
                
                stats = get_user_stats(user_id)
                stats['balance'] += win_amount
                
                stats['games_played'] = stats.get('games_played', 0) + 1
                stats['wins'] = stats.get('wins', 0) + 1
            else:

                stats = get_user_stats(user_id)
                stats['games_played'] = stats.get('games_played', 0) + 1
                stats['losses'] = stats.get('losses', 0) + 1
        
        embed.add_field(
            name="💰 Выигрыши",
            value=winners_text or "Никто не выиграл",
            inline=False
        )
        
        embed.add_field(
            name="📊 Банк",
            value=f"Всего в банке: {total_pot} монет",
            inline=False
        )
        
        save_casino_data()
    else:
        embed.add_field(
            name="😢 Ничья?",
            value="Все игроки проиграли? Странно...",
            inline=False
        )
    
    embed.set_thumbnail(url=MUSIC_IMAGES['blackjack'])
    embed.set_footer(text="Спасибо за игру!")

    del blackjack_games[game.game_id]
    save_blackjack_games()

    if game.message_id:
        try:
            msg = await channel.fetch_message(game.message_id)
            await msg.edit(embed=embed, view=None)
        except:
            await channel.send(embed=embed)
    else:
        await channel.send(embed=embed)

def format_duration(seconds):
    """Форматирует длительность из секунд в ЧЧ:ММ:СС"""
    if not seconds or seconds == 'N/A':
        return "N/A"
    try:
        seconds = int(seconds)
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"
    except:
        return "N/A"

def create_progress_bar(progress, total, length=15):
    """Создает текстовый прогресс-бар"""
    if total <= 0:
        return "`[----------]` N/A"
    
    progress = min(progress, total)
    percent = progress / total
    filled = int(length * percent)
    bar = '▬' * filled + '🔘' + '▬' * (length - filled - 1)
    time_passed = format_duration(progress)
    
    return f"`[{bar}]` {time_passed}/{format_duration(total)}"

async def extract_song_info(url):
    """Извлекает информацию о песне с правильным названием"""
    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)
    
    try:
        data = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        
        if 'entries' in data:
            data = data['entries'][0]
        
        if 'videoplayback' in data.get('url', '') and 'id' in data:
            video_info = await bot.loop.run_in_executor(
                None, 
                lambda: ytdl.extract_info(f"https://www.youtube.com/watch?v={data['id']}", download=False)
            )
            if video_info:
                data['title'] = video_info.get('title', 'Неизвестный трек')
                data['uploader'] = video_info.get('uploader', 'Неизвестный автор')
                data['thumbnail'] = video_info.get('thumbnail', MUSIC_IMAGES['now_playing'])
                data['duration'] = video_info.get('duration', 0)
        
        return {
            'url': data['url'],
            'title': data.get('title', 'Неизвестный трек'),
            'duration': data.get('duration', 0),
            'uploader': data.get('uploader', 'Неизвестный автор'),
            'thumbnail': data.get('thumbnail', MUSIC_IMAGES['now_playing'])
        }
    except Exception as e:
        print(f"Ошибка при извлечении информации: {e}")
        return None

class SongSelect(Select):
    def __init__(self, options, search_query):
        super().__init__(
            placeholder="Выберите трек для добавления",
            min_values=1,
            max_values=1,
            options=options
        )
        self.search_query = search_query
    
    async def callback(self, interaction: discord.Interaction):
        try:
            selected_index = int(self.values[0])
            selected_song = search_results[interaction.user.id][selected_index]
            
            voice_client = interaction.guild.voice_client
            
            song_queue.append(selected_song)
            embed = discord.Embed(
                title="🎵 Трек добавлен в очередь",
                description=f"**{selected_song['title']}**",
                color=COLORS['success']
            )
            embed.add_field(name="Длительность", value=format_duration(selected_song.get('duration')), inline=True)
            embed.add_field(name="Позиция в очереди", value=f"#{len(song_queue)}", inline=True)
            embed.set_thumbnail(url=MUSIC_IMAGES['added_to_queue'])
            embed.set_footer(text=f"Добавлено пользователем {interaction.user.display_name}", icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
            
            if not voice_client.is_playing():
                ctx = await bot.get_context(interaction.message)
                await play_next(ctx)
            
            if interaction.user.id in search_results:
                del search_results[interaction.user.id]
        except Exception as e:
            embed = discord.Embed(
                title="❌ Ошибка",
                description=f"Произошла ошибка: {str(e)}",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class MusicControls(View):
    def __init__(self):
        super().__init__(timeout=None)
        
        buttons = [
            ("🔁", "loop_queue", discord.ButtonStyle.blurple, self.toggle_queue_loop),
            ("⬅️", "seek_backward", discord.ButtonStyle.grey, self.seek_backward),
            ("⏸️", "pause", discord.ButtonStyle.grey, self.toggle_pause),
            ("➡️", "seek_forward", discord.ButtonStyle.grey, self.seek_forward),
            ("⏭️", "skip", discord.ButtonStyle.green, self.skip_song),
            ("⏹️", "stop", discord.ButtonStyle.red, self.stop_music),
            ("🚪", "leave", discord.ButtonStyle.grey, self.leave_voice)
        ]
        
        for emoji, custom_id, style, callback in buttons:
            button = Button(style=style, emoji=emoji, custom_id=custom_id)
            button.callback = callback
            self.add_item(button)
    
    async def update_buttons(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        
        for child in self.children:
            if child.custom_id == "pause":
                if voice_client and voice_client.is_paused():
                    child.emoji = "▶️"
                    child.style = discord.ButtonStyle.green
                else:
                    child.emoji = "⏸️"
                    child.style = discord.ButtonStyle.grey
            elif child.custom_id == "loop_queue":
                child.style = discord.ButtonStyle.green if loop_queue else discord.ButtonStyle.blurple
        
        await interaction.response.edit_message(view=self)
    
    async def seek(self, interaction: discord.Interaction, seconds: int):
        """Функция перемотки"""
        global current_song, current_message
        
        voice_client = interaction.guild.voice_client
        
        if not voice_client or not voice_client.is_playing():
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Нет активного воспроизведения",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not current_song:
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Информация о текущем треке недоступна",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        current_position = time.time() - current_song['start_time']
        new_position = current_position + seconds
        
        duration = current_song.get('duration_seconds', 0)
        if new_position < 0:
            new_position = 0
        elif new_position > duration:
            new_position = duration
        
        try:

            current_url = current_song['url']

            voice_client.stop()

            seek_options = FFMPEG_OPTIONS.copy()
            seek_options['before_options'] = f'-ss {new_position} -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'

            current_song['start_time'] = time.time() - new_position

            voice_client.play(
                discord.FFmpegPCMAudio(current_url, **seek_options),
                after=lambda e: asyncio.run_coroutine_threadsafe(play_next( bot.get_context(interaction.message)), bot.loop)
            )

            progress_bar = create_progress_bar(new_position, duration)
            
            embed = discord.Embed(
                title="🎶 Сейчас играет",
                description=f"**{current_song['title']}**",
                color=COLORS['music']
            )
            embed.add_field(name="Автор", value=current_song.get('uploader', 'Неизвестный'), inline=True)
            embed.add_field(name="Длительность", value=current_song.get('duration', 'N/A'), inline=True)
            embed.add_field(name="Прогресс", value=progress_bar, inline=False)
            embed.set_thumbnail(url=current_song.get('thumbnail', MUSIC_IMAGES['now_playing']))
            embed.set_footer(text=f"Перемотка: {'+' if seconds > 0 else '-'}{abs(seconds)} сек | Запрошено пользователем {interaction.user.display_name}", 
                           icon_url=interaction.user.avatar.url)

            await interaction.response.edit_message(embed=embed, view=self)

            seek_embed = discord.Embed(
                title="⏪ Перемотка" if seconds < 0 else "⏩ Перемотка",
                description=f"Перемотка на **{abs(seconds)}** секунд {'назад' if seconds < 0 else 'вперед'}",
                color=COLORS['info']
            )
            await interaction.followup.send(embed=seek_embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Ошибка при перемотке",
                description=str(e),
                color=COLORS['error']
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def seek_forward(self, interaction: discord.Interaction):
        """Перемотка вперед на 10 секунд"""
        await self.seek(interaction, 10)
    
    async def seek_backward(self, interaction: discord.Interaction):
        """Перемотка назад на 10 секунд"""
        await self.seek(interaction, -10)
    
    async def toggle_pause(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        
        if not voice_client or not (voice_client.is_playing() or voice_client.is_paused()):
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Нет активного воспроизведения",
                color=COLORS['error']
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if voice_client.is_paused():
            voice_client.resume()
            action = "▶️ Воспроизведение возобновлено"
        else:
            voice_client.pause()
            action = "⏸️ Воспроизведение приостановлено"
        
        await self.update_buttons(interaction)
        
        embed = discord.Embed(
            title=action,
            color=COLORS['info']
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def stop_music(self, interaction: discord.Interaction):
        global current_song, loop_queue, song_queue
        if interaction.guild.voice_client:
            current_song = None
            loop_queue = False
            song_queue.clear()
            interaction.guild.voice_client.stop()
            
            embed = discord.Embed(
                title="⏹️ Воспроизведение остановлено",
                description="Очередь была очищена",
                color=COLORS['info']
            )
            embed.set_thumbnail(url=MUSIC_IMAGES['error'])
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await self.update_buttons(interaction)
        else:
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Бот не в голосовом канале",
                color=COLORS['error']
            )
            embed.set_thumbnail(url=MUSIC_IMAGES['error'])
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def toggle_queue_loop(self, interaction: discord.Interaction):
        global loop_queue
        loop_queue = not loop_queue
        
        embed = discord.Embed(
            title="🔁 Режим повтора очереди",
            description="Режим повтора очереди включен" if loop_queue else "Режим повтора очереди выключен",
            color=COLORS['music']
        )
        embed.set_thumbnail(url=MUSIC_IMAGES['queue'])
        
        for child in self.children:
            if child.custom_id == "loop_queue":
                child.style = discord.ButtonStyle.green if loop_queue else discord.ButtonStyle.blurple
        
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def skip_song(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            interaction.guild.voice_client.stop()
            
            embed = discord.Embed(
                title="⏭️ Трек пропущен",
                description="Переход к следующему треку в очереди",
                color=COLORS['info']
            )
            embed.set_thumbnail(url=MUSIC_IMAGES['now_playing'])
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Бот не в голосовом канале",
                color=COLORS['error']
            )
            embed.set_thumbnail(url=MUSIC_IMAGES['error'])
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def leave_voice(self, interaction: discord.Interaction):
        global current_song, loop_queue, current_view, song_queue
        if interaction.guild.voice_client:
            current_song = None
            loop_queue = False
            song_queue.clear()
            await interaction.guild.voice_client.disconnect()
            current_view = None
            
            embed = discord.Embed(
                title="🚪 Бот покинул голосовой канал",
                description="Все треки были удалены из очереди",
                color=COLORS['info']
            )
            embed.set_thumbnail(url=MUSIC_IMAGES['error'])
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Бот не в голосовом канале",
                color=COLORS['error']
            )
            embed.set_thumbnail(url=MUSIC_IMAGES['error'])
            await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command()
async def forward(ctx, seconds: int = 10):
    """Перематывает вперед на указанное количество секунд (по умолчанию 10)"""
    await seek_command(ctx, seconds)

@bot.command()
async def back(ctx, seconds: int = 10):
    """Перематывает назад на указанное количество секунд (по умолчанию 10)"""
    await seek_command(ctx, -seconds)

@bot.command(aliases=['seek'])
async def seek_command(ctx, seconds: int):
    """Перематывает на указанное количество секунд (отрицательное значение - назад)"""
    global current_song
    
    try:
        voice_client = ctx.voice_client
        
        if not voice_client or not voice_client.is_playing():
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Нет активного воспроизведения",
                color=COLORS['error']
            )
            return await ctx.send(embed=embed)
        
        if not current_song:
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Информация о текущем треке недоступна",
                color=COLORS['error']
            )
            return await ctx.send(embed=embed)

        current_position = time.time() - current_song['start_time']
        new_position = current_position + seconds
        
        duration = current_song.get('duration_seconds', 0)
        if new_position < 0:
            new_position = 0
        elif new_position > duration:
            new_position = duration
        
        current_url = current_song['url']
        
        voice_client.stop()
        
        seek_options = FFMPEG_OPTIONS.copy()
        seek_options['before_options'] = f'-ss {new_position} -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        
        current_song['start_time'] = time.time() - new_position
        
        voice_client.play(
            discord.FFmpegPCMAudio(current_url, **seek_options),
            after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        )
        
        embed = discord.Embed(
            title="⏪ Перемотка" if seconds < 0 else "⏩ Перемотка",
            description=f"Перемотка на **{abs(seconds)}** секунд {'назад' if seconds < 0 else 'вперед'}",
            color=COLORS['info']
        )
        embed.add_field(name="Текущая позиция", value=format_duration(new_position), inline=True)
        embed.add_field(name="Длительность", value=current_song.get('duration', 'N/A'), inline=True)
        embed.set_thumbnail(url=current_song.get('thumbnail', MUSIC_IMAGES['now_playing']))
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        embed = discord.Embed(
            title="❌ Ошибка при перемотке",
            description=str(e),
            color=COLORS['error']
        )
        await ctx.send(embed=embed)

@bot.event
async def on_disconnect():
    """Сохраняет данные при отключении бота"""
    print("Бот отключается, сохраняем данные...")
    save_casino_data()
    save_blackjack_games()
    print("Данные сохранены")

import signal
import sys

def signal_handler(sig, frame):
    """Обработчик сигналов завершения"""
    print(f"\nПолучен сигнал {sig}, сохраняем данные...")
    save_casino_data()
    save_blackjack_games()
    print("Данные сохранены. Завершаем работу.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

@bot.event
async def on_ready():
    print(f'***Бот {bot.user.name} готов к работе!***')
    bot.add_view(MusicControls())
    
    global casino_stats, blackjack_games
    
    print("🔄 Загрузка данных казино...")
    casino_stats = load_casino_data()
    
    if not casino_stats:
        print("⚠️ Данные казино пусты, создаем тестовые данные?")
    
    print(f"📊 Загружены данные казино: {len(casino_stats)} пользователей")
    
    for i, (user_id, stats) in enumerate(list(casino_stats.items())[:3]):
        print(f"   Пользователь {user_id}: баланс {stats.get('balance', 0)}")
    
    blackjack_games = load_blackjack_games()
    print(f"🃏 Загружены игры в блэкджек: {len(blackjack_games)} активных игр")
    
    atexit.register(lambda: save_casino_data())
    
    bot.loop.create_task(passive_income_task())
    bot.loop.create_task(cleanup_old_games())
    bot.loop.create_task(auto_save_task())
    
    saved_status = load_status()
    
    if saved_status:
        status_type = saved_status.get('status_type', 'online')
        activity_type = saved_status.get('activity_type')
        activity_message = saved_status.get('activity_message')
        
        status = STATUS_TYPES.get(status_type.lower(), discord.Status.online)
        
        activity = None
        if activity_type and activity_message:
            activity_type = activity_type.lower()
            
            if activity_type == "streaming":
                parts = activity_message.split("|")
                name = parts[0].strip()
                url = parts[1].strip() if len(parts) > 1 else "https://twitch.tv"
                
                activity = discord.Streaming(
                    name=name,
                    url=url,
                    platform="Twitch" if "twitch.tv" in url else "YouTube"
                )
            else:
                activity = discord.Activity(
                    name=activity_message,
                    type=ACTIVITY_TYPES.get(activity_type, discord.ActivityType.playing)
                )
        
        await bot.change_presence(status=status, activity=activity)
        print(f"Загружен сохраненный статус: {status_type}, {activity_type if activity_type else 'нет активности'}")
    else:
        await bot.change_presence(
            activity=discord.Activity(
                name=f"{PREFIX}bothelp | tg @newersquad",
                type=discord.ActivityType.listening
            ),
            status=discord.Status.online
        )
        print("Установлен стандартный статус")

async def cleanup_old_games():
    """Фоновая задача для очистки старых игр"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            current_time = time.time()
            games_to_remove = []
            
            for game_id, game in blackjack_games.items():
                if current_time - game.created_at > 3600:
                    games_to_remove.append(game_id)

                    if game.status == 'waiting':
                        channel = bot.get_channel(int(game.channel_id))
                        if channel and game.message_id:
                            try:
                                msg = await channel.fetch_message(game.message_id)
                                embed = discord.Embed(
                                    title="⏰ Игра удалена",
                                    description="Игра была удалена из-за истечения времени ожидания",
                                    color=COLORS['error']
                                )
                                await msg.edit(embed=embed, view=None)
                            except:
                                pass
            
            for game_id in games_to_remove:
                del blackjack_games[game_id]
            
            if games_to_remove:
                save_blackjack_games()
                print(f"Удалено {len(games_to_remove)} старых игр в блэкджек")
            
            await asyncio.sleep(3600)
        except Exception as e:
            print(f"Ошибка при очистке старых игр: {e}")
            await asyncio.sleep(3600)

async def update_progress_bar(ctx, message, duration):
    global current_song, current_message
    
    current_message = message
    
    while True:
        await asyncio.sleep(5)
        
        if not current_song or not ctx.voice_client or not ctx.voice_client.is_playing():
            break
            
        try:
            elapsed = time.time() - current_song['start_time']
            progress_bar = create_progress_bar(elapsed, duration)
            
            embed = message.embeds[0]
            if len(embed.fields) >= 3:
                embed.set_field_at(2, name="Прогресс", value=progress_bar, inline=False)
            
            await message.edit(embed=embed)
            
            if elapsed >= duration:
                break
                
        except Exception as e:
            print(f"Ошибка при обновлении прогресс-бара: {e}")
            break

async def play_next(ctx):
    global current_song, song_queue, loop_queue, loop_single
    
    if song_queue:
        if loop_single and current_song:
            song_queue.appendleft(current_song)
        elif loop_queue:
            song_queue.append(current_song)
        
        next_song = song_queue.popleft()
        await play_song(ctx, next_song['url'])
    elif loop_single and current_song:
        await play_song(ctx, current_song['url'])


async def play_song(ctx, url):
    global current_song, current_view
    
    try:
        song_info = await extract_song_info(url)
        if not song_info:
            raise Exception("Не удалось получить информацию о треке")
        
        audio_url = song_info['url']
        title = song_info['title']
        duration_seconds = song_info['duration']
        duration = format_duration(duration_seconds)
        thumbnail = song_info['thumbnail']
        uploader = song_info['uploader']
        
        current_song = {
            'url': audio_url,
            'title': title,
            'duration': duration,
            'duration_seconds': duration_seconds,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'start_time': time.time()
        }
        
        current_view = MusicControls()
        
        progress_bar = create_progress_bar(0, duration_seconds)
        
        embed = discord.Embed(
            title="🎶 Сейчас играет",
            description=f"**{title}**",
            color=COLORS['music']
        )
        embed.add_field(name="Автор", value=uploader, inline=True)
        embed.add_field(name="Длительность", value=duration, inline=True)
        embed.add_field(name="Прогресс", value=progress_bar, inline=False)
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text=f"Запрошено пользователем {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        
        message = await ctx.send(embed=embed, view=current_view)
        
        voice_client = ctx.guild.voice_client
        voice_client.play(discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS), 
                        after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        
        if duration_seconds > 0:
            bot.loop.create_task(update_progress_bar(ctx, message, duration_seconds))
            
    except Exception as e:
        embed = discord.Embed(
            title="❌ Ошибка воспроизведения",
            description=str(e),
            color=COLORS['error']
        )
        embed.set_thumbnail(url=MUSIC_IMAGES['error'])
        await ctx.send(embed=embed)
        await play_next(ctx)

async def show_search_results(ctx, query, results):
    options = []
    for i, song in enumerate(results[:5]):
        title = song.get('title', 'Без названия')[:100]
        duration = format_duration(song.get('duration'))
        options.append(discord.SelectOption(
            label=f"{i+1}. {title}",
            value=str(i),
            description=f"{duration} | {song.get('uploader', 'Неизвестный автор')}"[:100]
        ))
    
    select_menu = SongSelect(options=options, search_query=query)
    view = View()
    view.add_item(select_menu)
    
    embed = discord.Embed(
        title="🔍 Результаты поиска",
        description=f"По запросу: **{query}**\nВыберите трек из списка:",
        color=COLORS['info']
    )
    embed.set_thumbnail(url=MUSIC_IMAGES['search_results'])
    embed.set_footer(text=f"Найдено {len(results)} результатов | Запрошено пользователем {ctx.author.display_name}", 
                   icon_url=ctx.author.avatar.url)
    
    await ctx.send(embed=embed, view=view)

async def auto_save_task():
    """Фоновая задача для автоматического сохранения данных каждые 5 минут"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(300) 
        try:
            save_casino_data()
            save_blackjack_games()
            print(f"Автосохранение: данные казино ({len(casino_stats)} пользователей) и игры ({len(blackjack_games)} игр)")
        except Exception as e:
            print(f"Ошибка при автосохранении: {e}")

@bot.command()
async def play(ctx, *, query: str):
    """Воспроизводит музыку по запросу или ссылке"""
    try:
        if not ctx.author.voice:
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Вы должны находиться в голосовом канале!",
                color=COLORS['error']
            )
            embed.set_thumbnail(url=MUSIC_IMAGES['error'])
            return await ctx.send(embed=embed)
        
        voice_channel = ctx.author.voice.channel
        
        if ctx.voice_client is None:
            await voice_channel.connect()
            
            embed = discord.Embed(
                title="🔊 Подключение к голосовому каналу",
                description=f"Подключился к {voice_channel.mention}",
                color=COLORS['success']
            )
            await ctx.send(embed=embed)
        elif ctx.voice_client.channel != voice_channel:
            await ctx.voice_client.move_to(voice_channel)
            
            embed = discord.Embed(
                title="🔊 Перемещение в голосовой канал",
                description=f"Переместился в {voice_channel.mention}",
                color=COLORS['success']
            )
            await ctx.send(embed=embed)
        
        if query.startswith(('http://', 'https://')):
            if 'list=' in query:
                await process_playlist(ctx, query)
            else:
                await process_single_track(ctx, query)
            return
        
        ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)
        
        try:
            data = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch5:{query}", download=False))
            
            if 'entries' in data:
                results = []
                for entry in data['entries']:
                    if entry:
                        results.append({
                            'url': entry['url'],
                            'title': entry.get('title', 'Без названия'),
                            'duration': entry.get('duration'),
                            'uploader': entry.get('uploader', 'Неизвестный автор'),
                            'thumbnail': entry.get('thumbnail')
                        })
                
                if len(results) == 1:
                    await process_single_track(ctx, results[0]['url'])
                elif len(results) > 1:
                    search_results[ctx.author.id] = results
                    await show_search_results(ctx, query, results)
                else:
                    embed = discord.Embed(
                        title="🔍 Ничего не найдено",
                        description=f"По запросу **{query}** ничего не найдено",
                        color=COLORS['warning']
                    )
                    embed.set_thumbnail(url=MUSIC_IMAGES['error'])
                    await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Ошибка поиска",
                description=str(e),
                color=COLORS['error']
            )
            embed.set_thumbnail(url=MUSIC_IMAGES['error'])
            await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Ошибка в команде play",
            description=str(e),
            color=COLORS['error']
        )
        await ctx.send(embed=embed)

async def process_single_track(ctx, url):
    try:
        song_info = await extract_song_info(url)
        if not song_info:
            raise Exception("Не удалось получить информацию о треке")
        
        title = song_info['title']
        duration = format_duration(song_info['duration'])
        uploader = song_info['uploader']
        thumbnail = song_info['thumbnail']
        
        song_queue.append({
            'url': song_info['url'],
            'title': title,
            'duration': song_info['duration'],
            'uploader': uploader,
            'thumbnail': thumbnail
        })
        
        embed = discord.Embed(
            title="🎵 Трек добавлен в очередь",
            description=f"**{title}**",
            color=COLORS['success']
        )
        embed.add_field(name="Автор", value=uploader, inline=True)
        embed.add_field(name="Длительность", value=duration, inline=True)
        embed.add_field(name="Позиция в очереди", value=f"#{len(song_queue)}", inline=False)
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text=f"Добавлено пользователем {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        
        await ctx.send(embed=embed)
        
        if not ctx.voice_client.is_playing():
            await play_next(ctx)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Ошибка обработки трека",
            description=str(e),
            color=COLORS['error']
        )
        embed.set_thumbnail(url=MUSIC_IMAGES['error'])
        await ctx.send(embed=embed)

async def process_playlist(ctx, url):
    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)
    
    try:
        data = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        
        if 'entries' in data:
            entries = list(data['entries'])[:10]
            added_songs = []
            
            for entry in entries:
                if entry:
                    song_info = await extract_song_info(entry['url'])
                    if song_info:
                        song_data = {
                            'url': song_info['url'],
                            'title': song_info['title'],
                            'duration': song_info['duration'],
                            'uploader': song_info['uploader'],
                            'thumbnail': song_info['thumbnail']
                        }
                        song_queue.append(song_data)
                        added_songs.append(song_data)
            
            if not ctx.voice_client.is_playing():
                await play_next(ctx)
            
            songs_list = "\n".join([f"**{i}.** {song['title']} ({format_duration(song['duration'])})" for i, song in enumerate(added_songs, 1)])
            
            embed = discord.Embed(
                title="🎶 Плейлист добавлен в очередь",
                description=f"Добавлено {len(added_songs)} треков из плейлиста",
                color=COLORS['success']
            )
            embed.add_field(name="Добавленные треки", value=songs_list[:1024], inline=False)
            embed.set_thumbnail(url=data.get('thumbnail', MUSIC_IMAGES['added_to_queue']))
            embed.set_footer(text=f"Добавлено пользователем {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
            
            await ctx.send(embed=embed)
        else:
            await process_single_track(ctx, url)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Ошибка обработки плейлиста",
            description=str(e),
            color=COLORS['error']
        )
        embed.set_thumbnail(url=MUSIC_IMAGES['error'])
        await ctx.send(embed=embed)

@bot.command(aliases=['q'])
async def queue(ctx):
    """Показывает текущую очередь воспроизведения"""
    try:
        if not song_queue and not current_song:
            embed = discord.Embed(
                title="🎵 Очередь воспроизведения",
                description="Очередь пуста! Добавьте треки командой `!play`",
                color=COLORS['warning']
            )
            embed.set_thumbnail(url=MUSIC_IMAGES['queue'])
            return await ctx.send(embed=embed)
        
        embed = discord.Embed(
            title="🎵 Очередь воспроизведения",
            color=COLORS['music']
        )
        
        if current_song:
            embed.add_field(
                name="🎶 Сейчас играет",
                value=f"**{current_song['title']}**\n"
                     f"Автор: {current_song.get('uploader', 'Неизвестный')}\n"
                     f"Длительность: {current_song.get('duration', 'N/A')}",
                inline=False
            )
        
        if song_queue:
            queue_list = []
            for i, song in enumerate(list(song_queue)[:10], 1):
               queue_list.append(
                   f"**{i}.** {song['title']}\n"
                   f"`Длительность: {format_duration(song.get('duration', 'N/A'))} | "
                   f"Автор: {song.get('uploader', 'Неизвестный')}`"
        )
            
            embed.add_field(
                name=f"⏭️ Следующие в очереди ({len(song_queue)})",
                value="\n\n".join(queue_list)[:1024],
                inline=False
            )
            
            if len(song_queue) > 10:
                embed.set_footer(text=f"И ещё {len(song_queue) - 10} треков в очереди")
        else:
            embed.add_field(
                name="⏭️ Следующие в очереди",
                value="Нет треков в очереди",
                inline=False
            )
        
        embed.set_thumbnail(url=MUSIC_IMAGES['queue'])
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Ошибка при показе очереди",
            description=str(e),
            color=COLORS['error']
        )
        await ctx.send(embed=embed)

@bot.command()
async def skip(ctx):
    """Пропускает текущий трек"""
    try:
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            ctx.voice_client.stop()
            
            embed = discord.Embed(
                title="⏭️ Трек пропущен",
                description="Переход к следующему треку в очереди",
                color=COLORS['info']
            )
            embed.set_thumbnail(url=MUSIC_IMAGES['now_playing'])
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Нечего пропускать",
                color=COLORS['error']
            )
            embed.set_thumbnail(url=MUSIC_IMAGES['error'])
            await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Ошибка при пропуске трека",
            description=str(e),
            color=COLORS['error']
        )
        await ctx.send(embed=embed)

@bot.command()
async def pause(ctx):
    """Приостанавливает воспроизведение"""
    try:
        voice_client = ctx.voice_client
        
        if not voice_client or not (voice_client.is_playing() or voice_client.is_paused()):
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Нет активного воспроизведения",
                color=COLORS['error']
            )
            return await ctx.send(embed=embed)
        
        if voice_client.is_paused():
            embed = discord.Embed(
                title="⚠️ Уже на паузе",
                description="Воспроизведение уже приостановлено",
                color=COLORS['warning']
            )
            return await ctx.send(embed=embed)
        
        voice_client.pause()
        
        embed = discord.Embed(
            title="⏸️ Воспроизведение приостановлено",
            color=COLORS['info']
        )
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Ошибка при паузе",
            description=str(e),
            color=COLORS['error']
        )
        await ctx.send(embed=embed)

@bot.command()
async def resume(ctx):
    """Возобновляет воспроизведение"""
    try:
        voice_client = ctx.voice_client
        
        if not voice_client or not voice_client.is_paused():
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Воспроизведение не приостановлено",
                color=COLORS['error']
            )
            return await ctx.send(embed=embed)
        
        voice_client.resume()
        
        embed = discord.Embed(
            title="▶️ Воспроизведение возобновлено",
            color=COLORS['info']
        )
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Ошибка при возобновлении",
            description=str(e),
            color=COLORS['error']
        )
        await ctx.send(embed=embed)

@bot.command()
async def clear(ctx):
    """Очищает очередь воспроизведения"""
    try:
        global song_queue
        count = len(song_queue)
        song_queue.clear()
        
        embed = discord.Embed(
            title="🗑️ Очередь очищена",
            description=f"Удалено {count} треков из очереди",
            color=COLORS['success']
        )
        embed.set_thumbnail(url=MUSIC_IMAGES['queue'])
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Ошибка при очистке очереди",
            description=str(e),
            color=COLORS['error']
        )
        await ctx.send(embed=embed)

@bot.command()
async def nowplaying(ctx):
    """Показывает информацию о текущем треке"""
    try:
        if not current_song:
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Сейчас ничего не играет",
                color=COLORS['error']
            )
            embed.set_thumbnail(url=MUSIC_IMAGES['error'])
            return await ctx.send(embed=embed)
        
        elapsed = time.time() - current_song['start_time']
        duration_seconds = current_song.get('duration_seconds', 0)
        progress_bar = create_progress_bar(elapsed, duration_seconds)
        
        embed = discord.Embed(
            title="🎶 Сейчас играет",
            description=f"**{current_song['title']}**",
            color=COLORS['music']
        )
        embed.add_field(name="Автор", value=current_song.get('uploader', 'Неизвестный'), inline=True)
        embed.add_field(name="Длительность", value=current_song.get('duration', 'N/A'), inline=True)
        embed.add_field(name="Прогресс", value=progress_bar, inline=False)
        embed.add_field(name="Перемотка", value="Используйте `!forward [сек]` или `!back [сек]` для перемотки", inline=False)
        embed.set_thumbnail(url=current_song.get('thumbnail', MUSIC_IMAGES['now_playing']))
        embed.set_footer(text=f"Запрошено пользователем {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        
        message = await ctx.send(embed=embed)
        
        if ctx.voice_client and ctx.voice_client.is_playing() and duration_seconds > 0:
            bot.loop.create_task(update_progress_bar(ctx, message, duration_seconds))
    except Exception as e:
        embed = discord.Embed(
            title="❌ Ошибка при показе текущего трека",
            description=str(e),
            color=COLORS['error']
        )
        await ctx.send(embed=embed)

@bot.command()
async def loopqueue(ctx):
    """Включает/выключает повтор очереди или текущего трека"""
    try:
        global loop_queue, loop_single
        
        if not loop_queue and not loop_single:
            loop_queue = True
            mode = "очереди"
        elif loop_queue and not loop_single:
            loop_queue = False
            loop_single = True
            mode = "текущего трека"
        else:
            loop_queue = False
            loop_single = False
            mode = "выключен"
        
        embed = discord.Embed(
            title="🔁 Режим повтора",
            description=f"Режим повтора {mode} {'включен' if loop_queue or loop_single else 'выключен'}",
            color=COLORS['music']
        )
        embed.set_thumbnail(url=MUSIC_IMAGES['queue'])
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Ошибка при изменении режима повтора",
            description=str(e),
            color=COLORS['error']
        )
        await ctx.send(embed=embed)

@bot.command()
async def stop(ctx):
    """Останавливает воспроизведение и очищает очередь"""
    try:
        global current_song, loop_queue, loop_single, song_queue
        if ctx.voice_client:
            current_song = None
            loop_queue = False
            loop_single = False
            song_queue.clear()
            ctx.voice_client.stop()
            
            embed = discord.Embed(
                title="⏹️ Воспроизведение остановлено",
                description="Очередь была очищена, режимы повтора сброшены",
                color=COLORS['info']
            )
            embed.set_thumbnail(url=MUSIC_IMAGES['error'])
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Бот не в голосовом канале",
                color=COLORS['error']
            )
            embed.set_thumbnail(url=MUSIC_IMAGES['error'])
            await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Ошибка при остановке",
            description=str(e),
            color=COLORS['error']
        )
        await ctx.send(embed=embed)

@bot.command()
async def leave(ctx):
    """Отключает бота от голосового канала"""
    try:
        global current_song, loop_queue, current_view, song_queue
        if ctx.voice_client:
            current_song = None
            loop_queue = False
            song_queue.clear()
            await ctx.voice_client.disconnect()
            current_view = None
            
            embed = discord.Embed(
                title="🚪 Бот покинул голосовой канал",
                description="Все треки были удалены из очереди",
                color=COLORS['info']
            )
            embed.set_thumbnail(url=MUSIC_IMAGES['error'])
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Бот не в голосовом канале",
                color=COLORS['error']
            )
            embed.set_thumbnail(url=MUSIC_IMAGES['error'])
            await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Ошибка",
            description="Бот не в голосовом канале",
            color=COLORS['error']
        )
        embed.set_thumbnail(url=MUSIC_IMAGES['error'])
        await ctx.send(embed=embed)

@bot.command()
async def bothelp(ctx):
    """Показывает список команд"""
    embed = discord.Embed(
        title="🎵 Помощь по музыкальному боту",
        description="Список доступных команд:",
        color=COLORS['info']
    )
    
    commands_list = [
        ("!play <запрос/ссылка>", "Добавляет трек или плейлист в очередь"),
        ("!queue (!q)", "Показывает текущую очередь воспроизведения"),
        ("!skip", "Пропускает текущий трек"),
        ("!pause", "Приостанавливает воспроизведение"),
        ("!resume", "Возобновляет воспроизведение"),
        ("!nowplaying", "Показывает информацию о текущем треке"),
        ("!forward [сек=10]", "Перемотка вперед на указанное количество секунд"),
        ("!back [сек=10]", "Перемотка назад на указанное количество секунд"),
        ("!seek [сек]", "Перемотка на указанное количество секунд (отрицательное - назад)"),
        ("!clear", "Очищает очередь воспроизведения"),
        ("!loopqueue", "Циклически переключает режимы повтора (очередь/1 трек/выкл)"),
        ("!stop", "Останавливает воспроизведение и очищает очередь"),
        ("!leave", "Отключает бота от голосового канала"),
        ("!daily", "🎁 Получить ежедневный бонус 50000 монет"),
        ("!work", "💼 Заработать 10000 монет (раз в 5 минут)"),
        ("!casino [ставка]", "🎰 Игра в казино (слоты)"),
        ("!balance", "💰 Показать ваш баланс в казино"),
        ("!casinotop", "🏆 Топ 10 богатейших игроков"),
        ("!blackjack <ставка>", "🃏 Создать игру в блэкджек (21) с другими игроками"),
        ("!blackjacklist", "📋 Показать список активных игр в блэкджек"),
        ("!bothelp", "Показывает это сообщение"),
    ]
    
    for name, value in commands_list:
        embed.add_field(name=name, value=value, inline=False)
    
    embed.set_thumbnail(url=MUSIC_IMAGES['now_playing'])
    embed.set_footer(text=f"Запрошено пользователем {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
    
    await ctx.send(embed=embed)

@bot.command()
@commands.is_owner()
async def setstatus(ctx, status_type: str = None, activity_type: str = None, *, message: str = None):
    """Устанавливает статус бота"""
    try:
        status = STATUS_TYPES.get(status_type.lower() if status_type else "online", discord.Status.online)
        
        activity = None
        if activity_type and message:
            activity_type = activity_type.lower()
            
            if activity_type == "streaming":
                parts = message.split("|")
                name = parts[0].strip()
                url = parts[1].strip() if len(parts) > 1 else "https://twitch.tv/yosh1vl"
                
                activity = discord.Streaming(
                    name=name,
                    url=url,
                    platform="Twitch" if "twitch.tv" in url else "YouTube"
                )
            else:
                activity = discord.Activity(
                    name=message,
                    type=ACTIVITY_TYPES.get(activity_type, discord.ActivityType.playing)
                )
        
        await bot.change_presence(status=status, activity=activity)
        
        save_status(status_type, activity_type, message)
        
        embed = discord.Embed(
            title="✅ Статус бота обновлен",
            color=COLORS['success']
        )
        
        if status_type:
            embed.add_field(name="Статус", value=status_type, inline=True)
        if activity:
            embed.add_field(name="Активность", value=f"{activity_type}: {message}", inline=True)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        embed = discord.Embed(
            title="❌ Ошибка при установке статуса",
            description=f"Правильное использование: `{PREFIX}setstatus [online/idle/dnd/offline/invisible] [playing/streaming/listening/watching/competing] [текст]`\n\nОшибка: {str(e)}",
            color=COLORS['error']
        )
        await ctx.send(embed=embed)

async def passive_income_task():
    """Фоновая задача для пассивного заработка"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:

            await asyncio.sleep(300) 

            for guild in bot.guilds:
                for voice_channel in guild.voice_channels:
                    for member in voice_channel.members:
                        if not member.bot: 
                            user_id = str(member.id)
                            if user_id not in casino_stats:
                                casino_stats[user_id] = {
                                    'balance': 10000, 
                                    'games_played': 0,
                                    'wins': 0,
                                    'losses': 0,
                                    'jackpots': 0,
                                    'last_work': 0,
                                    'last_daily': 0
                                }
                            else:
                                casino_stats[user_id]['balance'] += 10000
                            
                            save_casino_data()
                            
                            print(f"Бонус 10000 монет выдан {member.name} за нахождение в голосовом канале")
        except Exception as e:
            print(f"Ошибка в пассивном заработке: {e}")

def get_user_stats(user_id):
    """Получает или создает статистику пользователя"""
    if user_id not in casino_stats:
        casino_stats[user_id] = {
            'balance': 10000,
            'games_played': 0,
            'wins': 0,
            'losses': 0,
            'jackpots': 0,
            'last_work': 0,
            'last_daily': 0
        }

        save_casino_data()
    return casino_stats[user_id]

@bot.command(aliases=['bal'])
async def balance(ctx, member: discord.Member = None):
    """Показывает баланс пользователя в казино"""
    target = member or ctx.author
    user_id = str(target.id)
    stats = get_user_stats(user_id)
    
    embed = discord.Embed(
        title=f"💰 Баланс {target.display_name}",
        color=COLORS['casino']
    )
    embed.add_field(name="Монеты", value=f"**{stats['balance']}** 💰", inline=True)
    embed.add_field(name="Сыграно игр", value=stats['games_played'], inline=True)
    embed.add_field(name="Побед/Поражений", value=f"{stats['wins']}/{stats['losses']}", inline=True)
    
    if stats['jackpots'] > 0:
        embed.add_field(name="🎉 Джекпотов", value=stats['jackpots'], inline=True)

    current_time = time.time()
    work_cooldown = max(0, 300 - (current_time - stats.get('last_work', 0)))
    daily_cooldown = max(0, 86400 - (current_time - stats.get('last_daily', 0)))
    
    if work_cooldown > 0:
        work_time = f"{int(work_cooldown // 60)}м {int(work_cooldown % 60)}с"
        embed.add_field(name="💼 Работа", value=f"Доступна через {work_time}", inline=False)
    else:
        embed.add_field(name="💼 Работа", value="✅ Доступна! Используйте !work", inline=False)
    
    if daily_cooldown > 0:
        daily_time = f"{int(daily_cooldown // 3600)}ч {int((daily_cooldown % 3600) // 60)}м"
        embed.add_field(name="🎁 Daily", value=f"Доступен через {daily_time}", inline=False)
    else:
        embed.add_field(name="🎁 Daily", value="✅ Доступен! Используйте !daily", inline=False)
    
    embed.set_thumbnail(url=MUSIC_IMAGES['casino'])
    embed.set_footer(text="Используйте !work для работы или !daily для ежедневного бонуса")
    
    await ctx.send(embed=embed)

@bot.command()
@commands.is_owner()
async def casino_path(ctx):
    """Показывает где ищутся файлы с данными"""
    embed = discord.Embed(
        title="📁 Информация о путях к файлам",
        color=COLORS['info']
    )
    
    current_dir = os.getcwd()
    script_dir = os.path.dirname(__file__) if '__file__' in locals() else 'unknown'
    
    embed.add_field(name="Текущая директория", value=current_dir, inline=False)
    embed.add_field(name="Директория скрипта", value=script_dir, inline=False)
    embed.add_field(name="Путь к файлу данных", value=CASINO_DATA_FILE, inline=False)

    if os.path.exists(CASINO_DATA_FILE):
        size = os.path.getsize(CASINO_DATA_FILE)
        mtime = datetime.fromtimestamp(os.path.getmtime(CASINO_DATA_FILE)).strftime("%Y-%m-%d %H:%M:%S")
        embed.add_field(name="Файл существует", value=f"✅ Да ({size} байт, изменен {mtime})", inline=False)
    else:
        embed.add_field(name="Файл существует", value="❌ Нет", inline=False)

    json_files = glob.glob("**/*.json", recursive=True)
    if json_files:
        files_list = "\n".join(json_files[:10])
        if len(json_files) > 10:
            files_list += f"\n... и еще {len(json_files) - 10}"
        embed.add_field(name="Найденные JSON файлы", value=files_list[:1024], inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
@commands.is_owner()
async def casino_import(ctx, source_file: str = None):
    """Импортирует данные из указанного файла"""
    if source_file is None:

        json_files = glob.glob("*.json")
        if not json_files:
            await ctx.send("❌ Нет JSON файлов для импорта")
            return
        
        file_list = "\n".join([f"{i+1}. {f}" for i, f in enumerate(json_files)])
        await ctx.send(f"📋 Доступные файлы:\n{file_list}\n\nИспользуйте: !casino_import <имя_файла>")
        return
    
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            imported_data = json.load(f)
        
        if not isinstance(imported_data, dict):
            await ctx.send("❌ Неверный формат данных")
            return
        
        global casino_stats
        old_count = len(casino_stats)
        casino_stats.update(imported_data)
        save_casino_data()
        
        embed = discord.Embed(
            title="✅ Данные импортированы",
            description=f"Было: {old_count} пользователей\nСтало: {len(casino_stats)} пользователей\nДобавлено: {len(imported_data)}",
            color=COLORS['success']
        )
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Ошибка импорта: {e}")

@bot.command()
async def daily(ctx):
    """Ежедневный бонус 50000 монет"""
    user_id = str(ctx.author.id)
    stats = get_user_stats(user_id)
    
    current_time = time.time()
    last_daily = stats.get('last_daily', 0)

    if current_time - last_daily < 86400:
        time_left = 86400 - (current_time - last_daily)
        hours = int(time_left // 3600)
        minutes = int((time_left % 3600) // 60)
        
        embed = discord.Embed(
            title="❌ Daily уже получен",
            description=f"Следующий daily будет доступен через **{hours}ч {minutes}м**",
            color=COLORS['error']
        )
        embed.set_thumbnail(url=MUSIC_IMAGES['error'])
        return await ctx.send(embed=embed)
    
    stats['balance'] += 50000
    stats['last_daily'] = current_time
    save_casino_data()
    
    embed = discord.Embed(
        title="🎁 Ежедневный бонус получен!",
        description=f"**{ctx.author.display_name}**, вы получили **50000** монет!",
        color=COLORS['success']
    )
    embed.add_field(name="💰 Новый баланс", value=f"**{stats['balance']}** монет", inline=True)
    embed.set_thumbnail(url=MUSIC_IMAGES['casino'])
    
    await ctx.send(embed=embed)

@bot.command()
async def work(ctx):
    """Заработать 10000 монет (раз в 5 минут)"""
    user_id = str(ctx.author.id)
    stats = get_user_stats(user_id)
    
    current_time = time.time()
    last_work = stats.get('last_work', 0)
    
    if current_time - last_work < 300: 
        time_left = 300 - (current_time - last_work)
        minutes = int(time_left // 60)
        seconds = int(time_left % 60)
        
        embed = discord.Embed(
            title="❌ Вы уже работали недавно",
            description=f"Следующая работа будет доступна через **{minutes}м {seconds}с**",
            color=COLORS['error']
        )
        embed.set_thumbnail(url=MUSIC_IMAGES['error'])
        return await ctx.send(embed=embed)
    
    earnings = random.randint(8000, 12000)
    
    stats['balance'] += earnings
    stats['last_work'] = current_time
    save_casino_data()
    
    work_messages = [
        "💼 Вы поработали грузчиком и получили",
        "👨‍💻 Вы написали код и заработали",
        "🎤 Вы выступили на концерте и получили",
        "🎨 Вы нарисовали картину и продали за",
        "🔧 Вы починили компьютер и заработали",
        "📚 Вы провели урок и получили",
        "🍳 Вы поработали поваром и заработали",
        "🚗 Вы таксовали и получили"
    ]
    
    embed = discord.Embed(
        title=random.choice(work_messages),
        description=f"**{earnings}** монет!",
        color=COLORS['success']
    )
    embed.add_field(name="💰 Новый баланс", value=f"**{stats['balance']}** монет", inline=True)
    embed.set_thumbnail(url=MUSIC_IMAGES['casino'])
    
    await ctx.send(embed=embed)

@bot.command(aliases=['top'])
async def casinotop(ctx, limit: int = 10):
    """Показывает топ игроков по балансу"""
    if limit > 20:
        limit = 20
    
    sorted_players = sorted(casino_stats.items(), key=lambda x: x[1]['balance'], reverse=True)[:limit]
    
    embed = discord.Embed(
        title="🏆 Топ игроков казино",
        color=COLORS['casino']
    )
    
    top_text = ""
    for i, (user_id, stats) in enumerate(sorted_players, 1):
        try:
            user = await bot.fetch_user(int(user_id))
            name = user.name
        except:
            name = f"Пользователь {user_id[:5]}..."
        
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        top_text += f"{medal} **{name}** - {stats['balance']} 💰\n"
    
    embed.description = top_text
    embed.set_thumbnail(url=MUSIC_IMAGES['casino'])
    embed.set_footer(text=f"Всего игроков: {len(casino_stats)}")
    
    await ctx.send(embed=embed)

@bot.command(aliases=['slot', 'slots'])
async def casino(ctx, bet: int = None):
    """
    🎰 Казино - игра в слоты!
    
    Использование: !casino [ставка]
    Пример: !casino 100
    
    Выигрышные комбинации:
    🍒🍒🍒 - x10
    🍋🍋🍋 - x10  
    🍊🍊🍊 - x10
    🍇🍇🍇 - x10
    💎💎💎 - x10
    7️⃣7️⃣7️⃣ - x20 (ДЖЕКПОТ!)
    
    Две одинаковых - x2
    """
    
    try:
        user_id = str(ctx.author.id)
        stats = get_user_stats(user_id)
        
        if bet is None:
            embed = discord.Embed(
                title="🎰 Ваш баланс в казино",
                description=f"**{ctx.author.display_name}**, у вас **{stats['balance']}** монет",
                color=COLORS['info']
            )
            embed.add_field(name="Сыграно игр", value=stats['games_played'], inline=True)
            embed.add_field(name="Побед", value=stats['wins'], inline=True)
            embed.add_field(name="Поражений", value=stats['losses'], inline=True)
            if stats['jackpots'] > 0:
                embed.add_field(name="🎉 Джекпотов", value=stats['jackpots'], inline=True)
            embed.set_thumbnail(url=MUSIC_IMAGES['casino'])
            return await ctx.send(embed=embed)
        
        if bet <= 0:
            embed = discord.Embed(
                title="❌ Ошибка",
                description="Ставка должна быть положительным числом!",
                color=COLORS['error']
            )
            return await ctx.send(embed=embed)
        
        if bet > stats['balance']:
            embed = discord.Embed(
                title="❌ Недостаточно средств",
                description=f"У вас только **{stats['balance']}** монет",
                color=COLORS['error']
            )
            return await ctx.send(embed=embed)
        
        results = [random.randint(0, len(SLOT_EMOJI_LIST)-1) for _ in range(3)]
        slot_display = ' | '.join([SLOT_EMOJI_LIST[r] for r in results])
        
        win_amount = 0
        win_type = ""
        
        if results[0] == results[1] == results[2] == SLOT_EMOJI_LIST.index('7️⃣'):
            win_amount = bet * 50
            stats['jackpots'] += 1
            win_type = "🎉 ДЖЕКПОТ! 🎉"

        elif results[0] == results[1] == results[2]:
            multiplier = SLOT_EMOJIS[SLOT_EMOJI_LIST[results[0]]] * 10
            win_amount = bet * multiplier
            win_type = f"🎰 ТРИ ОДИНАКОВЫХ! x{multiplier}"

        elif results[0] == results[1] or results[1] == results[2] or results[0] == results[2]:

            if results[0] == results[1]:
                pair_emoji = SLOT_EMOJI_LIST[results[0]]
            elif results[1] == results[2]:
                pair_emoji = SLOT_EMOJI_LIST[results[1]]
            else:
                pair_emoji = SLOT_EMOJI_LIST[results[0]]
            
            multiplier = SLOT_EMOJIS[pair_emoji] * 2
            win_amount = bet * multiplier
            win_type = f"🎰 ПАРА! x{multiplier}"

        stats['games_played'] += 1
        
        if win_amount > 0:
            stats['balance'] += win_amount - bet
            stats['wins'] += 1
            result_text = f"**ВЫИГРЫШ! +{win_amount}**"
            color = COLORS['success']
        else:
            stats['balance'] -= bet
            stats['losses'] += 1
            win_amount = 0
            result_text = "**ПРОИГРЫШ**"
            color = COLORS['error']
            win_type = "😢 Повезет в следующий раз!"

        save_casino_data()

        embed = discord.Embed(
            title="🎰 КАЗИНО 🎰",
            color=color
        )

        spin_message = await ctx.send("🎰 **ВРАЩАЕМ СЛОТЫ...** 🎰")
        await asyncio.sleep(1)
        
        for i in range(3):
            fake_spin = f"`{random.choice(SLOT_EMOJI_LIST)} | {random.choice(SLOT_EMOJI_LIST)} | {random.choice(SLOT_EMOJI_LIST)}`"
            await spin_message.edit(content=f"🎰 {fake_spin}")
            await asyncio.sleep(0.5)

        embed.description = f"**{slot_display}**\n\n{result_text}"
        embed.add_field(name="💰 Ставка", value=f"{bet} монет", inline=True)
        embed.add_field(name="💎 Выигрыш", value=f"{win_amount} монет", inline=True)
        embed.add_field(name="📊 Результат", value=win_type, inline=False)
        embed.add_field(name="💳 Новый баланс", value=f"**{stats['balance']}** монет", inline=False)
        
        if win_type == "🎉 ДЖЕКПОТ! 🎉":
            embed.set_thumbnail(url=MUSIC_IMAGES['jackpot'])
        
        embed.set_footer(text=f"Игрок: {ctx.author.display_name} | Сыграно игр: {stats['games_played']}", 
                        icon_url=ctx.author.avatar.url)
        
        await spin_message.edit(content=None, embed=embed)
        
    except Exception as e:
        embed = discord.Embed(
            title="❌ Ошибка в казино",
            description=f"Произошла ошибка: {str(e)}",
            color=COLORS['error']
        )
        await ctx.send(embed=embed)

@bot.command(aliases=['casinostats', 'cs'])
async def casinostat(ctx, member: discord.Member = None):
    """Показывает статистику в казино"""
    target = member or ctx.author
    user_id = str(target.id)
    stats = get_user_stats(user_id)
    
    win_rate = (stats['wins'] / stats['games_played'] * 100) if stats['games_played'] > 0 else 0
    
    embed = discord.Embed(
        title=f"🎰 Статистика казино для {target.display_name}",
        color=COLORS['info']
    )
    embed.add_field(name="💰 Баланс", value=f"**{stats['balance']}** монет", inline=True)
    embed.add_field(name="🎮 Сыграно игр", value=stats['games_played'], inline=True)
    embed.add_field(name="📊 Процент побед", value=f"{win_rate:.1f}%", inline=True)
    embed.add_field(name="🏆 Побед", value=stats['wins'], inline=True)
    embed.add_field(name="💔 Поражений", value=stats['losses'], inline=True)
    if stats['jackpots'] > 0:
        embed.add_field(name="🎉 Джекпотов", value=stats['jackpots'], inline=True)
    
    embed.set_footer(text="Используйте !casino [ставка] для игры")
    
    await ctx.send(embed=embed)

@bot.command(aliases=['casinoadmin'])
@commands.is_owner()
async def casino_setbalance(ctx, member: discord.Member, amount: int):
    """Админская команда для установки баланса в казино"""
    try:
        user_id = str(member.id)
        stats = get_user_stats(user_id)
        
        old_balance = stats['balance']
        stats['balance'] = amount
        save_casino_data() 
        
        embed = discord.Embed(
            title="✅ Баланс обновлен",
            description=f"Баланс для {member.mention} изменен с **{old_balance}** на **{amount}** монет",
            color=COLORS['success']
        )
        await ctx.send(embed=embed)
        
    except Exception as e:
        embed = discord.Embed(
            title="❌ Ошибка",
            description=str(e),
            color=COLORS['error']
        )
        await ctx.send(embed=embed)

@bot.command(aliases=['bj'])
async def blackjack(ctx, bet: int):
    """Создает игру в блэкджек (21) с указанной ставкой"""
    
    user_id = str(ctx.author.id)
    stats = get_user_stats(user_id)
    
    if bet <= 0:
        embed = discord.Embed(
            title="❌ Ошибка",
            description="Ставка должна быть положительным числом!",
            color=COLORS['error']
        )
        return await ctx.send(embed=embed)
    
    if bet > stats['balance']:
        embed = discord.Embed(
            title="❌ Недостаточно средств",
            description=f"У вас только **{stats['balance']}** монет",
            color=COLORS['error']
        )
        return await ctx.send(embed=embed)
    
    stats['balance'] -= bet
    save_casino_data()
    
    game_id = f"{ctx.channel.id}-{int(time.time())}"
    game = BlackjackGame(game_id, str(ctx.channel.id), user_id, bet)
    blackjack_games[game_id] = game
    save_blackjack_games()

    embed = create_game_lobby_embed(game)
    
    view = BlackjackJoinView(game_id, user_id, bet)
    
    msg = await ctx.send(embed=embed, view=view)
    game.message_id = msg.id
    save_blackjack_games()
    
    embed_info = discord.Embed(
        title="🃏 Игра в блэкджек создана!",
        description=f"Ставка: **{bet}** монет\n"
                   f"Для присоединения нажмите кнопку ниже.\n"
                   f"Минимум игроков: 2",
        color=COLORS['success']
    )
    await ctx.send(embed=embed_info)

@bot.command(aliases=['bjlist'])
async def blackjacklist(ctx):
    """Показывает список активных игр в блэкджек"""
    
    active_games = []
    for game_id, game in blackjack_games.items():
        if game.status == 'waiting' and game.channel_id == str(ctx.channel.id):
            active_games.append(game)
    
    if not active_games:
        embed = discord.Embed(
            title="📋 Активные игры в блэкджек",
            description="В этом канале нет активных игр",
            color=COLORS['info']
        )
        return await ctx.send(embed=embed)
    
    embed = discord.Embed(
        title="📋 Активные игры в блэкджек",
        description=f"В этом канале найдено {len(active_games)} игр:",
        color=COLORS['blackjack']
    )
    
    for game in active_games[:5]: 
        embed.add_field(
            name=f"🃏 Игра от <@{game.creator_id}>",
            value=f"Ставка: **{game.bet_amount}** монет\n"
                 f"Игроков: {len(game.players)}\n"
                 f"ID: `{game.game_id}`",
            inline=False
        )
    
    embed.set_thumbnail(url=MUSIC_IMAGES['blackjack'])
    embed.set_footer(text="Используйте !blackjackjoin <ID> чтобы присоединиться")
    
    await ctx.send(embed=embed)

@bot.command()
@commands.is_owner()
async def casinosave(ctx):
    """Принудительно сохраняет данные казино"""
    try:
        save_casino_data()
        save_blackjack_games()
        embed = discord.Embed(
            title="✅ Данные сохранены",
            description=f"Казино: {len(casino_stats)} пользователей\nБлэкджек: {len(blackjack_games)} игр",
            color=COLORS['success']
        )
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Ошибка при сохранении",
            description=str(e),
            color=COLORS['error']
        )
        await ctx.send(embed=embed)

@bot.command()
@commands.is_owner()
async def casinodata(ctx):
    """Показывает информацию о сохраненных данных"""
    try:
        file_size = os.path.getsize(CASINO_DATA_FILE) if os.path.exists(CASINO_DATA_FILE) else 0
        
        embed = discord.Embed(
            title="📊 Информация о данных казино",
            color=COLORS['info']
        )
        embed.add_field(name="Пользователей в памяти", value=len(casino_stats), inline=True)
        embed.add_field(name="Активных игр", value=len(blackjack_games), inline=True)
        embed.add_field(name="Размер файла", value=f"{file_size} байт", inline=True)
        
        if os.path.exists(CASINO_DATA_FILE):
            mod_time = os.path.getmtime(CASINO_DATA_FILE)
            last_save = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
            embed.add_field(name="Последнее сохранение", value=last_save, inline=False)
        
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Ошибка",
            description=str(e),
            color=COLORS['error']
        )
        await ctx.send(embed=embed)

@bot.command(aliases=['bjjoin'])
async def blackjackjoin(ctx, game_id: str):
    """Присоединяется к существующей игре в блэкджек по ID"""
    
    game = blackjack_games.get(game_id)
    
    if not game:
        embed = discord.Embed(
            title="❌ Игра не найдена",
            description=f"Игра с ID `{game_id}` не существует",
            color=COLORS['error']
        )
        return await ctx.send(embed=embed)
    
    if game.status != 'waiting':
        embed = discord.Embed(
            title="❌ Игра уже началась",
            description="Эта игра уже началась или завершена",
            color=COLORS['error']
        )
        return await ctx.send(embed=embed)
    
    user_id = str(ctx.author.id)
    
    if user_id in game.players:
        embed = discord.Embed(
            title="❌ Вы уже в игре",
            description="Вы уже присоединились к этой игре",
            color=COLORS['error']
        )
        return await ctx.send(embed=embed)
    
    stats = get_user_stats(user_id)
    if stats['balance'] < game.bet_amount:
        embed = discord.Embed(
            title="❌ Недостаточно средств",
            description=f"Для игры в блэкджек нужно **{game.bet_amount}** монет, а у вас только **{stats['balance']}**",
            color=COLORS['error']
        )
        return await ctx.send(embed=embed)
    
    stats['balance'] -= game.bet_amount
    save_casino_data()
    
    game.add_player(user_id, game.bet_amount)
    save_blackjack_games()
    
    embed = discord.Embed(
        title="✅ Вы присоединились к игре!",
        description=f"Ставка: **{game.bet_amount}** монет\n"
                   f"Игроков в игре: {len(game.players)}",
        color=COLORS['success']
    )
    await ctx.send(embed=embed)
    
    try:
        channel = bot.get_channel(int(game.channel_id))
        if channel and game.message_id:
            msg = await channel.fetch_message(game.message_id)
            embed = create_game_lobby_embed(game)
            await msg.edit(embed=embed)
    except:
        pass

@bot.command(aliases=['bjstart'])
async def blackjackstart(ctx, game_id: str = None):
    """Начинает игру в блэкджек (если создатель)"""
    
    if not game_id:
        for gid, game in blackjack_games.items():
            if game.creator_id == str(ctx.author.id) and game.status == 'waiting':
                game_id = gid
                break
    
    if not game_id:
        embed = discord.Embed(
            title="❌ Игра не найдена",
            description="У вас нет активных игр в этом канале",
            color=COLORS['error']
        )
        return await ctx.send(embed=embed)
    
    game = blackjack_games.get(game_id)
    
    if not game:
        embed = discord.Embed(
            title="❌ Игра не найдена",
            description=f"Игра с ID `{game_id}` не существует",
            color=COLORS['error']
        )
        return await ctx.send(embed=embed)
    
    if str(ctx.author.id) != game.creator_id:
        embed = discord.Embed(
            title="❌ Недостаточно прав",
            description="Только создатель игры может начать её",
            color=COLORS['error']
        )
        return await ctx.send(embed=embed)
    
    if len(game.players) < 2:
        embed = discord.Embed(
            title="❌ Недостаточно игроков",
            description="Для начала игры нужно минимум 2 игрока",
            color=COLORS['error']
        )
        return await ctx.send(embed=embed)
    
    if not game.start_game():
        embed = discord.Embed(
            title="❌ Ошибка",
            description="Не удалось начать игру",
            color=COLORS['error']
        )
        return await ctx.send(embed=embed)
    
    save_blackjack_games()
    
    try:
        channel = bot.get_channel(int(game.channel_id))
        if channel and game.message_id:
            msg = await channel.fetch_message(game.message_id)
            await msg.edit(view=None)
    except:
        pass
    
    await show_game_turn(ctx.channel, game)

bot.run(TOKEN)
