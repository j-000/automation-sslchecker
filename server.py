from flask import Flask, render_template, jsonify, request
from main import SSLChecker
import datetime
from flask_cors import CORS
import threading


app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})


def days_delta(domain):
    # Calculate difference in days between expiry date and today
    expiry = datetime.datetime.strptime(domain['expiry'], '%d %b %Y')
    today = datetime.datetime.today()
    return abs(expiry - today).days

def min_daysleft(client):
    # Map days_delta for all domains and return the minimum value
    return min(map(lambda domain: days_delta(domain), client['domains']))


async_threads = []


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/run-all', methods=['POST'])
def api_run_all():
    # Thread is not JSON serializable so using its __repr__() str representation
    threads_repr = list(map(str, async_threads))
    # Do not start a new thread if one already running
    if len(async_threads) > 0:
        return jsonify(success=False, message='Thread already running for all clients.', threads=threads_repr)

    def check_all_async():
        sslchecker = SSLChecker()
        sslchecker.check_all()
        async_threads.pop() # Remove thread from list

    t = threading.Thread(target=check_all_async)
    async_threads.append(t)
    t.start()
    return jsonify(success=True, threads=threads_repr)


@app.route('/api/run/<int:client_id>', methods=['POST'])
def api_run_client(client_id):
    sslchecker = SSLChecker()
    sslchecker.check_client(client_id)
    return jsonify(success=True)


@app.route('/api/clients', methods=['GET', 'POST'])
def api_clients():
    sslchecker = SSLChecker()
    if request.method == 'GET':
        clients = sorted(sslchecker.db['clients'], key=min_daysleft)
    if request.method == 'POST':
        name = request.json.get('name')
        domains = request.json.get('domains')
        # Confirm required data 
        if not name or not domains:
            return jsonify(success=False, message='Missing client name or domains.')
        # Validate domains
        if not all(map(lambda domain: 'url' in domain, domains)):
            return jsonify(success=False, message='Domains list contain invalid data.', domains_received=domains)
        # Add new client
        new_client = sslchecker.add_client(name, domains)
        # Run check for new client
        sslchecker.check_client(new_client['id'])
        # Return new client object (after check)
        updated_client = sslchecker.get_client(new_client['id'])
        return jsonify(success=True, new_client=updated_client)
    return jsonify(clients=clients, last_checked_all=sslchecker.db['last_checked_all'])


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)