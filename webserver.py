from flask import Flask, request, render_template, send_from_directory
from threading import Thread
from bot import *
from discord_send_plots import start_scheduler
import asyncio
from data_plotting import get_options_data
import re

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Crear un event loop global para manejar las tareas asíncronas
loop = asyncio.get_event_loop()

HTML_TEMPLATE = "index.html"

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        if request.method == 'POST':
            ticker = request.form['ticker']
            exp = request.form['exp']
            greek = request.form['greek']
            
        #try:
            # Validar entradas
            if not ticker.isalnum() or len(ticker) > 10:
                return render_template(HTML_TEMPLATE, error="Ticker not valid", greek=greek)
            if greek not in ['delta', 'gamma', 'vanna', 'charm']:
                return render_template(HTML_TEMPLATE, error="Greek not valid", greek=greek)
            if not re.match(r'^\d{4}-\d{2}-\d{2}$|^(0dte|1dte|weekly|monthly|opex|all)$', exp):
                return render_template(HTML_TEMPLATE, error="Formato de expiración inválido (YYYY-MM-DD o 0dte/1dte/monthly/opex/all)", greek=greek)
            
            # Llamar a get_options_data de forma asíncrona
            #print(f"Calling get_options_data with ticker={ticker}, exp={exp}, greek={greek}")
            print("Web loading:", ticker, exp, greek)
            future = asyncio.run_coroutine_threadsafe(
                get_options_data(ticker, exp, greek), loop
            )
            filenames = future.result(timeout=120) # If your system is fast, try timeout=90
            
            # Verificar y loggear los paths de las imágenes
            images = []

            for i in filenames:
                for filename in i:  
                    # Normalizar el path para evitar duplicados o prefijos incorrectos
                    print("Filename:", filename)
                    normalized_filename = os.path.normpath(filename)
                    # Asegurarse de que el path sea relativo a 'plots'
                    #if not normalized_filename.startswith('plots/'):
                    #    normalized_filename = os.path.join('plots', normalized_filename.lstrip('/'))
                    #print("normalized_filename:", normalized_filename)
                    if os.path.exists(normalized_filename):
                        # Crear el path para el navegador
                        web_path = f"/plots/{filename.lstrip('plots/').lstrip('/')}"
                        images.append(web_path)
                        print(f"Image found: {normalized_filename}, serving as {web_path}")
                    else:
                        print(f"Image not found: {filename}")
            
            if not images:
                print("No images found for the request")
                return render_template(HTML_TEMPLATE, error="Error plot not found, retry in a minute", greek=greek)
            
            print(f"Serving images: {images}")
            return render_template(HTML_TEMPLATE, images=images, greek=greek)
        
            #except Exception as e:
            #    print(f"Error processing request: ", e)
            #    return render_template(HTML_TEMPLATE, error=f"Error al cargar los gráficos: {str(e)}", greek=greek)
        
        return render_template(HTML_TEMPLATE, greek='')
    except Exception as e:
        print("Error in index()")
        print(e)
        return render_template(HTML_TEMPLATE, error="Ticker invalid or failed download, retry in a minute", greek=greek)


@app.route('/plots/<path:filename>')
def serve_plot(filename):
    try:
        #print(f"Attempting to serve file: plots/: {filename}")
        return send_from_directory("plots", filename)
    except Exception as e:
        print(f"Error serving file plots/{filename}: {str(e)}")
        return "Archivo no encontrado", 404


def run_flask():
    app.run(host='0.0.0.0', port=8000, use_reloader=False)

async def run_bot_async():
    try:
        await bot.start(DISCORD_TOKEN)
    except Exception as e:
        print(f"Error running Discord bot: {e}")
    finally:
        await bot.close()

async def run_scheduler_async():
    try:
        # Asumiendo que start_scheduler es async; si no, ajustar en consecuencia
        await start_scheduler()
    except Exception as e:
        print(f"Error running scheduler: {e}")

async def keep_alive():
    # Iniciar Flask en un hilo separado
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Ejecutar el bot y el scheduler como tareas asíncronas
    tasks = [
        run_bot_async(),
        run_scheduler_async()
    ]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    # Crear y configurar el event loop en el hilo principal
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(keep_alive())
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
