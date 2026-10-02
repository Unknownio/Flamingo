import json
import random
import time
import requests
from ddgs import DDGS

# Expanded list of 30 top data brokers, voter registries, and public directories
DATA_BROKERS = [
    # Group 1: Major People Search
    "spokeo.com", "whitepages.com", "radaris.com", "fastpeoplesearch.com", "truepeoplesearch.com",
    # Group 2: Aggregators
    "beenverified.com", "peoplelooker.com", "thatsthem.com", "nuwber.com", "searchpeoplefree.com",
    # Group 3: Background Checkers
    "cyberbackgroundchecks.com", "instantcheckmate.com", "truthfinder.com", "intelius.com", "checkpeople.com",
    # Group 4: Directories
    "peekyou.com", "zabasearch.com", "ussearch.com", "familytreenow.com", "usphonebook.com",
    # Group 5: Address & Phone
    "clustrmaps.com", "addresssearch.com", "anywho.com", "411.com", "spytox.com",
    # Group 6: Public & Voter Records
    "cubib.com", "voterrecords.com", "publicrecords360.com", "yellowpages.com", "smartfastfinder.com"
]

def scan_data_brokers(full_name: str, location: str = "") -> list:
    """Scans 30 data brokers in batches of 5 with a 60-second delay between batches."""
    print(f"\n[+] Scanning {len(DATA_BROKERS)} broker databases for '{full_name}'...")
    found_profiles = []
    
    # Split 30 domains into 6 batches of 5 domains each
    batch_size = 5
    broker_batches = [DATA_BROKERS[i:i + batch_size] for i in range(0, len(DATA_BROKERS), batch_size)]
    
    with DDGS() as ddgs:
        for idx, batch in enumerate(broker_batches, start=1):
            # Construct batch query: (site:site1.com OR site:site2.com ...) "Name" "Location"
            sites_or = " OR ".join([f"site:{site}" for site in batch])
            query = f'({sites_or}) "{full_name}"'
            if location:
                query += f' "{location}"'
            
            print(f"\n  [Batch {idx}/{len(broker_batches)}] Checking: {', '.join(batch[:3])}...")
            
            # Retry mechanism for temporary rate limits
            retries = 3
            for attempt in range(retries):
                try:
                    results = list(ddgs.text(query, max_results=10))
                    if results:
                        for r in results:
                            href = r.get("href", "")
                            # Map result back to the specific broker domain
                            matched_site = next((site for site in batch if site in href), "unknown broker")
                            found_profiles.append({
                                "broker": matched_site,
                                "title": r.get("title"),
                                "url": href,
                                "snippet": r.get("body")
                            })
                            print(f"    🔴 FOUND: {r.get('title')} ({href})")
                    else:
                        print(f"    🟢 Clear (No matches in this batch)")
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    if attempt < retries - 1:
                        wait_seconds = (attempt + 1) * 10
                        print(f"    ⚠️ Search rate-limited. Retrying in {wait_seconds}s...")
                        time.sleep(wait_seconds)
                    else:
                        print(f"    ❌ Skipped batch due to persistent rate limit")
            
            # 60-second pause between batches (skip countdown after final batch)
            if idx < len(broker_batches):
                delay_seconds = 60
                print(f"  [⏳] Pausing for {delay_seconds} seconds before next batch...")
                for remaining in range(delay_seconds, 0, -5):
                    print(f"      Waiting... {remaining}s remaining", end="\r")
                    time.sleep(5)
                print(" " * 40, end="\r")  # Clear timer line
            
    return found_profiles


def check_email_breaches(email: str) -> dict:
    """Queries public breach records."""
    print(f"\n[+] Checking breach status for '{email}'...")
    headers = {'User-Agent': 'ExposureScanner-Script/1.0'}
    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}?truncateResponse=false"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            breaches = response.json()
            return {"count": len(breaches), "details": [b.get("Name") for b in breaches]}
        elif response.status_code == 404:
            return {"count": 0, "details": []}
        elif response.status_code == 401:
            print("  [!] HIBP API requires an API key for full breach list details.")
            return {"count": -1, "details": ["API Key required for detailed list"]}
    except Exception as e:
        print(f"  [!] Breach search error: {e}")
        
    return {"count": 0, "details": []}


def calculate_cooked_score(broker_count: int, breach_count: int, has_location: bool) -> tuple:
    """Calculates exposure score based on total hits found."""
    score = 0
    
    # Broker visibility score (up to 70 points max)
    score += min(broker_count * 5, 70)
    
    # Breach score (up to 30 points max)
    if breach_count > 0:
        score += min(breach_count * 8, 30)
        
    if has_location and broker_count > 0:
        score = min(int(score * 1.1), 100)
        
    if score == 0:
        status = "🟢 RAW (Minimal or no public footprints found)"
    elif score < 30:
        status = "🟡 RARE (Low public broker visibility)"
    elif score < 60:
        status = "🟠 MEDIUM WELL (Moderate public exposure across several brokers)"
    else:
        status = "🔴 FULLY COOKED (Widely aggregated across major broker databases)"
        
    return score, status


def run_exposure_scan():
    print("==========================================")
    print("   EXPANDED PERSONAL OSINT & EXPOSURE SCAN")
    print("==========================================")
    
    full_name = input("Enter Full Name (e.g. Jane Doe): ").strip()
    location = input("Enter City/State or Country (optional, e.g. Seattle WA): ").strip()
    email = input("Enter Primary Email address: ").strip()
    
    if not full_name and not email:
        print("[!] Error: You must enter at least a Name or Email.")
        return

    broker_hits = scan_data_brokers(full_name, location) if full_name else []
    breach_info = check_email_breaches(email) if email else {"count": 0, "details": []}
    
    breach_count = max(breach_info["count"], 0)
    score, status = calculate_cooked_score(len(broker_hits), breach_count, bool(location))
    
    report = {
        "target": {
            "name": full_name,
            "location": location,
            "email": email
        },
        "exposure_score": score,
        "status": status,
        "data_broker_exposure": {
            "total_sites_scanned": len(DATA_BROKERS),
            "total_found": len(broker_hits),
            "listings": broker_hits
        },
        "breach_exposure": breach_info
    }
    
    print("\n==========================================")
    print(f"         EXPOSURE REPORT RESULTS          ")
    print("==========================================")
    print(f" Exposure Score : {score} / 100")
    print(f" Threat Level   : {status}")
    print(f" Brokers Found  : {len(broker_hits)} / {len(DATA_BROKERS)} scanned sites")
    print(f" Email Breaches : {breach_count} known leaks")
    print("==========================================\n")
    
    if broker_hits:
        print("--- DISCOVERED EXPOSURE URLS ---")
        for hit in broker_hits:
            print(f"• [{hit['broker']}] {hit['title']}")
            print(f"  URL: {hit['url']}\n")
            
    filename = "exposure_report.json"
    with open(filename, "w") as f:
        json.dump(report, f, indent=4)
    print(f"[+] Scan completed! Full results saved to '{filename}'.")

if __name__ == "__main__":
    run_exposure_scan()