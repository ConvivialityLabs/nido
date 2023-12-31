actor User {}

resource Group {
    permissions = ["query", "create", "update", "delete"];
    roles = ["member", "manager"];

    "query" if "member";

    "query" if "manager";
    "update" if "manager";
    "delete" if "manager";
}

has_permission(user: User, "create", group: Group) if
    associate in user.self_associates and
    associate matches {community_id: group.community_id};

has_role(user: User, "member", group: Group) if
    member in group.custom_members and
    member matches {user_id: user.id};

has_role(user: User, "manager", group: Group) if
    member in group.managed_by.custom_members and
    member matches {user_id: user.id};

resource Right {
    permissions = ["delegate", "revoke"];
    roles = ["possessor", "delegator"];

    "delegate" if "delegator";

}

has_role(user: User, "possessor", right: Right) if
    has_role(user, "member", group) and
    group matches {right_id: right.id};

has_role(user: User, "delegator", right: Right) if
    has_role(user, "member", group) and
    group matches {right_id: right.parent_right_id} and
    right.parent_right.permits(Permissions.CAN_DELEGATE) and
    right.parent_right.permits(right.permissions);

has_permission(user: User, "revoke", right: Right) if
    has_role(user, "delegator", right)
    and right.id != right.parent_right_id;

resource ContactMethod {
    permissions = ["query", "delete"];
    relations = { owner: User };

    "query" if "owner";
    "delete" if "owner";
}

# TODO Remove this rule when proper logic for "public" contact methods
# is implemented.
has_permission(_: User, "query", _: ContactMethod);

has_relation(user: User, "owner", contact_method: ContactMethod) if
    contact_method.user_id = user.id;


resource BillingCharge {
    permissions = ["query", "create", "edit", "delete"];

    "create" if "edit";
    "delete" if "edit";
}

has_permission(_: User, "edit", _: BillingCharge);
has_permission(_: User, "query", _: BillingCharge);


allow(actor, action, resource) if
    has_permission(actor, action, resource);
