#  Nido admin_blueprint.py
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

from flask import Blueprint

from .admin_dashboard import bp as dash_bp
from .admin_dashboard import index as dash_index
from .admin_manage_groups import bp as groups_bp
from .admin_manage_moveins import bp as moveins_bp
from .admin_manage_rights import bp as rights_bp
from .admin_manage_signatures import bp as sigs_bp

bp = Blueprint("admin", __name__)

bp.register_blueprint(dash_bp, url_prefix="/dashboard")
bp.register_blueprint(groups_bp, url_prefix="/manage-groups")
bp.register_blueprint(moveins_bp, url_prefix="/manage-moveins")
bp.register_blueprint(rights_bp, url_prefix="/manage-rights")
bp.register_blueprint(sigs_bp, url_prefix="/manage-signatures")
bp.add_url_rule("/", endpoint="index", view_func=dash_index)
