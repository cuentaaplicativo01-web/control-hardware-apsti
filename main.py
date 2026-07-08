import flet as ft
import serial
import serial.tools.list_ports
import time
import threading

def main(page: ft.Page):
    # --- CONFIGURACIÓN DE LA PÁGINA ---
    page.title = "Control LED RGB - TECNOTRONIC"
    page.bgcolor = "#121214" # Fondo oscuro del dashboard de la imagen
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    
    page.window_width = 440
    page.window_height = 850
    page.window_resizable = False

    # --- VARIABLE GLOBAL DE CONEXIÓN Y ESTADO ---
    page.data = {
        "arduino": None,
        "continuar_leyendo": False
    }

    # --- HILO EN SEGUNDO PLANO PARA LEER EL SENSOR LDR ---
    def recibir_datos_arduino():
        while page.data["continuar_leyendo"]:
            arduino = page.data["arduino"]
            if arduino and arduino.is_open:
                try:
                    if arduino.in_waiting > 0:
                        linea = arduino.readline().decode().strip()
                        if linea.startswith("LDR:"):
                            valor_ldr = int(linea.split(":")[1])
                            
                            porcentaje = (valor_ldr / 1023.0)
                            
                            # Ajuste dinámico de la barra vertical simulada (Alto máx: 80)
                            alto_dinamico = int(porcentaje * 80)
                            ldr_bar_fill.height = alto_dinamico
                            
                            ldr_text.value = f"--% ({valor_ldr})" if valor_ldr == 0 else f"{int(porcentaje * 100)}% ({valor_ldr})"
                            
                            if valor_ldr < 300:
                                ldr_status.value = "ESTADO:\nDESCONECTADO" if valor_ldr == 0 else "ESTADO:\nOSCURO"
                                ldr_status.color = "red"
                            else:
                                ldr_status.value = "ESTADO:\nILUMINADO"
                                ldr_status.color = "green"
                                
                            page.update()
                except Exception:
                    pass
            time.sleep(0.1)

    # --- LÓGICA DE COMUNICACIÓN SERIE ---
    def buscar_y_conectar(e):
        status_text.value = "ESTADO: BUSCANDO HARDWARE..."
        page.update()
        
        ports = list(serial.tools.list_ports.comports())
        found_port = None
        
        for port in ports:
            if "arduino" in port.description.lower() or "ch340" in port.description.lower() or "usb" in port.description.lower():
                found_port = port.device
                break
                
        if found_port:
            try:
                page.data["arduino"] = serial.Serial(found_port, 9600, timeout=1)
                time.sleep(2) 
                status_text.value = f"ESTADO: CONECTADO ({found_port})"
                btn_conectar.text = "CONECTADO"
                btn_conectar.disabled = True
                
                if switch_zumbador.value:
                    enviar_comando("BUZZER_ON")
                else:
                    enviar_comando("BUZZER_OFF")
                
                page.data["continuar_leyendo"] = True
                hilo = threading.Thread(target=recibir_datos_arduino, daemon=True)
                hilo.start()
            except Exception:
                status_text.value = "ESTADO: ERROR DE APERTURA"
        else:
            status_text.value = "ESTADO: DESCONECTADO"
            
        page.update()

    def enviar_comando(comando):
        arduino = page.data["arduino"]
        if arduino and arduino.is_open:
            try:
                arduino.write(f"{comando}\n".encode())
            except Exception:
                status_text.value = "ESTADO: CONEXIÓN PERDIDA"
                page.data["continuar_leyendo"] = False
                page.update()

    def actualizar_color(e):
        r = int(slider_r.value)
        g = int(slider_g.value)
        b = int(slider_b.value)
        
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        preview_box.bgcolor = hex_color
        
        if switch_hardware.value:
            enviar_comando(f"{255-r},{255-g},{255-b}")
        else:
            enviar_comando(f"{r},{g},{b}")
            
        preview_box.update()

    def activar_efecto(e):
        modo = e.control.data
        if modo == "FADE":
            enviar_comando("FADE")
        elif modo == "STROBE":
            enviar_comando("STROBE")
        elif modo == "OFF":
            slider_r.value = 0
            slider_g.value = 0
            slider_b.value = 0
            preview_box.bgcolor = "#000000"
            enviar_comando("OFF")
            slider_r.update()
            slider_g.update()
            slider_b.update()
            preview_box.update()

    def cambiar_estado_zumbador(e):
        if switch_zumbador.value:
            enviar_comando("BUZZER_ON")
        else:
            enviar_comando("BUZZER_OFF")

    # --- COMPONENTES VISUALES ADAPTADOS ---
    
    status_text = ft.Text("ESTADO: DESCONECTADO", size=11, weight=ft.FontWeight.BOLD, color="#A0AEC0")
    
    btn_conectar = ft.ElevatedButton(
        "CONECTAR ARDUINO", 
        on_click=buscar_y_conectar,
        style=ft.ButtonStyle(color="white", bgcolor="#2B6CB0", shape=ft.RoundedRectangleBorder(radius=8)),
        width=320,
        height=38
    )

    switch_hardware = ft.Switch(
        label="¿LED Ánodo Común?", 
        value=False, 
        label_position=ft.LabelPosition.LEFT
    )

    # BARRA VERTICAL SIMULADA PARA EL LDR (Tal como aparece en la imagen)
    ldr_bar_fill = ft.Container(width=16, height=30, bgcolor="#F59E0B", border_radius=4)
    ldr_bar_background = ft.Container(
        width=16, height=80, bgcolor="#2D3748", border_radius=4,
        alignment=ft.alignment.bottom_center,
        content=ldr_bar_fill
    )

    ldr_text = ft.Text("--% (0)", size=13, weight=ft.FontWeight.BOLD, color="#F59E0B")
    ldr_status = ft.Text("ESTADO:\nDESCONECTADO", size=10, weight=ft.FontWeight.BOLD, text_align="center", color="#A0AEC0")

    switch_zumbador = ft.Switch(
        value=True,
        active_color="#2B6CB0",
        on_change=cambiar_estado_zumbador
    )

    preview_box = ft.Container(
        width=110,
        height=110,
        bgcolor="#000000",
        border_radius=55,
        border=ft.border.all(3, "white"),
        alignment=ft.alignment.center
    )

    slider_r = ft.Slider(min=0, max=255, value=0, active_color="red", on_change=actualizar_color)
    slider_g = ft.Slider(min=0, max=255, value=0, active_color="green", on_change=actualizar_color)
    slider_b = ft.Slider(min=0, max=255, value=0, active_color="blue", on_change=actualizar_color)

    # --- DISEÑO Y DISTRIBUCIÓN BASADO EN LA IMAGEN ---
    page.add(
        # Cabecera Institucional
        ft.Container(
            content=ft.Column([
                ft.Text("TECNOTRONIC APSTI", size=20, weight=ft.FontWeight.BOLD, color="#2B6CB0"),
                ft.Text("LABORATORIO DE ELECTRONICA BASICA", size=10, color="#718096"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            margin=ft.margin.only(top=10, bottom=10)
        ),

        # BLOQUE 1: CONEXIÓN USB & SISTEMA
        ft.Container(
            bgcolor="#1E1E24", border_radius=8, padding=12, width=360,
            border=ft.border.all(1, "#2D3748"),
            content=ft.Column([
                ft.Text("CONEXIÓN USB & SISTEMA", size=11, weight=ft.FontWeight.BOLD, color="white"),
                status_text,
                btn_conectar,
                switch_hardware
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)
        ),

        ft.Container(height=8),

        # BLOQUE 2: CENTRAL DE MONITOREO (LDR Izquierda / Zumbador Derecha)
        ft.Container(
            bgcolor="#1E1E24", border_radius=8, padding=12, width=360,
            border=ft.border.all(1, "#2D3748"),
            content=ft.Column([
                ft.Text("CENTRAL DE MONITOREO", size=11, weight=ft.FontWeight.BOLD, color="white"),
                ft.Container(height=4),
                ft.Row([
                    # Caja LDR
                    ft.Container(
                        bgcolor="#141416", padding=10, border_radius=6, width=160, height=140,
                        content=ft.Column([
                            ft.Text("MONITOR SENSOR\nLDR (A1)", size=10, weight=ft.FontWeight.BOLD, text_align="center", color="white"),
                            ft.Row([
                                ldr_bar_background,
                                ft.Column([
                                    ft.Text("LUMINOSIDAD:", size=8, color="#718096"),
                                    ldr_text,
                                    ldr_status
                                ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)
                    ),
                    # Caja Zumbador
                    ft.Container(
                        bgcolor="#141416", padding=10, border_radius=6, width=160, height=140,
                        content=ft.Column([
                            ft.Text("CONTROL ZUMBADOR (D2)", size=10, weight=ft.FontWeight.BOLD, text_align="center", color="white"),
                            ft.Container(height=2),
                            ft.Text("HABILITAR ZUMBADOR (AUTO/MANUAL)", size=9, color="#718096", text_align="center"),
                            ft.Container(height=2),
                            ft.Row([
                                ft.Text("ON", size=11, weight=ft.FontWeight.BOLD, color="white"),
                                switch_zumbador
                            ], alignment=ft.MainAxisAlignment.CENTER, spacing=4)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        ),

        ft.Container(height=8),

        # BLOQUE 3: CONTROL LED RGB
        ft.Container(
            bgcolor="#1E1E24", border_radius=8, padding=12, width=360,
            border=ft.border.all(1, "#2D3748"),
            content=ft.Column([
                ft.Text("CONTROL LED RGB", size=11, weight=ft.FontWeight.BOLD, color="white"),
                ft.Container(height=4),
                preview_box,
                ft.Container(height=4),
                # R Slider Row
                ft.Row([
                    ft.Text("R", size=11, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text("0", size=10, color="#718096"),
                    ft.Container(slider_r, width=260),
                    ft.Text("100", size=10, color="#718096")
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
                # G Slider Row
                ft.Row([
                    ft.Text("G", size=11, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text("0", size=10, color="#718096"),
                    ft.Container(slider_g, width=260),
                    ft.Text("100", size=10, color="#718096")
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
                # B Slider Row
                ft.Row([
                    ft.Text("B", size=11, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text("0", size=10, color="#718096"),
                    ft.Container(slider_b, width=260),
                    ft.Text("100", size=10, color="#718096")
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        ),

        ft.Container(height=10),

        # Botones de efectos en la base
        ft.Row([
            ft.OutlinedButton("EFECTO FADE", data="FADE", on_click=activar_efecto, style=ft.ButtonStyle(color="#2B6CB0")),
            ft.OutlinedButton("EFECTO ESTROBO", data="STROBE", on_click=activar_efecto, style=ft.ButtonStyle(color="#2B6CB0")),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
        
        ft.Container(height=8),
        ft.ElevatedButton(
            "APAGAR EMISOR LUMÍNICO", 
            data="OFF", 
            bgcolor="#9B2C2C", 
            color="white", 
            on_click=activar_efecto,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
            width=360,
            height=40
        )
    )

    def realizar_limpieza():
        page.data["continuar_leyendo"] = False
    page.on_close = realizar_limpieza

ft.app(target=main)