import requests
from pathlib import Path
import time
from datetime import datetime, timezone
from multiprocessing import Process, Queue
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

    try:
        response = requests.get(url, headers=headers, cookies=cookies)
        response.raise_for_status()  # Raise exception jika status code tidak 200
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

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

def complete_missions():
    """Menyelesaikan misi menggunakan API"""
    session_token = get_session_token()
    if not session_token:
        print("Tidak dapat menemukan session token di cookies.txt")
        return

    # Endpoint untuk mendapatkan info box
    box_url = "https://www.goblin.meme/api/box/686cccc69f47ac6a1d4a0548"
    
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.7',
        'priority': 'u=1, i',
        'referer': 'https://www.goblin.meme/box/686cccc69f47ac6a1d4a0548',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Brave";v="138"',
        'content-type': 'application/json',
        'cookie': f'__Secure-next-auth.session-token={session_token}'
    }

    try:
        # Dapatkan info box untuk mendapatkan ID misi
        box_response = requests.get(box_url, headers=headers)
        box_data = box_response.json()
        
        # Periksa waktu siap box
        ready_at = box_data.get('readyAt')
        if not ready_at:
            print("\nBox belum siap, langsung mulai mining baru...")
            start_box(session_token, headers)
            return
            
        # Jika box belum siap, hitung waktu tunggu
        ready_time = datetime.strptime(ready_at, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        current_time = datetime.now(timezone.utc)
        
        if current_time < ready_time:
            # Hitung selisih waktu
            time_diff = (ready_time - current_time).total_seconds()
            print(f"\nBox belum siap, menunggu {int(time_diff/3600)} jam {int((time_diff%3600)/60)} menit lagi...")
            print("\n" + "="*50)
            print(f"{'MENUNGGU BOX SIAP':^50}")
            print("="*50 + "\n")
            countdown_timer(int(time_diff))
            
            # Setelah box siap, coba lagi
            complete_missions()
            return
            
        # Endpoint untuk menyelesaikan misi
        mission_url = "https://www.goblin.meme/api/box/686cccc69f47ac6a1d4a0548/mission"
        
        # Kirim request POST untuk menyelesaikan misi
        response = requests.post(mission_url, headers=headers)
        
        if response.status_code == 200:
            print("\nMisi berhasil diselesaikan!")
            
            # Setelah misi berhasil, coba klaim hadiah
            claim_prize(session_token, headers)
        elif response.status_code == 400 and "No active box to complete mission for." in response.text:
            print("\nNo active box found, skipping mission completion")
            print("Moving to next step...")
            
            # Langsung klaim hadiah
            claim_prize(session_token, headers)
        else:
            console.print(f"\n[AKUN {account_num}] Gagal menyelesaikan misi: {response.status_code}")
            console.print(response.text)
            
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")

def claim_prize(session_token, headers):
    """Mengklaim hadiah setelah misi berhasil"""
    console.print("\n=== KLAIM HADIAH ===")
    
    # Endpoint untuk klaim hadiah
    claim_url = "https://www.goblin.meme/api/box/686cccc69f47ac6a1d4a0548/claim"
    
    try:
        # Kirim request POST untuk klaim hadiah
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
            start_box(session_token, headers)
        elif response.status_code == 400 and "No active box to open." in response.text:
            console.print("\n[AKUN {account_num}] No active box found, skipping prize claim")
            console.print("Moving to next step...")
            
            # Langsung mulai box mining
            start_box(session_token, headers)
        else:
            console.print("[red]=== ✗ GAGAL MENGKLAIM HADIAH ===[/red]")
            console.print(f"[red]Status Code: {response.status_code}[/red]")
            console.print(f"[red]Error: {response.text}[/red]")
            
    except requests.exceptions.RequestException as e:
        console.print("[red]=== ERROR ===[/red]")
        console.print(f"[red]Error: {e}[/red]")

def start_box(session_token, headers):
    """Memulai box mining"""
    console.print("\n=== MEMULAI BOX MINING ===")
    
    # Endpoint untuk memulai box
    start_url = "https://www.goblin.meme/api/box/686cccc69f47ac6a1d4a0548/start"
    
    try:
        # Kirim request POST untuk memulai box
        response = requests.post(start_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            console.print("[green]=== ✓ BOX MINING DIMULAI ===[/green]")
            console.print(f"[green]• Message: {data['message']}[/green]")
            console.print(f"[green]• Box ID: {data['box']['id']}[/green]")
            console.print(f"[green]• Waktu Mulai: {format_timestamp(data['box']['startTime'])}[/green]")
            console.print(f"[green]• Waktu Selesai: {format_timestamp(data['box']['readyAt'])}[/green]")
            console.print(f"[green]• Tipe Hadiah: {data['box']['prizeType']}[/green]")
            console.print(f"[green]• Jumlah Hadiah: {data['box']['prizeAmount']:,} points[/green]")
        else:
            console.print("[red]=== ✗ GAGAL MEMULAI BOX MINING ===[/red]")
            console.print(f"[red]Status Code: {response.status_code}[/red]")
            console.print(f"[red]Error: {response.text}[/red]")
            
    except requests.exceptions.RequestException as e:
        console.print("[red]=== ERROR ===[/red]")
        console.print(f"[red]Error: {e}[/red]")

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
            
            progress.update(task, description=f"Time remaining: {hours:02d}:{minutes:02d}:{seconds:02d} {loading_char}")
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
                    start_box(token, headers={'cookie': f'__Secure-next-auth.session-token={token}'})
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