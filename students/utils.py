from .models import ActivityLog

def log_activity(
    action_type,
    profile,
    created_by=None,
    shift_type=None,
    shift_capacity=None,
    start_date=None,
    end_date=None,
    extra_data=None
):
    """
    Utility to create an ActivityLog entry. Use this everywhere you want to log an activity.
    """
    return ActivityLog.objects.create(
        action_type=action_type,
        profile=profile,
        created_by=created_by,
        shift_type=shift_type,
        shift_capacity=shift_capacity,
        start_date=start_date,
        end_date=end_date,
        extra_data=extra_data or {}
    ) 