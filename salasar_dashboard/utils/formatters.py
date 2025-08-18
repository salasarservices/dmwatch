from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import pycountry

def pct_change(current, previous):
    return 0 if previous == 0 else (current - previous) / previous * 100

def format_month_year(d):
    return d.strftime('%B %Y')

def country_name_to_code(name):
    # ... as in your code
