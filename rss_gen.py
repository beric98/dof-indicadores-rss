import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from xml.dom import minidom

url = "https://www.dof.gob.mx/indicadores.xml"
response = requests.get(url)
response.encoding = 'utf-8'
root = ET.fromstring(response.text)

rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")
ET.SubElement(channel, "title").text = "Indicadores DOF"
ET.SubElement(channel, "link").text = url
ET.SubElement(channel, "description").text = "Indicadores económicos publicados por el Diario Oficial de la Federación"

for item in root.findall("IndiceFecha"):
    titulo = item.find("titulo").text
    fecha = item.find("fecha").text
    dato = item.find("dato").text

    pub_date = datetime.strptime(fecha, "%d/%m/%Y").strftime("%a, %d %b %Y 00:00:00 GMT")

    rss_item = ET.SubElement(channel, "item")
    ET.SubElement(rss_item, "title").text = f"{titulo} - {dato}"
    ET.SubElement(rss_item, "description").text = f"Indicador: {titulo}<br/>Valor: {dato}<br/>Fecha: {fecha}"
    ET.SubElement(rss_item, "pubDate").text = pub_date
    ET.SubElement(rss_item, "guid").text = f"{titulo}-{fecha.replace('/', '-')}".replace(" ", "_")

rough_string = ET.tostring(rss, 'utf-8')
reparsed = minidom.parseString(rough_string)
rss_pretty = reparsed.toprettyxml(indent="  ")

with open("dof_rss.xml", "w", encoding="utf-8") as f:
    f.write(rss_pretty)
