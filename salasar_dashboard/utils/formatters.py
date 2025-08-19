from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import pycountry

def pct_change(current, previous):
    return 0 if previous == 0 else (current - previous) / previous * 100

def get_month_options():
    months, today, d = [], date.today(), date(2025,1,1)
    while d <= today:
        months.append(d)
        d += relativedelta(months=1)
    return [m.strftime('%B %Y') for m in months]

def get_month_range(sel):
    start = datetime.strptime(sel, '%B %Y').date().replace(day=1)
    end = start + relativedelta(months=1) - relativedelta(days=1)
    prev_end = start - relativedelta(days=1)
    prev_start = prev_end.replace(day=1)
    return start, end, prev_start, prev_end

def format_month_year(d):
    return d.strftime('%B %Y')

def country_name_to_code(name):
    try:
        country = pycountry.countries.lookup(name)
        return country.alpha_2.lower()
    except LookupError:
        for country in pycountry.countries:
            if name.lower() in country.name.lower():
                return country.alpha_2.lower()
        return None
