import json

from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from pydantic import ValidationError

from models.onboarding import OnboardingForm

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


def _format_validation_errors(exc):
    errors = {}
    for error in exc.errors():
        field = ".".join(str(part) for part in error["loc"]) or "form"
        message = error["msg"]
        if message.startswith("Value error, "):
            message = message.removeprefix("Value error, ")
        errors[field] = message
    return errors


@require_POST
def generate(request):
    if request.content_type != "application/json":
        return JsonResponse(
            {"message": "Request body must be valid JSON."},
            status=400,
        )

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"message": "Request body must be valid JSON."},
            status=400,
        )

    try:
        OnboardingForm.model_validate(payload)
    except ValidationError as exc:
        return JsonResponse(
            {
                "message": "Please correct the highlighted fields.",
                "errors": _format_validation_errors(exc),
            },
            status=400,
        )

    return JsonResponse({"status": "ok"})
