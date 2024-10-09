from datetime import datetime

def convert_time_format(time):
    convertedTimeZ = datetime.strptime(time[:-1], '%Y-%m-%dT%H:%M:%S.%f')
    convertedTime = convertedTimeZ.strftime('%Y-%m-%d %H:%M:%S.%f')
    return convertedTime