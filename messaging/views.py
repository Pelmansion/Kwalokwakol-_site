from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from marketplace.models import Vendor

from .forms import MessageForm
from .models import Message, Thread


@login_required
def contact_vendor(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id, is_active=True)
    thread, _ = Thread.objects.get_or_create(user=request.user, vendor=vendor)
    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.thread = thread
            message.sender = request.user
            message.save()
            return redirect("messaging:contact_vendor", vendor_id=vendor.id)
    else:
        form = MessageForm()
    messages = Message.objects.filter(thread=thread).select_related("sender")
    return render(
        request,
        "messaging/thread.html",
        {"vendor": vendor, "thread": thread, "messages": messages, "form": form},
    )


@login_required
def vendor_inbox(request):
    vendor = Vendor.objects.filter(owner=request.user).first()
    if not vendor:
        return redirect("marketplace:vendor_register")
    threads = Thread.objects.filter(vendor=vendor).select_related("user")
    return render(
        request, "messaging/vendor_inbox.html", {"vendor": vendor, "threads": threads}
    )


@login_required
def vendor_thread(request, thread_id):
    vendor = Vendor.objects.filter(owner=request.user).first()
    if not vendor:
        return redirect("marketplace:vendor_register")
    thread = get_object_or_404(Thread, id=thread_id, vendor=vendor)
    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.thread = thread
            message.sender = request.user
            message.save()
            return redirect("messaging:vendor_thread", thread_id=thread.id)
    else:
        form = MessageForm()
    messages = Message.objects.filter(thread=thread).select_related("sender")
    return render(
        request,
        "messaging/vendor_thread.html",
        {"vendor": vendor, "thread": thread, "messages": messages, "form": form},
    )
