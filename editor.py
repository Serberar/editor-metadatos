"""Lee, edita y anade metadatos de una imagen.

PNG: campos de texto (tEXt/iTXt, p.ej. Comment). JPEG/TIFF/WEBP: etiquetas EXIF
basicas (Artist, Copyright, ImageDescription, Software, DateTime...).

Uso: editor_metadatos.exe [imagen]  (o arrastrar la imagen sobre el exe)
"""
import io
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ExifTags, ImageTk, PngImagePlugin

from metadata import leer_metadatos

EXIF_POR_NOMBRE = {t.name: t.value for t in ExifTags.Base}


class Editor:
    def __init__(self, ruta):
        self.ruta = ruta
        # Abrir desde memoria: no bloquea el archivo (permite sobrescribirlo) y conserva
        # el tipo JPEG que necesita quality="keep".
        with open(ruta, "rb") as f:
            img = Image.open(io.BytesIO(f.read()))
        img.load()
        self.img = img
        self.formato = img.format
        self.exif = img.getexif()
        self.icc = img.info.get("icc_profile")
        self.texto = dict(getattr(img, "text", {})) if img.format == "PNG" else None
        # JPEG guarda "Comment" en su marcador COM, no en EXIF.
        com = img.info.get("comment") if img.format == "JPEG" else None
        self.comentario = com.decode("utf-8", "replace") if isinstance(com, bytes) else com

    def campos(self):
        if self.texto is not None:
            return dict(self.texto)
        campos = {ExifTags.TAGS.get(k, k): v for k, v in self.exif.items()}
        if self.comentario:
            campos["Comment"] = self.comentario
        return campos

    def poner(self, clave, valor):
        if self.texto is not None:
            self.texto[clave] = valor
        elif clave == "Comment" and self.formato == "JPEG":
            self.comentario = valor
        elif clave in EXIF_POR_NOMBRE:
            self.exif[EXIF_POR_NOMBRE[clave]] = valor
        else:
            raise KeyError(f"'{clave}' no es una etiqueta EXIF valida (ej: Artist, Copyright, ImageDescription)")

    def borrar(self, clave):
        if self.texto is not None:
            del self.texto[clave]
        elif clave == "Comment" and self.comentario:
            self.comentario = ""
        else:
            del self.exif[EXIF_POR_NOMBRE[clave]]

    def guardar(self, destino):
        opciones = {"exif": self.exif} if len(self.exif) else {}
        if self.icc:
            opciones["icc_profile"] = self.icc
        if self.texto is not None:
            info = PngImagePlugin.PngInfo()
            for k, v in self.texto.items():
                info.add_text(k, v)
            opciones["pnginfo"] = info
        elif self.formato == "JPEG":
            # Reutiliza las tablas de cuantizacion: minima perdida al recomprimir.
            opciones["quality"] = "keep"
            if self.comentario is not None:
                opciones["comment"] = self.comentario
        self.img.save(destino, format=self.formato, **opciones)


def copiar_campo(clave, valor, rutas, sobrescribir):
    """Escribe clave=valor en cada imagen. Devuelve (n_ok, lista_errores)."""
    ok, errores = 0, []
    for ruta in rutas:
        try:
            ed = Editor(ruta)
            ed.poner(clave, valor)
            base, ext = os.path.splitext(ruta)
            ed.guardar(ruta if sobrescribir else f"{base}_editado{ext}")
            ok += 1
        except (KeyError, OSError, ValueError) as e:
            errores.append(f"{os.path.basename(ruta)}: {e}")
    return ok, errores


class App(tk.Tk):
    def __init__(self, ruta=None):
        super().__init__()
        self.title("Editor de metadatos")
        self.geometry("1100x700")
        self.ed = None
        self.ruta = None
        self.cambios = False

        barra = ttk.Frame(self, padding=4)
        barra.pack(fill="x")
        ttk.Button(barra, text="Abrir imagen...", command=self.abrir).pack(side="left")
        self.btn_guardar = ttk.Button(barra, text="Guardar como...", command=self.guardar, state="disabled")
        self.btn_guardar.pack(side="left", padx=4)
        self.btn_copiar = ttk.Button(barra, text="Copiar campo a otras imagenes...", command=self.copiar_a_otras,
                                     state="disabled")
        self.btn_copiar.pack(side="left")
        self.lbl_ruta = ttk.Label(barra, text="Ninguna imagen abierta")
        self.lbl_ruta.pack(side="left", padx=8)

        panel = ttk.PanedWindow(self, orient="horizontal")
        panel.pack(fill="both", expand=True, padx=4, pady=4)

        # Izquierda: vista previa + todos los metadatos (solo lectura)
        izq = ttk.Frame(panel)
        panel.add(izq, weight=1)
        self.preview = ttk.Label(izq, anchor="center")
        self.preview.pack(fill="x", pady=4)
        ttk.Label(izq, text="Todos los metadatos (solo lectura)").pack(anchor="w")
        self.txt_info = tk.Text(izq, wrap="word", state="disabled", height=10)
        self.txt_info.pack(fill="both", expand=True)

        # Derecha: campos editables
        der = ttk.Frame(panel)
        panel.add(der, weight=2)
        self.lbl_campos = ttk.Label(der, text="Campos editables")
        self.lbl_campos.pack(anchor="w")
        self.tabla = ttk.Treeview(der, columns=("valor",), height=10)
        self.tabla.heading("#0", text="Campo")
        self.tabla.heading("valor", text="Valor")
        self.tabla.column("#0", width=160, stretch=False)
        self.tabla.bind("<<TreeviewSelect>>", self.seleccionar)

        form = ttk.Frame(der, padding=(0, 6))
        form.pack(side="bottom", fill="x")  # antes que la tabla: no se corta al encoger la ventana
        self.tabla.pack(fill="both", expand=True)
        ttk.Label(form, text="Campo:").grid(row=0, column=0, sticky="w")
        self.ent_clave = ttk.Entry(form)
        self.ent_clave.grid(row=0, column=1, sticky="ew")
        ttk.Label(form, text="Valor:").grid(row=1, column=0, sticky="nw")
        self.txt_valor = tk.Text(form, height=6, wrap="word")
        self.txt_valor.grid(row=1, column=1, sticky="ew", pady=4)
        form.columnconfigure(1, weight=1)
        botones = ttk.Frame(form)
        botones.grid(row=2, column=1, sticky="e")
        ttk.Button(botones, text="Nuevo", command=self.limpiar).pack(side="left")
        ttk.Button(botones, text="Aplicar (anadir/editar)", command=self.aplicar).pack(side="left", padx=4)
        ttk.Button(botones, text="Borrar campo", command=self.borrar).pack(side="left")

        self.protocol("WM_DELETE_WINDOW", self.salir)
        if ruta:
            self.cargar(ruta)

    def abrir(self):
        if self.cambios and not messagebox.askyesno("Cambios sin guardar", "Descartar los cambios?"):
            return
        ruta = self.dialogo_imagenes()
        if ruta:
            self.cargar(ruta)

    def cargar(self, ruta):
        try:
            self.ed = Editor(ruta)
        except (OSError, ValueError) as e:
            messagebox.showerror("Error", f"No se pudo abrir la imagen:\n{e}")
            return
        self.ruta = ruta
        self.cambios = False
        self.lbl_ruta.config(text=ruta)
        self.btn_guardar.config(state="normal")
        self.btn_copiar.config(state="normal")
        self.lbl_campos.config(text="Campos de texto PNG (nombre libre)" if self.ed.texto is not None
                               else "Etiquetas EXIF (Artist, Copyright, ImageDescription, Software...)")
        miniatura = self.ed.img.copy()
        miniatura.thumbnail((350, 250))
        self.foto = ImageTk.PhotoImage(miniatura)  # referencia necesaria o Tk la borra
        self.preview.config(image=self.foto)
        self.mostrar_info(ruta)
        self.refrescar()

    def mostrar_info(self, ruta):
        lineas = []
        for k, v in leer_metadatos(ruta).items():
            if isinstance(v, bytes):
                v = v[:80].decode("utf-8", "replace")
            lineas.append(f"{k}: {v}")
        self.txt_info.config(state="normal")
        self.txt_info.delete("1.0", "end")
        self.txt_info.insert("1.0", "\n\n".join(lineas))
        self.txt_info.config(state="disabled")

    def refrescar(self):
        self.tabla.delete(*self.tabla.get_children())
        for k, v in self.ed.campos().items():
            self.tabla.insert("", "end", iid=str(k), text=str(k), values=(str(v).replace("\n", " ")[:300],))
        self.title(f"Editor de metadatos{' *' if self.cambios else ''}")

    def seleccionar(self, _evento):
        sel = self.tabla.selection()
        if not sel:
            return
        self.limpiar()
        self.ent_clave.insert(0, sel[0])
        self.txt_valor.insert("1.0", str(self.ed.campos().get(sel[0], "")))

    def limpiar(self):
        self.ent_clave.delete(0, "end")
        self.txt_valor.delete("1.0", "end")

    def aplicar(self):
        clave = self.ent_clave.get().strip()
        if not self.ed or not clave:
            return
        try:
            self.ed.poner(clave, self.txt_valor.get("1.0", "end-1c"))
        except KeyError as e:
            messagebox.showerror("Campo no valido", str(e))
            return
        self.cambios = True
        self.refrescar()

    def borrar(self):
        clave = self.ent_clave.get().strip()
        if not self.ed or not clave:
            return
        try:
            self.ed.borrar(clave)
        except KeyError:
            messagebox.showerror("Error", f"El campo '{clave}' no existe")
            return
        self.cambios = True
        self.limpiar()
        self.refrescar()

    def guardar(self):
        base, ext = os.path.splitext(self.ruta)
        destino = filedialog.asksaveasfilename(  # el dialogo ya pide confirmar si sobrescribe
            initialdir=os.path.dirname(self.ruta), initialfile=os.path.basename(f"{base}_editado{ext}"),
            defaultextension=ext, filetypes=[(ext.upper().lstrip("."), f"*{ext}")])
        if not destino:
            return
        try:
            self.ed.guardar(destino)
        except (OSError, ValueError) as e:
            messagebox.showerror("Error al guardar", str(e))
            return
        messagebox.showinfo("Guardado", f"Guardado en:\n{destino}")
        self.cargar(destino)

    def copiar_a_otras(self):
        clave = self.ent_clave.get().strip() or "Comment"
        valor = self.ed.campos().get(clave)
        if valor is None:
            messagebox.showerror("Error", f"La imagen actual no tiene el campo '{clave}'.\n"
                                 "Selecciona en la tabla el campo que quieres copiar.")
            return
        rutas = self.dialogo_imagenes(multiple=True)
        if not rutas:
            return
        resp = messagebox.askyesnocancel(
            "Copiar campo",
            f"Copiar '{clave}' = {str(valor)[:100]}\na {len(rutas)} imagen(es).\n\n"
            "Si: sobrescribir los archivos originales\nNo: crear copias <nombre>_editado\nCancelar: no hacer nada")
        if resp is None:
            return
        ok, errores = copiar_campo(clave, valor, rutas, sobrescribir=resp)
        msg = f"Copiado en {ok} de {len(rutas)} imagen(es)."
        if errores:
            messagebox.showwarning("Copiar campo", msg + "\n\nErrores:\n" + "\n".join(errores))
        else:
            messagebox.showinfo("Copiar campo", msg)

    def dialogo_imagenes(self, multiple=False):
        tipos = [("Imagenes", "*.png *.jpg *.jpeg *.tif *.tiff *.webp"), ("Todos", "*.*")]
        if multiple:
            return filedialog.askopenfilenames(title="Imagenes de destino", filetypes=tipos)
        return filedialog.askopenfilename(filetypes=tipos)

    def salir(self):
        if self.cambios and not messagebox.askyesno("Cambios sin guardar", "Salir sin guardar?"):
            return
        self.destroy()


if __name__ == "__main__":
    App(sys.argv[1] if len(sys.argv) > 1 else None).mainloop()
