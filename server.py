from flask import Flask, render_template, request, jsonify
from logic import Logic
from pyngrok import ngrok
import sys
import os

app = Flask(__name__)
logic = Logic()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        data = request.json
        code = data.get('code', '')
        if not code:
            return jsonify({'error': 'No code provided'}), 400
            
        # Use logic to process
        result_text = logic.process(code)
        
        # Append Luggage
        hand_count = data.get('hand_count', '1')
        hand_weight = data.get('hand_weight', '8')
        pack_count = data.get('pack_count', '2')
        pack_weight = data.get('pack_weight', '23')
        
        luggage_info = f"\n经济舱往返 欧\n托运行李{pack_count} 件,每件{pack_weight}公斤\n手提行李{hand_count}件{hand_weight} 公斤\n"
        final_result = result_text + luggage_info
        
        return jsonify({'result': final_result})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/airports', methods=['GET'])
def get_airports():
    return jsonify(logic.airport_map)

@app.route('/airports', methods=['POST'])
def update_airport():
    try:
        data = request.json
        code = data.get('code', '').upper()
        name = data.get('name', '')
        
        if not code or not name:
             return jsonify({'error': 'Missing code or name'}), 400
             
        logic.update_airport(code, name)
        
        return jsonify({'message': f'Success: {code} -> {name}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Optional: Open ngrok tunnel if command line argument provided
    use_ngrok = len(sys.argv) > 1 and sys.argv[1] == '--public'
    
    if use_ngrok:
        # Set your authtoken if you haven't already (optional but recommended)
        ngrok.set_auth_token("36wYtOWEJDNl3vmUYOyXguf1IKF_2tFv2wBFAjZwsLiLTjTZG")
        
        # Open a HTTP tunnel on the default port 5000
        public_url = ngrok.connect(5000).public_url
        print(f" * Public URL: {public_url}")
        print(" * Share this URL with others to access the service.")
    
    app.run(host='0.0.0.0', port=5000)
