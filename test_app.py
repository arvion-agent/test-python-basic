import pytest
import json as std_json
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_items(client):
    """Test the get_items endpoint using the class-based view"""
    response = client.get('/api/items')
    assert response.status_code == 200
    assert len(response.json) == 3

def test_post_items(client):
    """Test posting to the items endpoint which uses flask.json.loads"""
    new_item = {"name": "New Item", "id": 4}
    response = client.post(
        '/api/items', 
        data=std_json.dumps(new_item),
        content_type='application/json'
    )
    assert response.status_code == 201
    assert response.json["name"] == "New Item"

def test_get_item(client):
    """Test the get_item endpoint which uses multiple Flask 1.x features"""
    response = client.get('/api/items/1')
    assert response.status_code == 200
    assert response.json['id'] == 1
    assert response.json['name'] == 'Item 1'
    assert 'next_item' in response.json

def test_404_handler(client):
    """Test the custom error handler that has a different signature in Flask 2.x"""
    response = client.get('/nonexistent-route')
    assert response.status_code == 404
    assert response.json['error'] == 'Not found' 
