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

# Ensure database module is reloaded on restart
import sys
if 'database' in sys.modules:
    import database
    importlib.reload(database)

# Force-load local logic.py to avoid importing an unrelated module named 'logic'
_logic_path = os.path.join(os.path.dirname(__file__), "logic.py")
_spec = importlib.util.spec_from_file_location("billete_logic", _logic_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
Logic = _mod.Logic
# logic = Logic() # REMOVED: Global instance is unsafe for concurrency
print(f" * Logic loaded from: {_logic_path}")
print(f" * Logic module name: {_mod.__name__}")

@app.route('/')
def home():
    return render_template('index.html')

import threading

@app.route('/process', methods=['POST'])
def process():
    try:
        data = request.json
        code = data.get('code', '')
        
        # Helper for safe int conversion
        def safe_int(val, default):
            try:
                return int(val)
            except (ValueError, TypeError):
                return default

        hand_count = safe_int(data.get('hand_count'), 1)
        hand_weight = safe_int(data.get('hand_weight'), 8)
        pack_count = safe_int(data.get('pack_count'), 2)
        pack_weight = safe_int(data.get('pack_weight'), 23)
        
        # Instantiate Logic per request to avoid state leakage
        current_logic = Logic()
        
        # Safe unpacking of process result
        process_result = current_logic.process(code)
        if isinstance(process_result, tuple) and len(process_result) == 2:
            result_text, structured_data = process_result
        else:
            # Handle unexpected return type or error
            result_text = str(process_result)
            structured_data = None
        
        # Synchronous History Saving for Debugging
        # We removed threading to ensure we capture any errors and ensure execution completes
        def save_sync(logic_instance):
            try:
                print("DEBUG: Starting save_sync...")
                # Add luggage info to structured data for history
                if structured_data:
                    structured_data['luggage'] = {
                        'hand_count': hand_count, 'hand_weight': hand_weight,
                        'pack_count': pack_count, 'pack_weight': pack_weight
                    }
                
                # If we have structured data, save that too
                import json
                data_json = json.dumps(structured_data, ensure_ascii=False) if structured_data else "{}"
                
                # Determine route info for summary
                route_info = "Unknown Route"
                if structured_data and structured_data.get('flights'):
                    f = structured_data['flights']
                    if len(f) > 0:
                        origin = f[0]['origin']
                        final_dest = f[-1]['dest']
                        
                        # Check for return trip logic
                        is_return_trip = False
                        turnaround = None
                        
                        # Strategy: Look for the first flight marked as 'is_return'
                        for flt in f:
                            if flt.get('is_return'):
                                is_return_trip = True
                                turnaround = flt['origin']
                                break
                        
                        # Fallback Strategy: If logic didn't mark is_return but start == end and multiple segments
                        if not is_return_trip and len(f) > 1 and final_dest == origin:
                            is_return_trip = True
                            # Assume the last leg's origin is the turnaround point
                            turnaround = f[-1]['origin']

                        if is_return_trip and turnaround:
                            route_info = f"{origin}-{turnaround}-{origin}"
                        else:
                            # One way or complex open jaw
                            if len(f) == 1:
                                route_info = f"{origin}-{final_dest}"
                            else:
                                # For multi-leg one-way, maybe show intermediate? For now just Start-End
                                route_info = f"{origin}-{final_dest}"
                
                # Passenger Info
                pax_info = "Unknown Pax"
                if structured_data and structured_data.get('passengers'):
                    pax_list = [p['name'] if isinstance(p, dict) else str(p) for p in structured_data['passengers']]
                    pax_info = ", ".join(pax_list)
                
                # Sanitize code: remove null bytes which break DB
                safe_code = code.replace('\x00', '') if code else ''
                
                # Sanitize other fields too - raw code might propagate null bytes into result/pax
                safe_result = result_text.replace('\x00', '') if result_text else ''
                safe_pax = pax_info.replace('\x00', '') if pax_info else ''
                safe_route = route_info.replace('\x00', '') if route_info else ''
                
                print(f"DEBUG: calling logic.save_to_history. Safe code len: {len(safe_code)}")
                logic_instance.save_to_history(safe_code, safe_result, safe_pax, safe_route, data_json=data_json)
                print("DEBUG: save_to_history completed.")
            except Exception as e:
                print(f"Sync Save Error: {e}")
                import traceback
                traceback.print_exc()

        # Run synchronously
        save_sync(current_logic)
        
        # Inject Luggage into response for immediate UI update
        if structured_data:
            structured_data['luggage'] = {
                'hand_count': hand_count,
                'hand_weight': hand_weight,
                'pack_count': pack_count,
                'pack_weight': pack_weight
            }
            
        return jsonify({'result': result_text, 'structured': structured_data})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/history', methods=['GET'])
def get_history():
    # Use a temporary logic instance or call DB directly
    temp_logic = Logic()
    return jsonify(temp_logic.get_history())

@app.route('/history', methods=['DELETE'])
def clear_history():
    temp_logic = Logic()
    # If JSON provided with 'id', delete single item
    if request.is_json:
        data = request.json
        if 'id' in data:
             if temp_logic.delete_history_item(data['id']):
                 return jsonify({'success': True, 'message': 'Deleted item'})
             else:
                 return jsonify({'error': 'Failed to delete item'}), 404
                 
    # Otherwise clear all
    success = temp_logic.clear_history()
    if success:
        return jsonify({'message': 'History cleared'})
    else:
        return jsonify({'error': 'Failed to clear history'}), 500

@app.route('/history/update', methods=['POST'])
def update_history():
    try:
        import database
        data = request.json
        history_id = data.get('id')
        cost = data.get('cost')
        price = data.get('price')
        data_json = data.get('data_json') # Can be passed as string or object
        
        if not history_id:
            return jsonify({'error': 'Missing history ID'}), 400
            
        if isinstance(data_json, dict):
            import json
            data_json = json.dumps(data_json)
            
        success = database.update_history_entry(history_id, cost, price, data_json)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to update'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    try:
        temp_logic = Logic()
        count = temp_logic.get_today_count()
        response = jsonify({'today_count': count})
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats/detailed', methods=['GET'])
def get_detailed_stats():
    try:
        import database
        days = request.args.get('days', 7, type=int)
        
        # Use optimized single-query aggregation to reduce latency on Render
        stats = database.get_detailed_stats_aggregated(days)
        return jsonify(stats)
    except Exception as e:
        print(f"Stats Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/history/export', methods=['GET'])
def export_history():
    try:
        import database
        import csv
        import io
        from flask import Response
        
        data = database.get_all_history_for_export()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['ID', 'Timestamp', 'Raw Code', 'Passengers', 'Route'])
        
        # Rows
        for row in data:
            writer.writerow([
                row['id'],
                row['timestamp'],
                row['code'],
                row['passenger_info'],
                row['route_info']
            ])
            
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=history_export.csv"}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/airports', methods=['GET', 'POST', 'DELETE'])
def manage_airports():
    temp_logic = Logic()
    if request.method == 'GET':
        return jsonify(temp_logic.load_airport_map())
    
    if request.method == 'POST':
        data = request.json
        code = data.get('code')
        name = data.get('name')
        if not code or not name:
            return jsonify({'error': 'Missing code or name'}), 400
        
        temp_logic.update_airport(code, name)
        return jsonify({'success': True, 'code': code, 'name': name})

    if request.method == 'DELETE':
        data = request.json
        code = data.get('code')
        if not code:
            return jsonify({'error': 'Missing code'}), 400
        
        if temp_logic.delete_airport(code):
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
        batch_list = []
        
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
            
            # Add to batch list
            batch_list.append({"code": code, "name": name})
            total += 1

        # Process batch
        temp_logic = Logic()
        if batch_list:
            try:
                if temp_logic.update_airports_batch(batch_list):
                    inserted = len(batch_list)
                else:
                    skipped.append("Batch insert failed in database.")
            except Exception as e:
                skipped.append(f"Batch insert error: {e}")
        
        latest_map = temp_logic.load_airport_map()
        
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
        temp_logic = Logic()
        airport_map = temp_logic.load_airport_map()
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
        # Note: logic.flights is stateful. We cannot generate ICS without processing first.
        # This endpoint assumes 'logic' has state from a previous request, which is flawed in REST.
        # Ideally, the client should send the flight data back, or we retrieve it from history ID.
        # For now, we'll return an error or placeholder as we removed the global logic instance.
        return jsonify({'error': 'ICS generation requires flight data context. Please use history export or client-side generation.'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/version', methods=['GET'])
def version():
    # Simple health/version info
    temp_logic = Logic()
    return jsonify({
        "module": _mod.__name__,
        "path": _logic_path,
        "has_year_field": True # Logic instantiated fresh, so we don't know flights state, but code supports it
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

@app.route('/db/health', methods=['GET'])
def db_health():
    try:
        import database
        from sqlalchemy import text as sq_text
        dialect = database.engine.dialect.name
        with database.engine.connect() as conn:
            ok = conn.execute(sq_text("SELECT 1")).scalar()
        return jsonify({"dialect": dialect, "ok": bool(ok)})
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
