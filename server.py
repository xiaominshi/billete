from flask import Flask, render_template, request, jsonify
import importlib.util
from pyngrok import ngrok
import sys
import os
import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
# Force-load local logic.py to avoid importing an unrelated module named 'logic'
_logic_path = os.path.join(os.path.dirname(__file__), "logic.py")
_spec = importlib.util.spec_from_file_location("billete_logic", _logic_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
Logic = _mod.Logic
logic = Logic()
print(f" * Logic loaded from: {_logic_path}")
print(f" * Logic module name: {_mod.__name__}")

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
            
        # Use logic to process (source text)
        # logic.process() returns the formatted text string
        result_text = logic.process(code)
        
        # Append Luggage
        hand_count = data.get('hand_count', '1')
        hand_weight = data.get('hand_weight', '8')
        pack_count = data.get('pack_count', '2')
        pack_weight = data.get('pack_weight', '23')
        
        luggage_info = f"\n经济舱往返 欧\n托运行李{pack_count} 件,每件{pack_weight}公斤\n手提行李{hand_count}件{hand_weight} 公斤\n"
        final_result = result_text + luggage_info
        
        # If result is suspiciously empty (only luggage), append debug logs
        if not result_text.strip() and logic.logs:
             final_result += "\n\n[Debug Logs (Render Fix)]:\n" + "\n".join(logic.logs)
        
        # Construct route string for history
        route_str = ""
        if logic.flights:
            if len(logic.flights) == 1:
                route_str = f"{logic.flights[0]['origin']}-{logic.flights[0]['dest']}"
            else:
                full_path = [logic.flights[0]['origin']]
                for f in logic.flights:
                    full_path.append(f['dest'])
                route_str = "-".join(full_path)

        # Extract passengers string for history
        pax_names = [p['name'] for p in logic.passengers]
        pax_str = ", ".join(pax_names)

        # Save to history
        logic.save_to_history(code, final_result, pax_str, route_str)
        
        return jsonify({
            'result': final_result,
            'structured': {
                'passengers': [p['name'] for p in logic.passengers],
                'flights': logic.flights,
                'layovers': logic.layovers,
                'luggage': {
                    'hand_count': hand_count,
                    'hand_weight': hand_weight,
                    'pack_count': pack_count,
                    'pack_weight': pack_weight
                }
            }
        })

    except Exception as e:
        print(f"Error in process: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/history', methods=['GET'])
def get_history():
    return jsonify(logic.get_history())

@app.route('/history', methods=['DELETE'])
def clear_history():
    success = logic.clear_history()
    if success:
        return jsonify({'message': 'History cleared'})
    else:
        return jsonify({'error': 'Failed to clear history'}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    try:
        count = logic.get_today_count()
        response = jsonify({'today_count': count})
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/airports', methods=['GET', 'POST', 'DELETE'])
def manage_airports():
    if request.method == 'GET':
        return jsonify(logic.load_airport_map())
    
    if request.method == 'POST':
        data = request.json
        code = data.get('code')
        name = data.get('name')
        if not code or not name:
            return jsonify({'error': 'Missing code or name'}), 400
        
        logic.update_airport(code, name)
        return jsonify({'success': True, 'code': code, 'name': name})

    if request.method == 'DELETE':
        data = request.json
        code = data.get('code')
        if not code:
            return jsonify({'error': 'Missing code'}), 400
        
        if logic.delete_airport(code):
             return jsonify({'success': True, 'message': f'Deleted {code}'})
        else:
             return jsonify({'error': 'Failed to delete'}), 500

@app.route('/airports/import', methods=['POST'])
def import_airports():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        content = file.read().decode('utf-8', errors='ignore')
        
        total = 0
        inserted = 0
        skipped = []
        
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if ":" not in line:
                skipped.append(f"Invalid format: {raw_line}")
                continue
            code, name = line.split(":", 1)
            code = code.strip().upper()
            name = name.strip()
            if not code or not name:
                skipped.append(f"Missing code or name: {raw_line}")
                continue
            try:
                logic.update_airport(code, name)
                inserted += 1
            except Exception as e:
                skipped.append(f"DB error for {code}: {e}")
            finally:
                total += 1
        
        latest_map = logic.load_airport_map()
        
        return jsonify({
            'success': True,
            'total': total,
            'inserted': inserted,
            'skipped': skipped,
            'map': latest_map
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/airports/export', methods=['GET'])
def export_airports():
    try:
        airport_map = logic.load_airport_map()
        # Sort by code
        lines = []
        for code in sorted(airport_map.keys()):
            name = airport_map[code]
            lines.append(f"{code}:{name}")
        
        content = "\n".join(lines)
        
        # Create a response with the content
        from flask import Response
        return Response(
            content,
            mimetype="text/plain",
            headers={"Content-disposition": "attachment; filename=airports_export.txt"}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_ics', methods=['GET'])
def download_ics():
    try:
        ics_content = logic.generate_ics()
        if not ics_content:
             return jsonify({'error': 'No flight data to generate ICS'}), 400
             
        from flask import Response
        return Response(
            ics_content,
            mimetype="text/calendar",
            headers={"Content-disposition": "attachment; filename=itinerary.ics"}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/version', methods=['GET'])
def version():
    # Simple health/version info
    return jsonify({
        "module": _mod.__name__,
        "path": _logic_path,
        "has_year_field": any('year' in f for f in logic.flights) if logic.flights else False
    })

@app.route('/template_info', methods=['GET'])
def template_info():
    try:
        searchpath = getattr(app.jinja_loader, 'searchpath', [])
        return jsonify({
            "searchpath": searchpath
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Optional: Open ngrok tunnel if command line argument provided
    use_ngrok = len(sys.argv) > 1 and sys.argv[1] == '--public'
    
    if use_ngrok:
        try:
            # Set your authtoken if you haven't already (optional but recommended)
            token = os.getenv("NGROK_AUTH_TOKEN")
            if token:
                ngrok.set_auth_token(token)
            else:
                print("Warning: NGROK_AUTH_TOKEN not found in .env")
            # Ensure previous tunnels are closed
            try:
                ngrok.kill()
            except Exception:
                pass
            # Open a HTTP tunnel on the default port 5000
            public_url = ngrok.connect(5000).public_url
            print(f" * Public URL: {public_url}")
            print(" * Share this URL with others to access the service.")
        except Exception as e:
            print(f" * Ngrok failed to start: {e}")
            print(" * Fallback to local/LAN service. Access via http://127.0.0.1:5000 or your LAN IP.")
    
    app.run(host='0.0.0.0', port=5000, debug=True)