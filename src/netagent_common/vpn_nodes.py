from sqlalchemy import func, select
from sqlalchemy.orm import Session

from netagent_db.models import Device, VpnNode


class VpnNodeCapacityError(RuntimeError):
    """All VPN nodes are at capacity."""


def pick_vpn_node(session: Session) -> VpnNode | None:
    """Pick active node with the fewest active devices under max_users."""
    nodes = session.scalars(
        select(VpnNode)
        .where(VpnNode.is_active.is_(True))
        .order_by(VpnNode.sort_order, VpnNode.id)
    ).all()
    if not nodes:
        return None

    counts: dict[int, int] = {}
    rows = session.execute(
        select(Device.vpn_node_id, func.count())
        .where(Device.status == "active", Device.vpn_node_id.is_not(None))
        .group_by(Device.vpn_node_id)
    ).all()
    for node_id, count in rows:
        if node_id is not None:
            counts[int(node_id)] = int(count)

    chosen: VpnNode | None = None
    chosen_count: int | None = None
    for node in nodes:
        active = counts.get(node.id, 0)
        if active >= node.max_users:
            continue
        if chosen is None or active < chosen_count:
            chosen = node
            chosen_count = active

    if chosen is None:
        raise VpnNodeCapacityError("Все VPN-ноды заполнены. Добавьте новую ноду или увеличьте лимит.")
    return chosen


def list_active_vpn_nodes(session: Session) -> list[VpnNode]:
    return list(
        session.scalars(
            select(VpnNode)
            .where(VpnNode.is_active.is_(True))
            .order_by(VpnNode.sort_order, VpnNode.id)
        ).all()
    )
