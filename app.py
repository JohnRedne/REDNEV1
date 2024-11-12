# -*- coding: utf-8 -*-
"""Untitled1.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1gBqEZln7C8krda4pQJoyDeTyj9jaHC5l
"""

from flask import Flask, request, send_file, jsonify
from obspy import read
import requests
import io
import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Para evitar problemas de GUI en entornos sin pantalla

app = Flask(__name__)

# Función auxiliar para verificar el intervalo de tiempo
def calculate_time_difference(start, end):
    start_time = datetime.datetime.fromisoformat(start)
    end_time = datetime.datetime.fromisoformat(end)
    difference = end_time - start_time
    return difference.total_seconds() / 60  # Diferencia en minutos

# Ruta principal para decidir entre sismograma y helicorder
@app.route('/generate_graph', methods=['GET'])
def generate_graph():
    try:
        # Obtener los parámetros de la URL
        net = request.args.get('net')
        sta = request.args.get('sta')
        loc = request.args.get('loc')
        cha = request.args.get('cha')
        start = request.args.get('start')
        end = request.args.get('end')

        # Verificar que todos los parámetros requeridos están presentes
        if not all([net, sta, loc, cha, start, end]):
            return jsonify({"error": "Faltan parámetros requeridos"}), 400

        # Verificar el intervalo de tiempo
        interval_minutes = calculate_time_difference(start, end)

        # Seleccionar el tipo de gráfico según el intervalo
        if interval_minutes <= 30:
            return generate_sismograma(net, sta, loc, cha, start, end)
        else:
            return generate_helicorder(net, sta, loc, cha, start, end)

    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {str(e)}"}), 500

# Función para generar sismograma
def generate_sismograma(net, sta, loc, cha, start, end):
    try:
        # Construir la URL para descargar el archivo MiniSEED desde Raspberry Shake
        url = f"https://data.raspberryshake.org/fdsnws/dataselect/1/query?starttime={start}&endtime={end}&network={net}&station={sta}&location={loc}&channel={cha}&nodata=404"

        # Realizar la solicitud al servidor para obtener los datos
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({"error": f"Error al descargar datos: {response.status_code}"}), 500

        # Guardar el archivo MiniSEED en memoria
        mini_seed_data = io.BytesIO(response.content)

        # Procesar el archivo MiniSEED para extraer los datos
        try:
            st = read(mini_seed_data)
        except Exception as e:
            return jsonify({"error": f"Error procesando el archivo MiniSEED: {str(e)}"}), 500

        # Extraer los datos para graficar con Matplotlib
        tr = st[0]
        start_time = tr.stats.starttime.datetime
        times = [start_time + datetime.timedelta(seconds=sec) for sec in tr.times()]
        data = tr.data

        # Crear el gráfico de sismograma
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(times, data, color='black', linewidth=0.8)
        ax.set_title(f"{start} - {end}", fontsize=10, y=1.05)
        ax.set_xlabel("Tiempo")
        ax.set_ylabel("Amplitud")
        ax.text(0.02, 0.98, f"{net}.{sta}.{loc}.{cha}", transform=ax.transAxes,
                fontsize=9, verticalalignment='top', bbox=dict(facecolor='white', edgecolor='black'))
        fig.autofmt_xdate()

        # Guardar el gráfico en memoria como imagen PNG
        output_image = io.BytesIO()
        plt.savefig(output_image, format='png', dpi=120, bbox_inches="tight")
        output_image.seek(0)
        plt.close(fig)

        return send_file(output_image, mimetype='image/png')

    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {str(e)}"}), 500

# Función para generar helicorder
def generate_helicorder(net, sta, loc, cha, start, end):
    try:
        # Construir la URL para descargar el archivo MiniSEED desde Raspberry Shake
        url = f"https://data.raspberryshake.org/fdsnws/dataselect/1/query?starttime={start}&endtime={end}&network={net}&station={sta}&location={loc}&channel={cha}&nodata=404"

        # Realizar la solicitud al servidor para obtener los datos
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({"error": f"Error al descargar datos: {response.status_code}"}), 500

        # Guardar el archivo MiniSEED en memoria
        mini_seed_data = io.BytesIO(response.content)

        # Procesar el archivo MiniSEED para extraer los datos
        try:
            st = read(mini_seed_data)
        except Exception as e:
            return jsonify({"error": f"Error procesando el archivo MiniSEED: {str(e)}"}), 500

        # Crear el helicorder usando la función `plot` de ObsPy
        fig = st.plot(
            type="dayplot",
            interval=60,
            right_vertical_labels=True,
            vertical_scaling_range=3000,
            color=['k', 'r', 'b','green'],
            show_y_UTC_label=True,
            one_tick_per_line=True,
            fig_size=(10, 5)
        )

        # Guardar el gráfico en memoria como imagen PNG
        output_image = io.BytesIO()
        fig.savefig(output_image, format='png', dpi=80, bbox_inches="tight")
        output_image.seek(0)
        plt.close(fig)

        return send_file(output_image, mimetype='image/png')

    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {str(e)}"}), 500

# Ejecutar el servidor Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

