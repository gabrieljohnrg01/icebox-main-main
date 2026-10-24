def notifications(request):
    """
    Context processor to fetch unread notifications for the currently logged-in user.
    This makes `unread_notifications` available in every template natively.
    """
    if request.user.is_authenticated:
        # Pre-fetch unread notifications, ordered newest first
        unread = request.user.notifications.filter(is_read=False).order_by('-created_at')
        return {
            'unread_notifications': unread,
            'unread_notifications_count': unread.count()
        }
    return {
        'unread_notifications': [],
        'unread_notifications_count': 0
    }
