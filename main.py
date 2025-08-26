import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from flask import Flask, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from estatecore_backend.models import db, LPREvent
from io import StringIO
import csv
from datetime import datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@127.0.0.1:5432/estatecore_devecs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
CORS(app)

@app.route('/api/lpr_events', methods=['GET'])
def get_lpr_events():
    events = LPREvent.query.order_by(LPREvent.timestamp.desc()).limit(200).all()
    result = []
    for ev in events:
        result.append({
            'id': ev.id,
            'timestamp': ev.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'plate': ev.plate,
            'camera': ev.camera,
            'confidence': ev.confidence,
            'image_url': ev.image_url,
            'notes': ev.notes
        })
    return jsonify(result)

@app.route('/api/lpr_events/csv', methods=['GET'])
def export_lpr_events_csv():
    events = LPREvent.query.order_by(LPREvent.timestamp.desc()).limit(200).all()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['ID', 'Timestamp', 'Plate', 'Camera', 'Confidence', 'Image URL', 'Notes'])
    for ev in events:
        writer.writerow([
            ev.id,
            ev.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            ev.plate,
            ev.camera,
            ev.confidence,
            ev.image_url,
            ev.notes
        ])
    output = si.getvalue()
    return send_file(
        StringIO(output),
        mimetype='text/csv',
        as_attachment=True,
        download_name='lpr_events.csv'
    )

@app.route('/api/lpr_events', methods=['POST'])
def add_lpr_event():
    data = request.json
    event = LPREvent(
        timestamp=datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S'),
        plate=data['plate'],
        camera=data.get('camera'),
        confidence=data.get('confidence'),
        image_url=data.get('image_url'),
        notes=data.get('notes'),
    )
    db.session.add(event)
    db.session.commit()
    return jsonify({'success': True, 'id': event.id})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
