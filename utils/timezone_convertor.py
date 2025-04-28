from datetime import datetime
import pytz

from config import TIME_STANDARD

local_timezone = pytz.timezone(TIME_STANDARD)

def get_local_time(timestamp):
    """
    Returns localtime and timestamp
    """
    if '+' in timestamp or '-' in timestamp:
        pub_time = datetime.strptime(timestamp,"%a, %d %b %Y %H:%M:%S %z")
    else:
        timezone_abbr = None
        if 'EST' in timestamp:
            timestamp = timestamp.replace('EST', '').strip()
            timezone_abbr = "US/Eastern"
        elif 'GMT' in timestamp:
            timestamp = timestamp.replace('GMT', '').strip()
            timezone_abbr = "UTC"
            
        pub_time = datetime.strptime(timestamp,"%a, %d %b %Y %H:%M:%S")
        
        if timezone_abbr == "US/Eastern":
            tz = pytz.timezone("US/Eastern")
            pub_time = tz.localize(pub_time)
        elif timezone_abbr == "UTC":
            pub_time = pytz.utc.localize(pub_time)
        else:
            pub_time = pytz.utc.localize(pub_time)

    pub_time = pub_time.astimezone(local_timezone)
    unix_pub_time = pub_time.timestamp()

    pub_time = pub_time.strftime('%a, %d %b %Y %H:%M:%S %Z')
    # print (pub_time, unix_pub_time)
    return pub_time, unix_pub_time