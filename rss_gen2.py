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
            # Try both pubDate and pubdate, as XML tag may be case sensitive
            pubdate = item.findtext("pubDate")
            if pubdate is None:
                pubdate = item.findtext("pubdate", "").strip()
            else:
                pubdate = pubdate.strip()
            return {
                "title": title,
                "description": description,
                "valuedate": valuedate,
                "pubdate": pubdate
            }
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

    pubdate = dolar_info.get("pubdate", "")
    if pubdate:
        ET.SubElement(item, "pubDate").text = pubdate
        description_body = f"{dolar_info['description']} (Fecha de publicación: {pubdate})"
    else:
        # If no pubdate, just show description without date info
        description_body = dolar_info["description"]

    ET.SubElement(item, "description").text = description_body
    ET.SubElement(item, "guid").text = f"dof-dolar-{dolar_info['valuedate']}"

    tree = ET.ElementTree(rss)
    tree.write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    dolar = fetch_dolar_item()
    if dolar:
        generate_rss(dolar)
    else:
        print("No DOLAR indicator found.")
