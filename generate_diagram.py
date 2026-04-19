"""
ShopCloud - Definitive Architecture (Best-of-4 Analysis)
ECS Fargate | 3-Tier Subnets | Cognito | WAF/Shield | PostgreSQL | eu-west-1 DR
+ CI/CD Pipeline | Dev VPC | CloudWatch Monitoring
Generates: shopcloud_final_architecture.png
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Fargate, Lambda, EC2
from diagrams.aws.database import RDS, ElastiCache
from diagrams.aws.network import ALB, CloudFront, NATGateway, Route53, InternetGateway
from diagrams.aws.storage import S3
from diagrams.aws.integration import SQS
from diagrams.aws.engagement import SES
from diagrams.aws.security import WAF, Shield, Cognito
from diagrams.aws.general import Users

# ── Colors ──
PURPLE = "#7B1FA2"
DARK = "#232F3E"
ORANGE = "#ED7100"
BLUE = "#1565C0"
RED = "#C62828"
TEAL = "#00695C"
INDIGO = "#283593"
GRAY = "#78909C"
FIRE = "#E65100"
CRIT = "#B71C1C"
PINK = "#AD1457"
GREEN = "#2E7D32"

graph_attr = {
    "fontsize": "18",
    "fontname": "Helvetica Bold",
    "bgcolor": "white",
    "nodesep": "0.7",
    "ranksep": "0.75",
    "splines": "spline",
    "pad": "0.5",
    "compound": "true",
    "dpi": "150",
}

node_attr = {"fontsize": "9", "fontname": "Helvetica"}
edge_attr = {"fontsize": "7", "fontname": "Helvetica"}

_svc = {
    "bgcolor": "#FFF3E0", "pencolor": "#BCAAA4",
    "style": "dashed,rounded", "penwidth": "0.5",
    "fontsize": "8", "fontname": "Helvetica", "fontcolor": "#5D4037",
}

_dev_tier = {
    "bgcolor": "#FAFAFA", "pencolor": "#9E9E9E",
    "style": "rounded", "penwidth": "1",
    "fontsize": "9", "fontname": "Helvetica Bold",
}

with Diagram(
    "ShopCloud - Complete Architecture | us-east-1 (N. Virginia)",
    filename="shopcloud_final_architecture",
    outformat="png",
    show=False,
    direction="TB",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
):
    # ══════════════════════════════════════
    # EXTERNAL USERS
    # ══════════════════════════════════════
    users = Users("EU + US\nCustomers")
    admin_user = Users("Admin\nStaff")

    # ══════════════════════════════════════
    # EDGE LAYER
    # ══════════════════════════════════════
    with Cluster("Edge Layer (Global)", graph_attr={
        "bgcolor": "#F3E5F5", "pencolor": PURPLE,
        "style": "rounded", "penwidth": "1.5",
        "fontsize": "11", "fontname": "Helvetica Bold",
    }):
        r53 = Route53("Route 53\nDNS")
        cf = CloudFront("CloudFront\nCDN")
        waf = WAF("AWS WAF")
        shield = Shield("Shield\nStandard")
        s3_static = S3("S3 Static\nAssets (OAC)")

    # ── Auth (managed, outside VPC) ──
    cognito = Cognito("Amazon Cognito\n2 User Pools\n(Customer + Admin)")

    # ══════════════════════════════════════
    # PRODUCTION VPC
    # ══════════════════════════════════════
    with Cluster("Production VPC - 10.0.0.0/16", graph_attr={
        "bgcolor": "#F1F8E9", "pencolor": "#1B5E20",
        "style": "dashed", "penwidth": "2",
        "fontsize": "13", "fontname": "Helvetica Bold",
    }):
        igw = InternetGateway("Internet\nGateway")

        with Cluster(
            "Public Subnets - 10.0.1.0/24 (AZ-A) + 10.0.2.0/24 (AZ-B)",
            graph_attr={
                "bgcolor": "#E8F5E9", "pencolor": GREEN,
                "style": "rounded", "penwidth": "1.5",
                "fontsize": "10", "fontname": "Helvetica Bold",
            },
        ):
            pub_alb = ALB("Public ALB\n(Multi-AZ)")
            bastion = EC2("Bastion Host\nt3.micro (AZ-A)")
            nat = NATGateway("NAT Gateway\n+ EIP (AZ-A)")

        with Cluster(
            "Private App Subnets - 10.0.10.0/24 (AZ-A) + 10.0.20.0/24 (AZ-B)",
            graph_attr={
                "bgcolor": "#E3F2FD", "pencolor": BLUE,
                "style": "rounded", "penwidth": "1.5",
                "fontsize": "10", "fontname": "Helvetica Bold",
            },
        ):
            with Cluster("Customer Services (ECS Fargate, Auto Scaling)", graph_attr=_svc):
                catalog = Fargate("Product\nCatalog")
                cart = Fargate("Shopping\nCart")
                checkout = Fargate("Checkout &\nPayment")

            with Cluster("Admin Panel (Network-Isolated)", graph_attr=_svc):
                int_alb = ALB("Internal ALB\n(No Public IP)")
                admin = Fargate("Admin\nPanel")

        with Cluster(
            "Private Data Subnets - 10.0.30.0/24 (AZ-A) + 10.0.40.0/24 (AZ-B)",
            graph_attr={
                "bgcolor": "#EDE7F6", "pencolor": "#4527A0",
                "style": "rounded", "penwidth": "1.5",
                "fontsize": "10", "fontname": "Helvetica Bold",
            },
        ):
            redis = ElastiCache("ElastiCache Redis\ncache.t3.micro (AZ-A)")
            rds_primary = RDS("RDS Primary\nPostgreSQL (AZ-A)")
            rds_standby = RDS("RDS Standby\nSync Replica (AZ-B)")

    # ══════════════════════════════════════
    # ASYNC INVOICE PIPELINE
    # ══════════════════════════════════════
    with Cluster("Async Invoice Pipeline (Serverless)", graph_attr={
        "bgcolor": "#FFF8E1", "pencolor": FIRE,
        "style": "rounded", "penwidth": "1.5",
        "fontsize": "10", "fontname": "Helvetica Bold",
    }):
        sqs = SQS("SQS\nOrder Queue")
        dlq = SQS("SQS DLQ\n(Dead Letters)")
        inv_lambda = Lambda("Lambda\nPDF Gen")
        s3_inv = S3("S3 Invoice\nPDF Storage")
        ses = SES("SES\nEmail")

    # ══════════════════════════════════════
    # DEVELOPMENT VPC
    # ══════════════════════════════════════
    with Cluster("Development VPC - 10.1.0.0/16 (Single AZ, Reduced Resources)", graph_attr={
        "bgcolor": "#FFF3E0", "pencolor": "#E65100",
        "style": "dashed", "penwidth": "1.5",
        "fontsize": "12", "fontname": "Helvetica Bold",
    }):
        with Cluster("Dev Public - 10.1.1.0/24", graph_attr=_dev_tier):
            dev_alb = ALB("Dev ALB")
            dev_bastion = EC2("Dev Bastion")

        with Cluster("Dev App - 10.1.10.0/24", graph_attr=_dev_tier):
            dev_app = Fargate("Customer App\n(0.25 vCPU)")
            dev_admin = Fargate("Dev Admin")

        with Cluster("Dev Data - 10.1.30.0/24", graph_attr=_dev_tier):
            dev_rds = RDS("Dev RDS\nPostgreSQL\n(Single Instance)")
            dev_redis = ElastiCache("Dev Redis")

    # ══════════════════════════════════════
    # DISASTER RECOVERY
    # ══════════════════════════════════════
    with Cluster("Disaster Recovery - eu-west-1 (Ireland)", graph_attr={
        "bgcolor": "#ECEFF1", "pencolor": GRAY,
        "style": "dashed", "penwidth": "1.5",
        "fontsize": "10", "fontname": "Helvetica Bold",
    }):
        rds_replica = RDS("RDS Read Replica\n(Cross-Region)")

    # ══════════════════════════════════════
    # LAYOUT CONTROL
    # ══════════════════════════════════════

    # Main vertical spine
    users >> Edge(style="invis") >> r53
    cf >> Edge(style="invis") >> igw
    igw >> Edge(style="invis") >> pub_alb
    pub_alb >> Edge(style="invis") >> catalog
    cart >> Edge(style="invis") >> int_alb
    admin >> Edge(style="invis") >> redis
    redis >> Edge(style="invis") >> rds_primary
    rds_primary >> Edge(style="invis") >> sqs
    ses >> Edge(style="invis") >> dev_alb
    dev_app >> Edge(style="invis") >> dev_rds
    dev_rds >> Edge(style="invis") >> rds_replica

    # Position Cognito
    r53 >> Edge(style="invis") >> cognito
    cognito >> Edge(style="invis") >> bastion

    # ══════════════════════════════════════
    # PRODUCTION DATA FLOWS
    # ══════════════════════════════════════

    # User -> Edge -> IGW -> ALB
    users >> Edge(label="HTTPS", color=PURPLE, style="bold") >> r53
    r53 >> Edge(color=PURPLE) >> cf
    cf >> Edge(label="static", color=PURPLE) >> s3_static
    cf >> Edge(label="dynamic\n/api/*", color=DARK, style="bold") >> igw
    igw >> Edge(color=DARK) >> pub_alb

    # ALB -> Services
    pub_alb >> Edge(color=ORANGE) >> catalog
    pub_alb >> Edge(color=ORANGE) >> cart
    pub_alb >> Edge(color=ORANGE) >> checkout

    # Admin access
    admin_user >> Edge(label="SSH", color=RED, style="dashed") >> bastion
    bastion >> Edge(
        label="SSH fwd", color=RED, style="dashed", constraint="false",
    ) >> int_alb
    int_alb >> Edge(color=RED, style="dashed") >> admin

    # Services -> DB
    catalog >> Edge(color=BLUE, constraint="false") >> rds_primary
    checkout >> Edge(color=BLUE, constraint="false") >> rds_primary
    admin >> Edge(color=BLUE, style="dashed", constraint="false") >> rds_primary

    # Sessions
    cart >> Edge(label="sessions", color=PINK) >> redis
    checkout >> Edge(
        label="read cart", color=PINK, style="dashed", constraint="false",
    ) >> redis

    # Auth (Cognito)
    pub_alb >> Edge(
        label="JWT\n(Customer)", color=TEAL, style="dashed", constraint="false",
    ) >> cognito
    int_alb >> Edge(
        label="JWT\n(Admin)", color=TEAL, style="dashed", constraint="false",
    ) >> cognito

    # Async Invoice
    checkout >> Edge(
        label="order event", color=FIRE, constraint="false",
    ) >> sqs
    sqs >> Edge(color=FIRE) >> inv_lambda
    inv_lambda >> Edge(label="PDF", color=FIRE) >> s3_inv
    inv_lambda >> Edge(label="email", color=FIRE) >> ses
    sqs >> Edge(label="failed", color=CRIT, style="dashed", constraint="false") >> dlq
    inv_lambda >> Edge(
        label="read order", color=BLUE, style="dashed", constraint="false",
    ) >> rds_primary

    # DB Replication
    rds_primary >> Edge(
        label="sync", color=INDIGO, style="bold", constraint="false",
    ) >> rds_standby
    rds_primary >> Edge(
        label="async replication\n(cross-region)",
        color=GRAY, style="dashed", constraint="false",
    ) >> rds_replica

    # ══════════════════════════════════════
    # DEV VPC INTERNAL FLOWS (simplified)
    # ══════════════════════════════════════
    dev_alb >> Edge(color=ORANGE) >> dev_app
    dev_app >> Edge(color=BLUE, constraint="false") >> dev_rds
    dev_app >> Edge(color=PINK, constraint="false") >> dev_redis
    dev_admin >> Edge(color=BLUE, style="dashed", constraint="false") >> dev_rds
