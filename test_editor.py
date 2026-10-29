"""Prueba rapida: python test_editor.py"""
import os
import tempfile
from PIL import Image

from editor import Editor, copiar_campo

with tempfile.TemporaryDirectory() as tmp:
    png, jpg = os.path.join(tmp, "a.png"), os.path.join(tmp, "a.jpg")
    Image.new("RGB", (8, 8), "red").save(png)
    Image.new("RGB", (8, 8), "red").save(jpg)

    ed = Editor(png)
    ed.poner("Comment", "hola")
    ed.poner("Autor", "Sergio")
    ed.guardar(png)
    ed = Editor(png)
    assert ed.campos() == {"Comment": "hola", "Autor": "Sergio"}, ed.campos()
    ed.borrar("Autor")
    ed.guardar(png)
    assert Editor(png).campos() == {"Comment": "hola"}

    ed = Editor(jpg)
    ed.poner("Artist", "Sergio")
    ed.poner("Copyright", "2026")
    ed.guardar(jpg)
    assert Editor(jpg).campos() == {"Artist": "Sergio", "Copyright": "2026"}, Editor(jpg).campos()
    try:
        ed.poner("NoExiste", "x")
        raise AssertionError("deberia fallar")
    except KeyError:
        pass

    # Comment en JPEG (marcador COM) y borrado
    ed = Editor(jpg)
    ed.poner("Comment", "ci1:abc")
    ed.guardar(jpg)
    assert Editor(jpg).campos()["Comment"] == "ci1:abc"
    ed = Editor(jpg)
    ed.borrar("Comment")
    ed.guardar(jpg)
    assert "Comment" not in Editor(jpg).campos(), Editor(jpg).campos()

    # Copia en lote: PNG y JPEG ok, WEBP falla (sin Comment), copias _editado
    webp = os.path.join(tmp, "a.webp")
    Image.new("RGB", (8, 8)).save(webp)
    ok, errores = copiar_campo("Comment", "ci1:xyz", [png, jpg, webp], sobrescribir=False)
    assert ok == 2 and len(errores) == 1, (ok, errores)
    assert Editor(os.path.join(tmp, "a_editado.png")).campos()["Comment"] == "ci1:xyz"
    assert Editor(os.path.join(tmp, "a_editado.jpg")).campos()["Comment"] == "ci1:xyz"
    assert Editor(png).campos()["Comment"] == "hola"  # original intacto
    copiar_campo("Comment", "ci1:xyz", [png], sobrescribir=True)
    assert Editor(png).campos()["Comment"] == "ci1:xyz"
print("OK")
