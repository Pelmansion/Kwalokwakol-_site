from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import Notification


@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    return render(
        request, "notifications/list.html", {"notifications": notifications}
    )


@login_required
def mark_read(request, notification_id):
    Notification.objects.filter(id=notification_id, user=request.user).update(is_read=True)
    return redirect("notifications:list")
