import numpy as np
from datetime import datetime, timedelta

day_check = lambda x: x.hour >= 8 and x.hour <= 18
weekday_check = lambda x: x.weekday() not in (5,6)
daily = lambda x: x.date()
monthly = lambda x: x.date().replace(day=1)
weekly = lambda x: x.date() - timedelta(days=x.weekday())

def split_day_data(self, grouped):
    weekend_days = []
    working_days = []
    night = []
    day = []

    dates = grouped.keys()
    dates.sort()

    for date in dates:
        l = grouped[date]
        if weekday_check(date):
            day_values = [x[1] for x in l if day_check(x[0])]
            night_values = [x[1] for x in l if not day_check(x[0])]

            day.append([date, sum(day_values)])
            night.append([date, sum(night_values)])
            working_days.append([date, sum([x[1] for x in l])])
        else:
            weekend_days.append([date, sum([x[1] for x in l])])

    return {'day':day, 'night':night, 'working_days':working_days, 'weekend_days':weekend_days}

def group_data(readings, index=daily):
    data = [(x.timestamp, x.value) for x in readings]

    grouped = {}
    for x in data:
        try:
            grouped[index(x[0])].append(x)
        except KeyError:
            grouped[index(x[0])] = [x,]
    return grouped

def calc_box_plot(values):
    v_lq = np.percentile(values, 25)
    v_uq = np.percentile(values, 75)
    # Interquartile range (whiskers are at uq + (1.5*iq), lq - (1.5*iq))
    iq = v_uq - v_lq

    # Calculate whiskers
    # Upper whisker
    hi_val = v_uq + 1.5 * iq
    v_uw = np.compress(values <= hi_val, values)
    if len(v_uw) == 0 or np.max(v_uw) < v_uq:
        v_uw = v_uq
    else:
        v_uw = max(v_uw)

    # Lower whisker
    lo_val = v_lq - 1.5 * iq
    v_lw = np.compress(values >= lo_val, values)
    if len(v_lw) == 0 or np.min(v_lw) > v_uq:
        v_lw = v_lq
    else:
        v_lw = min(v_lw)
    v_med = np.median(values)
    return (v_uw, v_uq, v_med, v_lq, v_lw)

def dump_header(ts=False):
    headers = ["Sensor",]
    if ts:
        headers.append("Timestamp")
    headers.extend(["Range", "Var", "UW", "UQ", "Med", "LQ", "LW"])
    return headers

def dump_stats(sensor, values, ts=None):
    data = [sensor.name,]
    if ts:
        data.append(str(ts))
    data.append(np.ptp(values))
    data.append(np.var(values))
    data.extend(calc_box_plot(values))
    return data

def cumulative(sensor, readings, index):
    result = []
    grouped = group_data(readings, index=index)
    timestamps = grouped.keys()
    timestamps.sort()
    values = []
    for ts in timestamps:
        values.append(sum([x[1] for x in grouped[ts]]))
    result.append(dump_stats(sensor, values))
    return result

def non_cumulative(sensor, readings, index):
    result = []
    grouped = group_data(readings, index=index)
    timestamps = grouped.keys()
    timestamps.sort()
    for ts in timestamps:
        result.append(dump_stats(sensor, [x[1] for x in grouped[ts]], ts=ts))
    return result