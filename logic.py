import re
import os
import datetime

class Logic:
    def __init__(self):
        self.airport_map = self.load_airport_map()
        self.passengers = []
        self.flights = []
        self.layovers = []

    def load_airport_map(self):
        mapping = {}
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(base_dir, "fly.txt")
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split(":")
                    if len(parts) == 2:
                        mapping[parts[0]] = parts[1]
        except Exception as e:
            print(f"Error loading fly.txt: {e}")
        return mapping

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
                
                # Map airports
                ori_name = self.airport_map.get(ori, ori)
                des_name = self.airport_map.get(des, des)
                
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
                    
                    self.flights.append({
                        "id": flight_id,
                        "origin": ori_name,
                        "dest": des_name,
                        "start": start_time_fmt,
                        "end": end_time_fmt,
                        "month": month,
                        "day": day,
                        "next_day": next_day,
                        "raw_start": start_time,
                        "raw_end": end_time
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
            # Assume same year
            try:
                # Convert to datetime objects for diff
                # We need a reference year, let's use current year
                year = datetime.datetime.now().year
                
                # Prev arrival
                prev_month = int(prev["month"])
                prev_day = int(prev["day"])
                prev_hour = int(prev["raw_end"][:2])
                prev_min = int(prev["raw_end"][2:])
                
                dt_prev = datetime.datetime(year, prev_month, prev_day, prev_hour, prev_min)
                if prev["next_day"]:
                    dt_prev += datetime.timedelta(days=1)
                
                # Curr departure
                curr_month = int(curr["month"])
                curr_day = int(curr["day"])
                curr_hour = int(curr["raw_start"][:2])
                curr_min = int(curr["raw_start"][2:])
                
                dt_curr = datetime.datetime(year, curr_month, curr_day, curr_hour, curr_min)
                
                # If curr is before prev (e.g. year wrap), add year? 
                # Or if the gap is huge (return flight), we don't calculate layover usually?
                # Java code checks if diff > 24h -> split trip (return flight).
                
                diff = dt_curr - dt_prev
                total_minutes = int(diff.total_seconds() / 60)
                hours = total_minutes // 60
                minutes = total_minutes % 60
                
                if hours >= 24:
                    # Return trip or stopover > 24h
                    # Add separator logic in text generation
                    curr["is_return"] = True
                else:
                    self.layovers.append({
                        "place": prev["dest"], # Layover at previous destination
                        "hours": hours,
                        "minutes": minutes,
                        "flight_index": i # Associate with current flight
                    })
                    
            except Exception as e:
                print(f"Error calculating layover: {e}")

    def process(self, raw_code):
        self.passengers = []
        self.flights = []
        self.layovers = []
        
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
            if layover:
                 res += f"{layover['place']}停留时间: {layover['hours']}小时{layover['minutes']}分\n"
            
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
