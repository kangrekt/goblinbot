import requests
from pathlib import Path
import time
from datetime import datetime, timezone
from multiprocessing import Process, Queue
from functools import wraps
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.text import Text
from rich.style import Style

box_url = "https://www.goblin.meme/api/box/686cccc69f47ac6a1d4a0548"

console = Console()

def make_api_request(account_num):
    """Fungsi untuk melakukan request API ke Goblin Meme"""
    try:
        tokens = get_session_tokens()
        if not tokens:
            console.print("[red]No session tokens found in cookies.txt[/red]")
            return None
            
        token = tokens[account_num - 1]
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.7',
            'priority': 'u=1, i',
            'referer': 'https://www.goblin.meme/box/686cccc69f47ac6a1d4a0548',
            'sec-ch-ua': '"Not)A;Brand";v=\"8\", \"Chromium\";v=\"138\", \"Brave\";v=\"138\"',
            'content-type': 'application/json',
            'cookie': f'__Secure-next-auth.session-token={token}'
        }
        response = requests.get(box_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            console.print(f"[red]Failed to get box info: {response.status_code}[/red]")
            return None
    except Exception as e:
        console.print(f"[red]Error making API request: {e}[/red]")
        return None

def get_session_tokens():
    """Membaca semua session token dari cookies.txt"""
    cookies_path = Path('cookies.txt')
    if cookies_path.exists():
        with open(cookies_path, 'r') as f:
            # Baca semua baris dan hapus whitespace
            tokens = [line.strip() for line in f.readlines() if line.strip()]
            return tokens
    return []

def format_timestamp(timestamp_str):
    """Format timestamp dari API ke format lokal"""
    from datetime import datetime
    if timestamp_str is None:
        return "-"
    try:
        dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return "-"

def display_box_info(data, account_num):
    """Menampilkan informasi box dalam format yang rapi dengan rich"""
    box_info = Panel(
        f"[bold]Box Name:[/bold] {data.get('name', 'Unknown')}\n"
        f"[bold]Reward:[/bold] {data.get('normalPrize', 'Unknown')} points\n"
        f"[bold]Box Type:[/bold] {data.get('boxType', 'Unknown').title()}\n"
        f"[bold]Status:[/bold] {'Closed' if data.get('opened') else 'Ready'}\n"
        f"[bold]Ready to Open:[/bold] {'Yes' if data.get('isReady') else 'No'}\n"
        f"[bold]Start Time:[/bold] {format_timestamp(data.get('startTime'))}\n"
        f"[bold]Ready Time:[/bold] {format_timestamp(data.get('readyAt'))}\n\n"
        f"[bold]Mission Description:[/bold]\n"
        + '\n'.join([f"  {i}. {desc}" for i, desc in enumerate(data.get('missionDesc', '').split('\n'), 1)]),
        title=f"[bold]Account {account_num} Box Information[/bold]",
        border_style="blue",
        expand=True  # Garis memenuhi layar
    )
    console.print(box_info)

def retry_on_failure(max_retries=5, delay=1, exponential_backoff=True):
    """Decorator untuk melakukan retry pada fungsi yang gagal dengan exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            account_num = args[0] if args and len(args) > 0 else 'Unknown'
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:  # Don't sleep on the last attempt
                        # Print error message
                        console.print(f"[yellow][AKUN {account_num}] Attempt {attempt + 1}/{max_retries} failed: {e}[/yellow]")
                        
                        # Calculate delay with exponential backoff if enabled
                        if exponential_backoff:
                            current_delay = min(30, delay * (2 ** attempt))  # Max delay 30 seconds
                        
                        # Print retry message
                        console.print(f"[yellow][AKUN {account_num}] Retrying in {current_delay} seconds...[/yellow]")
                        time.sleep(current_delay)
                    else:
                        console.print(f"[red][AKUN {account_num}] All {max_retries} attempts failed. Last error: {e}[/red]")
                        # Return None or raise exception based on function's needs
                        return None
            return None
        return wrapper
    return decorator

@retry_on_failure(max_retries=5, delay=1, exponential_backoff=True)
def complete_missions(account_num):
    """Menyelesaikan misi menggunakan API dengan retry mechanism"""
    try:
        # Get box info
        data = make_api_request(account_num)
        if not data:
            raise ValueError("Failed to get box information")
            
        # Display box info
        console.print(Panel(f"[bold]Processing Account {account_num}[/bold]", border_style="green"))
        display_box_info(data, account_num)
        
        # Check if box is ready
        ready_at = data.get('readyAt')
        if not ready_at:
            console.print(f"[yellow][AKUN {account_num}] Box belum siap, langsung mulai mining baru...[/yellow]")
            start_box(account_num)
            return
            
        ready_time = datetime.strptime(ready_at, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        current_time = datetime.now(timezone.utc)
        
        if current_time < ready_time:
            # Calculate time difference
            time_diff = (ready_time - current_time).total_seconds()
            console.print(f"[yellow][AKUN {account_num}] Box belum siap, menunggu {int(time_diff/3600)} jam {int((time_diff%3600)/60)} menit lagi...[/yellow]")
            countdown_timer(int(time_diff), account_num)
            complete_missions(account_num)
            return
            
        # Complete mission
        tokens = get_session_tokens()
        if not tokens or len(tokens) < account_num:
            raise ValueError("Invalid account number or no tokens available")
            
        token = tokens[account_num - 1]
        headers = {
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json',
            'cookie': f'__Secure-next-auth.session-token={token}'
        }
        
        mission_url = "https://www.goblin.meme/api/box/686cccc69f47ac6a1d4a0548/mission"
        response = requests.post(mission_url, headers=headers)
        
        if response.status_code == 200:
            console.print(f"[green][AKUN {account_num}] Misi berhasil diselesaikan![/green]")
            claim_prize(account_num)
        elif response.status_code == 400 and "No active box to complete mission for." in response.text:
            console.print(f"[yellow][AKUN {account_num}] No active box found, skipping mission completion[/yellow]")
            claim_prize(account_num)
        else:
            raise Exception(f"Failed to complete mission: {response.status_code} - {response.text}")
            
    except Exception as e:
        console.print(f"[red][AKUN {account_num}] Error: {e}[/red]")
        raise

@retry_on_failure(max_retries=5, delay=1, exponential_backoff=True)
def claim_prize(account_num):
    """Mengklaim hadiah setelah misi berhasil dengan retry mechanism"""
    try:
        tokens = get_session_tokens()
        if not tokens or len(tokens) < account_num:
            raise ValueError("Invalid account number or no tokens available")
            
        token = tokens[account_num - 1]
        headers = {
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json',
            'cookie': f'__Secure-next-auth.session-token={token}'
        }
        
        claim_url = "https://www.goblin.meme/api/box/686cccc69f47ac6a1d4a0548/claim"
        response = requests.post(claim_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            console.print("[green]=== ✓ HADIAH BERHASIL DIKLAIM ===[/green]")
            console.print(f"[green]• Message: {data['message']}[/green]")
            console.print(f"[green]• Prize Amount: {data['prizeAmount']:,} points[/green]")
            console.print(f"[green]• Prize Type: {data['prizeType']}[/green]")
            console.print(f"[green]• New Balance: {data['newBalance']:,} points[/green]")
            console.print(f"[green]• Promo Applied: {'✓ Yes' if data['promoApplied'] else '✗ No'}[/green]")
            
            # Tunggu 3 detik sebelum memulai mining
            console.print("\n=== MENUNGGU 3 DETIK ===")
            time.sleep(3)
            
            # Mulai box mining
            start_box(account_num)
        elif response.status_code == 400 and "No active box to open." in response.text:
            console.print(f"\n[AKUN {account_num}] No active box found, skipping prize claim")
        else:
            raise Exception(f"Failed to claim prize: {response.status_code} - {response.text}")
            
    except Exception as e:
        console.print(f"[red][AKUN {account_num}] Error claiming prize: {e}[/red]")
        raise

@retry_on_failure(max_retries=5, delay=1)
def start_box(account_num):
    """Memulai box mining"""
    try:
        tokens = get_session_tokens()
        if not tokens or len(tokens) < account_num:
            raise ValueError("Invalid account number or no tokens available")
            
        token = tokens[account_num - 1]
        headers = {
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json',
            'cookie': f'__Secure-next-auth.session-token={token}'
        }
        
        console.print(f"\n[AKUN {account_num}] === MEMULAI BOX MINING ===")
        start_url = "https://www.goblin.meme/api/box/686cccc69f47ac6a1d4a0548/start"
        response = requests.post(start_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            console.print(f"[green][AKUN {account_num}] ✓ BOX MINING DIMULAI[/green]")
            if 'box' in data:
                console.print(f"[green]• Message: {data.get('message', 'N/A')}[/green]")
                console.print(f"[green]• Box ID: {data['box'].get('id', 'N/A')}[/green]")
                console.print(f"[green]• Waktu Mulai: {format_timestamp(data['box'].get('startTime'))}[/green]")
                console.print(f"[green]• Waktu Selesai: {format_timestamp(data['box'].get('readyAt'))}[/green]")
                console.print(f"[green]• Tipe Hadiah: {data['box'].get('prizeType', 'N/A')}[/green]")
                console.print(f"[green]• Jumlah Hadiah: {data['box'].get('prizeAmount', 0):,} points[/green]")
            return data
        elif response.status_code == 400 and "already has an active box" in response.text.lower():
            console.print(f"[yellow][AKUN {account_num}] Box sudah aktif, melanjutkan...[/yellow]")
            return None
        elif response.status_code == 401:
            console.print(f"[red][AKUN {account_num}] Error: Unauthorized. Token mungkin sudah kadaluarsa[/red]")
            return None
        else:
            error_msg = f"Gagal memulai box mining (Status: {response.status_code})"
            if response.text:
                error_msg += f" - {response.text}"
            raise Exception(error_msg)
            
    except Exception as e:
        console.print(f"[red][AKUN {account_num}] Error starting box mining: {e}[/red]")
        raise

def countdown_timer(duration_seconds, account_num=None):
    """Menampilkan animasi countdown timer"""
    loading_chars = ['|', '/', '-', '\\']
    loading_index = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn()
    ) as progress:
        task = progress.add_task("Counting down...", total=duration_seconds)
        
        while duration_seconds > 0:
            hours = duration_seconds // 3600
            minutes = (duration_seconds % 3600) // 60
            seconds = duration_seconds % 60
            loading_char = loading_chars[loading_index % len(loading_chars)]
            loading_index += 1
            
            progress.update(task, description=f"Memproses Akun berikutnya: {hours:02d}:{minutes:02d}:{seconds:02d} {loading_char}")
            time.sleep(1)
            duration_seconds -= 1

def main_loop():
    """Loop utama yang menjalankan proses semua akun sebelum jeda"""
    console.print("\n" * 10)  # Tambahkan jarak di atas
    console.print(Panel(
        "[bold magenta]GOBLIN MEME BOX CHECKER[/bold magenta]\n"
        "[bold blue]BY KANGREKT[/bold blue]",
        border_style="magenta",
        title="[bold]Welcome[/bold]",
        expand=True  # Garis memenuhi layar
    ), justify="center")  # Pusatkan panel

    while True:
        # Dapatkan semua session token
        tokens = get_session_tokens()
        if not tokens:
            console.print("[red]Tidak ada session token yang ditemukan di cookies.txt[/red]")
            time.sleep(60)
            continue

        console.print(f"\n[green]Mengelola {len(tokens)} akun...[/green]")
        
        # Simpan semua waktu siap box
        ready_times = []
        
        # Proses semua akun untuk mendapatkan waktu siap
        for i, token in enumerate(tokens, 1):
            console.print(f"\n[blue]=== MEMULAI AKUN {i} ===[/blue]")
            
            try:
                # Dapatkan info box
                data = make_api_request(i)
                if data is None:
                    continue
                
                # Tampilkan info box
                console.print(Panel(f"[bold]Processing Account {i}[/bold]", border_style="green"))
                display_box_info(data, i)
                
                # Periksa waktu siap box
                ready_at = data.get('readyAt')
                if not ready_at:
                    console.print(f"\n[AKUN {i}] Box belum siap, langsung mulai mining baru...")
                    start_box(i)  # Pass only account number
                    continue
                    
                ready_time = datetime.strptime(ready_at, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
                current_time = datetime.now(timezone.utc)
                
                if current_time < ready_time:
                    # Hitung selisih waktu
                    time_diff = (ready_time - current_time).total_seconds()
                    console.print(f"\n[AKUN {i}] Box belum siap, menunggu {int(time_diff/3600)} jam {int((time_diff%3600)/60)} menit lagi...")
                    ready_times.append((i, time_diff))
                    continue
                    
                # Selesaikan misi
                complete_missions(i)
                    
            except Exception as e:
                console.print(f"[red][AKUN {i}] Error: {e}[/red]")
            finally:
                console.print(f"\n[blue]=== AKUN {i} SELESAI ===[/blue]")
                
                # Tambahkan jeda 10 detik antar akun
                if i < len(tokens):
                    countdown_timer(10, i)

        # Setelah semua akun selesai, langsung menunggu 24 jam
        console.print(Panel(
            "Waiting for 24 hours before next cycle...",
            title="[bold]WAITING 24 HOURS[/bold]",
            border_style="green"
        ))
        countdown_timer(24 * 3600)



if __name__ == "__main__":
    main_loop()
