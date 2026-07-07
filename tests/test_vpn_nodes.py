from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from netagent_common.vpn_nodes import pick_vpn_node
from netagent_db.base import Base
from netagent_db.models import VpnNode
from netagent_db.seed import seed_plans


def test_pick_vpn_node_returns_first_when_empty() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    with factory() as session:
        seed_plans(session)
        session.add_all(
            [
                VpnNode(
                    slug="lt1",
                    name="LT1",
                    public_host="1.1.1.1",
                    public_port=443,
                    agent_url="https://1.1.1.1:8443",
                    reality_public_key="key1",
                    reality_short_id="aaa",
                    max_users=50,
                    sort_order=1,
                ),
                VpnNode(
                    slug="fi1",
                    name="FI1",
                    public_host="2.2.2.2",
                    public_port=2087,
                    agent_url="https://2.2.2.2:8443",
                    reality_public_key="key2",
                    reality_short_id="bbb",
                    max_users=50,
                    sort_order=2,
                ),
            ]
        )
        session.commit()

        picked = pick_vpn_node(session)
        assert picked is not None
        assert picked.slug == "lt1"
