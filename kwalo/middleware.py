"""Middleware utilitaires (journalisation des erreurs en production)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class LogUnhandledExceptionsMiddleware:
    """Écrit la traceback complète dans les logs Render avant la page 500."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        logger.exception(
            "Erreur non gérée sur %s %s",
            request.method,
            request.path,
            exc_info=exception,
        )
        return None
