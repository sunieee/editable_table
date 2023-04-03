import eventlet
eventlet.monkey_patch()     # 使用eventlet而不是greenlet启动socketio
# import gevent
# from gevent import monkey
# monkey.patch_all(thread=False)

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Float
from datetime import datetime
import json
import queue
import signal
import sys
from utils import check_identical

app = Flask(__name__)
task_queue = queue.Queue()

engine = create_engine('sqlite:///editable_table.db?check_same_thread=False', echo=True)
Base = declarative_base()

class TableRow(Base):
    __tablename__ = 'table'

    id = Column(Integer, primary_key=True)
    source = Column(String(120), nullable=False)
    frequency = Column(String(120), nullable=True)
    user = Column(String(120), nullable=True)
    department = Column(String(120), nullable=True)
    target = Column(String(120), nullable=False)
    create_time = Column(DateTime, default=datetime.now())
    update_time = Column(DateTime, default=datetime.now())
    status = Column(String(120), nullable=False)

    def to_dict(self):
        dic = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        dic['create_time'] = self.create_time.strftime('%Y/%m/%d %H:%M:%S')
        dic['update_time'] = self.update_time.strftime('%Y/%m/%d %H:%M:%S')
        return dic

Base.metadata.create_all(engine)
db_session = sessionmaker(bind=engine)()

# 创建一个新的Session工厂
# with app.app_context():
#     Session = scoped_session(sessionmaker(bind=db.engine))
#     db.create_all()

socketio = SocketIO(app, cors_allowed_origins="*")


# worker_threads = [threading.Thread(target=worker) for _ in range(3)]
# for thread in worker_threads:
#     thread.start()

def signal_handler(sig, frame):
    print("Closing socket connections...")
    socketio.stop()  # Close the Socket.IO connections
    sys.exit(0)

# This code will catch the SIGINT signal (generated when you press Ctrl+C to stop the application) and close the Socket.IO connections before exiting.
signal.signal(signal.SIGINT, signal_handler)

@socketio.on('connect', namespace='/table')
def test_connect():
    print('socketio connected!')
    socketio.emit('server_response', {'data': 'connected'},namespace='/table')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-data', methods=['GET'])
def get_data():
    table_rows = db_session.query(TableRow).all()
    table_rows_dict = [row.to_dict() for row in table_rows]
    return jsonify(table_rows_dict)
    

@app.route('/create-row', methods=['POST'])
def create_row():
    row_id = request.form.get('row_id')
    content = request.form.get('content')
    if content:
        content = json.loads(content)
    
    print('create:', row_id, content)
    status = 'waiting'
    source = content[0]

    for x in source.split(','):
        row = db_session.query(TableRow).filter_by(id=row_id).first()

        if not row:
            row = TableRow(id=row_id, source=x.strip(), frequency=content[1], user=content[2], \
                department=content[3], target=content[4], status=status)
            db_session.add(row)
        sensetime_image = check_identical(row.source)
        if sensetime_image:
            row.status = 'identical'
            row.target = sensetime_image
        else:
            row.status = status
            task_queue.put(row)

    db_session.commit()
    return jsonify({"status": "success"})


if __name__ == '__main__':
    print('starting app')
    socketio.run(app, '0.0.0.0', 8080, debug=True, use_reloader=False)
