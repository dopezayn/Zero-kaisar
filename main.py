import aiohttp
import asyncio
import brotli
import gzip
import re
from datetime import datetime
import os

# Clear console function
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

# ANSI color codes for pink text
PINK = '\033[95m'
RESET = '\033[0m'

# Banner
BANNER = f"""{PINK}
███████╗███████╗██████╗  ██████╗ 
╚══███╔╝██╔════╝██╔══██╗██╔═══██╗
  ███╔╝ █████╗  ██████╔╝██║   ██║
 ███╔╝  ██╔══╝  ██╔══██╗██║   ██║
███████╗███████╗██║  ██║╚██████╔╝
╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ 
      Made by akhii - Zero Tool
{RESET}"""

BALANCE_URL = "https://zero-api.kaisar.io/user/balances?symbol=point"
SPIN_URL = "https://zero-api.kaisar.io/lucky/spin"
CONVERT_URL = "https://zero-api.kaisar.io/lucky/convert"

timeout = aiohttp.ClientTimeout(total=10)

def get_headers(token):
    return {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "authorization": f"Bearer {token.strip()}",
        "content-type": "application/json",
        "origin": "https://zero.kaisar.io",
        "referer": "https://zero.kaisar.io/",
        "user-agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36",
    }

async def decode_response(resp):
    raw_data = await resp.read()
    encoding = resp.headers.get("content-encoding", "")
    try:
        if "br" in encoding:
            raw_data = brotli.decompress(raw_data)
        elif "gzip" in encoding:
            raw_data = gzip.decompress(raw_data)
    except:
        pass
    return raw_data.decode("utf-8", errors="ignore")

async def is_token_valid(session, headers):
    try:
        async with session.get(BALANCE_URL, headers=headers) as resp:
            return resp.status == 200
    except:
        return False

async def check_balance(session, headers, name):
    try:
        async with session.get(BALANCE_URL, headers=headers) as resp:
            decoded = await decode_response(resp)
            match = re.search(r'"balance":"?([\d.]+)"?', decoded)
            if match:
                balance = float(match.group(1))
                print(f"{PINK}[{name}] [{datetime.now().strftime('%H:%M:%S')}] Balance: {balance}{RESET}")
                return balance
            return None
    except:
        return None

async def buy_ticket(session, headers, count, name):
    try:
        for _ in range(count):
            await session.post(CONVERT_URL, headers=headers, json={})
        print(f"{PINK}[{name}] [{datetime.now().strftime('%H:%M:%S')}] Bought {count} tickets.{RESET}")
    except Exception as e:
        print(f"{PINK}[{name}] [{datetime.now().strftime('%H:%M:%S')}] Ticket buying error: {e}{RESET}")

async def spin(session, headers):
    try:
        async with session.post(SPIN_URL, headers=headers, json={}) as resp:
            return resp.status
    except:
        return None

async def worker(token, target, name):
    headers = get_headers(token)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        if not await is_token_valid(session, headers):
            print(f"{PINK}[{name}] [{datetime.now().strftime('%H:%M:%S')}] Invalid token. Skipping.{RESET}")
            return

        while True:
            balance = await check_balance(session, headers, name)
            if balance is None:
                print(f"{PINK}[{name}] [{datetime.now().strftime('%H:%M:%S')}] Failed to fetch balance. Retry...{RESET}")
                await asyncio.sleep(5)
                continue

            if balance >= target:
                print(f"{PINK}[{name}] [{datetime.now().strftime('%H:%M:%S')}] Target reached! Done.{RESET}")
                break

            if balance >= 300:
                tickets = int(balance // 300)
                await buy_ticket(session, headers, min(tickets, 1), name)
            else:
                print(f"{PINK}[{name}] [{datetime.now().strftime('%H:%M:%S')}] Not enough for ticket. Waiting...{RESET}")
                await asyncio.sleep(5)
                continue

            results = await asyncio.gather(*[spin(session, headers) for _ in range(500)])
            spins = sum(1 for r in results if r == 200)
            print(f"{PINK}[{name}] [{datetime.now().strftime('%H:%M:%S')}] Spins success: {spins}{RESET}")
            await asyncio.sleep(1)

async def main():
    clear_console()
    print(BANNER)
    print(f"{PINK}Paste all your tokens line by line. End with an empty line:{RESET}")
    tokens = []
    while True:
        token = input()
        if not token.strip():
            break
        tokens.append(token.strip())

    if not tokens:
        print(f"{PINK}No tokens provided.{RESET}")
        return

    target = float(input(f"{PINK}Enter target points: {RESET}"))
    print(f"{PINK}\nStarting Zero Tool with {len(tokens)} accounts. Target: {target} points{RESET}")
    print(f"{PINK}{'=' * 60}{RESET}")
    
    tasks = [
        worker(token, target, f"Acc{i+1}")
        for i, token in enumerate(tokens)
    ]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())