"""Point de contrôle pour vérifier que PostgreSQL est actif en production."""

from django.conf import settings
from django.db import connection
from django.http import JsonResponse


def health_check(request):
    engine = settings.DATABASES["default"]["ENGINE"]
    ok = "postgresql" in engine
    db_ok = False
    error = ""
    if ok:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            db_ok = True
        except Exception as exc:
            error = str(exc)
    else:
        error = f"Moteur inattendu: {engine}"

    status = 200 if ok and db_ok else 503
    return JsonResponse(
        {
            "status": "ok" if status == 200 else "error",
            "database_engine": engine,
            "database_ok": db_ok,
            "error": error,
        },
        status=status,
    )
