from datetime import datetime
import pytz

def get_formatted_datetime(timezone_str):
    """
    Gets the current time in the specified timezone and formats it.

    Args:
        timezone_str (str): The timezone string (e.g., 'America/New_York').

    Returns:
        tuple: (day_of_week, date_str, time_str) or ("Invalid TZ", "", "")
    """
    try:
        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz)
        day_of_week = now.strftime("%a").upper()
        date_str = now.strftime("%m/%d")
        time_str = now.strftime("%I:%M %p")
        return day_of_week, date_str, time_str
    except pytz.exceptions.UnknownTimeZoneError:
        return "Invalid TZ", "", ""
    except Exception as e:
        # Catch any other unexpected errors during formatting or time retrieval
        print(f"Error getting formatted datetime for {timezone_str}: {e}")
        return "Error"

if __name__ == '__main__':
    # Test cases
    print(f"UTC: {get_formatted_datetime('UTC')}")
    print(f"New York: {get_formatted_datetime('America/New_York')}")
    print(f"Kolkata: {get_formatted_datetime('Asia/Kolkata')}")
    print(f"Tokyo: {get_formatted_datetime('Asia/Tokyo')}")
    print(f"Invalid TZ: {get_formatted_datetime('Invalid/Zone')}")
    # Example for a zone that might require specific handling or shows current locale's interpretation if not careful
    # print(f"London: {get_formatted_datetime('Europe/London')}")
    # pst_time = get_formatted_datetime('America/Los_Angeles')
    # print(f"Los Angeles (PST/PDT): {pst_time}")
    # print(f"Formatted PST: {datetime.strptime(pst_time, '%a, %I:%M %p').time() if pst_time not in ['Invalid TZ', 'Error'] else 'N/A'}")
    # est_time_obj = datetime.now(pytz.timezone('America/New_York'))
    # print(f"Raw EST object: {est_time_obj}")
    # print(f"Formatted EST from object: {est_time_obj.strftime('%a, %I:%M %p')}")
