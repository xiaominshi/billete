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
        self.logs = []
        self.passengers = []
        self.flights = []
        self.layovers = []
        self.base_year = datetime.datetime.now().year
        self.current_year = self.base_year
        self.last_month = None
        self.airports_db = {}
        
        try:
             self.airports_db = airportsdata.load('IATA')
        except Exception as e:
            self.log(f"Failed to load airportsdata: {e}")
            self.airports_db = {}
        
        # Initialize map from DB
        try:
             self.airport_map = database.get_all_airports()
        except Exception as e:
             self.log(f"Failed to load DB airports: {e}")
             self.airport_map = {}

    def log(self, msg):
        # Store log in memory to display in result if needed
        self.logs.append(str(msg))
        print(msg)

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
            # Timeout is important - Reduced to 2s to prevent hanging
            resp = requests.get(url, headers=headers, timeout=2)
            # This site uses legacy encoding
            resp.encoding = 'gbk'
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                rows = soup.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        txts = [c.get_text().strip() for c in cols]
                        if code in txts:
                            possible_name = txts[1] 
                            if possible_name == code:
                                possible_name = txts[2]
                            if possible_name and possible_name != code:
                                return possible_name
                                
        except Exception as e:
            self.log(f"Chinese lookup failed for {code}: {e}")
        
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
             self.log(f"Found online (Chinese): {code} -> {online_name}")
             self.update_airport(code, online_name)
             return online_name

        # 3. Offline DB (English Fallback)
        if code in self.airports_db:
             data = self.airports_db[code]
             city = data.get('city', '')
             name = data.get('name', '')
             final_name = city if city else name
             
             self.log(f"Found offline (English): {code} -> {final_name}")
             self.update_airport(code, final_name)
             return final_name
             
        # Not found
        return code

    def get_history(self):
        return database.get_history_entries(limit=50)

    def clear_history(self):
        return database.clear_history_entries()

    def get_today_count(self):
        return database.get_today_count()

    def save_to_history(self, code, result, passenger_info="", route_info=""):
        try:
            database.add_history_entry(code, result, passenger_info, route_info)
        except Exception as e:
            self.log(f"Error saving history: {e}")

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
        parts = line.split(".")
        for i in range(1, len(parts)):
            p_name = self.replace_number(parts[i]).strip()
            if p_name:
                self.passengers.append({"name": p_name, "id": f"P{len(self.passengers)+1}", "passport": "", "ticket": ""})

    def parse_ssr_docs(self, line_parts):
        try:
            data_part = None
            for part in line_parts:
                if part.startswith("P/"):
                    data_part = part
                    break
            
            if not data_part:
                for part in line_parts:
                    if "P/" in part and "/" in part:
                         data_part = part
                         break
            
            if data_part:
                 data_part = data_part.replace(" ", "")
                 split_data = data_part.split("/")
                 if len(split_data) >= 3:
                     passport = split_data[2]
                     if len(self.passengers) == 1:
                         self.passengers[0]["passport"] = passport
        except Exception as e:
            self.log(f"Error parsing SSR DOCS: {e}")

    def parse_fa_pax(self, line_parts):
        try:
            ticket_part = None
            for part in line_parts:
                if "FA" in part or "PAX" in part:
                    continue
                if "-" in part and "/" in part:
                    ticket_part = part
                    break
            
            if ticket_part:
                 ticket_data = ticket_part.split("/")
                 ticket_num = ticket_data[0]
                 if len(self.passengers) == 1:
                     self.passengers[0]["ticket"] = ticket_num
        except Exception as e:
            self.log(f"Error parsing FA PAX: {e}")

    def parse_flight(self, line_parts):
        try:
            date_idx = -1
            for i, part in enumerate(line_parts):
                if self.contain_month(part):
                    date_idx = i
                    break
            
            if date_idx != -1:
                flight_id = line_parts[1] + line_parts[2]
                date_str = line_parts[date_idx]
                
                ori_des_idx = date_idx + 2
                if ori_des_idx >= len(line_parts):
                     return

                ori_des = line_parts[ori_des_idx]
                ori = ori_des[:3]
                des = ori_des[3:]
                
                ori_name = self.resolve_airport(ori)
                des_name = self.resolve_airport(des)
                
                time_idx = -1
                for i in range(ori_des_idx + 1, len(line_parts)):
                    if re.match(r'^\d{4}$', line_parts[i]) or re.match(r'^\d{4}\+\d$', line_parts[i]):
                        time_idx = i
                        break
                
                if time_idx != -1:
                    start_time = line_parts[time_idx]
                    end_time = line_parts[time_idx+1]
                    
                    next_day = False
                    if "+" in end_time:
                        next_day = True
                        end_time = end_time.split("+")[0]
                    
                    start_time_fmt = f"{start_time[:2]}:{start_time[2:]}"
                    end_time_fmt = f"{end_time[:2]}:{end_time[2:]}"
                    if next_day:
                        end_time_fmt += "+1"
                    
                    day = date_str[:2]
                    month_str = date_str[2:]
                    month = self.get_month_num(month_str)

                    duration_fmt = ""
                    arrival_date_fmt = ""
                    
                    try:
                        import pytz
                        
                        tz_origin_str = 'UTC'
                        tz_dest_str = 'UTC'
                        
                        if ori in self.airports_db:
                            tz_origin_str = self.airports_db[ori]['tz']
                        if des in self.airports_db:
                            tz_dest_str = self.airports_db[des]['tz']
                            
                        tz_origin = pytz.timezone(tz_origin_str)
                        tz_dest = pytz.timezone(tz_dest_str)
                        
                        month_int = int(month)
                        day_int = int(day)
                        if self.last_month is None:
                            self.last_month = month_int
                            year_to_use = self.current_year
                        else:
                            if month_int < self.last_month:
                                self.current_year += 1
                            self.last_month = month_int
                            year_to_use = self.current_year
                        
                        start_h = int(start_time[:2])
                        start_m = int(start_time[2:])
                        end_h = int(end_time[:2])
                        end_m = int(end_time[2:])
                        
                        dt_start_local = datetime.datetime(year_to_use, month_int, day_int, start_h, start_m)
                        dt_end_local = datetime.datetime(year_to_use, month_int, day_int, end_h, end_m)
                        
                        if next_day:
                            dt_end_local += datetime.timedelta(days=1)
                        
                        dt_start_aware = tz_origin.localize(dt_start_local)
                        dt_end_aware = tz_dest.localize(dt_end_local)
                        
                        dur = dt_end_aware - dt_start_aware
                        dur_min = int(dur.total_seconds() / 60)
                        dur_h = dur_min // 60
                        dur_m = dur_min % 60
                        duration_fmt = f"{dur_h}小时 {dur_m}m"
                        
                        arr_month = dt_end_local.month
                        arr_day = dt_end_local.day
                        arrival_date_fmt = f"{arr_month:02d}-{arr_day:02d}"
                        
                    except Exception as e:
                        self.log(f"Timezone calc failed: {e}")
                        duration_fmt = "--"
                        arrival_date_fmt = f"{month}-{day}"
                    
                    self.flights.append({
                        "id": flight_id,
                        "origin": ori_name,
                        "dest": des_name,
                        "start": start_time_fmt,
                        "end": end_time_fmt,
                        "month": month,
                        "day": day,
                        "year": year_to_use if 'year_to_use' in locals() else self.current_year,
                        "next_day": next_day,
                        "raw_start": start_time,
                        "raw_end": end_time,
                        "duration": duration_fmt,
                        "arrival_date": arrival_date_fmt
                    })
                    
        except Exception as e:
            self.log(f"Error parsing flight: {e}")

    def calculate_layovers(self):
        self.layovers = []
        if len(self.flights) < 2:
            return

        for i in range(1, len(self.flights)):
            prev = self.flights[i-1]
            curr = self.flights[i]
            
            try:
                prev_year = int(prev.get("year", self.base_year))
                prev_month = int(prev["month"])
                prev_day = int(prev["day"])
                prev_hour = int(prev["raw_end"][:2])
                prev_min = int(prev["raw_end"][2:])
                
                dt_prev = datetime.datetime(prev_year, prev_month, prev_day, prev_hour, prev_min)
                if prev["next_day"]:
                    dt_prev += datetime.timedelta(days=1)
                
                curr_year = int(curr.get("year", prev_year))
                curr_month = int(curr["month"])
                curr_day = int(curr["day"])
                curr_hour = int(curr["raw_start"][:2])
                curr_min = int(curr["raw_start"][2:])
                
                dt_curr = datetime.datetime(curr_year, curr_month, curr_day, curr_hour, curr_min)
                
                diff = dt_curr - dt_prev
                total_minutes = int(diff.total_seconds() / 60)
                hours = total_minutes // 60
                minutes = total_minutes % 60
                
                if hours >= 72:
                    curr["is_return"] = True
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
                        "flight_index": i
                    })
                    
            except Exception as e:
                self.log(f"Error calculating layover: {e}")

    def process(self, raw_code):
        # Reset logs at start of process
        self.logs = []
        self.passengers = []
        self.flights = []
        self.layovers = []
        self.current_year = self.base_year
        self.last_month = None
        
        try:
            cleaned_code = self.merge_lines_without_sequence_number(raw_code)
            
            lines = cleaned_code.split("\n")
            passenger_mode = True
            
            for line in lines:
                parts = line.split()
                if not parts:
                    continue
                    
                if "." in line and passenger_mode and not "SSR" in line and not "FA" in line:
                    if "." in parts[0]: 
                        self.parse_passengers(line, None)
                        continue
                    else:
                        passenger_mode = False 
                
                if "SSR" in line and "DOCS" in line:
                    self.parse_ssr_docs(parts)
                elif "FA" in line and "PAX" in line:
                    self.parse_fa_pax(parts)
                elif self.contain_month(line) and not "SSR" in line and not "FA" in line:
                    self.parse_flight(parts)

            self.calculate_layovers()
            return self.generate_text()
            
        except Exception as e:
            self.log(f"Critical error in process: {e}")
            return f"Error processing: {e}"

    def generate_text(self):
        res = ""
        for i, p in enumerate(self.passengers):
            res += f"乘客{i+1}: {p['name']}\n"
        
        is_return = False
        for i, f in enumerate(self.flights):
            if f.get("is_return"):
                res += "---------<回程>---------\n"
                is_return = True
            
            if i == 0 or f.get("is_return"):
                res += f"【{f['month']}月{f['day']}日】\n"
            
            layover = next((l for l in self.layovers if l["flight_index"] == i), None)
            if layover and layover.get('type', 'layover') == 'layover' and layover['hours'] >= 0:
                 res += f"{layover.get('place', '')}停留时间: {layover['hours']}小时{layover['minutes']}分\n"
            
            res += f"{f['origin']}-{f['dest']}-->{f['start']}-{f['end']}\n"
        
        return res
