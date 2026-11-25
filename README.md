# Agente Autónomo de Ventas y Cotizaciones Tecnológicas

Aplicación web desarrollada en **Python** con **Streamlit** y el SDK oficial **`google-genai`** (`gemini-2.5-flash`) que implementa un agente conversacional autónomo capaz de consultar un inventario real y emitir cotizaciones formales descargables en pesos colombianos (COP).

## Descripción del Agente y Problema que Resuelve

En los comercios minoristas y distribuidores de tecnología, los clientes suelen abandonar el proceso de compra cuando deben esperar atención humana para confirmar disponibilidad de inventario, comparar especificaciones o recibir una cotización formal con impuestos incluidos. Asimismo, los chatbots tradicionales basados en respuestas genéricas presentan el riesgo de alucinar precios, prometer existencias inexistentes o desviarse hacia temas ajenos al negocio, generando reprocesos y desconfianza comercial.

Este agente autónomo especializado en ventas y cotizaciones tecnológicas (**TechNova Colombia**) resuelve dicha problemática combinando instrucciones estrictas de rol (`system_instruction`) con capacidades agénticas de *Function Calling* sobre el modelo `gemini-2.5-flash`. De forma autónoma, el agente decide cuándo invocar la herramienta `consultar_catalogo` para obtener precios y existencias reales, y cuándo ejecutar `generar_cotizacion` para validar stock, calcular subtotal, IVA (19%) y total en COP, habilitando al instante la descarga de la cotización formal en formato `.txt` desde la interfaz web.

## Estructura del Proyecto

- `app.py`: Aplicación principal de Streamlit, definición del catálogo, `system_instruction`, herramientas agénticas y manejo de sesión.
- `requirements.txt`: Dependencias mínimas del proyecto (`streamlit` y `google-genai`).
- `.streamlit/secrets.toml`: Plantilla local para configurar `GEMINI_API_KEY` (ignorada en Git).
- `.gitignore`: Protección contra la subida accidental de credenciales, entornos virtuales y caché.
- `README.md`: Documentación del proyecto.

## Ejecución Local

1. Clona o descarga este repositorio y ubica la terminal en la raíz del proyecto.
2. Crea y activa un entorno virtual e instala las dependencias:
   ```bash
   python -m venv .venv
   # En Windows:
   .venv\Scripts\activate
   # En macOS / Linux:
   source .venv/bin/activate

   pip install -r requirements.txt
   ```
3. Configura tu clave de Google AI Studio en `.streamlit/secrets.toml`:
   ```toml
   GEMINI_API_KEY = "tu_api_key_real"
   ```
4. Inicia la aplicación:
   ```bash
   streamlit run app.py
   ```

## Despliegue en Streamlit Community Cloud

1. Sube el proyecto a un repositorio de GitHub (el archivo `.gitignore` evitará subir `.streamlit/secrets.toml`).
2. Ingresa a [share.streamlit.io](https://share.streamlit.io/) y haz clic en **New app**.
3. Selecciona tu repositorio, la rama y el archivo principal `app.py`.
4. En **Advanced settings → Secrets** (o posteriormente en *App settings → Secrets*), agrega:
   ```toml
   GEMINI_API_KEY = "tu_api_key_real"
   ```
5. Haz clic en **Deploy** y prueba el agente en línea.
