import re
import os
import datetime
import json
import time
import requests
import airportsdata
from bs4 import BeautifulSoup
import database

class Logic:
    def __init__(self):
        self.passengers = []
        self.flights = []
        self.layovers = []
        self.base_year = datetime.datetime.now().year
        self.current_year = self.base_year
        self.last_month = None
        try:
             self.airports_db = airportsdata.load('IATA')
        except Exception as e:
            print(f"Failed to load airportsdata: {e}")
            self.airports_db = {}
        
        # Initialize map from DB
        try:
             self.airport_map = database.get_all_airports()
        except:
             self.airport_map = {}

    def load_airport_map(self):
        return database.get_all_airports()
    
    def reload_airport_map(self):
        self.airport_map = database.get_all_airports()

    def save_airport_map(self):
        pass

    def update_airport(self, code, name):
        database.upsert_airport(code, name)
        self.airport_map[code] = name

    def delete_airport(self, code):
        """Removes an airport from the database and local map."""
        if database.delete_airport(code):
            if code in self.airport_map:
                del self.airport_map[code]
            return True
        return False

    def fetch_online_airport_name(self, code):
        """
        Fallback to online search using a Chinese source.
        Target: airport.supfree.net
        """
        try:
            url = f"http://airport.supfree.net/search.asp?s={code}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            # Timeout is important
            resp = requests.get(url, headers=headers, timeout=5)
            # This site uses legacy encoding
            resp.encoding = 'gbk'
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # The result is usually in a table
                # Look for the first row that contains the code
                
                # Table structure is complex, but the data often looks like:
                # <td>CODE</td> ... <td>City Name</td> ... <td>Country</td>
                
                # Simplified strategy: Find the string in the body that matches predictable text
                # Or find the table cell with the code, and look at siblings.
                
                # supfree structure:
                # <th>IATA代码</th> ... <th>城市</th>
                
                # Find all rows
                rows = soup.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        # col 0 might be IATA, col 1 might be City, etc.
                        # It varies, but usually:
                        # Code | City | Airport Name | Country
                        # Let's clean text
                        txts = [c.get_text().strip() for c in cols]
                        if code in txts:
                            # Found the row!
                            # Let's guess indices. 
                            # Usually index 1 is City (Chinese)
                            # index 3 might be Country
                            
                            # Let's try to grab whatever looks like Chinese
                            possible_name = txts[1] 
                            # Check if it's the code itself
                            if possible_name == code:
                                possible_name = txts[2]
                                
                            # If we found something good
                            if possible_name and possible_name != code:
                                return possible_name
                                
        except Exception as e:
            print(f"Chinese lookup failed for {code}: {e}")
        
        # If Chinese fails, try English fallback DB or return Code
        return None

    def resolve_airport(self, code):
        """
        Resolve airport code to name using 3 levels:
        1. Local fly.txt (Priority)
        2. Online Scraping (Priority for Chinese)
        3. Offline airportsdata DB (Fallback, English)
        """
        code = code.upper()
        
        # 1. Local
        if code in self.airport_map:
            return self.airport_map[code]
        
        # 2. Online Chinese Fallback (Preferred for Language)
        online_name = self.fetch_online_airport_name(code)
        if online_name:
             print(f"Found online (Chinese): {code} -> {online_name}")
             self.update_airport(code, online_name)
             return online_name

        # 3. Offline DB (English Fallback)
        if code in self.airports_db:
             data = self.airports_db[code]
             city = data.get('city', '')
             name = data.get('name', '')
             final_name = city if city else name
             
             print(f"Found offline (English): {code} -> {final_name}")
             self.update_airport(code, final_name)
             return final_name
             
        # Not found
        return code

    def get_history(self):
        return database.get_history_entries(limit=50)

    def clear_history(self):
        return database.clear_history_entries()

    def save_to_history(self, code, result, passenger_info="", route_info=""):
        try:
            database.add_history_entry(code, result, passenger_info, route_info)
        except Exception as e:
            print(f"Error saving history: {e}")

    def merge_lines_without_sequence_number(self, text):
        lines = text.split("\n")
        output = []
        previous_line = None

        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line starts with a number (e.g., "1.", "1 ", "14")
            if re.match(r'^\d+.*', line):
                if previous_line is not None:
                    output.append(previous_line)
                previous_line = line
            else:
                if previous_line is not None:
                    previous_line += " " + line
                else:
                    previous_line = line
        
        if previous_line is not None:
            output.append(previous_line)
            
        return "\n".join(output)

    def replace_number(self, text):
        return re.sub(r'\d+', '', text)

    def contain_month(self, text):
        months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        return any(m in text for m in months)

    def get_month_num(self, month_str):
        months = {
            "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06",
            "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"
        }
        return months.get(month_str, "-1")

    def parse_passengers(self, line, scanner):
        # 1.XIAO/YIYI
        parts = line.split(".")
        # Start from index 1 because index 0 is the number
        for i in range(1, len(parts)):
            p_name = self.replace_number(parts[i]).strip()
            if p_name:
                self.passengers.append({"name": p_name, "id": f"P{len(self.passengers)+1}", "passport": "", "ticket": ""})

    def parse_ssr_docs(self, line_parts):
        # SSR DOCS CA HK1 P/CHN/EL9792535/CHN/22SEP93/F/26FEB34/XIAO/YIYI
        try:
            # Find the part that contains P/
            data_part = None
            for part in line_parts:
                if part.startswith("P/"):
                    data_part = part
                    break
            
            # If not found directly, it might be split across parts (though merge_lines should handle it)
            # In the user input example: 9 SSR DOCS ... P/CHN/...
            # line_parts would look like: ['9', 'SSR', 'DOCS', 'CA', 'HK1', 'P/CHN/...']
            
            if not data_part:
                # Fallback: look for the long string
                for part in line_parts:
                    if "P/" in part and "/" in part:
                         data_part = part
                         break
            
            if data_part:
                 # It might be split like P/CHN/EL9792535/CHN/22SEP93/F/26FEB34/XIAO/Y IYI (space merged)
                 # Reconstruct if needed, but merge_lines should have made it "P/CHN/.../XIAO/Y IYI"
                 # Actually, the slashes are key.
                 
                 # Let's look at the specific example:
                 # P/CHN/EL9792535/CHN/22SEP93/F/26FEB34/XIAO/Y IYI
                 # The " IYI" part comes from the merge.
                 
                 # Clean up spaces
                 data_part = data_part.replace(" ", "")
                 
                 split_data = data_part.split("/")
                 # Format: P / CHN / PASSPORT / CHN / DOB / GENDER / EXPIRY / SURNAME / NAME
                 # indices: 0   1       2        3     4      5        6        7       8
                 
                 if len(split_data) >= 3:
                     passport = split_data[2]
                     # Assign to passenger
                     # If multiple passengers, we need to match names or ID. 
                     # The Java code logic: if >1 pax, check ID at end of split? 
                     # Wait, Java code: String id = data_split[data_split.length-1];
                     # In the example: .../XIAO/YIYI -> split gives YIYI as last?
                     # Actually standard DOCS format ends with Surname/Firstname.
                     
                     # For now, simplistic assignment:
                     if len(self.passengers) == 1:
                         self.passengers[0]["passport"] = passport
                     else:
                         # Try to match name?
                         # The Java code logic was a bit specific to their input format.
                         # "P1" might be in the line?
                         pass
        except Exception as e:
            print(f"Error parsing SSR DOCS: {e}")

    def parse_fa_pax(self, line_parts):
        # 14 FA PAX 999-6690500729/ETCA/...
        try:
            # Find ticket number part
            ticket_part = None
            for part in line_parts:
                if "FA" in part or "PAX" in part:
                    continue
                if "-" in part and "/" in part:
                    ticket_part = part
                    break
            
            if ticket_part:
                 ticket_data = ticket_part.split("/")
                 ticket_num = ticket_data[0] # 999-6690500729
                 
                 if len(self.passengers) == 1:
                     self.passengers[0]["ticket"] = ticket_num
                 else:
                     # Match ID logic if needed
                     pass
        except Exception as e:
            print(f"Error parsing FA PAX: {e}")

    def parse_flight(self, line_parts):
        # 2 CA 908 L 10APR 3 MADPEK HK1 1 1310 0600+1 *1A/E*
        try:
            # Skip sequence number (index 0)
            # CA 908 L 10APR ...
            
            # Find date part (contains month)
            date_idx = -1
            for i, part in enumerate(line_parts):
                if self.contain_month(part):
                    date_idx = i
                    break
            
            if date_idx != -1:
                flight_id = "".join(line_parts[1:date_idx-1]) # CA 908 (L is class, maybe part of ID?)
                # Java code: flight_id = scline.next() + scline.next() (before date loop)
                # In "CA 908 L 10APR", Java loop consumes until date.
                
                # Let's take parts before date.
                # "CA", "908", "L"
                # Java code constructs flight_id from first two tokens usually? 
                # No, it does:
                # String vuelo_id = scline.next();
                # vuelo_id = vuelo_id + scline.next();
                # So "CA908".
                
                flight_id = line_parts[1] + line_parts[2] # CA908
                
                date_str = line_parts[date_idx] # 10APR
                
                # Origin/Dest is usually after date?
                # 10APR 3 MADPEK
                # "3" is day of week?
                # MADPEK is next.
                
                # Java: 
                # scline.next(); (skips "3"?)
                # String ori_des = scline.next();
                
                ori_des_idx = date_idx + 2
                if ori_des_idx >= len(line_parts):
                     # Not a standard flight line (e.g. TK line)
                     return

                ori_des = line_parts[ori_des_idx] # MADPEK
                
                ori = ori_des[:3]
                des = ori_des[3:]
                
                # Map airports (Auto-Resolve)
                ori_name = self.resolve_airport(ori)
                des_name = self.resolve_airport(des)
                
                # Times
                # HK1 1 1310 0600+1
                # Java skips next (HK1)
                # String hora_ini = scline.next();
                
                # We need to find the times. They look like 4 digits.
                time_idx = -1
                for i in range(ori_des_idx + 1, len(line_parts)):
                    if re.match(r'^\d{4}$', line_parts[i]) or re.match(r'^\d{4}\+\d$', line_parts[i]):
                        time_idx = i
                        break
                
                if time_idx != -1:
                    start_time = line_parts[time_idx]
                    end_time = line_parts[time_idx+1]
                    
                    # Handle +1 in end_time
                    next_day = False
                    if "+" in end_time:
                        next_day = True
                        end_time = end_time.split("+")[0]
                    
                    # Format times (insert :)
                    start_time_fmt = f"{start_time[:2]}:{start_time[2:]}"
                    end_time_fmt = f"{end_time[:2]}:{end_time[2:]}"
                    
                    # Month/Day
                    day = date_str[:2]
                    month_str = date_str[2:]
                    month = self.get_month_num(month_str)

                    # Calculate Duration and Arrival Date
                    duration_fmt = ""
                    arrival_date_fmt = ""
                    
                    try:
                        # 1. Resolve Timezones
                        import pytz
                        
                        tz_origin_str = 'UTC'
                        tz_dest_str = 'UTC'
                        
                        # Look up IATA codes from line parts
                        # ori, des were extracted above
                        if ori in self.airports_db:
                            tz_origin_str = self.airports_db[ori]['tz']
                        if des in self.airports_db:
                            tz_dest_str = self.airports_db[des]['tz']
                            
                        tz_origin = pytz.timezone(tz_origin_str)
                        tz_dest = pytz.timezone(tz_dest_str)
                        
                        # 2. Construct Datetime objects
                        # Use derived year that accounts for month wrap (e.g., DEC -> JAN).
                        month_int = int(month)
                        day_int = int(day)
                        # Determine correct year based on month progression
                        if self.last_month is None:
                            self.last_month = month_int
                            year_to_use = self.current_year
                        else:
                            if month_int < self.last_month:
                                # Month wrapped to next calendar year
                                self.current_year += 1
                            self.last_month = month_int
                            year_to_use = self.current_year
                        
                        start_h = int(start_time[:2])
                        start_m = int(start_time[2:])
                        end_h = int(end_time[:2])
                        end_m = int(end_time[2:])
                        
                        # Local times
                        dt_start_local = datetime.datetime(year_to_use, month_int, day_int, start_h, start_m)
                        dt_end_local = datetime.datetime(year_to_use, month_int, day_int, end_h, end_m)
                        
                        if next_day:
                            dt_end_local += datetime.timedelta(days=1)
                        # Identify if end time is actually next day but no +1 is marked (e.g. crossing midnight)?
                        # "1310 0600+1" matches explicitly.
                        # What if "2300 0030" without +1? Usually Amadeus adds +1.
                        # We will trust the input signs.
                        
                        # Localization
                        dt_start_aware = tz_origin.localize(dt_start_local)
                        # For end time, we need to apply the dest timezone offset, but we only have LOCAL time.
                        # So we treat it as local time in dest TZ.
                        # However, dt_end_local variable above was constructed using ORIGIN date + 1 day.
                        # Is the "+1" relative to origin date? Yes, flight arrival date.
                        
                        # Case: Departure 10APR 23:00. Arrival 11APR 05:00 (+1).
                        # dt_end_local is 11APR 05:00.
                        # We treat this as local time in Destination.
                        dt_end_aware = tz_dest.localize(dt_end_local)
                        
                        # Calculate Duration (Difference in absolute time)
                        dur = dt_end_aware - dt_start_aware
                        dur_min = int(dur.total_seconds() / 60)
                        dur_h = dur_min // 60
                        dur_m = dur_min % 60
                        duration_fmt = f"{dur_h}小时 {dur_m}m"
                        
                        # Calculate Arrival Date String
                        # dt_end_local is already the correct local date.
                        # User wants "Month-Day".
                        arr_month = dt_end_local.month
                        arr_day = dt_end_local.day
                        arrival_date_fmt = f"{arr_month:02d}-{arr_day:02d}"
                        
                    except Exception as e:
                        print(f"Timezone calc failed: {e}")
                        # Fallback
                        duration_fmt = "--"
                        arrival_date_fmt = f"{month}-{day}" # Fallback to same date? Or we don't know.
                    
                    self.flights.append({
                        "id": flight_id,
                        "origin": ori_name,
                        "dest": des_name,
                        "start": start_time_fmt,
                        "end": end_time_fmt,
                        "month": month,
                        "day": day,
                        "year": year_to_use,
                        "next_day": next_day,
                        "raw_start": start_time,
                        "raw_end": end_time,
                        "duration": duration_fmt,
                        "arrival_date": arrival_date_fmt
                    })
                    
        except Exception as e:
            print(f"Error parsing flight: {e}")

    def calculate_layovers(self):
        self.layovers = []
        if len(self.flights) < 2:
            return

        for i in range(1, len(self.flights)):
            prev = self.flights[i-1]
            curr = self.flights[i]
            
            # Simple layover calculation
            try:
                # Convert to datetime objects for diff
                # Prev arrival
                prev_year = int(prev.get("year", self.base_year))
                prev_month = int(prev["month"])
                prev_day = int(prev["day"])
                prev_hour = int(prev["raw_end"][:2])
                prev_min = int(prev["raw_end"][2:])
                
                dt_prev = datetime.datetime(prev_year, prev_month, prev_day, prev_hour, prev_min)
                if prev["next_day"]:
                    dt_prev += datetime.timedelta(days=1)
                
                # Curr departure
                curr_year = int(curr.get("year", prev_year))
                curr_month = int(curr["month"])
                curr_day = int(curr["day"])
                curr_hour = int(curr["raw_start"][:2])
                curr_min = int(curr["raw_start"][2:])
                
                dt_curr = datetime.datetime(curr_year, curr_month, curr_day, curr_hour, curr_min)
                
                # If curr is before prev (e.g. year wrap), add year? 
                # Or if the gap is huge (return flight), we don't calculate layover usually?
                # Java code checks if diff > 24h -> split trip (return flight).
                
                diff = dt_curr - dt_prev
                total_minutes = int(diff.total_seconds() / 60)
                hours = total_minutes // 60
                minutes = total_minutes % 60
                
                # Use 3 days threshold to mark return
                if hours >= 72:
                    # Return trip or stopover > 24h
                    # Add separator logic in text generation
                    curr["is_return"] = True
                    # Also record it as a split for the visual card
                    self.layovers.append({
                        "type": "return_split",
                        "flight_index": i
                    })
                else:
                    self.layovers.append({
                        "type": "layover",
                        "place": prev["dest"],
                        "version": "new",
                        "hours": hours,
                        "minutes": minutes,
                        "flight_index": i # Associate with current flight (it happens BEFORE current flight)
                    })
                    
            except Exception as e:
                print(f"Error calculating layover: {e}")

    def process(self, raw_code):
        self.passengers = []
        self.flights = []
        self.layovers = []
        self.current_year = self.base_year
        self.last_month = None
        
        cleaned_code = self.merge_lines_without_sequence_number(raw_code)
        
        lines = cleaned_code.split("\n")
        passenger_mode = True
        
        for line in lines:
            parts = line.split()
            if not parts:
                continue
                
            # Check for passenger line (contains "." and in passenger mode)
            if "." in line and passenger_mode and not "SSR" in line and not "FA" in line:
                # But wait, flight lines also start with numbers "2 CA..."
                # Passenger lines: "1.XIAO/YIYI"
                if "." in parts[0]: 
                    self.parse_passengers(line, None)
                    continue
                else:
                    passenger_mode = False # Switched to flights
            
            if "SSR" in line and "DOCS" in line:
                self.parse_ssr_docs(parts)
            elif "FA" in line and "PAX" in line:
                self.parse_fa_pax(parts)
            elif self.contain_month(line) and not "SSR" in line and not "FA" in line:
                self.parse_flight(parts)

        self.calculate_layovers()
        
        return self.generate_text()

    def generate_text(self):
        res = ""
        
        # Passengers
        for i, p in enumerate(self.passengers):
            res += f"乘客{i+1}: {p['name']}\n"
        
        # Flights
        is_return = False
        for i, f in enumerate(self.flights):
            # Check for return trip break
            if f.get("is_return"):
                # Print layovers before return block
                # Actually layovers are associated with the gap.
                # If gap > 24h, we cleared layovers in Java.
                # Here we can just print header.
                
                # Print accumulated layovers?
                # Java logic: iterates, prints flight, checks layover.
                
                res += "---------<回程>---------\n"
                is_return = True
            
            # Date header if first flight or return or significantly different?
            # Java: prints header for first flight, or if "change" (return).
            if i == 0 or f.get("is_return"):
                res += f"【{f['month']}月{f['day']}日】\n"
            
            # Layover output logic is tricky in Java code.
            # It prints layover calculated from (i-1) and (i).
            # If (i) is not return, print layover.
            
            # Let's find if there is a layover associated with this flight (meaning before this flight)
            layover = next((l for l in self.layovers if l["flight_index"] == i), None)
            if layover and layover.get('type', 'layover') == 'layover' and layover['hours'] >= 0:
                 res += f"{layover.get('place', '')}停留时间: {layover['hours']}小时{layover['minutes']}分\n"
            
            # Flight info
            res += f"{f['origin']}-{f['dest']}-->{f['start']}-{f['end']}\n"

        # Footer
        # Need to pass luggage info from UI, but for now placeholders or logic to inject?
        # The UI calls process(), which calls this. 
        # We can append the footer in UI or here if we have data.
        # I'll return the core text, UI can append luggage.
        
        return res

if __name__ == "__main__":
    # Test with the provided input
    sample_input = """
   1.XIAO/YIYI 
   2  CA 908 L 10APR 3 MADPEK HK1       1  1310 0600+1 *1A/E* 
   3  CA 907 T 06NOV 3 PEKMAD HK1       3  0155 0700   *1A/E* 
   4 APE AEREOMAD@SANHE.ES 
   5 TK OK27MAR/VLCI12260//ETCA 
   6 SSR RQST CA HK1 MADPEK/51DN,P1/S2   SEE RTSTR 
   7 SSR OTHS 1A DOCS INFO IS REQUIRED FOR CA FLT 
   8 SSR ADTK 1A BY VLC27MAR24/1621 OR CXL CA NON-TKT SEGS 
   9 SSR DOCS CA HK1 P/CHN/EL9792535/CHN/22SEP93/F/26FEB34/XIAO/Y 
        IYI 
 	    
  10 SSR CTCE CA HK1 DCZHANGCHUNA//HOTMAIL.COM 
  11 SSR CTCM CA HK1 0034640208200 
  12 SSR CTCM CA HK1 008613132225567 
  13 RMZ CONF*FORMAT:PDF 
  14 FA PAX 999-6690500729/ETCA/EUR696.11/27MAR24/VLCI12260/78234 
        063/S2-3 
  15 FB PAX 0000000000 TTP/RT OK ETICKET NO PRINTERS DEFINED IN 
        OFFICE PROFILE - PLEASE CALL HELP DESK/S2-3 
  16 FE PAX Q/ NON-END/PENALTY APPLY/S2-3 
  17 FM PAX *C*0.00/S2-3 
    """
    logic = Logic()
    print(logic.process(sample_input))
