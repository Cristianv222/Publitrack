from django import template
from datetime import datetime, time, timedelta

register = template.Library()

@register.filter
def is_in_slot(ubicacion, slot_time_str):
    """
    Check if the ad break (ubicacion) starts within the 30-minute slot defined by slot_time_str.
    slot_time_str is expected in "HH:MM" format.
    """
    if not ubicacion or not ubicacion.hora_pausa:
        return False
        
    try:
        # Parse slot start time
        hour, minute = map(int, slot_time_str.split(':'))
        slot_start = time(hour, minute)
        
        # Calculate slot end time (start + 30 minutes)
        # Using dummy date to handle time calculation
        dummy_date = datetime.today()
        slot_start_dt = datetime.combine(dummy_date, slot_start)
        slot_end_dt = slot_start_dt + timedelta(minutes=30)
        
        # Adjust for day rollover if necessary (though unlikely for 30 min slots within same day)
        # We really just care about the time part
        slot_end = slot_end_dt.time()
        
        pausa_time = ubicacion.hora_pausa
        
        # Handle the case where the slot ends on the next day (e.g., 23:30 -> 00:00)
        if slot_end_dt.date() > dummy_date.date():
             # If slot crosses midnight (23:30-00:00), we accept times >= 23:30 OR < 00:00 (which is always true for time < 00:00 effectively)
             # But strictly speaking, standard time objects don't go > 23:59:59.
             # So we just check if pausa_time >= slot_start.
             return pausa_time >= slot_start
        
        # Normal comparison: slot_start <= pausa_time < slot_end
        return slot_start <= pausa_time < slot_end
        
    except (ValueError, TypeError, AttributeError):
        return False
