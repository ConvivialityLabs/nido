#  Nido household.py
#  Copyright (C) John Arnold
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

from flask import (
    Blueprint,
    abort,
    current_app,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import select

from nido_backend.db_models import DBResidence, DBResidenceOccupancy

from .authentication import login_required

bp = Blueprint("household", __name__)


@bp.route("/")
@login_required
def index():
    gql_query = """
query MyHousehold {
  activeUser {
    residences {
      unitNo
      street
      locality
      region
      postcode
    }
  }
}"""

    user_id = session.get("user_id")
    # Use SQL for quick mockup until GraphQL story gets figured out
    # TODO: Replace with GraphQL
    stmt = (
        select(DBResidence)
        .join(DBResidenceOccupancy)
        .where(DBResidenceOccupancy.user_id == user_id)
    )
    residences = g.db_session.scalars(stmt)
    return render_template("household.html", residences=residences)