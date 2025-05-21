import requests
from xml.etree import ElementTree as ET
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DOF_URL = "https://www.dof.gob.mx/indicadores.xml"
OUTPUT_FILE = "dof_rss.xml"
FALLBACK_DATE = "Tue, 01 Jan 1991 00:00:00 +0000"

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
            return {
                "title": title,
                "description": description,
                "valuedate": valuedate,
                "pubdate": pubdate
            }
    return None

def iso8601_to_rfc822(dt_str):
    if not dt_str or len(dt_str) < 10:
        return None
    # Remove colon in timezone for %z compatibility
    if len(dt_str) > 5 and dt_str[-3] == ":":
        dt_str_fixed = dt_str[:-3] + dt_str[-2:]
    else:
        dt_str_fixed = dt_str
    try:
        dt = datetime.strptime(dt_str_fixed, "%Y-%m-%dT%H:%M:%S%z")
        return dt.strftime('%a, %d %b %Y %H:%M:%S %z')
    except Exception as e:
        print(f"Date parse error: {e}")
        return None

def generate_rss(dolar_info):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "DOF Indicador DOLAR"
    ET.SubElement(channel, "link").text = DOF_URL
    ET.SubElement(channel, "description").text = "Indicador DOLAR del Diario Oficial de la Federación"
    ET.SubElement(channel, "pubDate").text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')

    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = dolar_info["title"]

    # Parse pubdate from the XML
    pubdate_rfc822 = iso8601_to_rfc822(dolar_info.get("pubdate", "")) or iso8601_to_rfc822(dolar_info.get("valuedate", ""))
    if not pubdate_rfc822:
        pubdate_rfc822 = FALLBACK_DATE

    # Include pubdate in the description as well
    description_body = dolar_info["description"]
    if pubdate_rfc822:
        description_body += f" (Fecha de publicación: {pubdate_rfc822})"
    ET.SubElement(item, "description").text = description_body

    # Set pubDate as a direct child of the item (for RSSDog and RSS readers)
    ET.SubElement(item, "pubDate").text = pubdate_rfc822

    ET.SubElement(item, "guid").text = f"dof-dolar-{dolar_info['valuedate']}"

    tree = ET.ElementTree(rss)
    tree.write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    dolar = fetch_dolar_item()
    if dolar:
        generate_rss(dolar)
    else:
        print("No DOLAR indicator found.")
