import requests
from xml.etree import ElementTree as ET
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DOF_URL = "https://www.dof.gob.mx/indicadores.xml"
OUTPUT_FILE = "dof_rss.xml"

def fetch_dolar_item():
    resp = requests.get(DOF_URL, verify=False)
    resp.raise_for_status()
    tree = ET.fromstring(resp.content)
    for item in tree.findall(".//item"):
        title = item.findtext("title", "").strip()
        if title.upper() == "DOLAR":
            description = item.findtext("description", "").strip()
            valuedate = item.findtext("valuedate", "").strip()
            pubdate = item.findtext("pubdate", "").strip()
            print(f"DEBUG: Found DOLAR item with valuedate: '{valuedate}', pubdate: '{pubdate}'")
            return {
                "title": title,
                "description": description,
                "valuedate": valuedate,
                "pubdate": pubdate
            }
    print("DEBUG: No DOLAR indicator found.")
    return None

def iso8601_to_rfc822(dt_str):
    if not dt_str or len(dt_str) < 10:
        return None
    # Remove colon in timezone if present (for %z in strptime)
    if len(dt_str) > 5 and dt_str[-3] == ":":
        dt_str_fixed = dt_str[:-3] + dt_str[-2:]
    else:
        dt_str_fixed = dt_str
    print(f"DEBUG: Parsing date string: '{dt_str_fixed}'")
    try:
        dt = datetime.strptime(dt_str_fixed, "%Y-%m-%dT%H:%M:%S%z")
        rfc822_date = dt.strftime('%a, %d %b %Y %H:%M:%S %z')
        print(f"DEBUG: Parsed RFC-822 date: {rfc822_date}")
        return rfc822_date
    except Exception as e:
        print(f"DEBUG: Exception in date parsing: {e}")
        return None

def generate_rss(dolar_info):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "DOF Indicador DOLAR"
    ET.SubElement(channel, "link").text = DOF_URL
    ET.SubElement(channel, "description").text = "Indicador DOLAR del Diario Oficial de la Federación"
    ET.SubElement(channel, "pubDate").text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')

    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = dolar_info["title"]
    ET.SubElement(item, "description").text = dolar_info["description"]

    # Prefer pubdate (from XML) over valuedate
    pubdate_rfc822 = iso8601_to_rfc822(dolar_info.get("pubdate", "")) \
        or iso8601_to_rfc822(dolar_info.get("valuedate", ""))
    if pubdate_rfc822:
        ET.SubElement(item, "pubDate").text = pubdate_rfc822

    ET.SubElement(item, "guid").text = f"dof-dolar-{dolar_info['valuedate']}"

    tree = ET.ElementTree(rss)
    tree.write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)
    print(f"DEBUG: RSS feed written to {OUTPUT_FILE}")

if __name__ == "__main__":
    dolar = fetch_dolar_item()
    if dolar:
        generate_rss(dolar)
    else:
        print("No DOLAR indicator found.")
