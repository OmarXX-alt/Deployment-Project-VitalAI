import logging

from flask import Blueprint, render_template

from main.application.routes._auth_utils import login_required

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/dashboard")
@login_required
def dashboard(current_user_id: str):
    """
    Render the main dashboard page.

    Requires a valid JWT in the Authorization header or in localStorage
    (checked client-side). The @login_required decorator validates the token
    and injects current_user_id for any server-side personalisation needed.
    """
    return render_template("dashboard.html")
