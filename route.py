from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

# PostgreSQL connection settings
DB_NAME = "sensor_db"
DB_USER = "postgres"
DB_PASS = "nieljhon1"
DB_HOST = "localhost"  # local connection
DB_PORT = 5432

@app.route('/add_data', methods=['POST'])
def add_data():
    data = request.json
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute("""
    INSERT INTO sensor_readings (id, device_name, voltage, current, power, energy, frequency, power_factor, alarm, temperature, humidity, timestamp)
    VALUES (%(id)s, %(device_name)s, %(voltage)s, %(current)s, %(power)s, %(energy)s, %(frequency)s, %(power_factor)s, %(alarm)s, %(temperature)s, %(humidity)s, %(timestamp)s)
    ON CONFLICT (id) 
    DO UPDATE SET
        device_name = EXCLUDED.device_name,
        voltage = EXCLUDED.voltage,
        current = EXCLUDED.current,
        power = EXCLUDED.power,
        energy = EXCLUDED.energy,
        frequency = EXCLUDED.frequency,
        power_factor = EXCLUDED.power_factor,
        alarm = EXCLUDED.alarm,
        temperature = EXCLUDED.temperature,
        humidity = EXCLUDED.humidity,
        timestamp = EXCLUDED.timestamp
""", data)
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)