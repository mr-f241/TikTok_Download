#!/usr/bin/env python3
import os
import sys
import time
import json
import re
import requests
from pathlib import Path
from datetime import datetime
import subprocess
import platform
import socket
import uuid
import getpass
from threading import Thread
import random
import math

# ==================== SIÊU CẤP MÀU SẮC ====================
class Colors:
    RED = '\033[38;5;196m'
    GREEN = '\033[38;5;46m'
    YELLOW = '\033[38;5;226m'
    BLUE = '\033[38;5;51m'
    MAGENTA = '\033[38;5;201m'
    CYAN = '\033[38;5;87m'
    ORANGE = '\033[38;5;208m'
    PINK = '\033[38;5;213m'
    PURPLE = '\033[38;5;93m'
    GOLD = '\033[38;5;220m'
    SILVER = '\033[38;5;248m'
    WHITE = '\033[38;5;255m'
    RAINBOW = [
        '\033[38;5;196m', '\033[38;5;202m', '\033[38;5;208m',
        '\033[38;5;214m', '\033[38;5;220m', '\033[38;5;226m',
        '\033[38;5;190m', '\033[38;5;154m', '\033[38;5;118m',
        '\033[38;5;82m', '\033[38;5;46m', '\033[38;5;47m',
        '\033[38;5;48m', '\033[38;5;49m', '\033[38;5;51m',
        '\033[38;5;87m', '\033[38;5;123m', '\033[38;5;159m',
        '\033[38;5;195m', '\033[38;5;189m', '\033[38;5;183m',
        '\033[38;5;177m', '\033[38;5;171m', '\033[38;5;165m',
        '\033[38;5;201m', '\033[38;5;200m', '\033[38;5;199m',
        '\033[38;5;198m', '\033[38;5;197m'
    ]
    RESET = '\033[0m'
    BOLD = '\033[1m'
    BLINK = '\033[5m'

# Kiểm tra và cài đặt thư viện
def install_package(package):
    try:
        __import__(package)
        return True
    except ImportError:
        print(f"{Colors.CYAN}📦 Đang cài đặt {package}...{Colors.RESET}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except:
            return False

# Cài đặt package
required_packages = ["colorama", "tqdm", "requests", "yt-dlp"]
print(f"{Colors.GOLD}🔄 Đang kiểm tra thư viện...{Colors.RESET}")
for package in required_packages:
    install_package(package)

from colorama import init
from tqdm import tqdm
init(autoreset=True)

# ==================== TIKTOK DOWNLOADER TERMUX ULTIMATE ====================
class TikTokTermuxUltimate:
    def __init__(self):
        self.setup_download_directory()
        self.get_system_info()
        self.running = True
        self.current_time = ""
        self.particles = []
        self.stars = []
        self.init_effects()
        
    def init_effects(self):
        """Khởi tạo hiệu ứng"""
        # Tạo particles
        for _ in range(50):
            self.particles.append({
                'x': random.randint(0, 100),
                'y': random.randint(0, 25),
                'vx': random.uniform(-0.5, 0.5),
                'vy': random.uniform(-0.5, 0.5),
                'char': random.choice('⋅∙●○◦°'),
                'color': random.choice(Colors.RAINBOW)
            })
        
        # Tạo stars
        for _ in range(30):
            self.stars.append({
                'x': random.randint(0, 100),
                'y': random.randint(0, 25),
                'speed': random.uniform(0.1, 0.5),
                'brightness': random.uniform(0.3, 1.0)
            })
        
    def get_system_info(self):
        """Lấy thông tin hệ thống SIÊU CHI TIẾT"""
        try:
            response = requests.get('http://ip-api.com/json/', timeout=10)
            data = response.json()
            self.ip_info = {
                'ip': data.get('query', 'Unknown'),
                'city': data.get('city', 'Unknown'),
                'country': data.get('country', 'Unknown'),
                'isp': data.get('isp', 'Unknown'),
                'timezone': data.get('timezone', 'Unknown')
            }
        except:
            self.ip_info = {'ip': 'Unknown', 'city': 'Unknown', 'country': 'Unknown'}
            
        self.device_info = {
            'hostname': socket.gethostname(),
            'username': getpass.getuser(),
            'platform': platform.system(),
            'processor': platform.processor(),
        }

    def setup_download_directory(self):
        """Thiết lập thư mục download"""
        try:
            self.download_dir = Path("/storage/emulated/0/Download/TIKTOK_TERMUX_PRO")
            self.download_dir.mkdir(parents=True, exist_ok=True)
        except:
            self.download_dir = Path("./TIKTOK_TERMUX_PRO")
            self.download_dir.mkdir(exist_ok=True)

    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')

    def update_time(self):
        """Cập nhật thời gian thực"""
        while self.running:
            self.current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            time.sleep(1)

    def matrix_effect(self, duration=2):
        """Hiệu ứng Matrix cực ngầu"""
        chars = "01█▓▒░"
        width = 120
        start_time = time.time()
        
        while time.time() - start_time < duration:
            line = ''.join([chars[int.from_bytes(os.urandom(1), 'big') % len(chars)] for _ in range(width)])
            print(f"{Colors.GREEN}{line}{Colors.RESET}")
            time.sleep(0.05)
        self.clear_screen()

    def starfield_effect(self, duration=1.5):
        """Hiệu ứng trường sao"""
        start_time = time.time()
        while time.time() - start_time < duration:
            self.clear_screen()
            # Cập nhật stars
            for star in self.stars:
                star['x'] = (star['x'] + star['speed']) % 100
                
            # Vẽ stars
            for y in range(25):
                line = ""
                for x in range(100):
                    star_drawn = False
                    for star in self.stars:
                        if int(star['x']) == x and int(star['y']) == y:
                            brightness = int(star['brightness'] * 5)
                            char = [' ', '.', '*', '●', '★'][min(4, brightness)]
                            line += f"{Colors.WHITE}{char}{Colors.RESET}"
                            star_drawn = True
                            break
                    if not star_drawn:
                        line += " "
                print(line)
            time.sleep(0.1)
        self.clear_screen()

    def particle_effect(self, duration=2):
        """Hiệu ứng particle system"""
        start_time = time.time()
        while time.time() - start_time < duration:
            self.clear_screen()
            # Cập nhật particles
            for p in self.particles:
                p['x'] = (p['x'] + p['vx']) % 100
                p['y'] = (p['y'] + p['vy']) % 25
                
            # Vẽ particles
            for y in range(25):
                line = ""
                for x in range(100):
                    particle_drawn = False
                    for p in self.particles:
                        if int(p['x']) == x and int(p['y']) == y:
                            line += f"{p['color']}{p['char']}{Colors.RESET}"
                            particle_drawn = True
                            break
                    if not particle_drawn:
                        line += " "
                print(line)
            time.sleep(0.1)
        self.clear_screen()

    def fire_effect(self, duration=2):
        """Hiệu ứng lửa cháy"""
        start_time = time.time()
        fire_chars = " .:!=+%#@"
        fire_width = 80
        
        while time.time() - start_time < duration:
            fire_line = ""
            for i in range(fire_width):
                intensity = (math.sin(time.time() * 10 + i * 0.5) + 1) * 0.5
                char_idx = min(len(fire_chars)-1, int(intensity * (len(fire_chars)-1)))
                color_idx = min(len(Colors.RAINBOW)-1, int(intensity * (len(Colors.RAINBOW)-1)))
                fire_line += f"{Colors.RAINBOW[color_idx]}{fire_chars[char_idx]}{Colors.RESET}"
            print(fire_line)
            time.sleep(0.1)
        self.clear_screen()

    def rainbow_wave(self, text, duration=2):
        """Hiệu ứng sóng cầu vồng"""
        start_time = time.time()
        while time.time() - start_time < duration:
            for i, char in enumerate(text):
                color_idx = (int((time.time() * 10 + i) * 2) % len(Colors.RAINBOW))
                print(f"{Colors.RAINBOW[color_idx]}{char}{Colors.RESET}", end='', flush=True)
            print("\r", end='', flush=True)
            time.sleep(0.1)
        print()

    def glitch_text(self, text, iterations=5):
        """Hiệu ứng glitch text"""
        original_text = text
        for _ in range(iterations):
            # Tạo text glitch
            glitched = ''.join([random.choice("!@#$%^&*()_+-=[]{}|;:,.<>?~") if random.random() < 0.3 else char 
                              for char in original_text])
            print(f"{Colors.MAGENTA}{glitched}{Colors.RESET}\r", end='', flush=True)
            time.sleep(0.1)
        print(f"{Colors.CYAN}{original_text}{Colors.RESET}")

    def typewriter_effect(self, text, delay=0.03):
        """Hiệu ứng máy đánh chữ"""
        for i, char in enumerate(text):
            color = Colors.RAINBOW[i % len(Colors.RAINBOW)]
            print(f"{color}{char}{Colors.RESET}", end='', flush=True)
            time.sleep(delay)
            # Thêm tiếng gõ bàn phím
            if char != ' ':
                os.system('echo -n "\\a" > /dev/tty0 2>/dev/null || echo -n ""')
        print()

    def print_banner_ultimate(self):
        """Banner ULTIMATE với nhiều hiệu ứng"""
        self.clear_screen()
        
        # Hiệu ứng sequence
        self.matrix_effect(1)
        self.starfield_effect(1)
        self.particle_effect(1)
        self.fire_effect(1)
        
        banner = f"""
{Colors.RED}╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
{Colors.GREEN}║{Colors.BLINK}{Colors.GOLD}   🎭 TIKTOK DOWNLOADER TERMUX PRO - ULTIMATE EDITION 🎭   {Colors.RESET}{Colors.GREEN}║
{Colors.BLUE}╠══════════════════════════════════════════════════════════════════════════════════════════════════════════════╣
{Colors.MAGENTA}║ {Colors.CYAN}🔥 {Colors.RAINBOW[10]}DOWNLOAD ALL VIDEOS - MAX QUALITY - UNLIMITED POWER - REAL TIME TRACKING {Colors.CYAN}🔥 {Colors.MAGENTA}║
{Colors.YELLOW}║ {Colors.PINK}⚡ {Colors.GOLD}TERMUX OPTIMIZED - LIVE CLOCK - IP TRACKING - ULTIMATE PERFORMANCE {Colors.PINK}⚡ {Colors.YELLOW}║
{Colors.PURPLE}║ {Colors.ORANGE}🎯 {Colors.SILVER}ANH EM CỨ TIN - CODE MỚI FIX HẾT LỖI - SIÊU CẤP VJP PRO - REAL TIME {Colors.ORANGE}🎯 {Colors.PURPLE}║
{Colors.RED}╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝

{Colors.CYAN}╔────────────────────────── {Colors.GOLD}🌍 SYSTEM INFORMATION {Colors.CYAN}─────────────────────────────────────╗
{Colors.BLUE}│ {Colors.GREEN}📍 Vị trí: {Colors.YELLOW}{self.ip_info.get('city', 'Unknown')}, {self.ip_info.get('country', 'Unknown')} {Colors.RED}│ {Colors.CYAN}🌐 IP: {Colors.MAGENTA}{self.ip_info.get('ip', 'Unknown')} 
{Colors.BLUE}│ {Colors.PURPLE}🕐 Thời gian: {Colors.ORANGE}{self.current_time} {Colors.RED}│ {Colors.GOLD}💻 User: {Colors.PINK}{self.device_info['username']}
{Colors.BLUE}│ {Colors.SILVER}📁 Download: {Colors.CYAN}{self.download_dir} {Colors.RED}│ {Colors.BLUE}🤖 Host: {Colors.GREEN}{self.device_info['hostname']}
{Colors.CYAN}╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝

{Colors.RED}🎪 {Colors.YELLOW}TOOL CHUYÊN DỤNG - TẢI ALL VIDEO TỪ BẤT KỲ USER TIKTOK NÀO - REAL TIME CLOCK {Colors.RED}🎪
{Colors.GREEN}💫 {Colors.BLUE}AUTHOR: {Colors.MAGENTA}TRẦN VĂN THÀNH {Colors.GREEN}💫 {Colors.GOLD}📞 ZALO: {Colors.RED}0946855980 {Colors.GOLD}📞
{Colors.CYAN}🚀 {Colors.PINK}READY TO DOWNLOAD... {Colors.BLINK}{Colors.GREEN}LIVE CLOCK ACTIVATED {Colors.CYAN}🚀

"""
        print(banner)

    def animate_text(self, text, color=Colors.GREEN, delay=0.01, effect="rainbow"):
        """Hiệu ứng chữ đa dạng"""
        if effect == "rainbow":
            self.rainbow_wave(text, 1)
        elif effect == "glitch":
            self.glitch_text(text)
        elif effect == "typewriter":
            self.typewriter_effect(text, delay)
        else:
            for char in text:
                print(f"{color}{char}{Colors.RESET}", end='', flush=True)
                time.sleep(delay)
            print()

    def loading_animation_ultimate(self, text, duration=2):
        """Loading animation ULTIMATE"""
        symbols = ['🕐', '🕑', '🕒', '🕓', '🕔', '🕕', '🕖', '🕗', '🕘', '🕙', '🕚', '🕛']
        start_time = time.time()
        i = 0
        
        while time.time() - start_time < duration:
            color = Colors.RAINBOW[i % len(Colors.RAINBOW)]
            symbol = symbols[i % len(symbols)]
            # Tạo progress bar động
            progress = int((time.time() - start_time) / duration * 20)
            bar = "█" * progress + "░" * (20 - progress)
            print(f"\r{color}{symbol} {text} [{bar}] {i%4*'.'}{' '*(3-i%4)} {Colors.RESET}", end='', flush=True)
            time.sleep(0.1)
            i += 1
        
        print(f"\r{Colors.GREEN}✅ {text} {Colors.GOLD}COMPLETED!{' ' * 50}{Colors.RESET}")

    def quantum_loading(self, text, duration=3):
        """Hiệu ứng loading lượng tử"""
        start_time = time.time()
        dots = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        
        while time.time() - start_time < duration:
            for i, dot in enumerate(dots):
                progress = int((time.time() - start_time) / duration * 100)
                # Tạo hiệu ứng lượng tử
                quantum_chars = "∙⋅●○◌◍◎◦"
                quantum_bar = ""
                for j in range(20):
                    if j < progress // 5:
                        char_idx = int((time.time() * 10 + j) % len(quantum_chars))
                        quantum_bar += f"{Colors.RAINBOW[(i+j) % len(Colors.RAINBOW)]}{quantum_chars[char_idx]}{Colors.RESET}"
                    else:
                        quantum_bar += " "
                
                print(f"\r{Colors.CYAN}{dot} {text} [{quantum_bar}] {progress}% {Colors.RESET}", end='', flush=True)
                time.sleep(0.08)
        
        print(f"\r{Colors.GREEN}🎉 {text} QUANTUM COMPLETE!{' ' * 60}{Colors.RESET}")

    def get_user_info_ultimate(self, username):
        """Lấy thông tin user SIÊU CHI TIẾT"""
        try:
            clean_username = username.replace('@', '').strip()
            
            # Sử dụng multiple APIs để lấy thông tin chính xác
            apis = [
                f"https://www.tikwm.com/api/user/info?unique_id=@{clean_username}",
                f"https://api.tiktokuserinfo.com/user/info?username={clean_username}",
            ]
            
            for api_url in apis:
                try:
                    response = requests.get(api_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        user_data = data.get('data', {}).get('user') or data.get('user') or data.get('data') or {}
                        
                        if user_data:
                            return {
                                'nickname': user_data.get('nickname', clean_username),
                                'unique_id': user_data.get('unique_id', clean_username),
                                'signature': user_data.get('signature', 'No bio'),
                                'follower_count': user_data.get('follower_count', user_data.get('fans', 0)),
                                'following_count': user_data.get('following_count', user_data.get('follow', 0)),
                                'heart_count': user_data.get('heart_count', user_data.get('heart', 0)),
                                'video_count': user_data.get('video_count', user_data.get('video', 0)),
                                'verified': user_data.get('verified', False),
                                'private': user_data.get('private', False),
                                'avatar': user_data.get('avatar', '')
                            }
                except:
                    continue
            
            return None
        except Exception as e:
            return None

    def get_user_videos_ultimate(self, username):
        """Lấy danh sách video ULTIMATE - KHÔNG TRÙNG LẶP"""
        try:
            self.animate_text(f"🔍 SCANNING USER: @{username}", Colors.MAGENTA, effect="rainbow")
            
            clean_username = username.replace('@', '').strip()
            all_video_urls = []
            seen_ids = set()
            
            # PHƯƠNG PHÁP 1: yt-dlp QUÉT SÂU
            try:
                self.quantum_loading("METHOD 1: DEEP QUANTUM SCAN WITH YT-DLP", 2)
                import yt_dlp
                
                ydl_opts = {'quiet': True, 'extract_flat': True, 'playlistend': 500}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"https://www.tiktok.com/@{clean_username}", download=False)
                    if 'entries' in info:
                        for entry in info['entries']:
                            if entry.get('url'):
                                video_id = self.extract_video_id(entry['url'])
                                if video_id and video_id not in seen_ids:
                                    seen_ids.add(video_id)
                                    all_video_urls.append(entry['url'])
                
                self.animate_text(f"✅ YT-DLP FOUND: {len([x for x in all_video_urls])} VIDEOS", Colors.GREEN)
            except Exception as e:
                self.animate_text(f"❌ YT-DLP ERROR", Colors.RED)

            # PHƯƠNG PHÁP 2: TIKWM API PHÂN TRANG
            try:
                self.quantum_loading("METHOD 2: QUANTUM API PAGINATION", 2)
                
                for page in range(1, 11):  # Quét 10 trang
                    cursor = (page - 1) * 30
                    api_url = f"https://www.tikwm.com/api/user/posts?unique_id=@{clean_username}&count=30&cursor={cursor}"
                    
                    response = requests.get(api_url, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('data', {}).get('videos'):
                            new_videos = 0
                            for video in data['data']['videos']:
                                video_id = video.get('video_id', '')
                                if video_id and video_id not in seen_ids:
                                    seen_ids.add(video_id)
                                    video_url = f"https://www.tiktok.com/@{clean_username}/video/{video_id}"
                                    all_video_urls.append(video_url)
                                    new_videos += 1
                            
                            # Hiển thị real-time progress
                            print(f"{Colors.BLUE}📄 PAGE {page}: {Colors.GREEN}+{new_videos} NEW VIDEOS {Colors.RED}| {Colors.YELLOW}TOTAL: {len(all_video_urls)} {Colors.RED}| {Colors.CYAN}TIME: {self.current_time}")
                            if new_videos == 0:
                                break
                    time.sleep(0.3)
                
                self.animate_text(f"✅ TIKWM ADDED: {len([x for x in all_video_urls if 'tiktok.com' in x])} VIDEOS", Colors.CYAN)
            except Exception as e:
                self.animate_text(f"❌ TIKWM ERROR", Colors.RED)

            return all_video_urls
                
        except Exception as e:
            self.animate_text(f"💥 SCANNING ERROR: {str(e)}", Colors.RED)
            return []

    def extract_video_id(self, url):
        try:
            patterns = [r'/video/(\d+)', r'tiktok\.com.*?(\d{19})', r'@[\w\.-]+/video/(\d+)']
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            return None
        except:
            return None

    def display_user_info_ultimate(self, user_info):
        """Hiển thị thông tin user ULTIMATE"""
        print(f"\n{Colors.PURPLE}╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════╗")
        print(f"{Colors.CYAN}║{Colors.BLINK}{Colors.GOLD}                          🎪 USER INFORMATION - REAL TIME: {self.current_time} 🎪                         {Colors.RESET}{Colors.CYAN}║")
        print(f"{Colors.PURPLE}╠══════════════════════════════════════════════════════════════════════════════════════════════════════════════╣")
        print(f"{Colors.CYAN}║ {Colors.GREEN}📛 Name: {Colors.YELLOW}{user_info.get('nickname', 'N/A')} {Colors.RED}| {Colors.BLUE}🆔 Username: {Colors.MAGENTA}@{user_info.get('unique_id', 'N/A')}")
        
        verified_status = f"{Colors.GREEN}YES {Colors.GOLD}⭐" if user_info.get('verified') else f"{Colors.RED}NO"
        private_status = f"{Colors.RED}PRIVATE 🔒" if user_info.get('private') else f"{Colors.GREEN}PUBLIC 🔓"
        
        print(f"{Colors.CYAN}║ {Colors.GOLD}✅ Verified: {verified_status} {Colors.RED}| {Colors.PINK}🔒 Account: {private_status}")
        
        print(f"{Colors.CYAN}║ {Colors.ORANGE}👥 Followers: {Colors.GREEN}{user_info.get('follower_count', 0):,} {Colors.RED}| {Colors.CYAN}❤️  Total Likes: {Colors.MAGENTA}{user_info.get('heart_count', 0):,}")
        print(f"{Colors.CYAN}║ {Colors.PURPLE}📹 Total Videos: {Colors.BLUE}{user_info.get('video_count', 0):,} {Colors.RED}| {Colors.GOLD}🕐 Scan Time: {Colors.SILVER}{self.current_time}")
        
        signature = user_info.get('signature', 'No bio')
        if len(signature) > 80:
            signature = signature[:80] + "..."
        print(f"{Colors.CYAN}║ {Colors.GOLD}📝 Bio: {Colors.SILVER}{signature}")
        print(f"{Colors.PURPLE}╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝")

    def download_video_ultimate(self, video_url, filename):
        """Tải video ULTIMATE"""
        try:
            import yt_dlp
            
            ydl_opts = {
                'outtmpl': str(filename),
                'format': 'best',
                'quiet': True,
                'retries': 3,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            return os.path.exists(filename) and os.path.getsize(filename) > 1024
                
        except:
            return False

    def download_all_ultimate(self, username):
        """Tải tất cả video ULTIMATE"""
        try:
            # Start time thread
            time_thread = Thread(target=self.update_time)
            time_thread.daemon = True
            time_thread.start()
            
            time.sleep(1)  # Chờ time thread khởi động
            
            self.print_banner_ultimate()
            self.animate_text(f"🎬 STARTING ULTIMATE DOWNLOAD: @{username}", Colors.RED, effect="rainbow")
            
            clean_username = username.replace('@', '').strip()
            user_dir = self.download_dir / f"ULTIMATE_{clean_username.upper()}"
            user_dir.mkdir(exist_ok=True)
            
            # Lấy thông tin user
            user_info = self.get_user_info_ultimate(clean_username)
            if user_info:
                self.display_user_info_ultimate(user_info)
            else:
                self.animate_text("⚠️ COULD NOT GET USER INFO, CONTINUING...", Colors.YELLOW)
                user_info = {'nickname': clean_username, 'unique_id': clean_username}

            # Lấy danh sách video
            video_urls = self.get_user_videos_ultimate(clean_username)
            
            if not video_urls:
                self.animate_text("💔 NO VIDEOS FOUND!", Colors.RED)
                input(f"\n{Colors.YELLOW}🎪 PRESS ENTER TO CONTINUE...")
                return

            # Chọn số lượng
            print(f"\n{Colors.GREEN}🎯 FOUND {Colors.RED}{len(video_urls)} {Colors.GREEN}VIDEOS {Colors.RED}| {Colors.YELLOW}TIME: {self.current_time}")
            
            try:
                count_input = input(
                    f"{Colors.YELLOW}🎪 ENTER NUMBER TO DOWNLOAD (1-{len(video_urls)}, 'all' FOR ALL): "
                ).strip().lower()
                
                if count_input == 'all':
                    videos_to_download = video_urls
                else:
                    try:
                        count = int(count_input)
                        count = max(1, min(count, len(video_urls)))
                        videos_to_download = video_urls[:count]
                    except:
                        videos_to_download = video_urls[:20]
                        self.animate_text("⚠️ INVALID INPUT, DOWNLOADING 20 VIDEOS", Colors.YELLOW)
            except:
                videos_to_download = video_urls[:20]

            # Xác nhận
            print(f"\n{Colors.RED}🎯 PREPARING TO DOWNLOAD {Colors.GREEN}{len(videos_to_download)} {Colors.RED}VIDEOS")
            print(f"{Colors.YELLOW}📁 FOLDER: {Colors.CYAN}{user_dir}")
            print(f"{Colors.MAGENTA}🕐 START TIME: {Colors.GREEN}{self.current_time}")
            
            confirm = input(f"{Colors.MAGENTA}🎪 TYPE 'ULTIMATE' TO START DOWNLOAD: ")
            if confirm.lower() != 'ultimate':
                self.animate_text("🚫 DOWNLOAD CANCELLED!", Colors.RED)
                input(f"\n{Colors.YELLOW}🎪 PRESS ENTER TO CONTINUE...")
                return

            # BẮT ĐẦU TẢI
            success_count = 0
            failed_count = 0
            
            self.animate_text(f"🚀 LAUNCHING ULTIMATE DOWNLOAD...", Colors.GREEN, effect="rainbow")
            
            for i, video_url in enumerate(videos_to_download, 1):
                print(f"\n{Colors.CYAN}🎬 DOWNLOADING VIDEO {i}/{len(videos_to_download)} {Colors.RED}| {Colors.YELLOW}TIME: {self.current_time}")
                print(f"{Colors.BLUE}🔗 URL: {video_url}")
                
                filename = user_dir / f"video_{i:04d}.mp4"
                
                # Quantum progress bar
                self.quantum_loading(f"DOWNLOADING VIDEO {i}", 2)
                
                if self.download_video_ultimate(video_url, filename):
                    success_count += 1
                    self.animate_text(f"✅ SUCCESS: VIDEO {i} | TIME: {self.current_time}", Colors.GREEN)
                else:
                    failed_count += 1
                    self.animate_text(f"❌ FAILED: VIDEO {i} | TIME: {self.current_time}", Colors.RED)
                
                # Delay với đồng hồ đếm ngược
                if i < len(videos_to_download):
                    for sec in range(2, 0, -1):
                        print(f"\r{Colors.YELLOW}⏳ WAIT {sec}s... | TIME: {self.current_time}", end='', flush=True)
                        time.sleep(1)
                    print("\r" + " " * 50, end='\r')

            # KẾT QUẢ CUỐI CÙNG VỚI HIỆU ỨNG
            self.fire_effect(1)
            self.starfield_effect(1)
            
            print(f"\n{Colors.PURPLE}╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════╗")
            print(f"{Colors.CYAN}║{Colors.BLINK}{Colors.GOLD}                       🎊 DOWNLOAD COMPLETED! - {self.current_time} 🎊                      {Colors.RESET}{Colors.CYAN}║")
            print(f"{Colors.PURPLE}╠══════════════════════════════════════════════════════════════════════════════════════════════════════════════╣")
            print(f"{Colors.CYAN}║ {Colors.GREEN}✅ SUCCESS: {Colors.WHITE}{success_count} VIDEOS {Colors.RED}| {Colors.RED}❌ FAILED: {Colors.WHITE}{failed_count} VIDEOS")
            print(f"{Colors.CYAN}║ {Colors.BLUE}📁 FOLDER: {Colors.YELLOW}{user_dir}")
            print(f"{Colors.CYAN}║ {Colors.MAGENTA}🕐 STARTED: {Colors.CYAN}{self.current_time} {Colors.RED}| {Colors.GOLD}🕐 COMPLETED: {Colors.GREEN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{Colors.CYAN}║ {Colors.PINK}🎯 AUTHOR: {Colors.SILVER}TRẦN VĂN THÀNH {Colors.RED}| {Colors.CYAN}📞 ZALO: {Colors.MAGENTA}0946855980")
            print(f"{Colors.PURPLE}╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝")
            
            if success_count > 0:
                self.animate_text(f"🎉 DOWNLOADED {success_count} VIDEOS SUCCESSFULLY! | TIME: {self.current_time}", Colors.GREEN, effect="rainbow")
                # Hiệu ứng celebration
                for _ in range(3):
                    self.particle_effect(0.5)
            else:
                self.animate_text("😞 NO VIDEOS DOWNLOADED!", Colors.RED)
            
        except Exception as e:
            self.animate_text(f"💥 DOWNLOAD ERROR: {str(e)}", Colors.RED)
        
        input(f"\n{Colors.YELLOW}🎪 PRESS ENTER TO RETURN...")

    def show_ultimate_menu(self):
        """Menu ULTIMATE với thời gian thực"""
        # Start time thread
        time_thread = Thread(target=self.update_time)
        time_thread.daemon = True
        time_thread.start()
        
        time.sleep(1)
        
        while self.running:
            self.print_banner_ultimate()
            
            try:
                username = input(f"{Colors.CYAN}🎪 ENTER TIKTOK USERNAME {Colors.RED}(@username){Colors.YELLOW}: {Colors.GREEN}")
                
                if username.strip():
                    if not username.startswith('@'):
                        username = '@' + username
                    
                    self.download_all_ultimate(username.strip())
                else:
                    self.animate_text("🎪 PLEASE ENTER USERNAME!", Colors.RED)
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                self.exit_ultimate()
            except Exception as e:
                self.animate_text(f"🎪 MENU ERROR: {str(e)}", Colors.RED)
                time.sleep(2)

    def exit_ultimate(self):
        """Thoát ULTIMATE"""
        self.running = False
        self.clear_screen()
        
        # Hiệu ứng goodbye
        self.matrix_effect(1)
        self.starfield_effect(1)
        
        farewell = f"""
{Colors.RED}╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
{Colors.GREEN}║{Colors.BLINK}{Colors.GOLD}                    🎭 THANK YOU FOR USING TERMUX ULTIMATE! 🎭                   {Colors.RESET}{Colors.GREEN}║
{Colors.RED}╠══════════════════════════════════════════════════════════════════════════════════════════════════════════════╣
{Colors.GREEN}║ {Colors.CYAN}🎯 TIKTOK DOWNLOADER TERMUX PRO - ULTIMATE EDITION                      {Colors.GREEN}║
{Colors.GREEN}║ {Colors.BLUE}💾 DOWNLOAD FOLDER: {Colors.YELLOW}{self.download_dir}         {Colors.GREEN}║
{Colors.GREEN}║ {Colors.MAGENTA}📞 CONTACT ZALO: {Colors.RED}0946855980 {Colors.MAGENTA}                                  {Colors.GREEN}║
{Colors.GREEN}║ {Colors.PURPLE}🌍 YOUR LOCATION: {Colors.ORANGE}{self.ip_info.get('city')}, {self.ip_info.get('country')}          {Colors.GREEN}║
{Colors.GREEN}║ {Colors.GOLD}🕐 EXIT TIME: {Colors.SILVER}{self.current_time}            {Colors.GREEN}║
{Colors.GREEN}║ {Colors.PINK}🎯 AUTHOR: {Colors.SILVER}TRẦN VĂN THÀNH - TERMUX DEVELOPER               {Colors.GREEN}║
{Colors.GREEN}║ {Colors.CYAN}🤡 SEE YOU SPACE COWBOY... QUANTUM EFFECTS ACTIVATED 🤡                 {Colors.GREEN}║
{Colors.RED}╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝
"""
        print(farewell)
        time.sleep(3)
        self.clear_screen()

def main():
    """Hàm chính"""
    try:
        print(f"{Colors.GOLD}🚀 INITIALIZING TIKTOK TERMUX ULTIMATE...{Colors.RESET}")
        time.sleep(2)
        
        downloader = TikTokTermuxUltimate()
        downloader.show_ultimate_menu()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}🎪 PROGRAM STOPPED!{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}💥 INIT ERROR: {str(e)}{Colors.RESET}")

if __name__ == "__main__":
    main()
