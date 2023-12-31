#  Nido enums.py
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

from enum import Enum, Flag, auto

import strawberry


@strawberry.enum
class ApplicationStatus(Enum):
    AWAITING_APPLICANT_SIGNATURE = auto()
    AWAITING_MOVEIN = auto()


class BillingFrequency(Enum):
    YEARLY = auto()
    MONTHLY = auto()
    WEEKLY = auto()
    DAILY = auto()


class ContactMethodType(Enum):
    Email = auto()


@strawberry.enum
class PermissionsFlag(Flag):
    CAN_DELEGATE = auto()
    CREATE_GROUPS = auto()

    def __bool__(self):
        return bool(self.value)
