from datetime import date,timedelta

def total_days_passed(a):
    # satrting_date=date(a)
    today_date=date.today()
    days_passed=today_date-a
    return days_passed.days
tru=date(2053,3,5)
