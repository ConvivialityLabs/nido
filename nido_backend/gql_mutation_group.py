#  Nido gql_mutation_group.py
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

from typing import List, Optional

import strawberry
from strawberry.types import Info

from .authorization import AuthorizationError, oso
from .db_models import DBGroup, DBGroupMembership
from .gql_errors import DatabaseError, Error, NotFound, Unauthorized
from .gql_helpers import decode_gql_id
from .gql_permissions import IsAuthenticated
from .gql_query import Group


@strawberry.input
class NewGroupInput:
    name: str
    custom_members: Optional[List[strawberry.ID]] = None
    managing_group: Optional[strawberry.ID] = None


@strawberry.type
class NewGroupPayload:
    groups: Optional[List[Group]] = None
    errors: Optional[List[Error]] = None


@strawberry.input
class RenameGroupInput:
    group: strawberry.ID
    name: str


@strawberry.type
class RenameGroupPayload:
    groups: Optional[List[Group]] = None
    errors: Optional[List[Error]] = None


@strawberry.input
class DeleteGroupInput:
    group: strawberry.ID


@strawberry.type
class DeleteGroupPayload:
    errors: Optional[List[Error]] = None


@strawberry.type
class GroupMutations:
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def new(self, info: Info, input: List[NewGroupInput]) -> NewGroupPayload:
        new_groups: List[Group] = []
        errors: List[Error] = []

        au = info.context.active_user
        community_id = info.context.community_id
        for i in input:
            ng = DBGroup(name=i.name, community_id=community_id)
            try:
                oso.authorize(au, "create", ng)
            except AuthorizationError as err:
                errors.append(Unauthorized())
                continue
            if i.managing_group:
                managing_id = decode_gql_id(i.managing_group)[1]
                ng.managing_group_id = managing_id
                info.context.db_session.add(ng)
            else:
                info.context.db_session.add(ng)
                try:
                    info.context.db_session.flush()
                except:
                    errors.append(DatabaseError())
                    info.context.db_session.rollback()
                    continue
                ng.managing_group_id = ng.id
                info.context.db_session.add(ng)
            if i.custom_members:
                for mem_id in i.custom_members:
                    entry = DBGroupMembership(
                        user_id=decode_gql_id(mem_id)[1],
                        community_id=community_id,
                        group_id=ng.id,
                    )
                    info.context.db_session.add(entry)
            else:
                entry = DBGroupMembership(
                    user_id=au.id, community_id=community_id, group_id=ng.id
                )
                info.context.db_session.add(entry)
            try:
                info.context.db_session.commit()
                new_groups.append(Group(db=ng))
            except:
                errors.append(DatabaseError())
                info.context.db_session.rollback()
        return NewGroupPayload(groups=new_groups, errors=errors)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def rename(self, info: Info, input: List[RenameGroupInput]) -> RenameGroupPayload:
        groups: List[Group] = []
        errors: List[Error] = []

        user = info.context.active_user
        for i in input:
            group = info.context.db_session.get(DBGroup, decode_gql_id(i.group)[1])
            try:
                oso.authorize(user, "update", group)
            except AuthorizationError as err:
                errors.append(Unauthorized())
                continue
            group.name = i.name
            info.context.db_session.add(group)
            try:
                info.context.db_session.commit()
                groups.append(Group(db=group))
            except:
                errors.append(DatabaseError())
                info.context.db_session.rollback()
        return RenameGroupPayload(groups=groups, errors=errors)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    def delete(self, info: Info, input: List[DeleteGroupInput]) -> DeleteGroupPayload:
        errors: List[Error] = []
        user = info.context.active_user
        for i in input:
            group = info.context.db_session.get(DBGroup, decode_gql_id(i.group)[1])
            if not group:
                errors.append(NotFound())
                continue
            try:
                oso.authorize(user, "delete", group)
            except AuthorizationError as err:
                errors.append(Unauthorized())
                continue
            info.context.db_session.delete(group)
            try:
                info.context.db_session.commit()
            except:
                errors.append(DatabaseError())
                info.context.db_session.rollback()
        return DeleteGroupPayload(errors=errors)
