import pytest
import json as std_json
from app import app, engine, metadata, items_table
from sqlalchemy import text

@pytest.fixture
def client():
    app.config['TESTING'] = True
    
    # Clear and recreate tables
    metadata.drop_all(engine)
    metadata.create_all(engine)
    
    # Seed test data using connection based execution
    with engine.begin() as conn:
        conn.execute(
            text('INSERT INTO item (id, name) VALUES (:id, :name)'),
            [
                {'id': 1, 'name': 'Item 1'},
                {'id': 2, 'name': 'Item 2'},
                {'id': 3, 'name': 'Item 3'}
            ]
        )
    
    with app.test_client() as client:
        yield client
        
    # Clean up
    metadata.drop_all(engine)


def test_get_items(client):
    """Test the get_items endpoint using the class-based view with connection based execution"""
    response = client.get('/api/items')
    assert response.status_code == 200
    assert len(response.json) == 3
    assert response.json[0]['name'] == 'Item 1'


def test_post_items(client):
    """Test posting to the items endpoint using connection based execution"""
    new_item = {"name": "New Item", "id": 4}
    response = client.post(
        '/api/items', 
        data=std_json.dumps(new_item),
        content_type='application/json'
    )
    assert response.status_code == 201
    assert response.json["name"] == "New Item"
    
    # Verify item was added to database using connection based execution
    with engine.connect() as conn:
        result = conn.execute(text('SELECT name FROM item WHERE id = :id'), {'id': 4})
        row = result.first()
    assert row is not None
    assert row[0] == "New Item"


def test_bulk_create_items(client):
    """Test bulk creation of items using connection based execution"""
    items = [
        {"name": "Bulk Item 1", "id": 10},
        {"name": "Bulk Item 2", "id": 11},
        {"name": "Bulk Item 3", "id": 12}
    ]
    
    response = client.post(
        '/api/items/bulk',
        json=items,
        content_type='application/json'
    )
    
    assert response.status_code == 201
    assert "Created 3 items" in response.json["message"]
    
    # Verify items were added using connection based execution
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM item WHERE id IN (10, 11, 12)'))
        count = result.scalar()
    assert count == 3


def test_get_item(client):
    """Test the get_item endpoint which uses connection based execution"""
    response = client.get('/api/items/1')
    assert response.status_code == 200
    assert response.json['id'] == 1
    assert response.json['name'] == 'Item 1'
    assert 'next_item' in response.json


def test_get_nonexistent_item(client):
    """Test getting a non-existent item using connection based execution"""
    response = client.get('/api/items/999')
    assert response.status_code == 404


def test_404_handler(client):
    """Test the custom error handler"""
    response = client.get('/nonexistent-route')
    assert response.status_code == 404
    assert response.json['error'] == 'Not found' 
