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
        
        # Extract Metadata for history
        pax_names = [p['name'] for p in logic.passengers]
        pax_str = ", ".join(pax_names)
        
        route_str = ""
        if logic.flights:
            # Simple Route: First Origin -> Last Destination
            # Or list all stops? "MAD->PEK, PEK->MAD"
            # Let's do: Origin -> Dest
            # If multiple flights, maybe connect them?
            # User wants "Start End".
            
            # Let's try to make a compact route string: MAD-PEK
            # taking first origin and last dest might be misleading if it's round trip MAD-PEK-MAD.
            # So maybe "MAD-PEK-MAD" if return?
            
            stops = [logic.flights[0]['origin']]
            for f in logic.flights:
                stops.append(f['dest'])
            
            # Remove consecutive duplicates (if any, though origin of next should be dest of prev)
            # Actually standard route string: MAD-PEK / PEK-MAD
            
            if len(logic.flights) == 1:
                route_str = f"{logic.flights[0]['origin']}-{logic.flights[0]['dest']}"
            else:
                 # Check if round trip?
                 stops_short = [logic.flights[0]['origin'], logic.flights[-1]['dest']]
                 route_str = "-".join(stops_short)
                 # Add intermediate? No, keep it short. "MAD-MAD" implies round trip.
                 
                 # Better: Construct full path "MAD-PEK-MAD"
                 full_path = [logic.flights[0]['origin']]
                 for f in logic.flights:
                     full_path.append(f['dest'])
                 route_str = "-".join(full_path)

        # Save to history
        logic.save_to_history(code, final_result, pax_str, route_str)
        
        return jsonify({'result': final_result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/history', methods=['GET'])
def get_history():
    return jsonify(logic.get_history())

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
