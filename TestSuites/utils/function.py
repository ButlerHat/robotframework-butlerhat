from datetime import datetime
from datetime import timedelta
import re

# Create function to get the day today, tomorrow or two days later
def get_date(relative_day):
    """
    Get the day today, tomorrow or 'x days later' in dictionary {day: dd, month: mm, year: yyyy}
    """

    if relative_day.lower() == "today":
        date = datetime.today()
    elif relative_day.lower() == "tomorrow":
        date = datetime.today() + timedelta(days=1)
    else:
        # Get number of days with regex
        days = re.search(r"(\d+) days later", relative_day)
        if days:
            date = datetime.today() + timedelta(days=int(days.group(1)))
        else:
            raise ValueError("The relative day is not valid")
    return {"day": date.day, "month": date.month, "year": date.year}