#  Nido main_menu.py
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

import dataclasses

from flask import url_for


@dataclasses.dataclass
class MenuLink:
    name: str
    href: str


def get_main_menu(is_admin: bool):
    menu_list = []
    menu_list.append(MenuLink("My Household", url_for("household.index")))
    menu_list.append(MenuLink("Billing", url_for("billing.index")))
    menu_list.append(MenuLink("Report Issues", url_for("report_issues.index")))
    menu_list.append(MenuLink("Resident Directory", url_for("resident_dir.index")))
    menu_list.append(MenuLink("Documents", url_for("documents.index")))
    menu_list.append(MenuLink("Signatures", url_for("signatures.index")))
    if is_admin:
        menu_list.append(MenuLink("Administrative View", url_for("admin.index")))
    menu_list.append(MenuLink("Logout", url_for("authentication.logout")))
    return menu_list


def get_admin_menu():
    menu_list = []
    menu_list.append(MenuLink("Dashboard", url_for("admin.admin_dashboard.index")))
    menu_list.append(MenuLink("Manage Move-ins", url_for("admin.admin_moveins.index")))
    menu_list.append(
        MenuLink("Manage Signatures", url_for("admin.admin_signatures.index"))
    )
    menu_list.append(MenuLink("Manage Groups", url_for("admin.admin_groups.index")))
    menu_list.append(MenuLink("Manage Rights", url_for("admin.admin_rights.index")))
    menu_list.append(MenuLink("User View", url_for("index")))
    menu_list.append(MenuLink("Logout", url_for("authentication.logout")))
    return menu_list
