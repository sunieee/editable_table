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
import time
import threading
import signal
import sys
import subprocess
from utils import check_identical, pull_image, upload_image

app = Flask(__name__)
task_queue = queue.Queue()

engine = create_engine('sqlite:///editable_table.db?check_same_thread=False', echo=True)
Base = declarative_base()

def check_output(_CMD, **kwargs):
    if type(_CMD) == str:
        _CMD = _CMD.split()
    return subprocess.check_output(_CMD, **kwargs).decode("utf-8", "ignore").replace("\"", "").strip()


def get_local_image_id(image_name):
    try:
        return check_output("docker image inspect --format '{{.Id}}' " + image_name)
    except:
        return ''

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

class Worker:
    worker_count = 3
    worker_idle = worker_count

    def __init__(self):
        self.thread = eventlet.spawn(self.run)
        print('spawn sussess!')

    def run(self):
        while True:
            try:
                self.work()
            except queue.Empty:
                eventlet.sleep(1)
    
    def work(self):
        data = task_queue.get(timeout=0.5)
        if data is None:
            return
        self.worker_idle -= 1

        # 将原始对象与新Session关联
        row = db_session.merge(data)
        print(row, row.id, row.source, row.status)

        row.status = 'pulling'
        row.update_time = datetime.now()
        socketio.emit('status_change', row.to_dict(), namespace='/table')

        pull_image(row.source)

        row.status = 'uploading'
        row.update_time = datetime.now()
        socketio.emit('status_change', row.to_dict(), namespace='/table')
        
        ret = upload_image(row.source)
            
        row.status = 'done'
        row.target = ret
        row.update_time = datetime.now()
        socketio.emit('status_change', row.to_dict(), namespace='/table')
        
        db_session.commit()
        self.worker_idle += 1


# 在gevent与threading矛盾：https://xiaorui.cc/archives/4710
# 创建三个worker线程
workers = [Worker() for _ in range(Worker.worker_count)]

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

@app.route('/update-row', methods=['POST'])
def update_row():
    row_id = request.form.get('row_id')
    content = request.form.get('content')
    if content:
        content = json.loads(content)
    print(content)
    row = db_session.query(TableRow).filter_by(id=row_id).first()
    if not row:
        return jsonify({"status": "error", "reason": "no such row"})
    row.frequency = content[1]
    row.user = content[2]
    row.department = content[3]
    if row.source != content[0]:
        row.source = content[0]
        row.status = 'waiting'
        row.update_time = datetime.now()
        sensetime_image = check_identical(row.source)
        if sensetime_image:
            row.status = 'identical'
            row.target = sensetime_image
        else:
            task_queue.put(row)
    db_session.commit()
    return jsonify({"status": "success", 'row': row.to_dict()})
    

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


@app.route('/delete-row', methods=['POST'])
def delete_row():
    row_id = request.form.get('row_id')
    row = db_session.query(TableRow).filter_by(id=row_id).first()
    if not row:
        return jsonify({"status": "error", "reason": "no such row"})
    db_session.delete(row)
    db_session.commit()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    print('starting app')
    socketio.run(app, '0.0.0.0', 8080, debug=True, use_reloader=False)
