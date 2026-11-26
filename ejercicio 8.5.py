import tkinter as tk
from datetime import datetime
from tkinter import messagebox, simpledialog, ttk

FORMATO_FECHA = "%d/%m/%Y"


def leer_fecha(texto):
    """Retorna un datetime o None si el texto no es una fecha dd/mm/aaaa válida."""
    try:
        return datetime.strptime(texto.strip(), FORMATO_FECHA)
    except ValueError:
        return None


# ---------------------------------------------------------------- Modelo
class Huesped:
    def __init__(self, nombre, apellidos, documento):
        self.nombre = nombre
        self.apellidos = apellidos
        self.documento = documento

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellidos}"


class Habitacion:
    def __init__(self, numero, precio_dia):
        self.numero = numero
        self.precio_dia = precio_dia
        self.huesped = None
        self.fecha_ingreso = None

    @property
    def disponible(self):
        return self.huesped is None

    def ocupar(self, huesped, fecha_ingreso):
        self.huesped = huesped
        self.fecha_ingreso = fecha_ingreso

    def liberar(self):
        self.huesped = None
        self.fecha_ingreso = None

    def calcular_dias(self, fecha_salida):
        return (fecha_salida - self.fecha_ingreso).days

    def calcular_total(self, fecha_salida):
        return self.calcular_dias(fecha_salida) * self.precio_dia


class Hotel:
    """Diez habitaciones: 1-5 a $120.000 y 6-10 a $160.000 por día."""

    def __init__(self):
        self.habitaciones = [Habitacion(i + 1, 120_000 if i < 5 else 160_000)
                             for i in range(10)]

    def buscar(self, numero):
        return self.habitaciones[numero - 1] if 1 <= numero <= len(self.habitaciones) else None


# ------------------------------------------------------------------- GUI
def pedir_numero(ventana, texto):
    """Convierte texto a int; muestra error y retorna None si no es válido."""
    try:
        return int(texto.strip())
    except ValueError:
        messagebox.showerror("Dato incorrecto", "Ingrese un número de habitación válido.",
                             parent=ventana)
        return None


class VentanaHabitaciones(tk.Toplevel):
    """Muestra las 10 habitaciones (grid de 5x2) y permite elegir una para ocuparla."""

    def __init__(self, padre, hotel):
        super().__init__(padre)
        self.title("Consultar habitaciones")
        self.padre, self.hotel = padre, hotel

        rejilla = tk.Frame(self, padx=10, pady=10)
        rejilla.pack()
        for i, h in enumerate(hotel.habitaciones):
            estado = "Disponible" if h.disponible else "No disponible"
            color = "#c8ebc8" if h.disponible else "#f0c8c8"
            tk.Label(rejilla, bg=color, justify="left", padx=8, pady=6, width=28, anchor="w",
                     text=f"Habitación {h.numero} (${h.precio_dia:,.0f}/día)\n{estado}"
                     ).grid(row=i % 5, column=i // 5, padx=5, pady=5)

        sur = ttk.Frame(self, padding=(10, 0, 10, 10))
        sur.pack()
        ttk.Label(sur, text="Número de habitación:").pack(side="left")
        self.numero = tk.StringVar()
        ttk.Entry(sur, textvariable=self.numero, width=6).pack(side="left", padx=6)
        ttk.Button(sur, text="Ocupar habitación", command=self.seleccionar).pack(side="left")

        self.transient(padre)
        self.grab_set()

    def seleccionar(self):
        numero = pedir_numero(self, self.numero.get())
        if numero is None:
            return
        h = self.hotel.buscar(numero)
        if h is None:
            messagebox.showerror("Error", f"La habitación {numero} no existe (1 a 10).", parent=self)
        elif not h.disponible:
            messagebox.showerror("Habitación no disponible",
                                 f"La habitación {numero} está ocupada.", parent=self)
        else:
            self.destroy()
            VentanaRegistro(self.padre, h)


class VentanaRegistro(tk.Toplevel):
    """Registro del huésped (usa el administrador grid). Campos obligatorios."""

    def __init__(self, padre, habitacion):
        super().__init__(padre)
        self.title(f"Registro de huésped - Habitación {habitacion.numero}")
        self.resizable(False, False)
        self.habitacion = habitacion
        self.vars = {k: tk.StringVar() for k in ("fecha", "nombre", "apellidos", "documento")}

        marco = ttk.Frame(self, padding=12)
        marco.pack()
        etiquetas = (("fecha", "Fecha de ingreso (dd/mm/aaaa):"), ("nombre", "Nombre:"),
                     ("apellidos", "Apellidos:"), ("documento", "Documento de identidad:"))
        for r, (clave, texto) in enumerate(etiquetas):
            ttk.Label(marco, text=texto).grid(row=r, column=0, sticky="w", pady=5, padx=(0, 10))
            ttk.Entry(marco, textvariable=self.vars[clave], width=22).grid(row=r, column=1, pady=5)
        ttk.Button(marco, text="Registrar", command=self.registrar).grid(
            row=len(etiquetas), column=0, columnspan=2, pady=(10, 0))

        self.transient(padre)
        self.grab_set()

    def registrar(self):
        v = {k: var.get().strip() for k, var in self.vars.items()}
        if not all(v.values()):
            messagebox.showwarning("Datos incompletos", "Todos los campos son obligatorios.",
                                   parent=self)
            return
        fecha = leer_fecha(v["fecha"])
        if fecha is None:
            messagebox.showerror("Fecha incorrecta",
                                 "La fecha no es válida. Use el formato dd/mm/aaaa.", parent=self)
            return
        if not v["documento"].isdigit():
            messagebox.showerror("Documento incorrecto",
                                 "El documento debe contener solo números.", parent=self)
            return
        self.habitacion.ocupar(Huesped(v["nombre"], v["apellidos"], v["documento"]), fecha)
        messagebox.showinfo("Registro exitoso",
                            f"Huésped registrado en la habitación {self.habitacion.numero}.",
                            parent=self)
        self.destroy()


class VentanaSalida(tk.Toplevel):
    """Salida del huésped: valida fecha, calcula total y libera la habitación."""

    def __init__(self, padre, habitacion):
        super().__init__(padre)
        self.title(f"Salida de huésped - Habitación {habitacion.numero}")
        self.geometry("430x300")
        self.habitacion = habitacion

        info = ttk.Frame(self, padding=(12, 10, 12, 5))
        info.pack(fill="x")
        for texto in (f"Habitación: {habitacion.numero}  (precio por día: ${habitacion.precio_dia:,.0f})",
                      f"Huésped: {habitacion.huesped.nombre_completo}",
                      f"Documento: {habitacion.huesped.documento}",
                      f"Fecha de ingreso: {habitacion.fecha_ingreso.strftime(FORMATO_FECHA)}"):
            ttk.Label(info, text=texto).pack(anchor="w")

        centro = ttk.Frame(self, padding=(12, 5))
        centro.pack(fill="x")
        ttk.Label(centro, text="Fecha de salida (dd/mm/aaaa):").pack(side="left")
        self.fecha = tk.StringVar()
        ttk.Entry(centro, textvariable=self.fecha, width=12).pack(side="left", padx=6)

        self.resultado = ttk.Label(self, text="", padding=(12, 5), font=("TkDefaultFont", 10, "bold"))
        self.resultado.pack(anchor="w")

        botones = ttk.Frame(self, padding=10)
        botones.pack(side="bottom")
        self.btn_calcular = ttk.Button(botones, text="Calcular total", command=self.calcular,
                                       state="disabled")
        self.btn_registrar = ttk.Button(botones, text="Registrar salida",
                                        command=self.registrar_salida, state="disabled")
        self.btn_calcular.pack(side="left", padx=5)
        self.btn_registrar.pack(side="left", padx=5)

        # "Calcular" solo se habilita si la fecha es válida y posterior al ingreso
        self.fecha.trace_add("write", lambda *_: self.validar_fecha())

        self.transient(padre)
        self.grab_set()

    def _fecha_valida(self):
        f = leer_fecha(self.fecha.get())
        return f if f is not None and f > self.habitacion.fecha_ingreso else None

    def validar_fecha(self):
        self.btn_calcular.config(state="normal" if self._fecha_valida() else "disabled")
        self.btn_registrar.config(state="disabled")   # si cambia la fecha hay que recalcular
        self.resultado.config(text="")

    def calcular(self):
        salida = self._fecha_valida()
        self.resultado.config(
            text=f"Días de alojamiento: {self.habitacion.calcular_dias(salida)}\n"
                 f"Total a pagar: ${self.habitacion.calcular_total(salida):,.0f}")
        self.btn_registrar.config(state="normal")

    def registrar_salida(self):
        self.habitacion.liberar()
        messagebox.showinfo("Salida exitosa",
                            "Salida registrada. La habitación quedó disponible.", parent=self)
        self.destroy()


class VentanaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestión de hotel")
        self.geometry("400x250")
        self.hotel = Hotel()

        menu = tk.Menu(self)
        opciones = tk.Menu(menu, tearoff=0)
        opciones.add_command(label="Consultar habitaciones",
                             command=lambda: VentanaHabitaciones(self, self.hotel))
        opciones.add_command(label="Salida de huéspedes", command=self.solicitar_salida)
        menu.add_cascade(label="Opciones", menu=opciones)
        self.config(menu=menu)

        ttk.Label(self, text="Seleccione una opción del menú").pack(expand=True)

    def solicitar_salida(self):
        texto = simpledialog.askstring("Salida de huéspedes",
                                       "Número de habitación a entregar:", parent=self)
        if texto is None:       # el usuario canceló
            return
        numero = pedir_numero(self, texto)
        if numero is None:
            return
        h = self.hotel.buscar(numero)
        if h is None:
            messagebox.showerror("Error", f"La habitación {numero} no existe (1 a 10).")
        elif h.disponible:
            messagebox.showerror("Error", f"La habitación {numero} no está ocupada.")
        else:
            VentanaSalida(self, h)


if __name__ == "__main__":
    VentanaPrincipal().mainloop()