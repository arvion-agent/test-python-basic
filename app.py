from flask import Flask, url_for, jsonify, request, views, abort
import json
import sqlite3
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, text

app = Flask(__name__)
# Create in-memory SQLite database
engine = create_engine('sqlite:///:memory:')
metadata = MetaData()

# Define the Item table
items_table = Table(
    'item', 
    metadata, 
    Column('id', Integer, primary_key=True),
    Column('name', String(100), nullable=False)
)

# Create tables
metadata.create_all(engine)

json_encoder = json.JSONEncoder()

def get_app_context_data():
    return app.app_context()

def get_all_items_raw():
    """Get all items using raw SQL with engine.connect"""
    with engine.connect() as conn:
        result = conn.execute(text('SELECT id, name FROM item'))
        items = [{'id': row[0], 'name': row[1]} for row in result]
    return items

def get_item_by_id_raw(item_id):
    """Get a specific item using raw SQL with engine.connect"""
    with engine.connect() as conn:
        result = conn.execute(text('SELECT id, name FROM item WHERE id = :id'), {'id': item_id})
        row = result.first()
    if row is None:
        return None
    return {'id': row[0], 'name': row[1]}

def create_item_raw(item_data):
    """Create a new item using raw SQL with engine.begin"""
    with engine.begin() as conn:
        conn.execute(
            text('INSERT INTO item (id, name) VALUES (:id, :name)'),
            {'id': item_data.get('id'), 'name': item_data.get('name')}
        )
    return item_data

class ItemsView(views.MethodView):
    def get(self):
        # Using connection-based execution instead of engine.execute
        items = get_all_items_raw()
        return jsonify(items)
    
    def post(self):
        new_item = json.loads(request.data)
        # Using engine.begin for insert
        create_item_raw(new_item)
        return jsonify(new_item), 201

app.add_url_rule('/api/items', view_func=ItemsView.as_view('items_api'), methods=['GET', 'POST'])

@app.route('/api/items/<int:item_id>')
def get_item(item_id):
    # Using connection-based execution to fetch the item
    item_dict = get_item_by_id_raw(item_id)
    
    if not item_dict:
        abort(404)
    
    other_item_url = url_for(endpoint='get_item', item_id=item_id+1, _external=True)
    item_dict['next_item'] = other_item_url
    
    response_data = json.dumps(item_dict)
    
    return app.response_class(
        response=response_data,
        status=200,
        mimetype='application/json'
    )

@app.route('/api/items/bulk', methods=['POST'])
def bulk_create_items():
    """Bulk create items using engine.begin for transaction"""
    items_data = request.json
    
    # Create a list of dictionaries for bulk insert
    items_to_insert = [{'id': item['id'], 'name': item['name']} for item in items_data]
    
    # Use executemany for bulk operations within a transaction
    with engine.begin() as conn:
        conn.execute(
            text('INSERT INTO item (id, name) VALUES (:id, :name)'),
            items_to_insert
        )
    
    return jsonify({"message": f"Created {len(items_data)} items"}), 201

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

# Seed the database with initial data
def seed_database():
    # Check if we already have items using connection-based execution
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM item'))
        count = result.scalar()
    
    if count == 0:
        # Insert seed data using engine.begin
        with engine.begin() as conn:
            conn.execute(
                text('INSERT INTO item (id, name) VALUES (:id, :name)'),
                [
                    {'id': 1, 'name': 'Item 1'},
                    {'id': 2, 'name': 'Item 2'},
                    {'id': 3, 'name': 'Item 3'}
                ]
            )


if __name__ == '__main__':
    # Initialize database
    seed_database()
    
    app.run(debug=True)
