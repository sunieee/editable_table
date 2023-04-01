from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///editable_table.db'
db = SQLAlchemy(app)

class TableRow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(120), nullable=False)
    frequency = db.Column(db.String(120), nullable=True)
    user = db.Column(db.String(120), nullable=True)
    department = db.Column(db.String(120), nullable=True)
    target = db.Column(db.String(120), nullable=False)
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)
    status = db.Column(db.String(120), nullable=False)


db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-data', methods=['GET'])
def get_data():
    table_rows = TableRow.query.all()
    return jsonify(table_rows)

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
    content = request.form.get('new_content')
    new_row = TableRow(id=row_id, content=content)
    db.session.add(new_row)
    db.session.commit()
    return jsonify({"status": "success", "row_id": new_row.id})


if __name__ == '__main__':
    app.run(debug=True, port=8000)
