import hashlib
import json
import random
import time
import requests
from ddgs import DDGS

# 30 Top Data Brokers, Public Record Aggregators, and Voter Registries
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

# Direct Opt-Out / Data Removal Request Forms
OPT_OUT_LINKS = {
    "spokeo.com": "https://www.spokeo.com/optout",
    "whitepages.com": "https://www.whitepages.com/suppression-requests",
    "radaris.com": "https://radaris.com/page/opt-out",
    "fastpeoplesearch.com": "https://www.fastpeoplesearch.com/removal",
    "truepeoplesearch.com": "https://www.truepeoplesearch.com/removal",
    "beenverified.com": "https://www.beenverified.com/app/optout/search",
    "peoplelooker.com": "https://www.peoplelooker.com/f/optout/search",
    "thatsthem.com": "https://thatsthem.com/optout",
    "nuwber.com": "https://nuwber.com/removal/link",
    "searchpeoplefree.com": "https://www.searchpeoplefree.com/opt-out",
    "cyberbackgroundchecks.com": "https://www.cyberbackgroundchecks.com/removal",
    "instantcheckmate.com": "https://www.instantcheckmate.com/opt-out/",
    "truthfinder.com": "https://www.truthfinder.com/opt-out/",
    "intelius.com": "https://www.intelius.com/opt-out/",
    "checkpeople.com": "https://checkpeople.com/opt-out",
    "peekyou.com": "https://www.peekyou.com/about/contact/optout/",
    "zabasearch.com": "https://www.zabasearch.com/block_records/",
    "ussearch.com": "https://www.ussearch.com/opt-out/",
    "familytreenow.com": "https://www.familytreenow.com/optout",
    "usphonebook.com": "https://www.usphonebook.com/opt-out",
    "clustrmaps.com": "https://clustrmaps.com/bl/opt-out",
    "addresssearch.com": "https://www.addresssearch.com/remove-name.php",
    "anywho.com": "https://www.anywho.com/optout",
    "411.com": "https://www.411.com/opt-out",
    "spytox.com": "https://www.spytox.com/optout",
    "cubib.com": "https://cubib.com/optout.php",
    "voterrecords.com": "https://voterrecords.com/optout",
    "publicrecords360.com": "https://www.publicrecords360.com/optout",
    "yellowpages.com": "https://www.yellowpages.com/about/opt-out",
    "smartfastfinder.com": "https://smartfastfinder.com/optout"
}


def scan_data_brokers(full_name: str, location: str = "") -> list:
    """
    Scans 30 data brokers in batches of 5.
    Attaches direct opt-out removal links for every discovered listing.
    """
    print(f"\n[+] Scanning {len(DATA_BROKERS)} broker databases for '{full_name}'...")
    found_profiles = []
    
    batch_size = 5
    broker_batches = [DATA_BROKERS[i:i + batch_size] for i in range(0, len(DATA_BROKERS), batch_size)]
    
    with DDGS() as ddgs:
        for idx, batch in enumerate(broker_batches, start=1):
            sites_or = " OR ".join([f"site:{site}" for site in batch])
            query = f'{sites_or} "{full_name}"'
            if location:
                query += f' "{location}"'
            
            print(f"\n  [Batch {idx}/{len(broker_batches)}] Checking: {', '.join(batch[:3])}...")
            
            retries = 3
            for attempt in range(retries):
                try:
                    results = list(ddgs.text(query, max_results=10))
                    if results:
                        valid_hits = 0
                        for r in results:
                            title = r.get("title") or r.get("heading") or ""
                            href = r.get("href") or r.get("url") or r.get("link") or ""
                            snippet = r.get("body") or r.get("snippet") or ""
                            
                            if not title and not href:
                                continue
                            
                            matched_site = next((site for site in batch if site in href), "data broker")
                            opt_out_link = OPT_OUT_LINKS.get(matched_site, "N/A")
                            
                            found_profiles.append({
                                "broker": matched_site,
                                "title": title if title else f"Listing on {matched_site}",
                                "url": href,
                                "opt_out_url": opt_out_link,
                                "snippet": snippet
                            })
                            valid_hits += 1
                            display_title = title if title else f"Listing on {matched_site}"
                            print(f"    🔴 FOUND: {display_title} -> {href}")
                            
                        if valid_hits == 0:
                            print("    🟢 Clear (No matches in this batch)")
                    else:
                        print("    🟢 Clear (No matches in this batch)")
                    break
                    
                except Exception as e:
                    if attempt < retries - 1:
                        wait_seconds = (attempt + 1) * 10
                        print(f"    ⚠️ Search rate-limited. Retrying in {wait_seconds}s...")
                        time.sleep(wait_seconds)
                    else:
                        print("    ❌ Skipped batch due to persistent rate limit")
            
            if idx < len(broker_batches):
                delay_seconds = 60
                print(f"  [⏳] Pausing for {delay_seconds}s to respect search rate limits...")
                for remaining in range(delay_seconds, 0, -5):
                    print(f"      Next batch in {remaining}s...", end="\r")
                    time.sleep(5)
                print(" " * 40, end="\r")
            
    return found_profiles


def check_gravatar_profile(email: str) -> dict:
    """Queries Gravatar API for public profile and avatar existence for the given email."""
    if not email:
        return {"exists": False}
        
    print(f"\n[+] Checking Gravatar public footprint for '{email}'...")
    email_clean = email.strip().lower().encode('utf-8')
    sha256_hash = hashlib.sha256(email_clean).hexdigest()
    
    headers = {'User-Agent': 'ExposureScanner-Script/1.0'}
    json_url = f"https://gravatar.com/{sha256_hash}.json"
    avatar_url = f"https://www.gravatar.com/avatar/{sha256_hash}?d=404"
    
    profile_data = {
        "exists": False,
        "avatar_url": f"https://www.gravatar.com/avatar/{sha256_hash}",
        "profile_url": f"https://gravatar.com/{sha256_hash}",
        "display_name": None,
        "about": None,
        "location": None,
        "social_accounts": []
    }
    
    try:
        # Check Gravatar public profile JSON
        res = requests.get(json_url, headers=headers, timeout=8)
        if res.status_code == 200:
            data = res.json()
            if "entry" in data and len(data["entry"]) > 0:
                entry = data["entry"][0]
                profile_data["exists"] = True
                profile_data["display_name"] = entry.get("displayName")
                profile_data["about"] = entry.get("aboutMe")
                profile_data["location"] = entry.get("currentLocation")
                profile_data["profile_url"] = entry.get("profileUrl", profile_data["profile_url"])
                
                accounts = entry.get("accounts", [])
                profile_data["social_accounts"] = [acc.get("url") for acc in accounts if acc.get("url")]
                
                print(f"  🔴 FOUND: Active Gravatar Profile ({profile_data['profile_url']})")
                if profile_data["display_name"]:
                    print(f"      - Display Name : {profile_data['display_name']}")
                if profile_data["location"]:
                    print(f"      - Location     : {profile_data['location']}")
                if profile_data["social_accounts"]:
                    print(f"      - Linked Socials: {', '.join(profile_data['social_accounts'])}")
                return profile_data
        
        # Fallback check for uploaded custom avatar image
        img_res = requests.head(avatar_url, headers=headers, timeout=8)
        if img_res.status_code == 200:
            profile_data["exists"] = True
            print("  🔴 FOUND: Active Gravatar Avatar detected (Profile details hidden)")
            return profile_data
            
        print("  🟢 Clear (No public Gravatar account or custom avatar linked)")
        return profile_data

    except Exception as e:
        print(f"  [!] Gravatar lookup error: {e}")
        return profile_data


def check_email_breaches(email: str) -> dict:
    """Queries XposedOrNot free API to check email breach exposure without an API key."""
    if not email:
        return {"count": 0, "details": []}

    print(f"\n[+] Checking breach status for '{email}' via XposedOrNot...")
    headers = {'User-Agent': 'ExposureScanner-Script/1.0'}
    url = f"https://api.xposedornot.com/v1/check-email/{email}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "breaches" in data and data["breaches"]:
                raw_breaches = data["breaches"]
                breach_list = raw_breaches[0] if isinstance(raw_breaches[0], list) else raw_breaches
                
                print(f"  🔴 FOUND: {len(breach_list)} breach leak(s) linked to this email!")
                for b in breach_list:
                    print(f"      - {b}")
                return {"count": len(breach_list), "details": breach_list}
            else:
                print("  🟢 Clear (No known breaches found for this email)")
                return {"count": 0, "details": []}
                
        elif response.status_code == 404 or "Not found" in response.text:
            print("  🟢 Clear (No known breaches found for this email)")
            return {"count": 0, "details": []}
            
        else:
            print(f"  ⚠️ Breach service returned status code {response.status_code}")
            return {"count": 0, "details": []}
            
    except Exception as e:
        print(f"  [!] Breach search error: {e}")
        return {"count": 0, "details": []}


def calculate_cooked_score(broker_count: int, breach_count: int, gravatar_found: bool, has_location: bool) -> tuple:
    """Calculates exposure score based on broker hits, data breaches, and Gravatar footprints."""
    score = 0
    
    # Broker visibility score (up to 60 points max)
    score += min(broker_count * 5, 60)
    
    # Breach score (up to 30 points max)
    if breach_count > 0:
        score += min(breach_count * 8, 30)
        
    # Gravatar exposure score (10 points max)
    if gravatar_found:
        score += 10
        
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
    gravatar_info = check_gravatar_profile(email) if email else {"exists": False}
    breach_info = check_email_breaches(email) if email else {"count": 0, "details": []}
    
    breach_count = max(breach_info["count"], 0)
    score, status = calculate_cooked_score(
        len(broker_hits), 
        breach_count, 
        gravatar_info.get("exists", False), 
        bool(location)
    )
    
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
        "gravatar_footprint": gravatar_info,
        "breach_exposure": breach_info
    }
    
    print("\n==========================================")
    print("         EXPOSURE REPORT RESULTS          ")
    print("==========================================")
    print(f" Exposure Score : {score} / 100")
    print(f" Threat Level   : {status}")
    print(f" Brokers Found  : {len(broker_hits)} / {len(DATA_BROKERS)} scanned sites")
    print(f" Gravatar Found : {'YES' if gravatar_info.get('exists') else 'NO'}")
    print(f" Email Breaches : {breach_count} known leaks")
    print("==========================================\n")
    
    if broker_hits:
        print("--- DISCOVERED EXPOSURE & OPT-OUT LINKS ---")
        for hit in broker_hits:
            print(f"• [{hit['broker']}] {hit['title']}")
            print(f"  Exposure URL : {hit['url']}")
            print(f"  Opt-Out Form : {hit['opt_out_url']}\n")
            
    filename = "exposure_report.json"
    with open(filename, "w") as f:
        json.dump(report, f, indent=4)
    print(f"[+] Scan completed! Full enriched results saved to '{filename}'.")

if __name__ == "__main__":
    run_exposure_scan()