# Editor de metadatos de imagenes

Programa de escritorio para Windows (Python + Tkinter) que lee, edita y anade metadatos de imagenes, y copia un campo (por ejemplo `Comment`) de una imagen a muchas otras de una vez.

## Que hace

- Muestra todos los metadatos: formato, tamano, EXIF, GPS, campos de texto PNG y la lista de chunks PNG en crudo (incluidos los que Pillow ignora, como firmas C2PA `caBX`).
- Edita, anade y borra campos:
  - **PNG**: campos de texto con cualquier nombre (`Comment`, `prompt`, `Autor`...).
  - **JPEG**: `Comment` (marcador COM) y etiquetas EXIF estandar (`Artist`, `Copyright`, `ImageDescription`, `Software`, `DateTime`...).
  - **TIFF / WEBP**: etiquetas EXIF estandar.
- Copia un campo a varias imagenes en lote, sobrescribiendo los originales o creando copias `<nombre>_editado`.
- Guarda por defecto en un archivo nuevo y avisa si hay cambios sin guardar.

## Descarga

**[Descargar editor_metadatos.exe](https://github.com/Serberar/editor-metadatos/releases/latest/download/editor_metadatos.exe)** (Windows, no necesita Python).

Windows puede mostrar un aviso de SmartScreen porque el ejecutable no esta firmado: pulsa *Mas informacion* > *Ejecutar de todas formas*.

## Requisitos (para ejecutar desde el codigo)

- Python 3.10+
- [Pillow](https://pypi.org/project/pillow/)

```bash
pip install pillow
```

## Uso

Interfaz grafica:

```bash
python editor.py [imagen]
```

Solo leer metadatos desde la consola:

```bash
python metadata.py imagen1.png imagen2.jpg
```

### Copiar `Comment` a otras imagenes

1. Abre la imagen que tiene el campo.
2. Selecciona el campo en la tabla (si no seleccionas ninguno se usa `Comment`).
3. Pulsa **Copiar campo a otras imagenes...** y elige los destinos.
4. Elige si sobrescribir los originales o crear copias `_editado`.

## Crear el ejecutable (.exe)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name editor_metadatos editor.py
```

El ejecutable queda en `dist/editor_metadatos.exe`. Se puede abrir con doble clic o arrastrando una imagen encima.

## Tests

```bash
python test_editor.py
```

## Limitaciones

- Guardar un JPEG lo recomprime (con las mismas tablas de cuantizacion, la perdida es minima).
- Al guardar un PNG se pierden los chunks que Pillow no reconoce.
- No edita GPS ni los datos de camara del EXIF.
- Copiar un hash o firma (como `ci1:...`) a otra imagen no lo hace valido para esa imagen.
