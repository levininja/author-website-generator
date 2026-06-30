from django.http import JsonResponse
from django.shortcuts import redirect, render

DIVI_TEMPLATES = [
    "Classic Author",
    "Modern Minimalist",
    "Bold & Bright",
    "Cozy Romance",
    "Thriller Dark",
    "Literary Fiction",
]


def index(request):
    return redirect("/onboard")


def onboard(request):
    return render(request, "onboarding/onboard.html", {"divi_templates": DIVI_TEMPLATES})


def generate(request):
    return JsonResponse({"status": "ok"})
