"""Lee los metadatos de una imagen (info basica, EXIF, GPS y chunks de texto PNG).

Uso: python metadata.py <imagen> [<imagen> ...]
"""
import sys
from PIL import Image, ExifTags


def leer_metadatos(ruta):
    with Image.open(ruta) as img:
        datos = {
            "Formato": img.format,
            "Modo": img.mode,
            "Tamano": f"{img.width}x{img.height}",
        }
        # img.info incluye chunks de texto PNG, dpi, icc_profile, etc.
        for k, v in img.info.items():
            if k in ("exif", "icc_profile"):
                v = f"<{len(v)} bytes>"
            datos[f"Info.{k}"] = v

        exif = img.getexif()
        for tag, v in exif.items():
            datos[f"EXIF.{ExifTags.TAGS.get(tag, tag)}"] = v
        # Sub-IFDs: Exif (camara, fechas) y GPS
        for tag, v in exif.get_ifd(ExifTags.IFD.Exif).items():
            datos[f"EXIF.{ExifTags.TAGS.get(tag, tag)}"] = v
        for tag, v in exif.get_ifd(ExifTags.IFD.GPSInfo).items():
            datos[f"GPS.{ExifTags.GPSTAGS.get(tag, tag)}"] = v
        if img.format == "PNG":
            datos["PNG.chunks"] = chunks_png(ruta)
    return datos


def chunks_png(ruta):
    # Pillow ignora chunks desconocidos (p.ej. caBX de C2PA); se listan en crudo.
    with open(ruta, "rb") as f:
        d = f.read()
    i, tipos = 8, []
    while i + 8 <= len(d):
        n = int.from_bytes(d[i:i + 4], "big")
        tipo = d[i + 4:i + 8].decode("latin1")
        if not tipos or tipos[-1][0] != tipo:
            tipos.append([tipo, 0, 0])
        tipos[-1][1] += 1
        tipos[-1][2] += n
        i += 12 + n
    res = ", ".join(f"{t}x{c} ({b} B)" if c > 1 else f"{t} ({b} B)" for t, c, b in tipos)
    if i < len(d):
        res += f", datos tras IEND: {len(d) - i} B"
    return res


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for ruta in sys.argv[1:]:
        print(f"== {ruta} ==")
        try:
            datos = leer_metadatos(ruta)
        except (OSError, ValueError) as e:
            print(f"  Error: {e}")
            continue
        for k, v in datos.items():
            if isinstance(v, bytes):
                v = v[:80].decode("utf-8", "replace")
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
