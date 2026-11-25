"""
Agente Autónomo Simplificado de Ventas y Cotizaciones Tecnológicas.

Aplicación web construida con Streamlit y el SDK oficial `google-genai`
(modelo `gemini-2.5-flash`) con Function Calling automático para consultar un
catálogo interno y generar cotizaciones formales descargables en formato .txt.
"""

from datetime import datetime
import unicodedata

from google import genai
from google.genai import types
import streamlit as st


# ---------------------------------------------------------------------------
# 1. Configuración general de la página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Agente de Ventas TechNova",
    page_icon="🛒",
    layout="centered",
)

# ---------------------------------------------------------------------------
# 2. Catálogo interno de productos tecnológicos (Precios en COP)
# ---------------------------------------------------------------------------
CATALOGO_PRODUCTOS: list[dict] = [
    {
        "id": "TECH-001",
        "nombre": "Laptop Lenovo ThinkPad E14 Gen 5",
        "categoria": "Portátiles",
        "precio_cop": 3_490_000,
        "stock": 8,
        "especificaciones": "Intel Core i5-1335U, 16 GB RAM, SSD 512 GB, 14\" FHD",
    },
    {
        "id": "TECH-002",
        "nombre": "Laptop ASUS Vivobook 15 OLED",
        "categoria": "Portátiles",
        "precio_cop": 2_890_000,
        "stock": 5,
        "especificaciones": "AMD Ryzen 7 7730U, 16 GB RAM, SSD 512 GB, 15.6\" OLED",
    },
    {
        "id": "TECH-003",
        "nombre": "Monitor LG UltraGear 27\"",
        "categoria": "Monitores",
        "precio_cop": 1_250_000,
        "stock": 12,
        "especificaciones": "27\" IPS QHD, 165 Hz, 1 ms, HDR10",
    },
    {
        "id": "TECH-004",
        "nombre": "Monitor Samsung ViewFinity S6 24\"",
        "categoria": "Monitores",
        "precio_cop": 890_000,
        "stock": 10,
        "especificaciones": "24\" IPS QHD, 75 Hz, USB-C, diseño ergonómico",
    },
    {
        "id": "TECH-005",
        "nombre": "Teclado Mecánico Logitech MX Mechanical",
        "categoria": "Periféricos",
        "precio_cop": 680_000,
        "stock": 15,
        "especificaciones": "Inalámbrico Bluetooth/Logi Bolt, switches táctiles, retroiluminado",
    },
    {
        "id": "TECH-006",
        "nombre": "Mouse Logitech MX Master 3S",
        "categoria": "Periféricos",
        "precio_cop": 450_000,
        "stock": 20,
        "especificaciones": "8000 DPI, clics silenciosos, desplazamiento MagSpeed, USB-C",
    },
    {
        "id": "TECH-007",
        "nombre": "Audífonos Sony WH-1000XM5",
        "categoria": "Audio",
        "precio_cop": 1_490_000,
        "stock": 6,
        "especificaciones": "Cancelación activa de ruido, Bluetooth 5.2, hasta 30 h de batería",
    },
    {
        "id": "TECH-008",
        "nombre": "SSD Externo Samsung T7 Shield 1TB",
        "categoria": "Almacenamiento",
        "precio_cop": 480_000,
        "stock": 14,
        "especificaciones": "USB 3.2 Gen 2 hasta 1050 MB/s, resistente a agua y polvo IP65",
    },
]

IVA_PORCENTAJE = 0.19

# ---------------------------------------------------------------------------
# 3. Instrucción del sistema (System Instruction) estricta
# ---------------------------------------------------------------------------
SYSTEM_INSTRUCTION = """
Eres el Asistente Especialista en Ventas y Cotizaciones Tecnológicas de la tienda **TechNova Colombia**.

REGLAS ESTRICTAS DE COMPORTAMIENTO:
1. **Alcance exclusivo:** Solo puedes atender consultas relacionadas con los productos tecnológicos del catálogo de TechNova Colombia, asesoría de compra sobre dichos equipos, disponibilidad de inventario y generación de cotizaciones formales en pesos colombianos (COP).
2. **Prohibido inventar datos:** NUNCA inventes productos, modelos, especificaciones, precios, descuentos ni cantidades en stock. Antes de mencionar precios, stock o características, debes consultar obligatoriamente la herramienta `consultar_catalogo`.
3. **Uso autónomo de herramientas:**
   - Usa `consultar_catalogo(categoria)` cuando el usuario pregunte qué productos hay, busque recomendaciones por categoría o quiera verificar precio y disponibilidad. Si desea ver todo el inventario, pásale una cadena vacía `""`.
   - Usa `generar_cotizacion(nombre_producto, cantidad)` cuando el usuario solicite cotizar, calcular el total con IVA o generar un presupuesto formal para un producto y una cantidad específica.
4. **Manejo de consultas fuera de tema:** Si el usuario pregunta sobre cualquier tema ajeno a ventas y cotizaciones tecnológicas de la tienda (por ejemplo: cocina, política, medicina, tareas escolares, programación general, chistes, deportes, etc.), rechaza amablemente la solicitud e indícale que tu única función es asesorarlo con productos tecnológicos y cotizaciones de TechNova Colombia.
5. **Estilo de respuesta:** Responde siempre en español claro, cordial y profesional. Presenta los valores monetarios en pesos colombianos (COP) y, cuando generes una cotización exitosamente, informa al cliente que ya puede descargar el archivo `.txt` desde la barra lateral izquierda.
""".strip()


# ---------------------------------------------------------------------------
# 4. Funciones auxiliares y herramientas agénticas (Tools)
# ---------------------------------------------------------------------------
def _normalizar_texto(texto: str) -> str:
    """Convierte texto a minúsculas y elimina tildes para búsquedas flexibles."""
    texto_limpio = texto.strip().lower()
    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto_limpio)
        if unicodedata.category(caracter) != "Mn"
    )


def _formatear_cop(valor: int | float) -> str:
    """Formatea un valor numérico en pesos colombianos (ej. $1.250.000 COP)."""
    monto_entero = int(round(valor))
    return f"${monto_entero:,}".replace(",", ".") + " COP"


def consultar_catalogo(categoria: str = "") -> str:
    """Consulta los productos reales disponibles en el catálogo de TechNova Colombia.

    Utiliza esta herramienta para listar todos los productos o filtrarlos por
    categoría (por ejemplo: 'Portátiles', 'Monitores', 'Periféricos', 'Audio',
    'Almacenamiento').

    Args:
        categoria: Nombre de la categoría a filtrar. Si se deja vacío (""),
            devuelve todo el catálogo disponible.

    Returns:
        Cadena con el listado detallado de productos (ID, nombre, categoría,
        precio en COP, stock disponible y especificaciones) o un aviso si la
        categoría no tiene coincidencias.
    """
    categoria_norm = _normalizar_texto(categoria)

    if not categoria_norm:
        productos_filtrados = CATALOGO_PRODUCTOS
    else:
        productos_filtrados = [
            prod
            for prod in CATALOGO_PRODUCTOS
            if categoria_norm in _normalizar_texto(prod["categoria"])
            or _normalizar_texto(prod["categoria"]) in categoria_norm
        ]

    if not productos_filtrados:
        categorias_disponibles = sorted({p["categoria"] for p in CATALOGO_PRODUCTOS})
        return (
            f"No se encontraron productos para la categoría '{categoria}'. "
            f"Las categorías disponibles son: {', '.join(categorias_disponibles)}."
        )

    lineas = ["Productos disponibles en TechNova Colombia:"]
    for prod in productos_filtrados:
        lineas.append(
            f"- [{prod['id']}] {prod['nombre']} | Categoría: {prod['categoria']} | "
            f"Precio unitario: {_formatear_cop(prod['precio_cop'])} | "
            f"Stock: {prod['stock']} unidades | Specs: {prod['especificaciones']}"
        )
    return "\n".join(lineas)


def generar_cotizacion(nombre_producto: str, cantidad: int) -> str:
    """Valida producto y stock, calcula subtotal, IVA (19%) y total en COP, y
    habilita la descarga de la cotización formal en formato .txt.

    Args:
        nombre_producto: Nombre exacto o parcial (o ID) del producto a cotizar.
        cantidad: Número entero de unidades solicitadas (debe ser mayor o igual a 1).

    Returns:
        Resultado de la validación y detalle completo de la cotización en COP,
        o un mensaje descriptivo si el producto no existe o no hay stock suficiente.
    """
    try:
        cantidad_int = int(cantidad)
    except (TypeError, ValueError):
        return "Error: La cantidad solicitada debe ser un número entero válido."

    if cantidad_int <= 0:
        return "Error: La cantidad debe ser mayor o igual a 1 unidad."

    consulta_norm = _normalizar_texto(nombre_producto)
    if not consulta_norm:
        return "Error: Debes indicar el nombre o ID del producto a cotizar."

    # Búsqueda exacta por ID o nombre, luego coincidencia parcial en ambos sentidos
    coincidencias = [
        prod
        for prod in CATALOGO_PRODUCTOS
        if _normalizar_texto(prod["id"]) == consulta_norm
        or _normalizar_texto(prod["nombre"]) == consulta_norm
    ]
    if not coincidencias:
        coincidencias = [
            prod
            for prod in CATALOGO_PRODUCTOS
            if consulta_norm in _normalizar_texto(prod["nombre"])
            or _normalizar_texto(prod["nombre"]) in consulta_norm
            or _normalizar_texto(prod["id"]) in consulta_norm
        ]

    if not coincidencias:
        nombres = ", ".join(p["nombre"] for p in CATALOGO_PRODUCTOS)
        return (
            f"No se encontró el producto '{nombre_producto}' en el catálogo. "
            f"Productos disponibles: {nombres}."
        )

    if len(coincidencias) > 1:
        opciones = ", ".join(f"{p['nombre']} ({p['id']})" for p in coincidencias)
        return (
            f"La búsqueda '{nombre_producto}' coincide con varios productos: {opciones}. "
            "Por favor especifica el nombre exacto o el ID del producto."
        )

    producto = coincidencias[0]

    if cantidad_int > producto["stock"]:
        return (
            f"Stock insuficiente para '{producto['nombre']}'. "
            f"Solicitaste {cantidad_int} unidades, pero solo hay {producto['stock']} disponibles."
        )

    # Cálculo de totales en COP
    precio_unitario = producto["precio_cop"]
    subtotal = precio_unitario * cantidad_int
    iva = int(round(subtotal * IVA_PORCENTAJE))
    total = subtotal + iva

    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    codigo_cotizacion = f"COT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    texto_cotizacion = (
        "============================================================\n"
        "              TECHNOVA COLOMBIA - COTIZACIÓN FORMAL         \n"
        "============================================================\n"
        f"N° Cotización : {codigo_cotizacion}\n"
        f"Fecha/Hora    : {fecha_actual}\n"
        "Moneda        : Pesos Colombianos (COP)\n"
        "------------------------------------------------------------\n"
        f"ID Producto   : {producto['id']}\n"
        f"Producto      : {producto['nombre']}\n"
        f"Categoría     : {producto['categoria']}\n"
        f"Especificac.  : {producto['especificaciones']}\n"
        f"Precio Unit.  : {_formatear_cop(precio_unitario)}\n"
        f"Cantidad      : {cantidad_int} unidad(es)\n"
        "------------------------------------------------------------\n"
        f"Subtotal      : {_formatear_cop(subtotal)}\n"
        f"IVA (19%)     : {_formatear_cop(iva)}\n"
        f"TOTAL A PAGAR : {_formatear_cop(total)}\n"
        "============================================================\n"
        "Validez de la cotización: 5 días calendario o hasta agotar existencias.\n"
        "Garantía oficial de 12 meses directamente con TechNova Colombia.\n"
    )

    # Guardar en session_state para activar el botón de descarga en la barra lateral
    st.session_state["ultima_cotizacion"] = texto_cotizacion
    st.session_state["ultima_cotizacion_archivo"] = f"{codigo_cotizacion}.txt"

    return (
        f"Cotización generada exitosamente ({codigo_cotizacion}).\n"
        f"Producto: {producto['nombre']} ({producto['id']})\n"
        f"Cantidad: {cantidad_int} | Precio unitario: {_formatear_cop(precio_unitario)}\n"
        f"Subtotal: {_formatear_cop(subtotal)} | IVA (19%): {_formatear_cop(iva)} | "
        f"Total: {_formatear_cop(total)}.\n"
        "El archivo .txt ya está listo para descargarse en la barra lateral."
    )


# ---------------------------------------------------------------------------
# 5. Validación segura de credenciales (Streamlit Secrets)
# ---------------------------------------------------------------------------
def obtener_api_key() -> str | None:
    """Obtiene la API Key de Gemini desde `st.secrets` de forma segura."""
    try:
        api_key_raw = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return None

    api_key_limpia = str(api_key_raw).strip() if api_key_raw else ""
    if not api_key_limpia or api_key_limpia == "PEGA_AQUI_TU_API_KEY":
        return None
    return api_key_limpia


api_key = obtener_api_key()
if not api_key:
    st.title("🛒 Agente Autónomo de Ventas — TechNova Colombia")
    st.error(
        "⚠️ No se encontró una clave válida `GEMINI_API_KEY` en `st.secrets`.\n\n"
        "- **En ejecución local:** Edita el archivo `.streamlit/secrets.toml` y reemplaza "
        "`\"PEGA_AQUI_TU_API_KEY\"` con tu clave real de Google AI Studio.\n"
        "- **En Streamlit Community Cloud:** Ve a *App settings → Secrets* y agrega "
        "`GEMINI_API_KEY = \"tu_clave_aqui\"`."
    )
    st.stop()


# ---------------------------------------------------------------------------
# 6. Inicialización del cliente Gemini y estado de la sesión
# ---------------------------------------------------------------------------
def crear_sesion_chat(clave_api: str):
    """Inicializa el cliente `google-genai` y crea una sesión de chat con herramientas."""
    client = genai.Client(api_key=clave_api)
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        tools=[consultar_catalogo, generar_cotizacion],
        temperature=0.2,
    )
    return client.chats.create(model="gemini-2.5-flash", config=config)


MENSAJE_BIENVENIDA = (
    "¡Hola! Soy el asesor virtual de **TechNova Colombia**. "
    "Puedo ayudarte a consultar nuestro catálogo tecnológico, verificar stock "
    "y generar cotizaciones formales con IVA incluido en COP. ¿Qué equipo buscas hoy?"
)


def reiniciar_sesion(clave_api: str, mensaje_inicial: str = MENSAJE_BIENVENIDA) -> None:
    """Restablece el historial de mensajes, la cotización activa y la sesión de chat."""
    st.session_state["messages"] = [{"role": "assistant", "content": mensaje_inicial}]
    st.session_state["ultima_cotizacion"] = None
    st.session_state["ultima_cotizacion_archivo"] = "cotizacion_technova.txt"
    st.session_state["chat_session"] = crear_sesion_chat(clave_api)


def inicializar_estado() -> None:
    """Inicializa las variables necesarias en `st.session_state`."""
    if "messages" not in st.session_state or "chat_session" not in st.session_state:
        reiniciar_sesion(api_key)
    else:
        st.session_state.setdefault("ultima_cotizacion", None)
        st.session_state.setdefault("ultima_cotizacion_archivo", "cotizacion_technova.txt")


inicializar_estado()


# ---------------------------------------------------------------------------
# 7. Barra lateral: Catálogo rápido, reinicio de chat y descarga de cotización
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("🖥️ TechNova Colombia")
    st.caption("Panel de control y referencia rápida para pruebas")

    if st.button("🔄 Reiniciar conversación", use_container_width=True):
        reiniciar_sesion(
            api_key,
            mensaje_inicial=(
                "Conversación reiniciada. ¿En qué producto tecnológico de "
                "**TechNova Colombia** te puedo asesorar hoy?"
            ),
        )
        st.rerun()

    # Contenedor reservado para el botón de descarga (se actualiza tras cada turno)
    descarga_slot = st.container()

    st.divider()
    st.subheader("📦 Vista rápida del catálogo")
    resumen_catalogo = [
        {
            "ID": p["id"],
            "Producto": p["nombre"],
            "Categoría": p["categoria"],
            "Precio (COP)": _formatear_cop(p["precio_cop"]).replace(" COP", ""),
            "Stock": p["stock"],
        }
        for p in CATALOGO_PRODUCTOS
    ]
    st.dataframe(resumen_catalogo, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# 8. Interfaz principal del chat
# ---------------------------------------------------------------------------
st.title("🛒 Agente Autónomo de Ventas Tecnológicas")
st.markdown(
    "Asistente inteligente impulsado por **Gemini 2.5 Flash** (`google-genai`) con "
    "**Function Calling** autónomo para consultar inventario real y generar cotizaciones en COP."
)

# Renderizar historial persistente de mensajes
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Entrada conversacional del usuario
if prompt := st.chat_input("Pregunta por portátiles, monitores, periféricos o pide una cotización..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Consultando asesor e inventario..."):
            try:
                response = st.session_state["chat_session"].send_message(prompt)
                respuesta_texto = (
                    response.text
                    if response and response.text
                    else "Lo siento, no recibí una respuesta del modelo. Intenta reformular tu consulta."
                )
            except Exception as exc:
                respuesta_texto = (
                    "⚠️ Ocurrió un error al comunicarse con la API de Gemini. "
                    f"Verifica tu `GEMINI_API_KEY` o intenta nuevamente.\n\nDetalle: `{exc}`"
                )

        st.markdown(respuesta_texto)

    st.session_state["messages"].append({"role": "assistant", "content": respuesta_texto})


# ---------------------------------------------------------------------------
# 9. Renderizado dinámico del botón de descarga en la barra lateral
# ---------------------------------------------------------------------------
with descarga_slot:
    if st.session_state.get("ultima_cotizacion"):
        st.divider()
        st.subheader("📄 Cotización lista")
        st.success("Tu última cotización ya está disponible para descargar.")
        st.download_button(
            label="⬇️ Descargar cotización (.txt)",
            data=st.session_state["ultima_cotizacion"],
            file_name=st.session_state["ultima_cotizacion_archivo"],
            mime="text/plain",
            use_container_width=True,
        )
