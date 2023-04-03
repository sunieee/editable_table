import eventlet
eventlet.monkey_patch()     # 使用eventlet而不是greenlet启动socketio

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime
import json
import queue
import time
import threading

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///editable_table.db'
db = SQLAlchemy(app)
task_queue = queue.Queue()

# 创建一个新的Session工厂
Session = scoped_session(sessionmaker(bind=db.engine))

class TableRow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(120), nullable=False)
    frequency = db.Column(db.String(120), nullable=True)
    user = db.Column(db.String(120), nullable=True)
    department = db.Column(db.String(120), nullable=True)
    target = db.Column(db.String(120), nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now())
    update_time = db.Column(db.DateTime, default=datetime.now())
    status = db.Column(db.String(120), nullable=False)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


db.create_all()
socketio = SocketIO(app, cors_allowed_origins="*")
# 创建一个字典来存储每个worker的状态
worker_count = 3
worker_idle = worker_count

def worker():
    global worker_idle
    while True:
        data = task_queue.get()
        if data is None:
            break
        worker_idle -= 1

        # 创建一个新的Session
        session = Session()

        # 将原始对象与新Session关联
        table_row = session.merge(data)

        print(table_row, table_row.id, table_row.source, table_row.status)
        # 模拟一个耗时任务
        time.sleep(5)
        print({'row_id': table_row.id, 'status': 'uploading'})
        socketio.emit('status_change', {'row_id': table_row.id, 'status': 'uploading'}, namespace='/table')
        
        time.sleep(5)
        print({'row_id': table_row.id, 'status': 'done'})
        socketio.emit('status_change', {'row_id': table_row.id, 'status': 'done'}, namespace='/table')
        table_row.status = 'done'
        table_row.update_time = datetime.now()
        session.commit()
        worker_idle += 1


# 创建三个worker线程
worker_threads = [threading.Thread(target=worker) for _ in range(3)]

# 启动worker线程
for thread in worker_threads:
    thread.start()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-data', methods=['GET'])
def get_data():
    table_rows = TableRow.query.all()
    table_rows_dict = [row.to_dict() for row in table_rows]
    return jsonify(table_rows_dict)

@app.route('/update-row', methods=['POST'])
def update_cell():
    row_id = request.form.get('row_id')
    new_content = request.form.get('content')
    row = TableRow.query.get(row_id)
    if row:
        row.content = new_content
        db.session.commit()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"})

@app.route('/create-row', methods=['POST'])
def create_row():
    row_id = request.form.get('row_id')
    content = request.form.get('content')
    if content:
        content = json.loads(content)
    print('create:', row_id, content)
    status = 'pulling' if worker_idle else 'waiting'
    new_row = TableRow(id=row_id, source=content[0], frequency=content[1], user=content[2], \
        department=content[3], target=content[4], status=status)
    db.session.add(new_row)
    db.session.commit()
    task_queue.put(new_row)
    return jsonify({"status": "success"})


if __name__ == '__main__':
    socketio.run(app, debug=True, port=8000, host='0.0.0.0')
