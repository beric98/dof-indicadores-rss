"""Copia el indicador DOLAR del DOF (https://www.dof.gob.mx/indicadores.xml) a dof_rss.xml.

Lo lee el ERP de Paraíso Mahahual (getExchangeRateFromDOFRss()) como segunda vía para
saber si hoy hubo publicación del tipo de cambio en el DOF, cuando el ERP no logra leer
el DOF directo.

Además del item DOLAR, el canal guarda:
  - <checkedAt>: hora (Ciudad de México, ISO 8601) de la última lectura EXITOSA del DOF.
  - <dofDolarHoy>: "si" si el DOF traía el dólar publicado ese día, "no" si no.

Así un día sin publicación (inhábil bancario) queda escrito como «revisé a las 07:40 y
no hay dólar de hoy», y ya no se confunde con «la tarea no corrió». Si el DOF no
responde, el script no escribe nada: el ERP ve una revisión vieja y no concluye
nada.

Para no llenar el repositorio de commits, el archivo solo se reescribe cuando cambia el
dólar, cuando es la primera revisión del día, o cuando la revisión guardada dice que no
hay dólar de hoy y es de antes de las 07:30 (TRUSTED_FROM: hora a partir de la cual el
ERP confía en un «no hay»).
"""
import os
import sys
from datetime import datetime
from email.utils import format_datetime
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DOF_URL = "https://www.dof.gob.mx/indicadores.xml"
OUTPUT_FILE = "dof_rss.xml"
MX = ZoneInfo("America/Mexico_City")
TRUSTED_FROM = "07:30"  # debe coincidir con FIX_MIRROR_MIN_CHECK del ERP


def fetch_dof():
    """Item DOLAR del DOF, o None si el DOF respondió sin él.

    Lanza excepción si el DOF no respondió con un XML de indicadores: en ese caso no
    hay que escribir nada.
    """
    # verify=False como siempre: el certificado del DOF no siempre valida.
    resp = requests.get(DOF_URL, verify=False, timeout=30)
    resp.raise_for_status()
    tree = ET.fromstring(resp.content)
    items = tree.findall(".//item")
    if not items:
        raise RuntimeError("el DOF respondió sin indicadores")
    for item in items:
        if item.findtext("title", "").strip().upper() == "DOLAR":
            pubdate = item.findtext("pubDate")
            if pubdate is None:
                pubdate = item.findtext("pubdate", "")
            return {
                "description": item.findtext("description", "").strip(),
                "valuedate": item.findtext("valuedate", "").strip(),
                "pubdate": pubdate.strip(),
            }
    return None


def previous_feed():
    if not os.path.exists(OUTPUT_FILE):
        return None
    try:
        channel = ET.parse(OUTPUT_FILE).getroot().find("channel")
    except ET.ParseError:
        return None
    if channel is None:
        return None
    item = channel.find("item")
    dolar = None
    if item is not None:
        dolar = {
            "description": item.findtext("description", "").split(" (Fecha de publicación")[0].strip(),
            "valuedate": item.findtext("guid", "").replace("dof-dolar-", "", 1),
            "pubdate": item.findtext("pubDate", "").strip(),
        }
    return {
        "dolar": dolar,
        "checked_at": channel.findtext("checkedAt", "") or "",
        "dolar_hoy": channel.findtext("dofDolarHoy", "") == "si",
    }


def pub_day(pubdate):
    try:
        return datetime.strptime(pubdate, "%a, %d %b %Y %H:%M:%S %z").strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return ""


def write_feed(dolar, now):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "DOF Indicador DOLAR"
    ET.SubElement(channel, "link").text = DOF_URL
    ET.SubElement(channel, "description").text = "Indicador DOLAR del Diario Oficial de la Federación"
    ET.SubElement(channel, "pubDate").text = format_datetime(now)
    ET.SubElement(channel, "checkedAt").text = now.isoformat(timespec="minutes")
    hoy = dolar is not None and pub_day(dolar["pubdate"]) == now.strftime("%Y-%m-%d")
    ET.SubElement(channel, "dofDolarHoy").text = "si" if hoy else "no"

    if dolar:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = "DOLAR"
        if dolar["pubdate"]:
            ET.SubElement(item, "pubDate").text = dolar["pubdate"]
            body = f"{dolar['description']} (Fecha de publicación: {dolar['pubdate']})"
        else:
            body = dolar["description"]
        ET.SubElement(item, "description").text = body
        ET.SubElement(item, "guid").text = f"dof-dolar-{dolar['valuedate']}"

    ET.ElementTree(rss).write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)


def main():
    now = datetime.now(MX).replace(second=0, microsecond=0)
    try:
        dolar = fetch_dof()
    except Exception as exc:  # noqa: BLE001 — cualquier falla del DOF: no escribir
        # Sin fallar la tarea: GitHub mandaría un correo por cada corrida. El ERP ve
        # una revisión vieja y no concluye nada.
        print(f"El DOF no respondió: {exc}")
        return 0

    prev = previous_feed()
    if dolar is None:
        print("El DOF respondió sin el dólar (día sin publicación).")
        # Se conserva el último publicado para que el feed siga trayendo un valor.
        dolar = prev["dolar"] if prev else None

    prev_checked = prev["checked_at"] if prev else ""
    checked_today = prev_checked[:10] == now.strftime("%Y-%m-%d")
    checked_trusted = checked_today and prev_checked[11:16] >= TRUSTED_FROM
    now_trusted = now.strftime("%H:%M") >= TRUSTED_FROM
    same_dolar = bool(prev) and prev["dolar"] == dolar

    # Un «sí hay dólar de hoy» vale a cualquier hora; un «no hay» solo desde TRUSTED_FROM.
    if same_dolar and checked_today and (checked_trusted or not now_trusted or prev["dolar_hoy"]):
        print("Sin cambios: el feed ya tiene la revisión de hoy.")
        return 0

    write_feed(dolar, now)
    print("Feed actualizado:", now.isoformat(timespec="minutes"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
