from django.shortcuts import get_object_or_404, redirect, render

from orders.models import Order

from .models import Payment


def payment_sandbox(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    order = payment.order
    if request.method == "POST":
        payment.status = Payment.STATUS_SUCCESS
        payment.reference = f"PAY-{payment.id}"
        payment.save()
        order.payment_status = Order.PAYMENT_SUCCESS
        order.status = Order.STATUS_PAID
        order.save()
        return redirect("store:order_success", order_id=order.id)
    return render(request, "payments/payment_sandbox.html", {"payment": payment, "order": order})
