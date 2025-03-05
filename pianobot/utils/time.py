from datetime import datetime, timedelta, timezone

from corkus.objects.player import Player


def get_rounded_time(minutes: int) -> datetime:
    time = datetime.now(timezone.utc)
    interval = minutes * 60
    seconds = (time.replace(tzinfo=None) - time.min).seconds
    difference = (seconds + interval / 2) // interval * interval - seconds
    return time + timedelta(0, difference, -time.microsecond)


def format_last_seen(player: Player) -> tuple[float, str]:
    if player.online:
        days_offline = 0.0
        display_time = 'Online'
    else:
        diff = datetime.now(timezone.utc) - player.last_online
        days_offline = diff.days + (diff.seconds / 86400)
        value = days_offline
        unit = 'day'
        if value < 1:
            value *= 24
            unit = 'hour'
            if value < 1:
                value *= 60
                unit = 'minute'
        if round(value) != 1:
            unit += 's'
        display_time = f'{round(value)} {unit}'
    return days_offline, display_time

def get_cycle(dt: datetime) -> str:
    return f'{dt.year % 100}{dt.month:02}{"A" if dt.day < 15 else "B"}'
