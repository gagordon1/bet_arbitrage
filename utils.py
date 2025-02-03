from datetime import datetime, timezone
def get_annualized_return(r : float, end_date : datetime):
    """Given a return per (i.e. .1), 

    Args:
        r (float): return percentage expressed as a decimal
        end_date (datetime): end date - time whenwe would return return proceeds
    """
    now = datetime.now().astimezone(timezone.utc)

    # Calculate the time difference between now and the end_date
    time_difference = end_date - now
    
    # Convert the time difference to years
    years = time_difference.days / 365.25  # 365.25 accounts for leap years
    
    # Calculate the annualized return
    if years > 0:
        annualized_return = (1 + r) ** (1 / years) - 1
    else:
        raise ValueError("The end date must be in the future.")
    
    return annualized_return
