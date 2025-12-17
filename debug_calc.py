
import airportsdata
import pytz
import datetime

def test_calc():
    try:
        airports = airportsdata.load('IATA')
        print(f"Loaded {len(airports)} airports.")
        
        ori = "MAD"
        des = "PEK"
        
        tz_origin_str = 'UTC'
        tz_dest_str = 'UTC'
        
        if ori in airports:
            tz_origin_str = airports[ori]['tz']
            print(f"Origin TZ: {tz_origin_str}")
        else:
            print("MAD not found")
            
        if des in airports:
            tz_dest_str = airports[des]['tz']
            print(f"Dest TZ: {tz_dest_str}")
        else:
            print("PEK not found")
            
        tz_origin = pytz.timezone(tz_origin_str)
        tz_dest = pytz.timezone(tz_dest_str)
        
        start_time = "1310"
        end_time = "0600"
        next_day = True
        
        current_year = datetime.datetime.now().year
        month_int = 4
        day_int = 10
        
        dt_start_local = datetime.datetime(current_year, month_int, day_int, 13, 10)
        dt_end_local = datetime.datetime(current_year, month_int, day_int, 6, 0)
        
        if next_day:
            dt_end_local += datetime.timedelta(days=1)
            
        dt_start_aware = tz_origin.localize(dt_start_local)
        dt_end_aware = tz_dest.localize(dt_end_local)
        
        dur = dt_end_aware - dt_start_aware
        print(f"Duration: {dur}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_calc()
