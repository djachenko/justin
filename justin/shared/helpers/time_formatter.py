from datetime import timedelta


def format_time(delta: timedelta) -> str:
    total_seconds = round(delta.total_seconds(), 1)
    total_minutes = total_seconds // 60
    total_hours = total_minutes // 60

    seconds = total_seconds % 60
    minutes = total_minutes % 60
    hours = total_hours % 60

    if hours > 0:
        fractional_minutes = round(minutes / 60, 1)
        fractional_hours = hours + fractional_minutes

        return f"{fractional_hours:.1f} h"
    elif minutes > 0:
        fractional_seconds = round(seconds / 60, 1)
        fractional_minutes = minutes + fractional_seconds

        return f"{fractional_minutes:.1f} m"
    else:
        return f"{seconds} s"
