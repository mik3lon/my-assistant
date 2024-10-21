from django.shortcuts import render

def custom_csrf_failure_view(request, reason=""):
    return render(request, 'csrf_failure.html', {"reason": reason})
