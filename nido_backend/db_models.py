#  Nido db_models.py
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

import datetime
from dataclasses import field, make_dataclass
from functools import reduce
from typing import List, Optional

import sqlalchemy.schema as sql_schema
import sqlalchemy.types as sql_types
from sqlalchemy import ForeignKey
from sqlalchemy import func as sql_func
from sqlalchemy import select
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    column_property,
    mapped_column,
    relationship,
)

from .enums import (
    ApplicationStatus,
    BillingFrequency,
    ContactMethodType,
    PermissionsFlag,
)


class BooleanFlag(sql_types.TypeDecorator):
    impl = sql_types.Boolean
    cache_ok = True

    def __init__(self, true_flag, false_flag, *arg, **kw):
        self.true_flag = true_flag
        self.false_flag = false_flag
        sql_types.TypeDecorator.__init__(self, *arg, **kw)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        try:
            return value & self.true_flag == self.true_flag
        except:
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif value is True:
            return self.true_flag
        else:
            return self.false_flag


class Base(DeclarativeBase, MappedAsDataclass):
    pass


class DBNode(MappedAsDataclass):
    id: Mapped[int] = mapped_column(primary_key=True, init=False, repr=False)


class DBCommunity(Base, DBNode):
    __tablename__ = "community"

    name: Mapped[str]

    associates: Mapped[List["DBAssociate"]] = relationship(
        back_populates="community", init=False, repr=False
    )
    residences: Mapped[List["DBResidence"]] = relationship(
        back_populates="community", init=False, repr=False
    )
    occupancies: Mapped[List["DBResidenceOccupancy"]] = relationship(
        back_populates="community",
        viewonly=True,
        init=False,
        repr=False,
    )
    recurring_billing_charges: Mapped[List["DBBillingRecurringCharge"]] = relationship(
        back_populates="community", viewonly=True, init=False, repr=False
    )
    billing_charges: Mapped[List["DBBillingCharge"]] = relationship(
        order_by="DBBillingCharge.charge_date.desc()",
        back_populates="community",
        viewonly=True,
        init=False,
        repr=False,
    )
    billing_payments: Mapped[List["DBBillingPayment"]] = relationship(
        back_populates="community", viewonly=True, init=False, repr=False
    )
    groups: Mapped[List["DBGroup"]] = relationship(
        back_populates="community", viewonly=True, init=False, repr=False
    )
    rights: Mapped[List["DBRight"]] = relationship(
        back_populates="community", viewonly=True, init=False, repr=False
    )
    occupancy_applications: Mapped[List["DBOccupancyApplication"]] = relationship(
        back_populates="community", init=False, repr=False
    )


class DBAssociate(Base, DBNode):
    __tablename__ = "associate"
    __table_args__ = (sql_schema.UniqueConstraint("id", "community_id"),)

    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"), default=None
    )
    community_id: Mapped[int] = mapped_column(
        ForeignKey("community.id", ondelete="CASCADE"), kw_only=True
    )

    personal_name: Mapped[str] = mapped_column(kw_only=True)
    family_name: Mapped[str] = mapped_column(kw_only=True)

    full_name: Mapped[str] = column_property(personal_name + " " + family_name)
    collation_name: Mapped[str] = column_property(family_name + ", " + personal_name)

    user: Mapped[Optional["DBUser"]] = relationship(init=False, repr=False)
    contact_methods: Mapped[List["DBContactMethod"]] = relationship(
        secondary="associate_contact_listing", init=False, repr=False
    )
    community: Mapped[DBCommunity] = relationship(
        back_populates="associates", init=False, repr=False
    )
    residences: Mapped[List["DBResidence"]] = relationship(
        secondary="residence_occupancy",
        viewonly=True,
        back_populates="occupants",
        init=False,
        repr=False,
    )
    occupancies: Mapped[List["DBResidenceOccupancy"]] = relationship(
        back_populates="occupant",
        viewonly=True,
        init=False,
        repr=False,
    )
    occupancy_applications: Mapped[List["DBOccupancyApplication"]] = relationship(
        foreign_keys="DBOccupancyApplication.applicant_id",
        back_populates="applicant",
        init=False,
        repr=False,
    )
    applications_sponsored: Mapped[List["DBOccupancyApplication"]] = relationship(
        primaryjoin="DBAssociate.id == DBOccupancyApplication.sponsor_id",
        foreign_keys="DBOccupancyApplication.sponsor_id",
        back_populates="sponsor",
        init=False,
        repr=False,
    )
    groups: Mapped[List["DBGroup"]] = relationship(
        secondary="group_membership",
        back_populates="custom_members",
        init=False,
        repr=False,
    )
    recurring_billing_charges: Mapped[List["DBBillingRecurringCharge"]] = relationship(
        back_populates="occupant", viewonly=True, init=False, repr=False
    )
    billing_charges: Mapped[List["DBBillingCharge"]] = relationship(
        order_by="DBBillingCharge.charge_date.desc()",
        back_populates="occupant",
        viewonly=True,
        init=False,
        repr=False,
    )


class DBResidence(Base, DBNode):
    __tablename__ = "residence"
    __table_args__ = (
        sql_schema.UniqueConstraint("id", "community_id"),
        sql_schema.CheckConstraint("on_market = true OR available_starting IS NULL"),
    )

    community_id: Mapped[int] = mapped_column(
        ForeignKey("community.id", ondelete="CASCADE")
    )

    unit_no: Mapped[Optional[str]]
    street: Mapped[str]
    locality: Mapped[str]
    postcode: Mapped[str]
    region: Mapped[str]
    on_market: Mapped[bool] = mapped_column(default=False)
    available_starting: Mapped[Optional[datetime.date]] = mapped_column(default=None)

    community: Mapped[DBCommunity] = relationship(
        back_populates="residences", init=False, repr=False
    )
    occupancies: Mapped[List["DBResidenceOccupancy"]] = relationship(
        back_populates="residence",
        viewonly=True,
        init=False,
        repr=False,
    )
    occupants: Mapped[List[DBAssociate]] = relationship(
        secondary="residence_occupancy",
        back_populates="residences",
        init=False,
        repr=False,
    )
    occupancy_applications: Mapped[List["DBOccupancyApplication"]] = relationship(
        foreign_keys="DBOccupancyApplication.residence_id",
        back_populates="residence",
        init=False,
        repr=False,
    )
    billing_charges: Mapped[List["DBBillingCharge"]] = relationship(
        order_by="DBBillingCharge.charge_date.desc()",
        back_populates="residence",
        init=False,
        repr=False,
    )
    recurring_billing_charges: Mapped[List["DBBillingRecurringCharge"]] = relationship(
        back_populates="residence",
        init=False,
        repr=False,
    )


class DBResidenceOccupancy(Base, DBNode):
    __tablename__ = "residence_occupancy"
    __table_args__ = (
        sql_schema.UniqueConstraint("community_id", "residence_id", "occupant_id"),
        sql_schema.ForeignKeyConstraint(
            ["residence_id", "community_id"],
            ["residence.id", "residence.community_id"],
            ondelete="RESTRICT",
        ),
        sql_schema.ForeignKeyConstraint(
            ["occupant_id", "community_id"],
            ["associate.id", "associate.community_id"],
            ondelete="RESTRICT",
        ),
    )
    # CASCADE when community is deleted, because deleting the community can
    # only mean that they are no longer interested in using the service. But
    # if a residence known to have occupants is deleted, what does that mean?
    # Unclear, so RESTRICT and have the programmer delete the occupancy first
    # if the deletion is intentional. Same reason for user_id RESTRICT.

    community_id: Mapped[int] = mapped_column(
        ForeignKey("community.id", ondelete="CASCADE")
    )
    residence_id: Mapped[int]
    occupant_id: Mapped[int]
    date_begun: Mapped[Optional[datetime.date]] = mapped_column(default=None)
    date_ended: Mapped[Optional[datetime.date]] = mapped_column(default=None)

    community: Mapped[DBCommunity] = relationship(
        back_populates="occupancies", viewonly=True, init=False, repr=False
    )
    occupant: Mapped[DBAssociate] = relationship(
        back_populates="occupancies",
        viewonly=True,
        init=False,
        repr=False,
    )
    residence: Mapped[DBResidence] = relationship(
        back_populates="occupancies",
        viewonly=True,
        init=False,
        repr=False,
    )


class DBUser(Base, DBNode):
    __tablename__ = "user"

    personal_name: Mapped[str] = mapped_column()
    family_name: Mapped[str] = mapped_column()
    full_name: Mapped[str] = column_property(personal_name + " " + family_name)
    collation_name: Mapped[str] = column_property(family_name + ", " + personal_name)

    contact_methods: Mapped[List["DBContactMethod"]] = relationship(
        back_populates="user", init=False, repr=False
    )
    self_associates: Mapped[List["DBAssociate"]] = relationship(
        back_populates="user", init=False, repr=False
    )


class DBOccupancyApplication(Base, DBNode):
    __tablename__ = "occupancy_application"
    __table_args__ = (
        sql_schema.UniqueConstraint("id", "community_id"),
        sql_schema.ForeignKeyConstraint(
            ["residence_id", "community_id"],
            ["residence.id", "residence.community_id"],
            ondelete="CASCADE",
        ),
        sql_schema.ForeignKeyConstraint(
            ["applicant_id", "community_id"],
            ["associate.id", "associate.community_id"],
            ondelete="RESTRICT",
        ),
        # While we never join with residence_occupancy directly,
        # we do want to make sure a sponsor can only sponsor for a
        # residence the sponsor occupies.
        sql_schema.ForeignKeyConstraint(
            ["sponsor_id", "residence_id", "community_id"],
            [
                "residence_occupancy.occupant_id",
                "residence_occupancy.residence_id",
                "residence_occupancy.community_id",
            ],
            ondelete="CASCADE",
        ),
    )

    community_id: Mapped[int] = mapped_column(
        ForeignKey("community.id", ondelete="CASCADE")
    )
    residence_id: Mapped[int] = mapped_column()
    applicant_id: Mapped[int] = mapped_column(default=None)
    sponsor_id: Mapped[Optional[int]] = mapped_column(default=None)

    application_status: Mapped[ApplicationStatus] = mapped_column(
        default=ApplicationStatus.AWAITING_MOVEIN
    )
    scheduled_occupancy_start_date: Mapped[Optional[datetime.date]] = mapped_column(
        default=None
    )
    scheduled_occupancy_end_date: Mapped[Optional[datetime.date]] = mapped_column(
        default=None
    )

    community: Mapped[DBCommunity] = relationship(
        back_populates="occupancy_applications", init=False, repr=False
    )
    applicant: Mapped[DBAssociate] = relationship(
        foreign_keys=applicant_id,
        back_populates="occupancy_applications",
        init=False,
        repr=False,
    )
    residence: Mapped[DBResidence] = relationship(
        foreign_keys=residence_id,
        back_populates="occupancy_applications",
        init=False,
        repr=False,
    )
    sponsor: Mapped[Optional[DBAssociate]] = relationship(
        primaryjoin="DBAssociate.id == DBOccupancyApplication.sponsor_id",
        foreign_keys=sponsor_id,
        back_populates="applications_sponsored",
        init=False,
        repr=False,
    )


class DBGroup(Base, DBNode):
    __tablename__ = "group"
    __table_args__ = (
        sql_schema.UniqueConstraint("id", "community_id"),
        sql_schema.UniqueConstraint("community_id", "name"),
        sql_schema.ForeignKeyConstraint(
            ["managing_group_id", "community_id"],
            ["group.id", "group.community_id"],
            # DEFERRABLE INITIALLY DEFERRED is necessary in sqlite for defered
            # enforcement of this foreign key constraint. Defered enforcement
            # is needed to correctly build the row when a group manages itself.
            deferrable=True,
            initially="DEFERRED",
            # Use ON DELETE SET DEFAULT with nonsense defaults in the columns.
            # ON DELETE CASCADE is the wrong behavior; we don't want users
            # unthinkingly deleting a parent group and unintentionally deleting
            # all child groups.
            # ON DELETE RESTRICT and ON DELETE SET NULL don't work well with
            # rows that self-reference.
            ondelete="SET DEFAULT",
        ),
        sql_schema.ForeignKeyConstraint(
            ["right_id", "community_id"],
            ["right.id", "right.community_id"],
            # ON DELETE NO ACTION because the right_id single column constraint
            # will set the column to NULL and community_id shouldn't be changed
            ondelete="NO ACTION",
        ),
    )

    community_id: Mapped[int] = mapped_column(
        ForeignKey("community.id", ondelete="CASCADE"), server_default="0"
    )
    managing_group_id: Mapped[int] = mapped_column(server_default="0", init=False)
    right_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("right.id", ondelete="SET NULL"), init=False
    )

    name: Mapped[str]

    community: Mapped[DBCommunity] = relationship(
        back_populates="groups", init=False, repr=False
    )
    managed_by: Mapped["DBGroup"] = relationship(
        back_populates="manages",
        remote_side="DBGroup.id",
        foreign_keys=[managing_group_id],
        passive_deletes="all",
        post_update=True,
        init=False,
        repr=False,
    )
    manages: Mapped[List["DBGroup"]] = relationship(
        back_populates="managed_by",
        foreign_keys=[managing_group_id],
        passive_deletes="all",
        post_update=True,
        init=False,
        repr=False,
    )
    right: Mapped[Optional["DBRight"]] = relationship(
        back_populates="groups",
        foreign_keys=[right_id],
        init=False,
        repr=False,
    )
    custom_members: Mapped[List[DBAssociate]] = relationship(
        secondary="group_membership",
        back_populates="groups",
        init=False,
        repr=False,
    )


class DBGroupMembership(Base):
    __tablename__ = "group_membership"
    __table_args__ = (
        sql_schema.ForeignKeyConstraint(
            ["group_id", "community_id"],
            ["group.id", "group.community_id"],
            ondelete="CASCADE",
        ),
        sql_schema.ForeignKeyConstraint(
            ["member_id", "community_id"],
            ["associate.id", "associate.community_id"],
            ondelete="CASCADE",
        ),
    )

    community_id: Mapped[int] = mapped_column(
        ForeignKey("community.id", ondelete="CASCADE"), primary_key=True, default=None
    )
    group_id: Mapped[int] = mapped_column(primary_key=True, default=None)
    member_id: Mapped[int] = mapped_column(primary_key=True, default=None)

    group: Mapped["DBGroup"] = relationship(
        passive_deletes="all",
        overlaps="custom_members,groups",
        init=False,
        repr=False,
    )


# Creates a class with SQLALchemy mapped Boolean columns for each member
# of PermissionsFlag.
PermissionsMixin = make_dataclass(
    "PermissionsMixin",
    [
        (
            member.name.lower(),
            Mapped[BooleanFlag],
            field(
                default=mapped_column(
                    BooleanFlag(member, PermissionsFlag(0)),
                    default=PermissionsFlag(0),
                    init=False,
                )
            ),
        )
        for member in PermissionsFlag
        if member.name is not None
    ],
    bases=(MappedAsDataclass,),
)


class DBRight(Base, DBNode, PermissionsMixin):  # type: ignore
    __tablename__ = "right"
    __table_args__ = (
        sql_schema.UniqueConstraint("id", "community_id"),
        sql_schema.UniqueConstraint("community_id", "name"),
        sql_schema.ForeignKeyConstraint(
            ["parent_right_id", "community_id"],
            ["right.id", "right.community_id"],
            # DEFERRABLE INITIALLY DEFERRED is necessary in sqlite for defered
            # enforcement of this foreign key constraint. Defered enforcement is
            # needed to correctly build the row when a right is its own parent.
            deferrable=True,
            initially="DEFERRED",
            ondelete="CASCADE",
        ),
    )

    community_id: Mapped[int] = mapped_column(
        ForeignKey("community.id", ondelete="CASCADE"), server_default="0"
    )
    parent_right_id: Mapped[int] = mapped_column(server_default="0", init=False)

    name: Mapped[str]

    @hybrid_property
    def permissions(self):
        return reduce(
            lambda a, b: a | b, [getattr(self, m.name.lower()) for m in PermissionsFlag]
        )

    @permissions.inplace.expression
    @classmethod
    def _permissions_expression(cls):
        return reduce(
            lambda a, b: a + b,
            [m.value for m in PermissionsFlag if getattr(cls, m.name.lower())],
        )

    @permissions.inplace.setter
    def _permissions_setter(self, value: PermissionsFlag):
        for member in PermissionsFlag:
            setattr(self, member.name.lower(), member & value)  # type: ignore

    @hybrid_method
    def permits(self, request):
        return self.permissions & request == request

    community: Mapped[DBCommunity] = relationship(
        back_populates="rights", init=False, repr=False
    )
    parent_right: Mapped["DBRight"] = relationship(
        back_populates="child_rights",
        remote_side="DBRight.id",
        foreign_keys=[parent_right_id],
        passive_deletes="all",
        init=False,
        repr=False,
    )
    child_rights: Mapped[List["DBRight"]] = relationship(
        back_populates="parent_right",
        foreign_keys=[parent_right_id],
        passive_deletes="all",
        init=False,
        repr=False,
    )
    groups: Mapped[List[DBGroup]] = relationship(
        back_populates="right",
        foreign_keys=[DBGroup.right_id],
        init=False,
        repr=False,
    )


class DBAssociateContactListing(Base):
    __tablename__ = "associate_contact_listing"
    __table_args__ = (
        sql_schema.ForeignKeyConstraint(
            ["associate_id", "community_id"],
            ["associate.id", "associate.community_id"],
            ondelete="CASCADE",
        ),
    )
    associate_id: Mapped[int] = mapped_column(primary_key=True)
    community_id: Mapped[int] = mapped_column(
        ForeignKey("community.id", ondelete="CASCADE"), primary_key=True
    )
    contact_method_id: Mapped[int] = mapped_column(
        ForeignKey("contact_method.id", ondelete="CASCADE"), primary_key=True
    )


class DBContactMethod(Base, DBNode):
    __tablename__ = "contact_method"

    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"), default=None
    )
    type: Mapped[ContactMethodType] = mapped_column(init=False, repr=False)

    user: Mapped[Optional[DBUser]] = relationship(
        back_populates="contact_methods", init=False, repr=False
    )

    __mapper_args__ = {
        "polymorphic_on": "type",
    }


class DBEmailContact(DBContactMethod):
    email: Mapped[str] = mapped_column(unique=True, nullable=True, default=None)

    __mapper_args__ = {
        "polymorphic_identity": ContactMethodType.Email,
        "polymorphic_load": "inline",
    }


class DBSignatureTemplate(Base, DBNode):
    __tablename__ = "signature_template"
    __table_args__ = (
        sql_schema.UniqueConstraint("id", "community_id"),
        sql_schema.UniqueConstraint("community_id", "name"),
    )

    community_id: Mapped[int] = mapped_column(
        ForeignKey("community.id", ondelete="CASCADE")
    )

    name: Mapped[str]
    data: Mapped[bytes]
    signature_field_name: Mapped[str]

    community: Mapped[DBCommunity] = relationship(viewonly=True, init=False, repr=False)


class DBSignatureAssignment(Base):
    __tablename__ = "signature_assignment"
    __table_args__ = (
        sql_schema.ForeignKeyConstraint(
            ["template_id", "community_id"],
            ["signature_template.id", "signature_template.community_id"],
            ondelete="CASCADE",
        ),
        sql_schema.ForeignKeyConstraint(
            ["signer_id", "community_id"],
            ["associate.id", "associate.community_id"],
            ondelete="CASCADE",
        ),
    )

    community_id: Mapped[int] = mapped_column(
        ForeignKey("community.id", ondelete="CASCADE"), primary_key=True
    )
    template_id: Mapped[int] = mapped_column(primary_key=True)
    signer_id: Mapped[int] = mapped_column(primary_key=True)

    community: Mapped[DBCommunity] = relationship(init=False, repr=False)
    signature_template: Mapped[DBSignatureTemplate] = relationship(
        foreign_keys=template_id, init=False, repr=False
    )
    signer: Mapped[DBAssociate] = relationship(
        foreign_keys=signer_id, init=False, repr=False
    )


class DBSignatureRecord(Base, DBNode):
    __tablename__ = "signature_record"
    __table_args__ = (
        sql_schema.UniqueConstraint("id", "community_id"),
        sql_schema.UniqueConstraint("signer_id", "name"),
        sql_schema.ForeignKeyConstraint(
            ["signer_id", "community_id"],
            ["associate.id", "associate.community_id"],
            ondelete="RESTRICT",
        ),
    )

    community_id: Mapped[int] = mapped_column(
        ForeignKey("community.id", ondelete="CASCADE")
    )
    signer_id: Mapped[int]

    name: Mapped[str]
    data: Mapped[bytes]
    signature_date: Mapped[datetime.date]

    community: Mapped[DBCommunity] = relationship(viewonly=True, init=False, repr=False)
    signer: Mapped[DBAssociate] = relationship(viewonly=True, init=False, repr=False)


class DBDirFolder(Base, DBNode):
    __tablename__ = "directory_folder"
    __table_args__ = (
        sql_schema.UniqueConstraint("id", "community_id"),
        sql_schema.ForeignKeyConstraint(
            ["parent_folder_id", "community_id"],
            ["directory_folder.id", "directory_folder.community_id"],
            ondelete="CASCADE",
        ),
        sql_schema.UniqueConstraint("parent_folder_id", "name"),
        # Prevent names from containing an underscore, so space characters can
        # be escaped in urls.
        sql_schema.CheckConstraint("name NOT LIKE '%\\_%' ESCAPE '\\'"),
    )

    community_id: Mapped[int] = mapped_column(
        ForeignKey("community.id", ondelete="CASCADE")
    )
    parent_folder_id: Mapped[int] = mapped_column(nullable=True, init=False)

    name: Mapped[str]

    community: Mapped[DBCommunity] = relationship(viewonly=True, init=False, repr=False)
    parent_folder: Mapped["DBDirFolder"] = relationship(
        back_populates="subfolders",
        remote_side="DBDirFolder.id, DBDirFolder.community_id",
        init=False,
        repr=False,
    )
    subfolders: Mapped[List["DBDirFolder"]] = relationship(
        back_populates="parent_folder",
        init=False,
        repr=False,
    )
    files: Mapped[List["DBDirFile"]] = relationship(
        back_populates="parent_folder",
        init=False,
        repr=False,
    )
    reader_groups: Mapped[List[DBGroup]] = relationship(
        secondary="directory_folder_group_permissions",
        init=False,
        repr=False,
    )


class DBDirFile(Base, DBNode):
    __tablename__ = "directory_file"
    __table_args__ = (
        sql_schema.UniqueConstraint("id", "community_id"),
        sql_schema.ForeignKeyConstraint(
            ["folder_id", "community_id"],
            ["directory_folder.id", "directory_folder.community_id"],
            ondelete="CASCADE",
        ),
        sql_schema.UniqueConstraint("folder_id", "name"),
        # Prevent names from containing an underscore, so space characters can
        # be escaped in urls.
        sql_schema.CheckConstraint("name NOT LIKE '%\\_%' ESCAPE '\\'"),
        sql_schema.CheckConstraint(
            "(url IS NULL AND data IS NOT NULL) OR "
            "(data IS NULL AND url IS NOT NULL)"
        ),
    )

    community_id: Mapped[int] = mapped_column(
        ForeignKey("community.id", ondelete="CASCADE")
    )
    folder_id: Mapped[int] = mapped_column(init=False)

    name: Mapped[str]
    url: Mapped[Optional[str]] = mapped_column(default=None)
    data: Mapped[Optional[bytes]] = mapped_column(default=None)

    community: Mapped[DBCommunity] = relationship(viewonly=True, init=False, repr=False)
    parent_folder: Mapped[DBDirFolder] = relationship(
        back_populates="files",
        kw_only=True,
        repr=False,
    )
    reader_groups: Mapped[List[DBGroup]] = relationship(
        secondary="directory_file_group_permissions",
        init=False,
        repr=False,
    )


class DBDirFolderGroupPermissions(Base):
    __tablename__ = "directory_folder_group_permissions"
    __table_args__ = (
        sql_schema.ForeignKeyConstraint(
            ["folder_id", "community_id"],
            ["directory_folder.id", "directory_folder.community_id"],
            ondelete="CASCADE",
        ),
        sql_schema.ForeignKeyConstraint(
            ["group_id", "community_id"],
            ["group.id", "group.community_id"],
            ondelete="CASCADE",
        ),
    )

    community_id: Mapped[int] = mapped_column(
        ForeignKey("community.id", ondelete="CASCADE"), primary_key=True
    )
    folder_id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(primary_key=True)


class DBDirFileGroupPermissions(Base):
    __tablename__ = "directory_file_group_permissions"
    __table_args__ = (
        sql_schema.ForeignKeyConstraint(
            ["file_id", "community_id"],
            ["directory_file.id", "directory_file.community_id"],
            ondelete="CASCADE",
        ),
        sql_schema.ForeignKeyConstraint(
            ["group_id", "community_id"],
            ["group.id", "group.community_id"],
            ondelete="CASCADE",
        ),
    )

    community_id: Mapped[int] = mapped_column(
        ForeignKey("community.id", ondelete="CASCADE"), primary_key=True
    )
    file_id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(primary_key=True)


class DBBillingPayment(Base, DBNode):
    __tablename__ = "billing_payment"
    __table_args__ = (
        sql_schema.ForeignKeyConstraint(
            ["payer_id", "community_id"],
            ["associate.id", "associate.community_id"],
            ondelete="RESTRICT",
        ),
        sql_schema.UniqueConstraint("id", "community_id"),
    )

    community_id: Mapped[int] = mapped_column(
        ForeignKey("community.id", ondelete="CASCADE")
    )
    payer_id: Mapped[int]

    amount: Mapped[int] = mapped_column()
    payment_date: Mapped[datetime.datetime]

    community: Mapped[DBCommunity] = relationship(viewonly=True, init=False, repr=False)
    charges: Mapped[List["DBBillingCharge"]] = relationship(
        secondary="billing_transaction",
        back_populates="payments",
        viewonly=True,
        init=False,
        repr=False,
    )


class DBBillingCharge(Base, DBNode):
    __tablename__ = "billing_charge"
    __table_args__ = (
        sql_schema.UniqueConstraint("id", "community_id"),
        sql_schema.ForeignKeyConstraint(
            ["residence_id", "community_id"],
            ["residence.id", "residence.community_id"],
            ondelete="RESTRICT",
        ),
        sql_schema.ForeignKeyConstraint(
            ["occupant_id", "community_id"],
            ["associate.id", "associate.community_id"],
            ondelete="RESTRICT",
        ),
        sql_schema.CheckConstraint(
            "(residence_id IS NULL AND occupant_id IS NOT NULL) OR "
            "(occupant_id IS NULL AND residence_id IS NOT NULL)"
        ),
    )
    # CASCADE when community is deleted, because deleting the community can
    # only mean that they are no longer interested in using the service. But
    # if a residence is deleted, what should be done with the billing data?
    # Unclear, so RESTRICT and have the programmer delete this data first
    # if the deletion is intentional. Same reason for user_id RESTRICT.

    community_id: Mapped[int] = mapped_column(
        ForeignKey("community.id", ondelete="CASCADE")
    )
    residence_id: Mapped[Optional[int]] = mapped_column(init=False)
    occupant_id: Mapped[Optional[int]] = mapped_column(init=False)

    name: Mapped[str]
    amount: Mapped[int] = mapped_column()
    charge_date: Mapped[datetime.datetime] = mapped_column(
        init=False, server_default=sql_func.now()
    )
    due_date: Mapped[datetime.date]

    community: Mapped[DBCommunity] = relationship(
        viewonly=True, init=False, repr=False, back_populates="billing_charges"
    )
    residence: Mapped[Optional[DBResidence]] = relationship(
        init=False, repr=False, back_populates="billing_charges"
    )
    occupant: Mapped[Optional[DBAssociate]] = relationship(
        init=False,
        repr=False,
        back_populates="billing_charges",
        overlaps="billing_charges,residence",
    )
    payments: Mapped[List[DBBillingPayment]] = relationship(
        secondary="billing_transaction",
        back_populates="charges",
        viewonly=True,
        init=False,
        repr=False,
    )


class DBBillingRecurringCharge(Base, DBNode):
    __tablename__ = "billing_recurring_charge"
    __table_args__ = (
        sql_schema.ForeignKeyConstraint(
            ["residence_id", "community_id"],
            ["residence.id", "residence.community_id"],
            ondelete="RESTRICT",
        ),
        sql_schema.ForeignKeyConstraint(
            ["occupant_id", "community_id"],
            ["associate.id", "associate.community_id"],
            ondelete="RESTRICT",
        ),
        sql_schema.CheckConstraint(
            "(residence_id IS NULL AND occupant_id IS NOT NULL) OR "
            "(occupant_id IS NULL AND residence_id IS NOT NULL)"
        ),
    )
    # CASCADE when community is deleted, because deleting the community can
    # only mean that they are no longer interested in using the service. But
    # if a residence is deleted, what should be done with the billing data?
    # Unclear, so RESTRICT and have the programmer delete this data first
    # if the deletion is intentional. Same reason for user_id RESTRICT.

    community_id: Mapped[int] = mapped_column(
        ForeignKey("community.id", ondelete="CASCADE")
    )
    residence_id: Mapped[Optional[int]]
    occupant_id: Mapped[Optional[int]] = mapped_column(init=False)

    name: Mapped[str]
    amount: Mapped[int]
    frequency: Mapped[BillingFrequency]
    frequency_skip: Mapped[int] = mapped_column(insert_default=1)
    time_to_pay = Mapped[datetime.timedelta]
    next_charge_date: Mapped[datetime.datetime]

    community: Mapped[DBCommunity] = relationship(
        viewonly=True,
        init=False,
        repr=False,
        back_populates="recurring_billing_charges",
    )
    residence: Mapped[Optional[DBResidence]] = relationship(
        init=False, repr=False, back_populates="recurring_billing_charges"
    )
    occupant: Mapped[Optional[DBAssociate]] = relationship(
        init=False,
        repr=False,
        back_populates="recurring_billing_charges",
        overlaps="recurring_billing_charges,residence",
    )


class DBBillingTransaction(Base):
    __tablename__ = "billing_transaction"
    __table_args__ = (
        sql_schema.ForeignKeyConstraint(
            ["payment_id", "community_id"],
            ["billing_payment.id", "billing_payment.community_id"],
            ondelete="CASCADE",
        ),
        sql_schema.ForeignKeyConstraint(
            ["charge_id", "community_id"],
            ["billing_charge.id", "billing_charge.community_id"],
            ondelete="CASCADE",
        ),
        sql_schema.CheckConstraint("charge_closing_balance >= 0"),
        sql_schema.CheckConstraint("payment_closing_balance >= 0"),
        sql_schema.CheckConstraint(
            "charge_closing_balance = charge_opening_balance - transaction_amount"
        ),
        sql_schema.CheckConstraint(
            "payment_closing_balance = payment_opening_balance - transaction_amount"
        ),
    )

    community_id: Mapped[int] = mapped_column(
        ForeignKey("community.id", ondelete="CASCADE"), primary_key=True, init=False
    )
    payment_id: Mapped[int] = mapped_column(primary_key=True, init=False)
    charge_id: Mapped[int] = mapped_column(primary_key=True, init=False)

    transaction_amount: Mapped[int]
    charge_opening_balance: Mapped[int] = mapped_column(init=False)
    charge_closing_balance: Mapped[int] = mapped_column(init=False)
    payment_opening_balance: Mapped[int] = mapped_column(init=False)
    payment_closing_balance: Mapped[int] = mapped_column(init=False)

    payment: Mapped["DBBillingPayment"] = relationship(repr=False, overlaps="charge")
    charge: Mapped["DBBillingCharge"] = relationship(repr=False, overlaps="payment")

    def __post_init__(self):
        self.charge_opening_balance = (
            self.charge.remaining_balance
            if self.charge.remaining_balance is not None
            else self.charge.amount
        )
        self.payment_opening_balance = (
            self.payment.remaining_balance
            if self.payment.remaining_balance is not None
            else self.payment.amount
        )
        self.charge_closing_balance = (
            self.charge_opening_balance - self.transaction_amount
        )
        self.payment_closing_balance = (
            self.payment_opening_balance - self.transaction_amount
        )


DBBillingCharge.remaining_balance = column_property(
    sql_func.coalesce(
        select(sql_func.min(DBBillingTransaction.charge_closing_balance))
        .where(DBBillingTransaction.charge_id == DBBillingCharge.id)
        .correlate_except(DBBillingTransaction)
        .scalar_subquery(),
        DBBillingCharge.amount,
    )
)


DBBillingPayment.remaining_balance = column_property(
    sql_func.coalesce(
        select(sql_func.min(DBBillingTransaction.payment_closing_balance))
        .where(DBBillingTransaction.payment_id == DBBillingPayment.id)
        .correlate_except(DBBillingTransaction)
        .scalar_subquery(),
        DBBillingPayment.amount,
    )
)
