from datetime import datetime

def convert_time_format(time):
    #convert from 2024-12-14T12:34:56.789Z to 2024-12-14 12:34:56.301991
    convertedTimeZ = datetime.strptime(time[:-1], '%Y-%m-%dT%H:%M:%S.%f')
    convertedTime = convertedTimeZ.strftime('%Y-%m-%d %H:%M:%S.%f')
    return convertedTime