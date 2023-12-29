from datetime import datetime, timedelta

class WorkHoursCalculator:
    def __init__(self, in_time: str, out_time: str):
        self.in_time = in_time
        self.out_time = out_time

    def calculate_hours(self):
        in_time_obj = datetime.strptime(self.in_time, "%H:%M")
        out_time_obj = datetime.strptime(self.out_time, "%H:%M")
        
        # if out_time is on the next day
        if out_time_obj < in_time_obj:
            out_time_obj += timedelta(days=1)

        time_difference = out_time_obj - in_time_obj
        hours, remainder = divmod(time_difference.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        return hours, minutes

