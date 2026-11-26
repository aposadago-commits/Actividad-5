import os
import tkinter as tk
from enum import Enum
from tkinter import filedialog, ttk


# ---------------------------------------------------------------- Modelo
class TipoCargo(Enum):
    DIRECTIVO = "Directivo"
    ESTRATEGICO = "Estratégico"
    OPERATIVO = "Operativo"


class TipoGenero(Enum):
    MASCULINO = "Masculino"
    FEMENINO = "Femenino"


class Empleado:
    def __init__(self, nombre, apellidos, cargo, genero, salario_dia,
                 dias_trabajados, otros_ingresos, pagos_salud, aporte_pensiones):
        self.nombre = nombre
        self.apellidos = apellidos
        self.cargo = cargo
        self.genero = genero
        self.salario_dia = salario_dia
        self.dias_trabajados = dias_trabajados
        self.otros_ingresos = otros_ingresos
        self.pagos_salud = pagos_salud
        self.aporte_pensiones = aporte_pensiones

    def calcular_salario_mensual(self):
        """(días * sueldo por día) + otros ingresos - salud - pensiones."""
        return (self.dias_trabajados * self.salario_dia + self.otros_ingresos
                - self.pagos_salud - self.aporte_pensiones)


class Empresa:
    def __init__(self):
        self.empleados = []

    def agregar_empleado(self, empleado):
        self.empleados.append(empleado)

    def calcular_total_nomina(self):
        return sum(e.calcular_salario_mensual() for e in self.empleados)

    def guardar_archivo(self, carpeta):
        """Genera 'Nómina.txt' en la carpeta indicada y retorna su ruta."""
        ruta = os.path.join(carpeta, "Nómina.txt")
        with open(ruta, "w", encoding="utf-8") as f:
            for e in self.empleados:
                f.write(f"Nombre: {e.nombre} {e.apellidos}\n")
                f.write(f"Cargo: {e.cargo.value} | Género: {e.genero.value}\n")
                f.write(f"Salario por día: {e.salario_dia:.2f} | "
                        f"Días trabajados: {e.dias_trabajados}\n")
                f.write(f"Otros ingresos: {e.otros_ingresos:.2f} | "
                        f"Salud: {e.pagos_salud:.2f} | "
                        f"Pensiones: {e.aporte_pensiones:.2f}\n")
                f.write(f"Sueldo mensual: {e.calcular_salario_mensual():.2f}\n")
                f.write("------------------------------------\n")
            f.write(f"TOTAL NÓMINA: {self.calcular_total_nomina():.2f}\n")
        return ruta


# ------------------------------------------------------------------- GUI
class VentanaAgregarEmpleado(tk.Toplevel):
    """Diálogo modal para ingresar los datos de un empleado."""

    def __init__(self, padre, empresa):
        super().__init__(padre)
        self.title("Agregar empleado")
        self.resizable(False, False)
        self.empresa = empresa

        self.nombre = tk.StringVar()
        self.apellidos = tk.StringVar()
        self.salario = tk.StringVar()
        self.otros = tk.StringVar(value="0")
        self.salud = tk.StringVar(value="0")
        self.pension = tk.StringVar(value="0")
        self.masculino = tk.BooleanVar()
        self.femenino = tk.BooleanVar()

        marco = ttk.Frame(self, padding=12)
        marco.pack()

        def fila(r, texto, widget):
            ttk.Label(marco, text=texto).grid(row=r, column=0, sticky="w", pady=4, padx=(0, 10))
            widget.grid(row=r, column=1, sticky="ew", pady=4)

        fila(0, "Nombre:", ttk.Entry(marco, textvariable=self.nombre, width=25))
        fila(1, "Apellidos:", ttk.Entry(marco, textvariable=self.apellidos, width=25))

        self.lista_cargo = tk.Listbox(marco, height=3, exportselection=False)
        for c in TipoCargo:
            self.lista_cargo.insert(tk.END, c.value)
        self.lista_cargo.selection_set(0)
        fila(2, "Cargo:", self.lista_cargo)

        panel_genero = ttk.Frame(marco)
        ttk.Checkbutton(panel_genero, text="Masculino", variable=self.masculino,
                        command=lambda: self.femenino.set(False)).pack(side="left")
        ttk.Checkbutton(panel_genero, text="Femenino", variable=self.femenino,
                        command=lambda: self.masculino.set(False)).pack(side="left", padx=10)
        fila(3, "Género:", panel_genero)

        fila(4, "Salario por día:", ttk.Entry(marco, textvariable=self.salario, width=25))
        self.dias = ttk.Spinbox(marco, from_=1, to=31, width=6, state="readonly")
        self.dias.set(1)
        fila(5, "Días trabajados:", self.dias)
        fila(6, "Otros ingresos:", ttk.Entry(marco, textvariable=self.otros, width=25))
        fila(7, "Pagos por salud:", ttk.Entry(marco, textvariable=self.salud, width=25))
        fila(8, "Aporte pensiones:", ttk.Entry(marco, textvariable=self.pension, width=25))

        botones = ttk.Frame(marco)
        ttk.Button(botones, text="Guardar", command=self.guardar).pack(side="left", padx=5)
        ttk.Button(botones, text="Cancelar", command=self.destroy).pack(side="left", padx=5)
        botones.grid(row=9, column=0, columnspan=2, pady=(10, 0))

        self.transient(padre)
        self.grab_set()          # modal: bloquea la ventana principal
        self.wait_visibility()

    def guardar(self):
        nombre, apellidos = self.nombre.get().strip(), self.apellidos.get().strip()
        if not nombre or not apellidos:
            return
        if not (self.masculino.get() or self.femenino.get()):
            return
        try:
            salario = float(self.salario.get())
            otros = float(self.otros.get())
            salud = float(self.salud.get())
            pension = float(self.pension.get())
            if min(salario, otros, salud, pension) < 0:
                raise ValueError
        except ValueError:
            return
        cargo = list(TipoCargo)[self.lista_cargo.curselection()[0]]
        genero = TipoGenero.MASCULINO if self.masculino.get() else TipoGenero.FEMENINO
        self.empresa.agregar_empleado(Empleado(nombre, apellidos, cargo, genero, salario,
                                               int(self.dias.get()), otros, salud, pension))
        self.destroy()


class VentanaNomina(tk.Toplevel):
    """Tabla con nombre, apellidos y sueldo; total de la nómina abajo."""

    def __init__(self, padre, empresa):
        super().__init__(padre)
        self.title("Nómina de la empresa")
        self.geometry("450x300")

        tabla = ttk.Treeview(self, columns=("nombre", "apellidos", "sueldo"), show="headings")
        for col, texto in (("nombre", "Nombre"), ("apellidos", "Apellidos"), ("sueldo", "Sueldo")):
            tabla.heading(col, text=texto)
            tabla.column(col, anchor="center", width=140)
        for e in empresa.empleados:
            tabla.insert("", tk.END, values=(e.nombre, e.apellidos,
                                             f"$ {e.calcular_salario_mensual():,.2f}"))
        tabla.pack(fill="both", expand=True)

        ttk.Label(self, text=f"Total nómina: $ {empresa.calcular_total_nomina():,.2f}",
                  font=("TkDefaultFont", 11, "bold")).pack(pady=8)

        self.transient(padre)
        self.grab_set()


class VentanaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Nómina de empleados")
        self.geometry("420x250")
        self.empresa = Empresa()

        menu = tk.Menu(self)
        opciones = tk.Menu(menu, tearoff=0)
        opciones.add_command(label="Agregar empleado",
                             command=lambda: VentanaAgregarEmpleado(self, self.empresa))
        opciones.add_command(label="Calcular nómina", command=self.calcular_nomina)
        opciones.add_separator()
        opciones.add_command(label="Guardar archivo", command=self.guardar_archivo)
        menu.add_cascade(label="Opciones", menu=opciones)
        self.config(menu=menu)

        ttk.Label(self, text="Seleccione una opción del menú").pack(expand=True)

    def _sin_empleados(self):
        if not self.empresa.empleados:
            return True
        return False

    def calcular_nomina(self):
        if not self._sin_empleados():
            VentanaNomina(self, self.empresa)

    def guardar_archivo(self):
        if self._sin_empleados():
            return
        carpeta = filedialog.askdirectory(title="Seleccione la carpeta donde guardar Nómina.txt")
        if not carpeta:
            return
        try:
            self.empresa.guardar_archivo(carpeta)
        except OSError:
            return


if __name__ == "__main__":
    VentanaPrincipal().mainloop()