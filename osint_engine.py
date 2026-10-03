# osint_engine.py

import hashlib
import time
import requests
from ddgs import DDGS
from config import DATA_BROKERS, OPT_OUT_LINKS, DORK_SITES

def scan_data_brokers(full_name: str, location: str = "", log_callback=None) -> list:
    """Scans 30 data brokers in 6 batches with callback logging for GUI support."""
    found = []
    batch_size = 5
    batches = [DATA_BROKERS[i:i + batch_size] for i in range(0, len(DATA_BROKERS), batch_size)]
    
    with DDGS() as ddgs:
        for idx, batch in enumerate(batches, start=1):
            sites_or = " OR ".join([f"site:{site}" for site in batch])
            query = f'{sites_or} "{full_name}"'
            if location:
                query += f' "{location}"'
            
            if log_callback:
                log_callback(f"[Batch {idx}/{len(batches)}] Scanning: {', '.join(batch[:3])}...")
                
            try:
                results = list(ddgs.text(query, max_results=10))
                if results:
                    for r in results:
                        title = r.get("title") or ""
                        href = r.get("href") or r.get("url") or ""
                        if not title and not href:
                            continue
                        matched_site = next((s for s in batch if s in href), "data broker")
                        found.append({
                            "category": "Data Broker",
                            "source": matched_site,
                            "title": title if title else f"Listing on {matched_site}",
                            "url": href,
                            "opt_out_url": OPT_OUT_LINKS.get(matched_site, "N/A")
                        })
                        if log_callback:
                            log_callback(f"  🔴 FOUND: {title[:50]}...")
            except Exception as e:
                if log_callback:
                    log_callback(f"  ⚠️ Rate limit encountered on batch {idx}")
                    
            if idx < len(batches):
                time.sleep(12)  # Delay between batches
                
    return found

def scan_google_dorks(full_name: str, email: str, log_callback=None) -> list:
    """Scans for exposed Pastebin dumps and exposed PDF/Doc files."""
    found = []
    if log_callback:
        log_callback("\n[+] Running Google Dork scans for paste dumps & exposed documents...")
        
    with DDGS() as ddgs:
        # Check Paste Dumps
        if email:
            paste_sites = " OR ".join([f"site:{s}" for s in DORK_SITES])
            query = f'{paste_sites} "{email}"'
            try:
                res = list(ddgs.text(query, max_results=5))
                for r in res:
                    found.append({
                        "category": "Paste Leak",
                        "source": "Paste Dump",
                        "title": r.get("title", "Exposed Paste Link"),
                        "url": r.get("href") or r.get("url"),
                        "opt_out_url": "N/A"
                    })
                    if log_callback:
                        log_callback(f"  🔴 PASTE LEAK FOUND: {r.get('title')[:50]}")
            except Exception:
                pass

        # Check Exposed Documents
        if full_name:
            doc_query = f'(filetype:pdf OR filetype:xlsx OR filetype:doc) "{full_name}"'
            try:
                res = list(ddgs.text(doc_query, max_results=5))
                for r in res:
                    found.append({
                        "category": "Document Leak",
                        "source": "Exposed File",
                        "title": r.get("title", "Public Document Mention"),
                        "url": r.get("href") or r.get("url"),
                        "opt_out_url": "N/A"
                    })
                    if log_callback:
                        log_callback(f"  🔴 EXPOSED FILE FOUND: {r.get('title')[:50]}")
            except Exception:
                pass
                
    return found

def check_gravatar_profile(email: str, log_callback=None) -> bool:
    """Checks for active public Gravatar profiles."""
    if not email:
        return False
    if log_callback:
        log_callback(f"\n[+] Checking Gravatar footprint for '{email}'...")
        
    email_clean = email.strip().lower().encode('utf-8')
    sha256_hash = hashlib.sha256(email_clean).hexdigest()
    url = f"https://gravatar.com/{sha256_hash}.json"
    
    try:
        res = requests.get(url, headers={'User-Agent': 'ExposureScanner/1.0'}, timeout=6)
        if res.status_code == 200:
            if log_callback:
                log_callback("  🔴 Gravatar Profile Active")
            return True
    except Exception:
        pass
    return False

def check_email_breaches(email: str, log_callback=None) -> list:
    """Queries XposedOrNot free API for breach exposures."""
    if not email:
        return []
    if log_callback:
        log_callback(f"\n[+] Checking breaches for '{email}' via XposedOrNot...")
        
    found = []
    try:
        res = requests.get(f"https://api.xposedornot.com/v1/check-email/{email}", timeout=8)
        if res.status_code == 200:
            data = res.json()
            if "breaches" in data and data["breaches"]:
                breaches = data["breaches"][0] if isinstance(data["breaches"][0], list) else data["breaches"]
                for b in breaches:
                    found.append({
                        "category": "Breach Leak",
                        "source": b,
                        "title": f"Credential Exposure in {b}",
                        "url": "https://xposedornot.com",
                        "opt_out_url": "N/A"
                    })
                    if log_callback:
                        log_callback(f"  🔴 BREACH: {b}")
    except Exception:
        pass
    return found