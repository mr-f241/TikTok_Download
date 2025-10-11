#!/usr/bin/env python3
import os
import sys
import time
from pathlib import Path
import subprocess
import json
from datetime import datetime

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
    RESET = '\033[0m'

class VideoErrorDetector:
    def __init__(self):
        self.setup_directories()
        self.results = []
        
    def setup_directories(self):
        """Thiết lập thư mục làm việc"""
        try:
            self.work_dir = Path("/storage/emulated/0/Download/VIDEO_ERROR_SCANNER")
            self.work_dir.mkdir(parents=True, exist_ok=True)
        except:
            self.work_dir = Path("./VIDEO_ERROR_SCANNER")
            self.work_dir.mkdir(exist_ok=True)
            
    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def print_banner(self):
        """Hiển thị banner"""
        banner = f"""
{Colors.CYAN}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║              🎬 AUTO BLACK SCREEN DELETE                    ║
║               - XOÁ VIDEO NỀN ĐEN TỰ ĐỘNG -                ║
║                                                              ║
║  🔍 Phát hiện video chỉ có nền đen + nhạc                   ║
║  🗑️  TỰ ĐỘNG XOÁ hoặc di chuyển file lỗi                   ║
║  ⚡ Xoá nhanh không hỏi - Xoá có hỏi                        ║
║  📊 Backup file trước khi xoá (tuỳ chọn)                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
{Colors.RESET}
"""
        print(banner)

    def get_video_detailed_info(self, file_path):
        """Lấy thông tin chi tiết video để phát hiện nền đen"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(file_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data
            return None
        except:
            return None
    
    def analyze_video_stream(self, video_stream):
        """Phân tích stream video để phát hiện nền đen"""
        analysis = {
            'is_black_screen': False,
            'is_low_quality': False,
            'is_slideshow': False,
            'issues': []
        }
        
        # Lấy thông tin video stream
        bit_rate = video_stream.get('bit_rate')
        width = video_stream.get('width', 0)
        height = video_stream.get('height', 0)
        avg_frame_rate = video_stream.get('avg_frame_rate', '0/1')
        codec_name = video_stream.get('codec_name', '')
        
        # Tính frame rate
        try:
            if '/' in avg_frame_rate:
                num, den = avg_frame_rate.split('/')
                frame_rate = int(num) / int(den) if int(den) > 0 else 0
            else:
                frame_rate = float(avg_frame_rate)
        except:
            frame_rate = 0
        
        # Kiểm tra bitrate video cực thấp (dấu hiệu nền đen)
        if bit_rate:
            try:
                video_bitrate = int(bit_rate)
                # Video bình thường thường có bitrate > 200kbps
                if video_bitrate < 100000:  # Dưới 100kbps
                    analysis['is_low_quality'] = True
                    analysis['issues'].append(f"BITRATE_THẤP({video_bitrate//1000}kbps)")
                    
                if video_bitrate < 50000:  # Dưới 50kbps - rất có thể là nền đen
                    analysis['is_black_screen'] = True
                    analysis['issues'].append("NỀN_ĐEN")
            except:
                pass
        
        # Kiểm tra frame rate thấp (video ảnh slideshow)
        if frame_rate < 10:  # Dưới 10fps
            analysis['is_slideshow'] = True
            analysis['issues'].append(f"SLIDESHOW({frame_rate:.1f}fps)")
        
        # Kiểm tra resolution thấp
        if width < 320 or height < 240:
            analysis['is_low_quality'] = True
            analysis['issues'].append(f"ĐỘ_PHÂN_GIẢI_THẤP({width}x{height})")
        
        return analysis
    
    def check_video_quality(self, file_path):
        """Kiểm tra chất lượng video chi tiết"""
        file_info = {
            'path': file_path,
            'name': file_path.name,
            'size': file_path.stat().st_size,
            'status': 'TỐT',
            'issues': [],
            'duration': 0,
            'has_video': False,
            'has_audio': False,
            'video_quality': 'UNKNOWN',
            'video_bitrate': 0,
            'audio_bitrate': 0,
            'resolution': 'Unknown',
            'frame_rate': 0,
            'is_black_screen_risk': False,
            'is_slideshow': False,
            'should_delete': False  # Flag để xoá
        }
        
        # Kiểm tra kích thước file
        if file_info['size'] < 1024 * 100:  # Dưới 100KB
            file_info['issues'].append("FILE_RẤT_NHỎ")
            file_info['status'] = 'NÊN_XOÁ'
            file_info['should_delete'] = True
            
        # Phân tích với ffprobe
        video_info = self.get_video_detailed_info(file_path)
        
        if not video_info:
            file_info['issues'].append("KHÔNG_ĐỌC_ĐƯỢC_METADATA")
            file_info['status'] = 'NÊN_XOÁ'
            file_info['should_delete'] = True
            return file_info
            
        # Lấy duration
        file_info['duration'] = float(video_info['format'].get('duration', 0))
        
        # Phân tích streams
        video_streams = [s for s in video_info.get('streams', []) if s.get('codec_type') == 'video']
        audio_streams = [s for s in video_info.get('streams', []) if s.get('codec_type') == 'audio']
        
        file_info['has_video'] = len(video_streams) > 0
        file_info['has_audio'] = len(audio_streams) > 0
        
        # Phân tích video stream
        if file_info['has_video']:
            video_stream = video_streams[0]
            video_analysis = self.analyze_video_stream(video_stream)
            
            # Cập nhật thông tin video
            file_info['video_bitrate'] = int(video_stream.get('bit_rate', 0))
            file_info['resolution'] = f"{video_stream.get('width', 0)}x{video_stream.get('height', 0)}"
            
            # Tính frame rate
            avg_frame_rate = video_stream.get('avg_frame_rate', '0/1')
            try:
                if '/' in avg_frame_rate:
                    num, den = avg_frame_rate.split('/')
                    file_info['frame_rate'] = int(num) / int(den) if int(den) > 0 else 0
            except:
                file_info['frame_rate'] = 0
            
            # Áp dụng kết quả phân tích
            file_info['is_black_screen_risk'] = video_analysis['is_black_screen']
            file_info['is_slideshow'] = video_analysis['is_slideshow']
            file_info['issues'].extend(video_analysis['issues'])
            
            # QUYẾT ĐỊNH CÓ NÊN XOÁ KHÔNG
            if video_analysis['is_black_screen']:
                file_info['video_quality'] = 'NỀN_ĐEN'
                file_info['status'] = 'NÊN_XOÁ'
                file_info['should_delete'] = True
            elif video_analysis['is_slideshow']:
                file_info['video_quality'] = 'VIDEO_ẢNH'
                file_info['status'] = 'NÊN_XOÁ'
                file_info['should_delete'] = True
            elif video_analysis['is_low_quality']:
                file_info['video_quality'] = 'CHẤT_LƯỢNG_THẤP'
                if file_info['video_bitrate'] < 80000:  # Dưới 80kbps
                    file_info['status'] = 'NÊN_XOÁ'
                    file_info['should_delete'] = True
                else:
                    file_info['status'] = 'CẢNH_BÁO'
            else:
                file_info['video_quality'] = 'TỐT'
        
        # Video chỉ có audio không có video -> XOÁ
        if file_info['has_audio'] and not file_info['has_video']:
            file_info['issues'].append("CHỈ_CÓ_AUDIO")
            file_info['status'] = 'NÊN_XOÁ'
            file_info['should_delete'] = True
        
        return file_info

    def auto_delete_black_screens(self, results, confirm=True, backup=False):
        """Tự động xoá video nền đen"""
        videos_to_delete = [r for r in results if r['should_delete']]
        
        if not videos_to_delete:
            print(f"{Colors.GREEN}✅ Không có video nào cần xoá!")
            return 0
            
        print(f"\n{Colors.RED}🚨 PHÁT HIỆN {len(videos_to_delete)} VIDEO NÊN XOÁ:")
        for video in videos_to_delete:
            print(f"  {Colors.RED}🗑️  {video['name']} - {video['video_quality']} - {video['issues'][0] if video['issues'] else ''}")
        
        if confirm:
            choice = input(f"\n{Colors.YELLOW}🎪 Bạn có chắc muốn xoá {len(videos_to_delete)} video? (y/N): {Colors.RESET}").strip().lower()
            if choice != 'y':
                print(f"{Colors.GREEN}✅ Đã huỷ xoá video!")
                return 0
        
        # Tạo backup nếu cần
        if backup:
            backup_dir = self.work_dir / "BACKUP_BLACK_SCREENS"
            backup_dir.mkdir(exist_ok=True)
            print(f"{Colors.BLUE}📦 Đang backup video vào: {backup_dir}")
        
        # XOÁ VIDEO
        deleted_count = 0
        print(f"\n{Colors.RED}🔥 BẮT ĐẦU XOÁ VIDEO NỀN ĐEN...")
        
        for video in videos_to_delete:
            try:
                # Backup nếu được chọn
                if backup:
                    backup_path = backup_dir / video['name']
                    import shutil
                    shutil.copy2(video['path'], backup_path)
                    print(f"{Colors.BLUE}📦 Đã backup: {video['name']}")
                
                # XOÁ FILE
                video['path'].unlink()
                deleted_count += 1
                print(f"{Colors.RED}🗑️  ĐÃ XOÁ: {video['name']}")
                
            except Exception as e:
                print(f"{Colors.RED}❌ Lỗi xoá {video['name']}: {e}")
        
        print(f"\n{Colors.GREEN}✅ ĐÃ XOÁ THÀNH CÔNG {deleted_count}/{len(videos_to_delete)} VIDEO!")
        return deleted_count

    def format_size(self, size_bytes):
        """Định dạng kích thước file"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
        
    def format_duration(self, seconds):
        """Định dạng thời lượng"""
        if seconds == 0:
            return "0s"
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            return f"{hours}h{minutes:02d}m{seconds:02d}s"
        elif minutes > 0:
            return f"{minutes}m{seconds:02d}s"
        else:
            return f"{seconds}s"
            
    def display_results_table(self, results):
        """Hiển thị kết quả dạng bảng cột"""
        print(f"\n{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗")
        print(f"║{Colors.YELLOW}🎬 AUTO BLACK SCREEN DELETE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.CYAN} 🎬{' ' * 40}║")
        print(f"╠══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╣")
        
        # Header
        header = (f"{Colors.CYAN}║ {Colors.GREEN}STT  {Colors.MAGENTA}| {Colors.GREEN}TÊN FILE{' ' * 20} {Colors.MAGENTA}| {Colors.GREEN}TRẠNG THÁI {Colors.MAGENTA}| "
                  f"{Colors.GREEN}CHẤT LƯỢNG{' ' * 8} {Colors.MAGENTA}| {Colors.GREEN}VIDEO BITRATE {Colors.MAGENTA}| {Colors.GREEN}RESOLUTION {Colors.MAGENTA}| {Colors.GREEN}HÀNH ĐỘNG")
        print(header)
        print(f"{Colors.CYAN}╠══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╣")
        
        # Data rows
        for i, result in enumerate(results, 1):
            filename = result['name'][:25] + "..." if len(result['name']) > 25 else result['name']
            
            # Màu sắc theo trạng thái
            if result['status'] == 'NÊN_XOÁ':
                status_color = Colors.RED
                status_text = "NÊN_XOÁ "
                action_text = "🗑️ XOÁ"
            elif result['status'] == 'CẢNH_BÁO':
                status_color = Colors.YELLOW
                status_text = "CẢNH_BÁO"
                action_text = "⚠️ CẢNH_BÁO"
            else:
                status_color = Colors.GREEN
                status_text = "TỐT     "
                action_text = "✅ GIỮ LẠI"
            
            # Màu chất lượng video
            if 'NỀN_ĐEN' in result['video_quality']:
                quality_color = Colors.RED
            elif 'VIDEO_ẢNH' in result['video_quality']:
                quality_color = Colors.ORANGE
            elif 'THẤP' in result['video_quality']:
                quality_color = Colors.YELLOW
            else:
                quality_color = Colors.GREEN
                
            # Hiển thị video bitrate
            video_bitrate = f"{result['video_bitrate']//1000}k" if result['video_bitrate'] > 0 else "N/A"
            
            row = (f"{Colors.CYAN}║ {Colors.WHITE}{i:<4} {Colors.MAGENTA}| {Colors.BLUE}{filename:<25} {Colors.MAGENTA}| "
                   f"{status_color}{status_text} {Colors.MAGENTA}| "
                   f"{quality_color}{result['video_quality']:<15} {Colors.MAGENTA}| "
                   f"{Colors.CYAN}{video_bitrate:<12} {Colors.MAGENTA}| "
                   f"{Colors.WHITE}{result['resolution']:<10} {Colors.MAGENTA}| "
                   f"{status_color}{action_text}")
            print(row)
            
        print(f"{Colors.CYAN}╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝")
        
        # Thống kê chi tiết
        total_files = len(results)
        good_files = len([r for r in results if r['status'] == 'TỐT'])
        warning_files = len([r for r in results if r['status'] == 'CẢNH_BÁO'])
        delete_files = len([r for r in results if r['status'] == 'NÊN_XOÁ'])
        
        print(f"\n{Colors.GREEN}📊 THỐNG KÊ XOÁ VIDEO:")
        print(f"  {Colors.CYAN}• Tổng số file: {Colors.WHITE}{total_files}")
        print(f"  {Colors.GREEN}• File tốt (giữ lại): {Colors.WHITE}{good_files}")
        print(f"  {Colors.YELLOW}• File cảnh báo: {Colors.WHITE}{warning_files}")
        print(f"  {Colors.RED}• File nên xoá: {Colors.WHITE}{delete_files}")
        
        return delete_files
        
    def scan_directory(self, directory_path):
        """Quét thư mục tìm video"""
        video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
        video_files = []
        
        directory = Path(directory_path)
        if not directory.exists():
            print(f"{Colors.RED}❌ Thư mục không tồn tại: {directory_path}")
            return []
            
        print(f"{Colors.BLUE}🔍 Đang quét thư mục: {directory}")
        
        for ext in video_extensions:
            video_files.extend(directory.glob(f"**/*{ext}"))
            
        print(f"{Colors.GREEN}📁 Tìm thấy {len(video_files)} file video")
        return video_files
        
    def show_main_menu(self):
        """Hiển thị menu chính"""
        while True:
            self.clear_screen()
            self.print_banner()
            
            print(f"{Colors.CYAN}1. {Colors.GREEN}Quét & Xem video nền đen")
            print(f"{Colors.CYAN}2. {Colors.RED}Quét & XOÁ LUÔN (có hỏi)")
            print(f"{Colors.CYAN}3. {Colors.RED}Quét & XOÁ LUÔN (không hỏi)")
            print(f"{Colors.CYAN}4. {Colors.BLUE}Quét & Xoá có Backup")
            print(f"{Colors.CYAN}5. {Colors.YELLOW}Thoát")
            
            choice = input(f"\n{Colors.MAGENTA}🎪 Chọn chế độ xoá (1-5): {Colors.RESET}").strip()
            
            if choice == '1':
                self.scan_and_show()
            elif choice == '2':
                self.scan_and_delete(confirm=True, backup=False)
            elif choice == '3':
                self.scan_and_delete(confirm=False, backup=False)
            elif choice == '4':
                self.scan_and_delete(confirm=True, backup=True)
            elif choice == '5':
                print(f"{Colors.GREEN}👋 Tạm biệt!")
                break
            else:
                print(f"{Colors.RED}❌ Lựa chọn không hợp lệ!")
                time.sleep(1)
                
    def scan_and_show(self):
        """Chỉ quét và hiển thị, không xoá"""
        video_files = self.scan_target_directory()
        if not video_files:
            return
            
        self.results = self.process_videos(video_files)
        delete_count = self.display_results_table(self.results)
        
        if delete_count > 0:
            choice = input(f"\n{Colors.YELLOW}🎪 Bạn có muốn xoá {delete_count} video nền đen ngay bây giờ? (y/N): {Colors.RESET}").strip().lower()
            if choice == 'y':
                self.auto_delete_black_screens(self.results, confirm=True, backup=False)
        
        input(f"\n{Colors.YELLOW}🎪 Nhấn Enter để tiếp tục...")
    
    def scan_and_delete(self, confirm=True, backup=False):
        """Quét và xoá theo chế độ"""
        video_files = self.scan_target_directory()
        if not video_files:
            return
            
        self.results = self.process_videos(video_files)
        self.display_results_table(self.results)
        
        deleted_count = self.auto_delete_black_screens(self.results, confirm=confirm, backup=backup)
        
        if deleted_count > 0:
            print(f"\n{Colors.GREEN}🎉 ĐÃ HOÀN THÀNH! {deleted_count} video nền đen đã được xoá!")
        else:
            print(f"\n{Colors.BLUE}ℹ️  Không có video nào bị xoá!")
            
        input(f"\n{Colors.YELLOW}🎪 Nhấn Enter để tiếp tục...")
        
    def scan_target_directory(self):
        """Quét thư mục đích"""
        print(f"\n{Colors.CYAN}📁 Chọn thư mục cần quét:")
        print(f"{Colors.YELLOW}1. Thư mục TikTok mặc định")
        print(f"{Colors.YELLOW}2. Thư mục tuỳ chỉnh")
        
        choice = input(f"{Colors.MAGENTA}🎪 Chọn (1/2): {Colors.RESET}").strip()
        
        if choice == '1':
            return self.scan_tiktok_directory()
        else:
            return self.scan_custom_directory()
        
    def scan_custom_directory(self):
        """Quét thư mục tùy chỉnh"""
        print(f"\n{Colors.CYAN}📁 Nhập đường dẫn thư mục cần quét:")
        directory = input(f"{Colors.YELLOW}🎪 Path: {Colors.RESET}").strip()
        
        if not directory:
            print(f"{Colors.RED}❌ Chưa nhập đường dẫn!")
            time.sleep(1)
            return []
            
        video_files = self.scan_directory(directory)
        if not video_files:
            print(f"{Colors.YELLOW}⚠️ Không tìm thấy file video nào!")
            time.sleep(2)
            return []
            
        return video_files
        
    def scan_tiktok_directory(self):
        """Quét thư mục TikTok mặc định"""
        tiktok_dirs = [
            "/storage/emulated/0/Download/TIKTOK_TERMUX_PRO",
            "/storage/emulated/0/Download",
            "./TIKTOK_TERMUX_PRO"
        ]
        
        video_files = []
        for tiktok_dir in tiktok_dirs:
            if os.path.exists(tiktok_dir):
                found = self.scan_directory(tiktok_dir)
                video_files.extend(found)
                print(f"{Colors.GREEN}✅ Đã quét: {tiktok_dir} - Tìm thấy {len(found)} video")
            else:
                print(f"{Colors.YELLOW}⚠️ Thư mục không tồn tại: {tiktok_dir}")
            
        if not video_files:
            print(f"{Colors.YELLOW}⚠️ Không tìm thấy file video TikTok nào!")
            time.sleep(2)
            return []
            
        return video_files
        
    def process_videos(self, video_files):
        """Xử lý và kiểm tra video"""
        print(f"\n{Colors.BLUE}🔍 Đang phân tích {len(video_files)} video...")
        print(f"{Colors.YELLOW}⚠️  Đang tìm video nền đen để XOÁ...")
        
        results = []
        for i, video_file in enumerate(video_files, 1):
            print(f"{Colors.CYAN}📹 Đang phân tích ({i}/{len(video_files)}): {video_file.name}")
            result = self.check_video_quality(video_file)
            results.append(result)
            
            # Hiển thị ngay nếu phát hiện nên xoá
            if result['should_delete']:
                print(f"  {Colors.RED}🚨 SẼ XOÁ: {result['name']} - {result['video_quality']}")
            
        return results

def main():
    """Hàm chính"""
    try:
        # Kiểm tra ffmpeg
        try:
            subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
            print(f"{Colors.GREEN}✅ FFmpeg đã được cài đặt")
        except:
            print(f"{Colors.RED}❌ Cần cài đặt ffmpeg trước!")
            print(f"{Colors.YELLOW}📦 Trên Termux: pkg install ffmpeg")
            print(f"{Colors.YELLOW}📦 Trên Linux: sudo apt install ffmpeg")
            return
            
        detector = VideoErrorDetector()
        detector.show_main_menu()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}👋 Đã dừng chương trình!")
    except Exception as e:
        print(f"{Colors.RED}💥 Lỗi: {e}")

if __name__ == "__main__":
    main()
