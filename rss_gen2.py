import requests
import xml.etree.ElementTree as ET
from datetime import datetime

DOF_URL = "https://www.dof.gob.mx/indicadores.xml"
RSS_FILENAME = "dof_rss.xml"
RSS_TITLE = "Indicadores DOF"
RSS_LINK = DOF_URL
RSS_DESCRIPTION = "Indicadores económicos publicados por el Diario Oficial de la Federación."

def fetch_dof_xml():
    response = requests.get(DOF_URL)
    response.raise_for_status()
    return response.content

def parse_indicators(xml_data):
    root = ET.fromstring(xml_data)
    items = []
    for indicador in root.findall(".//indicador"):
        nombre = indicador.find("nombre").text.strip()
        valor = indicador.find("valor").text.strip()
        fecha = indicador.find("fecha").text.strip()

        # Formato para pubDate
        try:
            pub_date = datetime.strptime(fecha, "%d/%m/%Y")
            pub_date_str = pub_date.strftime("%a, %d %b %Y 00:00:00 GMT")
        except ValueError:
            pub_date_str = fecha  # fallback si el formato no es reconocible

        items.append({
            "title": nombre,
            "description": f"{nombre}: {valor}",
            "pubDate": pub_date_str,
            "guid": f"{nombre}-{fecha}".replace(" ", "-")
        })
    return items

def build_rss(items):
    rss_items = ""
    for item in items:
        rss_items += f"""
        <item>
            <title>{item["title"]}</title>
            <description>{item["description"]}</description>
            <pubDate>{item["pubDate"]}</pubDate>
            <guid>{item["guid"]}</guid>
        </item>
        """

    rss_feed = f"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
    <channel>
        <title>{RSS_TITLE}</title>
        <link>{RSS_LINK}</link>
        <description>{RSS_DESCRIPTION}</description>
        {rss_items}
    </channel>
    </rss>
    """
    return rss_feed

def save_rss(content):
    with open(RSS_FILENAME, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    xml_data = fetch_dof_xml()
    indicators = parse_indicators(xml_data)
    rss = build_rss(indicators)
    save_rss(rss)

if __name__ == "__main__":
    main()
