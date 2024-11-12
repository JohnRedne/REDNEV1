# -*- coding: utf-8 -*-
"""Untitled1.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1gBqEZln7C8krda4pQJoyDeTyj9jaHC5l
"""

@app.route('/generate_helicorder', methods=['GET'])
def generate_helicorder():
    try:
        # Obtener los parámetros de la URL
        net = request.args.get('net')
        sta = request.args.get('sta')
        loc = request.args.get('loc')
        cha = request.args.get('cha')
        start = request.args.get('start')
        end = request.args.get('end')

        # Log para verificar los parámetros recibidos
        app.logger.info(f"Generando helicorder con parámetros: net={net}, sta={sta}, loc={loc}, cha={cha}, start={start}, end={end}")

        # Verificar que todos los parámetros requeridos están presentes
        if not all([net, sta, loc, cha, start, end]):
            app.logger.error("Faltan parámetros requeridos.")
            return jsonify({"error": "Faltan parámetros requeridos"}), 400

        # Construir la URL para descargar el archivo MiniSEED desde Raspberry Shake
        url = f"https://data.raspberryshake.org/fdsnws/dataselect/1/query?starttime={start}&endtime={end}&network={net}&station={sta}&location={loc}&channel={cha}&nodata=404"
        app.logger.info(f"URL de solicitud de datos: {url}")

        # Realizar la solicitud al servidor para obtener los datos
        response = requests.get(url)
        if response.status_code == 503:
            app.logger.error("El servidor de datos no está disponible.")
            return jsonify({"error": "El servidor no está disponible en este momento."}), 503
        if response.status_code != 200:
            app.logger.error(f"Error al descargar datos: Código de estado {response.status_code}")
            return jsonify({"error": f"Error al descargar datos: {response.status_code}"}), 500

        # Guardar el archivo MiniSEED en memoria
        mini_seed_data = io.BytesIO(response.content)

        # Procesar el archivo MiniSEED para extraer los datos
        try:
            st = read(mini_seed_data)
        except Exception as e:
            app.logger.error(f"Error procesando el archivo MiniSEED: {str(e)}")
            return jsonify({"error": f"Error procesando el archivo MiniSEED: {str(e)}"}), 500

        # Crear el helicorder usando la función `plot` de ObsPy con ajustes para mejorar la precisión
        fig = st.plot(
            type="dayplot",
            interval=60,  # Ajuste de intervalo a 60 minutos para reducir carga
            right_vertical_labels=True,
            vertical_scaling_range=3000,  # Rango vertical ajustado para reducir uso de memoria
            color=['k', 'r', 'b'],  # Colores alternados
            show_y_UTC_label=True,
            one_tick_per_line=True,
            fig_size=(10, 5)  # Tamaño del gráfico reducido
        )

        # Guardar el gráfico en memoria como imagen PNG con resolución más baja
        output_image = io.BytesIO()
        fig.savefig(output_image, format='png', dpi=80, bbox_inches="tight")  # DPI reducido
        output_image.seek(0)
        plt.close(fig)  # Cerrar el gráfico para liberar memoria

        # Devolver la imagen generada como respuesta
        app.logger.info("Helicorder generado exitosamente.")
        return send_file(output_image, mimetype='image/png')

    except Exception as e:
        app.logger.error(f"Ocurrió un error en /generate_helicorder: {str(e)}")
        return jsonify({"error": f"Ocurrió un error: {str(e)}"}), 500

