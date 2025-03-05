# utils/enricher.py
def enrich_apt_data(entity):
    # Add VirusTotal, Shodan, CVE data
    if entity["type"] == "Malware":
        entity["vt_score"] = get_virustotal_score(entity["name"])
    return entity