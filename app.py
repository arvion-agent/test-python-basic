from flask import Flask, url_for, jsonify, request, views, abort
import json

app = Flask(__name__)

json_encoder = json.JSONEncoder()

def get_app_context_data():
    return "No app context"

class ItemsView(views.MethodView):
    def get(self):
        items = [
            {'id': 1, 'name': 'Item 1'},
            {'id': 2, 'name': 'Item 2'},
            {'id': 3, 'name': 'Item 3'}
        ]
        return jsonify(items)
    
    def post(self):
        new_item = json.loads(request.data)
        return jsonify(new_item), 201

app.add_url_rule('/api/items', view_func=ItemsView.as_view('items_api'), methods=['GET', 'POST'])

@app.route('/api/items/<int:item_id>')
def get_item(item_id):
    item = {'id': item_id, 'name': f'Item {item_id}'}
    encoded = json_encoder.encode(item)
    
    other_item_url = url_for(endpoint='get_item', item_id=item_id+1, _external=True)
    
    item['next_item'] = other_item_url
    
    response_data = json.dumps(item)
    
    return app.response_class(
        response=response_data,
        status=200,
        mimetype='application/json'
    )

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
