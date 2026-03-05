from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import pandas as pd
import io
import time
import paho.mqtt.client as mqtt

# Default MQTT settings (used when form doesn't provide overrides)
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC = "server18"

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')



@app.route('/publish', methods=['POST'])
def publish_one():
    data = request.form or request.json or {}
    ident = (data.get('id') if isinstance(data, dict) else None) or request.form.get('id')
    if not ident:
        return jsonify({'error':'no id provided'}), 400
    broker = request.form.get('broker') or MQTT_BROKER
    mqtt_port = int(request.form.get('mqtt_port') or MQTT_PORT)
    topic = request.form.get('topic') or MQTT_TOPIC
    username = request.form.get('username') or None
    password = request.form.get('password') or None
    try:
        client = mqtt.Client()
        if username:
            client.username_pw_set(username, password)
        client.connect(broker, mqtt_port, 60)
        client.publish(topic, payload=str(ident))
        client.disconnect()
    except Exception as e:
        return jsonify({'error':'mqtt error: '+str(e)}), 500
    return jsonify({'sent': 1, 'topic': topic, 'broker': broker})

@app.route('/download-template')
def download_template():
    # generate a simple Excel template with one column named 'id'
    df = pd.DataFrame({'id': ['example1', 'example2', 'example3']})
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='id_template.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error':'no file uploaded'}), 400
    file = request.files['file']
    broker = request.form.get('broker') or MQTT_BROKER
    mqtt_port = int(request.form.get('mqtt_port') or MQTT_PORT)
    topic = request.form.get('topic') or MQTT_TOPIC
    username = request.form.get('username') or None
    password = request.form.get('password') or None

    # Read excel robustly and extract only the first-column values as IDs
    # Try modern .xlsx first (openpyxl), then legacy .xls (xlrd), then no-header fallback
    filename = getattr(file, 'filename', '') or ''
    tried = []
    df = None
    # first try default autodetect
    try:
        df = pd.read_excel(file, header=0, dtype=str)
    except Exception as e_default:
        tried.append(('autodetect', str(e_default)))
        # try explicit engines
        try:
            file.stream.seek(0)
            df = pd.read_excel(file, engine='openpyxl', header=0, dtype=str)
        except Exception as e_open:
            tried.append(('openpyxl', str(e_open)))
            try:
                file.stream.seek(0)
                df = pd.read_excel(file, engine='xlrd', header=0, dtype=str)
            except Exception as e_xlrd:
                tried.append(('xlrd', str(e_xlrd)))
                # final fallback: try no header
                try:
                    file.stream.seek(0)
                    df = pd.read_excel(file, header=None, dtype=str)
                except Exception as e_final:
                    tried.append(('no-header', str(e_final)))
                    return jsonify({'error': 'failed to read excel; attempts: '+str(tried)}), 400

    if df.shape[1] < 1 or df.shape[0] < 1:
        return jsonify({'error':'excel has no data'}), 400

    # determine first column series
    first_col = df.iloc[:, 0].astype(str)

    # If header row was kept as data accidentally, drop common header labels
    header_label = str(df.columns[0]).strip().lower() if df.columns.size > 0 else ''
    ids_series = first_col.str.strip()
    # Remove rows equal to header label (e.g., 'id')
    if header_label and header_label in ('id', 'ids', 'identifier'):
        ids_series = ids_series[ids_series.str.lower() != header_label]

    # Filter out empty/NaN and very long values
    ids = ids_series[ids_series.notna() & (ids_series != '')].tolist()
    ids = [str(x).strip() for x in ids if len(str(x).strip()) > 0 and len(str(x)) < 512]

    if not ids:
        return jsonify({'error':'no ids found in first column'}), 400

    try:
        client = mqtt.Client()
        if username:
            client.username_pw_set(username, password)
        client.connect(broker, mqtt_port, 60)
        sent = 0
        for ident in ids:
            line = ident.strip()
            if not line:
                continue
            client.publish(topic, payload=line)
            sent += 1
            time.sleep(0.02)
        client.disconnect()
    except Exception as e:
        # network-level errors (e.g., WinError 10060) mean the server couldn't reach the broker
        err_msg = str(e)
        return jsonify({'error':'mqtt error: '+err_msg, 'hint':'check broker address/port and network connectivity'}), 500

    return jsonify({'sent': sent, 'sample': ids[:5]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
