"""
Generate ShopCloud Phase 1 Report PDF - Enhanced version.
Fixes: empty TOC, thin content, excessive whitespace, shallow justifications.
"""

from fpdf import FPDF
import os

BLUE = (30, 70, 110)
DARK = (40, 40, 40)
GRAY = (120, 120, 120)
WHITE = (255, 255, 255)
LIGHT_BLUE_BG = (230, 240, 250)


class ShopCloudReport(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(*GRAY)
            self.cell(0, 8, "ShopCloud - Phase 1: Architecture & Design | EECE 503Q", align="L")
            self.set_font("Helvetica", "I", 9)
            self.cell(0, 8, f"", align="R")
            self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*GRAY)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, num, title):
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(*BLUE)
        self.cell(0, 12, f"{num}. {title}", new_x="LMARGIN", new_y="NEXT")
        # underline
        self.set_draw_color(*BLUE)
        self.set_line_width(0.5)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(6)

    def subsection_title(self, num, title):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*BLUE)
        self.cell(0, 10, f"{num} {title}", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def sub3_title(self, title):
        """Third-level heading."""
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(50, 50, 50)
        self.cell(0, 9, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 11)
        self.set_text_color(*DARK)
        self.multi_cell(0, 6.5, text)
        self.ln(3)

    def bold_label(self, label, text):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*DARK)
        self.write(6.5, f"{label} ")
        self.set_font("Helvetica", "", 11)
        self.write(6.5, text)
        self.ln(8)

    def bullet(self, text):
        self.set_font("Helvetica", "", 11)
        self.set_text_color(*DARK)
        x = self.get_x()
        self.cell(6, 6.5, "-")
        self.multi_cell(self.w - self.r_margin - x - 6, 6.5, text)
        self.ln(1)

    def bullet_bold(self, label, text):
        self.set_font("Helvetica", "", 11)
        self.set_text_color(*DARK)
        x = self.get_x()
        self.cell(6, 6.5, "-")
        self.set_font("Helvetica", "B", 11)
        self.write(6.5, f"{label}: ")
        self.set_font("Helvetica", "", 11)
        self.multi_cell(0, 6.5, text)
        self.ln(1)

    def add_table_row(self, cells, widths, bold=False, header=False):
        if header:
            self.set_font("Helvetica", "B", 10)
            self.set_fill_color(*BLUE)
            self.set_text_color(*WHITE)
        elif bold:
            self.set_font("Helvetica", "B", 10)
            self.set_fill_color(*LIGHT_BLUE_BG)
            self.set_text_color(*BLUE)
        else:
            self.set_font("Helvetica", "", 10)
            self.set_fill_color(*WHITE)
            self.set_text_color(*DARK)
        for i, (cell, w) in enumerate(zip(cells, widths)):
            align = "R" if i == len(cells) - 1 and not header else "L"
            self.cell(w, 8, cell, border=1, fill=True, align=align)
        self.ln()


pdf = ShopCloudReport()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)
pw = pdf.w - 2 * pdf.l_margin  # printable width

# ═══════════════════════════════════════════
# PAGE 1: TITLE PAGE
# ═══════════════════════════════════════════
pdf.add_page()
pdf.ln(50)
pdf.set_font("Helvetica", "", 13)
pdf.set_text_color(*GRAY)
pdf.cell(0, 10, "EECE 503Q - DevSecOps", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(8)
pdf.set_font("Helvetica", "B", 28)
pdf.set_text_color(*BLUE)
pdf.cell(0, 14, "Project ShopCloud", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 18)
pdf.set_text_color(50, 50, 50)
pdf.cell(0, 12, "E-Commerce Platform", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(2)
pdf.set_font("Helvetica", "", 14)
pdf.set_text_color(*BLUE)
pdf.cell(0, 10, "Phase 1: Architecture and Design Report", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(12)
pdf.set_draw_color(*BLUE)
pdf.set_line_width(0.8)
pdf.line(40, pdf.get_y(), pdf.w - 40, pdf.get_y())
pdf.ln(10)
pdf.set_font("Helvetica", "", 12)
pdf.set_text_color(60, 60, 60)
pdf.cell(0, 8, "American University of Beirut", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 8, "Maroun Semaan Faculty of Engineering & Architecture", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 8, "Spring 2026", align="C", new_x="LMARGIN", new_y="NEXT")

# ═══════════════════════════════════════════
# PAGE 2: TABLE OF CONTENTS
# ═══════════════════════════════════════════
pdf.add_page()
pdf.set_font("Helvetica", "B", 18)
pdf.set_text_color(*BLUE)
pdf.cell(0, 12, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
pdf.set_draw_color(*BLUE)
pdf.set_line_width(0.5)
pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
pdf.ln(8)

toc_entries = [
    (True,  "1.  Executive Summary", "3"),
    (True,  "2.  Architecture Overview", "4"),
    (False, "    2.1  How Traffic Flows Through the System", "7"),
    (False, "    2.2  ECS Fargate - Compute Layer", "7"),
    (False, "    2.3  Database, Async Pipeline, and Disaster Recovery", "7"),
    (False, "    2.4  Network Security Model", "7"),
    (False, "    2.5  VPC and Subnet Layout", "8"),
    (True,  "3.  Service-to-Infrastructure Mapping", "9"),
    (False, "    3.1  Product Catalog", "9"),
    (False, "    3.2  Shopping Cart", "10"),
    (False, "    3.3  Checkout & Payment", "11"),
    (False, "    3.4  Authentication", "12"),
    (False, "    3.5  Inventory Admin Panel", "13"),
    (False, "    3.6  Orders & Inventory Database", "14"),
    (False, "    3.7  Invoice Generation", "15"),
    (False, "    3.8  Dev & Production Environments", "16"),
    (True,  "4.  Cost Estimation", "17"),
    (False, "    4.1  Production Environment", "17"),
    (False, "    4.2  Development Environment", "18"),
    (False, "    4.3  Combined Summary and Cost Drivers", "18"),
    (True,  "5.  Design Methodology - Key Decisions", "19"),
    (False, "    5.1  Compute: ECS Fargate + Lambda", "19"),
    (False, "    5.2  Environment Isolation: Separate VPCs", "20"),
    (False, "    5.3  Region Strategy: Single Region + CDN + DR", "20"),
    (False, "    5.4  Database: RDS PostgreSQL Multi-AZ", "21"),
    (False, "    5.5  Invoice Pipeline: SQS + Lambda + S3 + SES", "21"),
    (False, "    5.6  Admin Access: Internal ALB + Bastion", "22"),
    (True,  "6.  Conclusion", "23"),
]

for is_main, label, page_num in toc_entries:
    sz = 11 if is_main else 10
    style = "B" if is_main else ""
    pdf.set_font("Helvetica", style, sz)
    pdf.set_text_color(*DARK)
    label_w = pdf.get_string_width(label)
    page_w = pdf.get_string_width(page_num)
    avail = pw - label_w - page_w - 2
    pdf.cell(label_w, 7, label)
    # draw dot leader
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(180, 180, 180)
    dot_char_w = pdf.get_string_width(".")
    num_dots = max(0, int(avail / dot_char_w))
    pdf.cell(avail, 7, " " + "." * num_dots + " ")
    # page number
    pdf.set_font("Helvetica", style, sz)
    pdf.set_text_color(*DARK)
    pdf.cell(page_w, 7, page_num, new_x="LMARGIN", new_y="NEXT")

# ═══════════════════════════════════════════
# SECTION 1: EXECUTIVE SUMMARY
# ═══════════════════════════════════════════
pdf.add_page()
pdf.section_title("1", "Executive Summary")

pdf.body_text(
    "ShopCloud is a lightweight e-commerce platform designed for a startup targeting customers "
    "in Europe and the United States. This report presents the AWS architecture for eight services: "
    "product catalog, shopping cart, checkout, authentication, admin panel, relational database, "
    "invoice generation, and isolated dev/prod environments. Every decision is justified on technical "
    "and economic grounds, with alternatives explicitly evaluated."
)

pdf.body_text(
    "Key architectural choices: ECS Fargate runs four synchronous services as independent, auto-scaling "
    "containers with no cluster management overhead. RDS PostgreSQL Multi-AZ provides automatic failover "
    "with a cross-region replica in eu-west-1 (Ireland) for European customers. Amazon Cognito handles "
    "authentication with two user pools (customer + admin) at zero cost. The admin panel is triply "
    "isolated behind an Internal ALB, bastion SSH tunnel, and Cognito Admin Pool. An async invoice "
    "pipeline (SQS + Lambda + S3 + SES + DLQ) operates entirely within free tier. Production and "
    "development run in separate VPCs (10.0.0.0/16 and 10.1.0.0/16) with three-tier subnets and no "
    "peering. Edge security uses Route 53, CloudFront, WAF, and Shield Standard."
)

pdf.body_text(
    "The estimated monthly cost is $225.49 for production and $117.04 for development, totaling "
    "$342.53/month ($4,110 annually) - 25% less than an equivalent EKS architecture by eliminating "
    "$237/month in Kubernetes control plane and worker node fees. The entire infrastructure is "
    "designed to be provisioned via Terraform from a single AWS account."
)

# ═══════════════════════════════════════════
# SECTION 2: ARCHITECTURE OVERVIEW + DIAGRAM
# ═══════════════════════════════════════════
pdf.add_page()
pdf.section_title("2", "Architecture Overview")

pdf.body_text(
    "The following diagram shows the complete ShopCloud architecture, deployed in the us-east-1 "
    "(N. Virginia) AWS region. The production VPC spans two Availability Zones (AZ-A and AZ-B) with "
    "three-tier subnet isolation (public, private app, private data). A separate development VPC "
    "mirrors the production architecture at reduced scale. The edge layer, async invoice pipeline, "
    "and disaster recovery region are shown alongside both VPCs."
)

# Insert diagram split across two pages
base_dir = os.path.dirname(os.path.abspath(__file__))
img_w = pw * 0.95
img_x = (pdf.w - img_w) / 2

pdf.set_font("Helvetica", "I", 10)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 6, "Figure 1: ShopCloud Complete Architecture (Part 1 of 2 - Edge, VPC, Services)", align="C",
         new_x="LMARGIN", new_y="NEXT")
pdf.ln(2)
pdf.image(os.path.join(base_dir, "shopcloud_diagram_top.png"), x=img_x, w=img_w)
pdf.image(os.path.join(base_dir, "shopcloud_diagram_bottom.png"), x=img_x, w=img_w)

# ═══════════════════════════════════════════
# SECTION 2.1: TRAFFIC FLOW
# ═══════════════════════════════════════════
pdf.add_page()
pdf.subsection_title("2.1", "How Traffic Flows Through the System")

pdf.body_text(
    "Static assets (images, CSS, JS) are served through CloudFront, which caches at edge locations "
    "near both EU and US customers (~10ms vs ~100ms cross-Atlantic). The S3 origin bucket is not "
    "publicly accessible - CloudFront accesses it via Origin Access Control (OAC)."
)
pdf.body_text(
    "Dynamic API requests enter the VPC through the Internet Gateway and reach the Public ALB in the "
    "public subnets. The ALB performs path-based routing (/api/products/*, /api/cart/*, /api/checkout/*) "
    "to the appropriate Fargate service and integrates with Cognito for JWT validation. The ALB spans "
    "both AZs for high availability. The Bastion Host (t3.micro, AZ-A) provides SSH access for admin "
    "panel access. The NAT Gateway enables outbound calls from private subnets (ECR image pulls, "
    "AWS API calls) without inbound exposure."
)

# ═══════════════════════════════════════════
# SECTION 2.2: FARGATE COMPUTE LAYER
# ═══════════════════════════════════════════
pdf.subsection_title("2.2", "ECS Fargate - Compute Layer")

pdf.body_text(
    "ECS Fargate runs all application containers with no cluster management. Each service has its own "
    "auto scaling policy, task definition, and security group. Three customer-facing services (Catalog, "
    "Cart, Checkout) are registered on the Public ALB. The Admin Panel runs behind an Internal ALB "
    "with no public IP - accessible only via bastion SSH tunnel, protected by the Cognito Admin Pool. "
    "ElastiCache Redis (cache.t3.micro) in the data subnet serves as the shared session store for "
    "Cart and Checkout, persisting sessions across task restarts."
)

# ═══════════════════════════════════════════
# SECTION 2.3: DB + ASYNC + DR
# ═══════════════════════════════════════════
pdf.subsection_title("2.3", "Database, Async Pipeline, and Disaster Recovery")

pdf.body_text(
    "RDS PostgreSQL Multi-AZ (db.t3.micro) stores all persistent data. The primary runs in AZ-A with "
    "a synchronous standby in AZ-B (RPO = 0, failover in 60-120 seconds). Automated snapshots run "
    "daily with 35-day retention. Three Fargate services and the Lambda invoice function connect to "
    "RDS; the Shopping Cart uses only ElastiCache Redis."
)
pdf.body_text(
    "The async invoice pipeline decouples PDF generation from checkout: Checkout publishes to SQS, "
    "Lambda generates the PDF, uploads it to S3 (for re-download), and emails a link via SES. "
    "Failed messages move to a DLQ after max retries - no invoice is silently lost. The entire "
    "pipeline operates within AWS free tier."
)
pdf.body_text(
    "A cross-region read replica in eu-west-1 (Ireland) provides geographic redundancy close to "
    "European customers. It serves both as a DR target and a low-latency read endpoint for EU traffic. "
    "Cost: ~$15/month."
)

# ═══════════════════════════════════════════
# SECTION 2.4: NETWORK SECURITY
# ═══════════════════════════════════════════
pdf.subsection_title("2.4", "Network Security Model")

pdf.body_text(
    "Defense-in-depth with eight security groups using SG-to-SG references (identity-based, not "
    "CIDR-based). The edge layer (WAF, Shield Standard) filters malicious traffic before it enters "
    "the VPC. Cognito validates JWT tokens at the ALB. Key SG chain:"
)

w_sg = [pw * 0.28, pw * 0.30, pw * 0.42]
pdf.add_table_row(["Security Group", "Inbound From", "Protects"], w_sg, header=True)
pdf.add_table_row(["Public ALB SG", "CloudFront only (443)", "VPC entry point"], w_sg)
pdf.add_table_row(["Customer Fargate SG", "Public ALB SG", "Catalog, Cart, Checkout"], w_sg)
pdf.add_table_row(["Internal ALB SG", "Bastion SG only", "Admin entry point (no public IP)"], w_sg)
pdf.add_table_row(["Admin Fargate SG", "Internal ALB SG", "Admin Panel task"], w_sg)
pdf.add_table_row(["RDS SG", "Customer + Admin + Lambda SG", "PostgreSQL (5432)"], w_sg)
pdf.add_table_row(["ElastiCache SG", "Customer Fargate SG", "Redis (6379)"], w_sg)
pdf.add_table_row(["Bastion SG", "Whitelisted admin IPs", "SSH (22) entry"], w_sg)
pdf.add_table_row(["Lambda SG", "N/A (outbound only)", "RDS + SES access"], w_sg)
pdf.ln(2)

pdf.body_text(
    "This layered model ensures that even if one security group is misconfigured, adjacent layers "
    "prevent unauthorized access. S3 is not publicly accessible (OAC only)."
)

# ═══════════════════════════════════════════
# SECTION 2.5: VPC AND SUBNET LAYOUT
# ═══════════════════════════════════════════
pdf.subsection_title("2.5", "VPC and Subnet Layout")

pdf.body_text(
    "Production VPC (10.0.0.0/16) is divided into three tiers across two Availability Zones:"
)

w_sub = [pw * 0.28, pw * 0.18, pw * 0.14, pw * 0.40]
pdf.add_table_row(["Subnet", "CIDR", "AZ", "Purpose"], w_sub, header=True)
pdf.add_table_row(["Public A", "10.0.1.0/24", "AZ-A", "Public ALB, Bastion, NAT GW"], w_sub)
pdf.add_table_row(["Public B", "10.0.2.0/24", "AZ-B", "Public ALB (multi-AZ)"], w_sub)
pdf.add_table_row(["Private App A", "10.0.10.0/24", "AZ-A", "Fargate: Catalog, Cart, Checkout"], w_sub)
pdf.add_table_row(["Private App B", "10.0.20.0/24", "AZ-B", "Fargate: Admin, Internal ALB"], w_sub)
pdf.add_table_row(["Private Data A", "10.0.30.0/24", "AZ-A", "RDS primary, ElastiCache Redis"], w_sub)
pdf.add_table_row(["Private Data B", "10.0.40.0/24", "AZ-B", "RDS standby replica"], w_sub)
pdf.ln(4)

pdf.body_text(
    "The data tier has no route to the internet - access is restricted to specific ports via SGs. "
    "Dev VPC (10.1.0.0/16) mirrors the same three-tier structure in a single AZ with reduced resources. "
    "No VPC peering exists between environments - complete network isolation."
)

# ═══════════════════════════════════════════
# SECTION 3: SERVICE-TO-INFRASTRUCTURE MAPPING
# ═══════════════════════════════════════════
pdf.add_page()
pdf.section_title("3", "Service-to-Infrastructure Mapping")

pdf.body_text(
    "This section maps each of the eight platform services defined in the project specification to "
    "its AWS infrastructure. For every service, we provide: the exact project requirement it addresses, "
    "the AWS components selected, a justification for why this combination was chosen, a list of "
    "alternatives that were considered and rejected (with reasons), and the cost impact on the monthly "
    "bill. This mapping ensures full traceability from requirement to infrastructure."
)

# ── 3.1 Product Catalog ──
pdf.subsection_title("3.1", "Product Catalog")

pdf.sub3_title("Project Requirement")
pdf.body_text(
    '"Public-facing storefront serving product listings, images, categories, and search results '
    'to anonymous and authenticated customers."'
)

pdf.sub3_title("AWS Components")
w_svc = [pw * 0.30, pw * 0.35, pw * 0.35]
pdf.add_table_row(["Component", "Configuration", "Role"], w_svc, header=True)
pdf.add_table_row(["ECS Fargate", "0.5 vCPU / 1 GB, Auto Scaling", "Runs catalog API container"], w_svc)
pdf.add_table_row(["Public ALB", "Multi-AZ, path: /api/products/*", "Routes customer traffic"], w_svc)
pdf.add_table_row(["CloudFront + S3", "OAC, edge caching", "Serves product images & static assets"], w_svc)
pdf.add_table_row(["RDS PostgreSQL", "Read queries via primary", "Product data, categories, search"], w_svc)
pdf.ln(2)

pdf.sub3_title("Why This Choice")
pdf.body_text(
    "Highest-traffic read service - every page view starts here. Fargate scales the catalog "
    "independently from other services. Static images are offloaded to S3 + CloudFront for edge "
    "caching. PostgreSQL's native full-text search (ts_vector, ts_query) powers product search "
    "without ElasticSearch, and JSONB handles variable product attributes (size, color, specs) "
    "without separate attribute tables."
)

pdf.sub3_title("Alternatives Rejected")
pdf.bullet_bold("EC2 + Auto Scaling Group",
    "Slower scaling (2-5 min instance launch vs seconds for Fargate tasks), requires AMI management, "
    "OS patching, and capacity planning. Over-provisioning wastes money; under-provisioning drops requests.")
pdf.bullet_bold("EKS (Kubernetes)",
    "$73/month control plane cost per cluster ($146 for prod + dev). Provides powerful orchestration "
    "but adds operational complexity (kubectl, Helm, RBAC) disproportionate to the workload. Fargate "
    "achieves the same per-service scaling without cluster management overhead.")
pdf.bullet_bold("Lambda (API Gateway + Lambda)",
    "Cold starts (100-500ms) create noticeable latency on product page loads. Not suitable for a "
    "consistently-accessed storefront. Better suited for event-driven workloads like invoice generation.")
pdf.ln(2)

pdf.bold_label("Cost Impact:",
    "Fargate: ~$18/month (0.5 vCPU x 730hrs x $0.04048 + 1GB x 730hrs x $0.004445). "
    "S3 + CloudFront: ~$0.12/month (free tier covers 1TB transfer + 10M requests).")

# ── 3.2 Shopping Cart ──
pdf.subsection_title("3.2", "Shopping Cart")

pdf.sub3_title("Project Requirement")
pdf.body_text(
    '"Session-aware cart service that persists items across page loads."'
)

pdf.sub3_title("AWS Components")
pdf.add_table_row(["Component", "Configuration", "Role"], w_svc, header=True)
pdf.add_table_row(["ECS Fargate", "0.5 vCPU / 1 GB, Auto Scaling", "Runs cart API container"], w_svc)
pdf.add_table_row(["ElastiCache Redis", "cache.t3.micro, AZ-A", "Session store (sub-ms reads)"], w_svc)
pdf.add_table_row(["Public ALB", "Path: /api/cart/*", "Routes cart requests"], w_svc)
pdf.ln(2)

pdf.sub3_title("Why This Choice")
pdf.body_text(
    "Cart sessions need sub-millisecond reads and automatic TTL expiration for abandoned carts (24h). "
    "ElastiCache Redis in the data subnet provides managed HA, patching, and backup. Unlike in-container "
    "Redis, sessions persist across Fargate task restarts. The checkout service reads cart data from the "
    "same Redis endpoint, avoiding inter-service API calls."
)

pdf.sub3_title("Alternatives Rejected")
pdf.bullet_bold("In-container Redis (sidecar or separate task)",
    "If the Redis container restarts, all active cart sessions are lost. Customers would need to "
    "re-add items - unacceptable for an e-commerce platform. No automatic backup or failover.")
pdf.bullet_bold("RDS-backed sessions (database table)",
    "10-50x slower than Redis for session reads (~5-10ms vs ~0.1ms). Every add-to-cart action would "
    "hit the database, adding unnecessary load to the RDS instance that handles orders and inventory.")
pdf.bullet_bold("Client-side storage (cookies or localStorage)",
    "Limited by cookie size (4KB), not shareable across devices, and vulnerable to tampering. "
    "Server-side sessions in Redis are more secure and support larger cart payloads.")
pdf.ln(2)

pdf.bold_label("Cost Impact:",
    "Fargate: ~$18/month. ElastiCache Redis (cache.t3.micro): ~$12.41/month.")

# ── 3.3 Checkout & Payment ──
pdf.subsection_title("3.3", "Checkout & Payment")

pdf.sub3_title("Project Requirement")
pdf.body_text(
    '"Orchestrates the checkout flow: validates cart contents, confirms stock, and records the order."'
)

pdf.sub3_title("AWS Components")
pdf.add_table_row(["Component", "Configuration", "Role"], w_svc, header=True)
pdf.add_table_row(["ECS Fargate", "0.5 vCPU / 1 GB, Auto Scaling", "Runs checkout API container"], w_svc)
pdf.add_table_row(["RDS PostgreSQL", "Read/write via primary", "Records orders, checks stock"], w_svc)
pdf.add_table_row(["ElastiCache Redis", "Shared with cart service", "Reads cart contents at checkout"], w_svc)
pdf.add_table_row(["SQS Queue", "Standard queue", "Publishes order event for invoice"], w_svc)
pdf.add_table_row(["Public ALB", "Path: /api/checkout/*", "Routes checkout requests"], w_svc)
pdf.ln(2)

pdf.sub3_title("Why This Choice")
pdf.body_text(
    "Most critical transaction path. Flow: (1) read cart from Redis, (2) validate stock in RDS, "
    "(3) record order, (4) publish to SQS for async invoice (<10ms, non-blocking), (5) return "
    "'Order Confirmed.' The customer never waits for invoice generation, directly satisfying "
    "the requirement. Reading from Redis avoids inter-service API calls."
)

pdf.sub3_title("Alternatives Rejected")
pdf.bullet_bold("Synchronous invoice generation",
    "Generating a PDF and sending an email adds 2-5 seconds to the checkout response. This directly "
    "violates the project requirement and degrades the customer experience.")
pdf.bullet_bold("SNS instead of SQS",
    "SNS is a push-based notification service - if the Lambda function is temporarily unavailable, "
    "the message is lost. SQS provides durable message storage with configurable retry and dead-letter "
    "queue support, ensuring no order event is ever lost.")
pdf.ln(2)

pdf.bold_label("Cost Impact:",
    "Fargate: ~$18/month. SQS: $0 (free tier covers 1M requests/month).")

# ── 3.4 Authentication ──
pdf.subsection_title("3.4", "Authentication")

pdf.sub3_title("Project Requirement")
pdf.body_text(
    '"Handles customer registration, login, and session management. A separate admin authentication '
    'flow controls access to the inventory management panel."'
)

pdf.sub3_title("AWS Components")
pdf.add_table_row(["Component", "Configuration", "Role"], w_svc, header=True)
pdf.add_table_row(["Amazon Cognito", "Customer User Pool", "Registration, login, JWT for customers"], w_svc)
pdf.add_table_row(["Amazon Cognito", "Admin User Pool", "Separate credentials for admin staff"], w_svc)
pdf.add_table_row(["ALB Integration", "JWT validation at ALB", "Token verification before reaching services"], w_svc)
pdf.ln(2)

pdf.sub3_title("Why This Choice")
pdf.body_text(
    "Cognito provides managed registration, login, JWT issuance, email verification, password reset, "
    "and brute-force protection with zero auth code. Two User Pools give complete credential separation "
    "(customer vs admin). The ALB natively validates JWT tokens before requests reach Fargate. "
    "Free tier covers 50,000 MAU - eliminating both the cost of an auth container (~$18/month) and "
    "the security risks of custom-built authentication (the #1 source of web app vulnerabilities)."
)

pdf.sub3_title("Alternatives Rejected")
pdf.bullet_bold("Custom auth service (ECS Fargate container)",
    "Requires implementing every auth feature from scratch: password hashing, JWT lifecycle, email "
    "verification, password reset, brute-force protection. Adds ~$18/month in Fargate costs for a "
    "service that Cognito provides for free with better security guarantees.")
pdf.bullet_bold("Auth0 / Okta (third-party managed auth)",
    "Similar functionality to Cognito but adds an external dependency outside the AWS ecosystem. "
    "Pricing is per-user beyond free tier (typically 7,000-7,500 free MAU vs Cognito's 50,000). "
    "No native ALB integration - requires custom middleware.")
pdf.bullet_bold("Embedded auth per service",
    "Duplicates auth logic across catalog, cart, and checkout. Inconsistent security policies, "
    "harder to audit, and violates separation of concerns.")
pdf.ln(2)

pdf.bold_label("Cost Impact:",
    "Cognito: $0/month (free tier: 50,000 MAU). Eliminates the need for a dedicated auth Fargate task, "
    "saving ~$18/month compared to a custom solution.")

# ── 3.5 Admin Panel ──
pdf.subsection_title("3.5", "Inventory Admin Panel")

pdf.sub3_title("Project Requirement")
pdf.body_text(
    '"Internal web interface... Must never be reachable from the public internet - accessible only '
    'via a controlled internal network entry point."'
)

pdf.sub3_title("AWS Components")
pdf.add_table_row(["Component", "Configuration", "Role"], w_svc, header=True)
pdf.add_table_row(["ECS Fargate", "0.25 vCPU / 0.5 GB", "Runs admin panel container"], w_svc)
pdf.add_table_row(["Internal ALB", "No public IP, private subnets", "Routes internal admin traffic"], w_svc)
pdf.add_table_row(["Bastion Host", "t3.micro, public subnet", "SSH entry point for admin access"], w_svc)
pdf.add_table_row(["Cognito Admin Pool", "Separate user pool", "Application-level admin authentication"], w_svc)
pdf.ln(2)

pdf.sub3_title("Why This Choice")
pdf.body_text(
    "Strongest security requirement. Three independent isolation layers:"
)
pdf.bullet_bold("Network (Internal ALB)",
    "No public IP, no public DNS. Resolves to private IP (10.0.x.x) unreachable from outside the VPC.")
pdf.bullet_bold("Access (Bastion SSH tunnel)",
    "Only reachable via 'ssh -L 8080:<internal-alb>:80 bastion'. Bastion SG restricts SSH to "
    "whitelisted admin IPs.")
pdf.bullet_bold("Auth (Cognito Admin Pool)",
    "Even after SSH tunnel access, admin must authenticate against a separate Cognito User Pool.")
pdf.ln(2)

pdf.sub3_title("Alternatives Rejected")
pdf.bullet_bold("AWS Client VPN + Internal ALB",
    "VPN costs ~$73/month base + $0.05/hour per active connection. Combined with the Internal ALB "
    "(~$18/month), this adds ~$91/month for admin access to a single internal tool. Disproportionate "
    "for a startup where 1-2 staff access the admin panel during business hours.")
pdf.bullet_bold("Public ALB with IP whitelist",
    "Technically accessible from the internet - violates 'must never be reachable from the public "
    "internet.' IP whitelists can be spoofed or become stale. Does not satisfy the requirement.")
pdf.bullet_bold("Direct Fargate access (no ALB)",
    "Fargate tasks receive dynamic IPs on each deployment. Without a load balancer, there is no "
    "stable endpoint for the SSH tunnel to target.")
pdf.ln(2)

pdf.bold_label("Cost Impact:",
    "Fargate (0.25 vCPU): ~$9/month. Internal ALB: ~$18/month. Bastion (t3.micro): ~$7.59/month. "
    "Total admin infrastructure: ~$34.59/month.")

# ── 3.6 Database ──
pdf.subsection_title("3.6", "Orders & Inventory Database")

pdf.sub3_title("Project Requirement")
pdf.body_text(
    '"Relational database... Requires high availability with automatic failover, geographic '
    'redundancy, and regular automated snapshots."'
)

pdf.sub3_title("AWS Components")
pdf.add_table_row(["Component", "Configuration", "Role"], w_svc, header=True)
pdf.add_table_row(["RDS PostgreSQL", "db.t3.micro, Multi-AZ, 20GB gp3", "Primary database (AZ-A)"], w_svc)
pdf.add_table_row(["RDS Standby", "Synchronous replica (AZ-B)", "Automatic failover target"], w_svc)
pdf.add_table_row(["RDS Cross-Region", "Read replica in eu-west-1", "Geographic redundancy (Ireland)"], w_svc)
pdf.add_table_row(["Automated Snapshots", "35-day retention", "Point-in-time recovery"], w_svc)
pdf.ln(2)

pdf.sub3_title("Why This Choice")
pdf.body_text(
    "Multi-AZ satisfies all three requirements: synchronous standby in AZ-B (RPO = 0, failover "
    "60-120s), automated snapshots with 35-day retention, and cross-region replica in eu-west-1 "
    "(Ireland) for geographic redundancy close to EU customers."
)
pdf.body_text(
    "PostgreSQL over MySQL for e-commerce: (1) JSONB for flexible product attributes without "
    "separate tables, (2) built-in full-text search without ElasticSearch, (3) superior analytics "
    "for sales reports. The eu-west-1 replica provides both DR and low-latency EU reads - an "
    "Oregon replica would only provide DR within North America. Database is in private data subnets "
    "with SG access restricted to Fargate and Lambda SGs only."
)

pdf.sub3_title("Alternatives Rejected")
pdf.bullet_bold("Amazon Aurora PostgreSQL",
    "~30% more expensive than standard RDS for equivalent instance sizes. No free-tier eligible "
    "instance class. For a startup seeking 'minimum investment to go live,' standard RDS satisfies "
    "every requirement at lower cost. Aurora is the natural upgrade path if the platform outgrows "
    "db.t3.micro.")
pdf.bullet_bold("Self-managed PostgreSQL on EC2",
    "No automatic failover - if the instance dies, the database is down until manual intervention. "
    "Must manually script backups, replication, patching, and monitoring. Directly contradicts the "
    "HA requirement and adds significant operational burden.")
pdf.bullet_bold("DynamoDB (NoSQL)",
    "The project explicitly requires a 'relational database' for orders, inventory, and customer "
    "records. DynamoDB's key-value model would require significant workarounds for relational queries "
    "like 'show all orders for customer X with product details.' Foreign keys and ACID transactions "
    "are natural in PostgreSQL but complex in DynamoDB.")
pdf.ln(2)

pdf.bold_label("Cost Impact:",
    "RDS Multi-AZ (db.t3.micro): ~$27.88/month. Cross-region replica: ~$14.74/month. "
    "Total database: ~$42.62/month. Dev: ~$14.74/month (Single-AZ, no replica).")

# ── 3.7 Invoice Generation ──
pdf.subsection_title("3.7", "Invoice Generation")

pdf.sub3_title("Project Requirement")
pdf.body_text(
    '"When an order is confirmed, a PDF invoice is automatically generated and emailed to the '
    'customer. This job must not block or delay the checkout response."'
)

pdf.sub3_title("AWS Components")
pdf.add_table_row(["Component", "Configuration", "Role"], w_svc, header=True)
pdf.add_table_row(["SQS Queue", "Standard, 4x retry", "Buffers order events from checkout"], w_svc)
pdf.add_table_row(["SQS DLQ", "Dead Letter Queue", "Captures permanently failed messages"], w_svc)
pdf.add_table_row(["Lambda", "Python, 128MB, 30s timeout", "Generates PDF invoice on trigger"], w_svc)
pdf.add_table_row(["S3 Bucket", "Invoice storage, lifecycle policy", "Stores PDFs for re-download"], w_svc)
pdf.add_table_row(["SES", "Verified domain", "Emails invoice PDF to customer"], w_svc)
pdf.ln(2)

pdf.sub3_title("Why This Choice")
pdf.body_text(
    "Checkout publishes to SQS and returns immediately (<200ms). Lambda generates the PDF, uploads "
    "to S3 (enabling re-download for returns/warranties), and emails a link via SES. SQS retries on "
    "Lambda failure; after max retries, messages move to a DLQ for inspection. No invoice is silently "
    "lost. Lambda scales from 0 to handle bursts. Entire pipeline is within AWS free tier at startup."
)

pdf.sub3_title("Alternatives Rejected")
pdf.bullet_bold("Background Fargate task (queue poller)",
    "Runs 24/7 at ~$10-15/month even with zero invoices to generate. Must implement queue polling, "
    "retry logic, and dead-letter handling manually - all of which SQS + Lambda provides natively. "
    "At startup volume (~10 invoices/day), this container would be idle >99% of the time.")
pdf.bullet_bold("In-process async thread in checkout",
    "If the checkout container restarts or scales down mid-generation, the invoice is permanently "
    "lost with no retry mechanism. No durability guarantee. Violates the decoupling principle.")
pdf.bullet_bold("Step Functions orchestration",
    "Adds orchestration overhead for a simple linear pipeline (generate -> store -> email). Step "
    "Functions are better suited for complex workflows with branching logic and human approval steps. "
    "SQS + Lambda is simpler and cheaper for this use case.")
pdf.ln(2)

pdf.bold_label("Cost Impact:",
    "Effectively $0/month at startup volume. Lambda free tier: 1M requests + 400,000 GB-seconds. "
    "SQS free tier: 1M requests. SES: $0.10/1,000 emails. S3: ~$0.023/GB/month for stored PDFs.")

# ── 3.8 Environments ──
pdf.subsection_title("3.8", "Dev & Production Environments")

pdf.sub3_title("Project Requirement")
pdf.body_text(
    '"The platform must run in two fully isolated environments... A misconfiguration or failure '
    'in dev must have zero impact on production."'
)

pdf.sub3_title("AWS Components")
pdf.add_table_row(["Component", "Configuration", "Role"], w_svc, header=True)
pdf.add_table_row(["Production VPC", "10.0.0.0/16, 2 AZs, 3-tier subnets", "Full HA production env"], w_svc)
pdf.add_table_row(["Development VPC", "10.1.0.0/16, 1 AZ, 3-tier subnets", "Reduced-cost dev env"], w_svc)
pdf.add_table_row(["SSM Parameter Store", "/prod/* and /dev/* paths", "Environment-scoped secrets"], w_svc)
pdf.add_table_row(["ECR", "Per-service repositories", "Container image storage"], w_svc)
pdf.ln(2)

pdf.sub3_title("Why This Choice")
pdf.body_text(
    "Separate VPCs with no peering provide the strongest network isolation within a single account. "
    "No network path exists between environments. Dev uses reduced resources: single AZ, 0.25 vCPU "
    "Fargate tasks, Single-AZ RDS, no cross-region replica."
)
pdf.body_text(
    "SSM Parameter Store scopes secrets by environment (/prod/db/password vs /dev/db/password) with "
    "IAM roles preventing cross-environment reads. ECR stores per-service images; both environments "
    "use the same Terraform modules with different variable files for consistency."
)

pdf.sub3_title("Alternatives Rejected")
pdf.bullet_bold("Separate AWS accounts (AWS Organizations)",
    "The project specifies 'a clean AWS account' (singular), implying the grading team uses one "
    "account. Multi-account adds IAM cross-account roles, separate billing, and requires the grading "
    "team to configure AWS Organizations - unnecessary complexity.")
pdf.bullet_bold("Same VPC with subnet isolation",
    "Directly violates 'completely isolated at the network level.' Environments would share route "
    "tables, NAT Gateways, and Internet Gateways. A misconfigured route in dev could disrupt "
    "production traffic. Subnets are not a security boundary - they share the same VPC routing domain.")
pdf.bullet_bold("Kubernetes namespaces (same cluster)",
    "Namespaces provide logical isolation but not network isolation. Pods in dev namespace can reach "
    "pods in prod namespace by default. Network Policies can restrict this, but a single misconfigured "
    "policy breaks isolation. Not equivalent to separate VPCs.")
pdf.ln(2)

pdf.bold_label("Cost Impact:",
    "Dev VPC mirrors prod at reduced scale. Key savings: no Multi-AZ RDS (~$13/month saved), "
    "no cross-region replica (~$15/month saved), no Internal ALB (~$18/month saved), no WAF "
    "(~$9/month saved), smaller Fargate tasks (~$45/month saved), single AZ. "
    "Total dev: ~$117/month vs prod ~$225/month.")

# ═══════════════════════════════════════════
# SECTION 4: COST ESTIMATION
# ═══════════════════════════════════════════
pdf.add_page()
pdf.section_title("4", "Cost Estimation")

pdf.body_text(
    "All prices are for the us-east-1 (N. Virginia) region using on-demand Linux pricing at "
    "730 hours/month. Costs were verified against official AWS pricing pages (April 2026) and are "
    "independently verifiable at calculator.aws. The goal is to estimate the minimum investment "
    "to go live, as specified by the project requirements."
)

# 4.1 Production
pdf.subsection_title("4.1", "Production Environment - $225.49/month")
pdf.ln(2)

w = [pw * 0.35, pw * 0.35, pw * 0.30]
pdf.add_table_row(["Resource", "Configuration", "$/month"], w, header=True)
pdf.add_table_row(["Fargate - Customer Svc", "3x (0.5 vCPU, 1 GB) 24/7", "$54.06"], w)
pdf.add_table_row(["Fargate - Admin Panel", "1x (0.25 vCPU, 0.5 GB) 24/7", "$9.01"], w)
pdf.add_table_row(["EC2 Bastion Host", "1x t3.micro ($0.0104/hr)", "$7.59"], w)
pdf.add_table_row(["RDS PostgreSQL Multi-AZ", "db.t3.micro + 20GB gp3", "$27.88"], w)
pdf.add_table_row(["RDS Cross-Region Replica", "db.t3.micro, eu-west-1", "$15.33"], w)
pdf.add_table_row(["ElastiCache Redis", "cache.t3.micro", "$12.41"], w)
pdf.add_table_row(["NAT Gateway", "1 gateway + ~50GB data", "$35.10"], w)
pdf.add_table_row(["Public ALB", "1 ALB + ~1 LCU average", "$22.27"], w)
pdf.add_table_row(["Internal ALB", "1 ALB + ~0.5 LCU average", "$18.11"], w)
pdf.add_table_row(["Public IPv4 addresses", "~4 IPs ($0.005/hr each)", "$14.60"], w)
pdf.add_table_row(["WAF + Route 53", "1 ACL + 3 rules + 1 zone", "$9.00"], w)
pdf.add_table_row(["CloudFront + S3", "Free tier + ~5GB storage", "$0.12"], w)
pdf.add_table_row(["Cognito", "Free tier (50K MAU)", "$0.00"], w)
pdf.add_table_row(["Lambda + SQS + SES + S3", "All within free tier", "$0.01"], w)
pdf.add_table_row(["TOTAL", "", "$225.49"], w, bold=True)
pdf.ln(4)

pdf.body_text(
    "Fargate compute ($63.07) is the largest line item, but it replaces both EKS control planes "
    "($73/month) and EC2 worker nodes ($61/month) from a Kubernetes-based architecture - a net saving "
    "of $71/month. The NAT Gateway ($35.10) is the second-largest cost, charged per-hour plus per-GB "
    "of data processed. The Internal ALB ($18.11) is the cost of admin panel isolation - the only way "
    "to provide a stable, non-public endpoint for the Fargate admin service."
)

# 4.2 Development
pdf.subsection_title("4.2", "Development Environment - $117.04/month")
pdf.ln(2)

pdf.add_table_row(["Resource", "Configuration", "$/month"], w, header=True)
pdf.add_table_row(["Fargate - Customer App", "1x (0.25 vCPU, 0.5 GB)", "$9.01"], w)
pdf.add_table_row(["Fargate - Dev Admin", "1x (0.25 vCPU, 0.5 GB)", "$9.01"], w)
pdf.add_table_row(["EC2 Bastion Host", "1x t3.micro ($0.0104/hr)", "$7.59"], w)
pdf.add_table_row(["RDS PostgreSQL Single-AZ", "db.t3.micro + 20GB gp3", "$14.74"], w)
pdf.add_table_row(["ElastiCache Redis", "cache.t3.micro", "$12.41"], w)
pdf.add_table_row(["NAT Gateway", "1 gateway + ~25GB data", "$33.98"], w)
pdf.add_table_row(["Dev ALB", "1 ALB + ~0.5 LCU average", "$19.35"], w)
pdf.add_table_row(["Public IPv4 addresses", "~3 IPs ($0.005/hr each)", "$10.95"], w)
pdf.add_table_row(["TOTAL", "", "$117.04"], w, bold=True)
pdf.ln(4)

pdf.body_text(
    "The development environment saves $108/month compared to production. Key savings: no Multi-AZ "
    "RDS ($13 saved), no cross-region replica ($15 saved), no Internal ALB ($18 saved), no WAF/Route 53 "
    "($9 saved), smaller Fargate tasks (0.25 vCPU vs 0.5 vCPU, $45 saved), and combined customer "
    "services into a single task. The NAT Gateway ($33.98) remains the largest dev cost - it is "
    "required for Fargate tasks to pull container images from ECR and make AWS API calls."
)

# 4.3 Combined Summary
pdf.subsection_title("4.3", "Combined Summary and Cost Drivers")
pdf.ln(2)

w2 = [pw * 0.35, pw * 0.325, pw * 0.325]
pdf.add_table_row(["Environment", "Monthly", "Annual"], w2, header=True)
pdf.add_table_row(["Production", "$225.49", "$2,705.88"], w2)
pdf.add_table_row(["Development", "$117.04", "$1,404.48"], w2)
pdf.add_table_row(["Combined", "$342.53", "$4,110.36"], w2, bold=True)
pdf.ln(4)

pdf.body_text(
    "The three largest cost categories account for approximately 60% of total spending:"
)
pdf.bullet("Fargate compute: $63 (prod) + $18 (dev) = $81/month (24%). Per-second billing for "
           "actual vCPU and memory - no idle worker nodes or cluster management fees.")
pdf.bullet("NAT Gateways: $35 (prod) + $34 (dev) = $69/month (20%). Charged per-hour plus "
           "per-GB of data processed. Required for private subnet internet access.")
pdf.bullet("RDS PostgreSQL: $43 (prod Multi-AZ + replica) + $15 (dev Single-AZ) = $58/month (17%). "
           "Managed database with automatic failover and geographic redundancy.")
pdf.ln(2)

pdf.body_text(
    "Compared to an EKS-based architecture, Fargate eliminates $146/month in Kubernetes control plane "
    "fees and $91/month in EC2 worker nodes - a combined saving of $237/month ($2,844/year). The "
    "serverless invoice pipeline (Lambda + SQS + SES + S3) costs $0.01/month at startup volume. "
    "Cognito authentication is free for up to 50,000 monthly active users. CloudFront's free tier "
    "(1TB transfer, 10M requests) covers static asset delivery at near-zero cost."
)

# ═══════════════════════════════════════════
# SECTION 5: DESIGN METHODOLOGY
# ═══════════════════════════════════════════
pdf.add_page()
pdf.section_title("5", "Design Methodology - Key Decisions")

pdf.body_text(
    "This section documents the six most consequential design decisions, showing the options "
    "considered, evaluation criteria, and the reasoning behind each choice. Every decision was "
    "evaluated against four criteria: (1) project requirements, (2) startup cost-effectiveness, "
    "(3) course material alignment, and (4) Phase 2/3 implementation impact."
)

# 5.1
pdf.subsection_title("5.1", "Compute: ECS Fargate + Lambda")

pdf.sub3_title("Options Considered")
pdf.bullet("Option A: ECS Fargate (serverless containers) for synchronous services")
pdf.bullet("Option B: Amazon EKS (managed Kubernetes) for all services")
pdf.bullet("Option C: EC2 instances with Docker / Docker Swarm")
pdf.ln(2)

pdf.sub3_title("Decision: ECS Fargate for 4 synchronous services + Lambda for async invoice")
pdf.body_text(
    "ECS Fargate provides per-service auto scaling, zero-downtime rolling deployments, and health "
    "check-based task replacement - all without managing a cluster. Each service (catalog, cart, "
    "checkout, admin) runs as an independent Fargate service with its own task definition, scaling "
    "policy, and security group. Fargate bills per-second for actual vCPU/memory consumed, with no "
    "minimum commitment."
)
pdf.body_text(
    "EKS was rejected primarily for cost: $73/month per cluster ($146 for prod + dev) just for the "
    "control plane, before any compute. EKS also adds operational complexity (kubectl, Helm charts, "
    "RBAC policies, worker node AMI management) that is disproportionate for four web services. "
    "Fargate achieves the same per-service scaling without cluster management overhead."
)
pdf.body_text(
    "EC2 with Docker was rejected because it requires manual capacity planning, OS patching, "
    "and instance management. EC2 Auto Scaling Groups take 2-5 minutes to launch new instances "
    "compared to Fargate's seconds. Docker Swarm lacks managed health checks and has been "
    "effectively deprecated in favor of Kubernetes and ECS."
)
pdf.body_text(
    "Lambda handles invoice generation because it is fundamentally different from the synchronous "
    "services: event-driven, bursty (perhaps 10 invocations/day), and completely free under the "
    "Lambda free tier (1M requests/month). Running a 24/7 container for this workload would cost "
    "~$10-15/month with >99% idle time."
)

# 5.2
pdf.subsection_title("5.2", "Environment Isolation: Separate VPCs")

pdf.sub3_title("Options Considered")
pdf.bullet("Option A: Separate VPCs in the same AWS account (no peering)")
pdf.bullet("Option B: Separate AWS accounts (AWS Organizations)")
pdf.bullet("Option C: Same VPC with namespace/subnet isolation")
pdf.ln(2)

pdf.sub3_title("Decision: Separate VPCs, no peering, same AWS account")
pdf.body_text(
    "The project requires 'completely isolated at the network level' and 'zero impact' from dev "
    "failures on production. Separate VPCs provide true network isolation: different CIDRs, different "
    "route tables, different security groups, different NAT Gateways. With no VPC peering, there is "
    "literally no network path between the two environments."
)
pdf.body_text(
    "Separate AWS accounts were rejected because the project specifies 'a clean AWS account' "
    "(singular), implying the grading team will use a single account. Multi-account also adds IAM "
    "cross-account role complexity and separate billing."
)
pdf.body_text(
    "Same-VPC isolation with subnet separation was rejected because it directly violates "
    "'completely isolated at the network level.' Environments would share route tables, NAT Gateways, "
    "and Internet Gateways - a misconfigured route in dev could disrupt prod traffic."
)

# 5.3
pdf.subsection_title("5.3", "Region Strategy: Single Region + CDN + Cross-Region DR")

pdf.sub3_title("Options Considered")
pdf.bullet("Option A: Single region (us-east-1) + CloudFront CDN")
pdf.bullet("Option B: Multi-region active-active (full infrastructure in 2 regions)")
pdf.bullet("Option C: Single region + CloudFront + cross-region database replica")
pdf.ln(2)

pdf.sub3_title("Decision: Option C - us-east-1 with CloudFront and eu-west-1 replica")
pdf.body_text(
    "Multi-region active-active would double every component: 2x VPCs, 2x Fargate services, 2x ALBs, "
    "2x NAT Gateways, 2x RDS instances. For a startup seeking 'minimum investment to go live,' "
    "this is unjustifiable - it would more than double the monthly cost. Cross-region "
    "database synchronization is also the hardest problem in distributed systems."
)
pdf.body_text(
    "us-east-1 was chosen because it is the cheapest AWS region with the broadest service "
    "availability. Latency to US customers is ~10ms; to European customers ~100ms. CloudFront "
    "closes this gap for static content by serving from edge locations near both populations. "
    "The cross-region RDS replica in eu-west-1 (Ireland) provides both geographic redundancy AND "
    "a performance benefit for European customers. Unlike a replica in another US region (e.g., "
    "us-west-2), the Irish replica can serve EU read traffic at low latency and provides a DR target "
    "geographically close to half the customer base."
)

# 5.4
pdf.subsection_title("5.4", "Database: RDS PostgreSQL Multi-AZ")

pdf.sub3_title("Options Considered")
pdf.bullet("Option A: RDS PostgreSQL Multi-AZ (managed, automatic failover)")
pdf.bullet("Option B: RDS MySQL Multi-AZ (managed, simpler)")
pdf.bullet("Option C: Amazon Aurora PostgreSQL (managed, higher performance)")
pdf.bullet("Option D: Self-managed PostgreSQL on EC2 (full control)")
pdf.ln(2)

pdf.sub3_title("Decision: RDS PostgreSQL Multi-AZ (db.t3.micro)")
pdf.body_text(
    "RDS PostgreSQL Multi-AZ directly satisfies every database requirement with a single managed "
    "service: automatic failover in 60-120 seconds, automated snapshots with 35-day retention, and "
    "cross-region read replicas for geographic redundancy. The db.t3.micro instance class provides "
    "2 vCPUs and 1 GB RAM with burstable performance - sufficient for startup-scale transaction volume."
)
pdf.body_text(
    "PostgreSQL was chosen over MySQL for three e-commerce-specific advantages: (1) native JSONB "
    "support handles variable product attributes (clothing: size/color; electronics: specs) without "
    "separate attribute tables - a common e-commerce data modeling challenge; (2) built-in full-text "
    "search (ts_vector/ts_query) powers product search without a separate ElasticSearch cluster; and "
    "(3) wire-compatible with Aurora PostgreSQL, providing a seamless upgrade path if the platform "
    "outgrows db.t3.micro."
)
pdf.body_text(
    "Aurora was rejected because it costs ~30% more than standard RDS with no free-tier eligible "
    "instance class. Self-managed PostgreSQL on EC2 was rejected because it lacks automatic failover, "
    "requires manually scripted backups and replication, and directly contradicts the HA requirements."
)

# 5.5
pdf.subsection_title("5.5", "Invoice Pipeline: SQS + Lambda + S3 + SES")

pdf.sub3_title("Options Considered")
pdf.bullet("Option A: SQS + Lambda + S3 + SES + DLQ (serverless, event-driven)")
pdf.bullet("Option B: Background Fargate task polling a queue (always-on)")
pdf.bullet("Option C: In-process async thread within the checkout service")
pdf.ln(2)

pdf.sub3_title("Decision: SQS + Lambda + S3 + SES with Dead Letter Queue")
pdf.body_text(
    "The project explicitly requires 'this job must not block or delay the checkout response.' This "
    "maps directly to an asynchronous, event-driven architecture. SQS provides durable message "
    "storage - messages persist until processed, surviving Lambda failures. Lambda scales per-message "
    "and costs $0 at startup volume. S3 stores generated PDFs for customer re-download (essential for "
    "returns, warranties, and expense reporting). SES handles email at $0.10 per 1,000 emails."
)
pdf.body_text(
    "A background Fargate task would run 24/7 at ~$10-15/month even with zero invoices to generate. "
    "It would also require implementing queue polling logic, retry mechanisms, and dead-letter "
    "handling manually - all of which SQS + Lambda provides natively. An in-process async thread "
    "within checkout is fragile: if the checkout container restarts mid-generation, the invoice is "
    "permanently lost with no retry mechanism."
)

# 5.6
pdf.subsection_title("5.6", "Admin Panel Access: Internal ALB + Bastion SSH Tunnel")

pdf.sub3_title("Options Considered")
pdf.bullet("Option A: Internal ALB (no public IP) + Bastion SSH tunnel + Cognito Admin Pool")
pdf.bullet("Option B: Public ALB with IP whitelist")
pdf.bullet("Option C: AWS Client VPN + Internal ALB")
pdf.ln(2)

pdf.sub3_title("Decision: Internal ALB + Bastion + Cognito Admin Pool")
pdf.body_text(
    "The project's strongest requirement: 'must never be reachable from the public internet.' "
    "The Internal ALB has no public IP address, no public DNS record, and exists only within the "
    "private app subnets. There is no internet-routable path to reach it. The bastion host in the "
    "public subnet serves as the 'controlled internal network entry point' the project requires."
)
pdf.body_text(
    "Administrators access the panel by SSHing into the bastion and creating an SSH tunnel to the "
    "Internal ALB. They then open their browser to localhost, which tunnels through the encrypted "
    "SSH connection. This provides a real web interface experience - more practical for non-technical "
    "warehouse staff than alternatives requiring specialized tools."
)
pdf.body_text(
    "Defense-in-depth is achieved through three independent layers: (1) the Internal ALB has no "
    "public exposure at the network level, (2) the bastion's security group restricts SSH to "
    "whitelisted administrator IPs, and (3) the Cognito Admin User Pool requires separate admin "
    "credentials at the application level. All three layers must be bypassed to access the panel."
)
pdf.body_text(
    "A public ALB with IP whitelist was rejected because it is technically reachable from the "
    "internet, violating the requirement. AWS Client VPN was rejected on cost: ~$73/month base + "
    "$0.05/hour per connection. For 1-2 staff accessing the admin panel during business hours, "
    "the SSH tunnel approach provides identical security at a fraction of the cost (~$18/month for "
    "the Internal ALB + $7.59/month for the bastion, which is already needed)."
)

# ═══════════════════════════════════════════
# SECTION 6: CONCLUSION
# ═══════════════════════════════════════════
pdf.section_title("6", "Conclusion")

pdf.body_text(
    "The ShopCloud architecture balances production-grade reliability with startup-appropriate cost "
    "discipline. Every design decision is justified on both technical and economic grounds, with "
    "alternatives explicitly evaluated and rejected where applicable."
)

pdf.body_text(
    "The compute model uses ECS Fargate for synchronous services and Lambda for event-driven work, "
    "demonstrating workload-appropriate infrastructure selection. Fargate provides per-service auto "
    "scaling without cluster management overhead, while the serverless invoice pipeline (SQS + Lambda "
    "+ S3 + SES + DLQ) operates at zero marginal cost. RDS PostgreSQL Multi-AZ delivers the required "
    "high availability, automatic failover, and geographic redundancy through a cross-region replica "
    "in eu-west-1 (Ireland), strategically placed to serve European customers."
)

pdf.body_text(
    "Security is enforced through defense-in-depth at every layer: AWS WAF and Shield Standard filter "
    "malicious traffic at the CloudFront edge, Amazon Cognito validates JWT tokens at the ALB before "
    "requests reach services, eight security groups with SG-to-SG references enforce least-privilege "
    "access, three-tier subnet isolation separates public, application, and data resources, and the "
    "admin panel is triply isolated behind an Internal ALB, a bastion SSH tunnel, and a Cognito Admin "
    "User Pool. Environment isolation via separate VPCs (10.0.0.0/16 and 10.1.0.0/16) with no "
    "peering ensures development failures cannot propagate to production."
)

pdf.body_text(
    "The estimated minimum investment to go live is $342.53 per month ($4,110 annually) for both "
    "environments - 25% less than an equivalent EKS-based architecture, primarily by eliminating "
    "$146/month in Kubernetes control plane fees and $91/month in EC2 worker nodes. The architecture is designed to be fully "
    "provisionable via Terraform from a single AWS account (Phase 2), monitorable via AWS CloudWatch "
    "(Phase 3), and evolvable as the platform grows. Clear upgrade paths exist: standard RDS to "
    "Aurora PostgreSQL for higher throughput, single-region to multi-region for lower global latency, "
    "and bastion SSH tunnel to AWS Client VPN for improved admin UX."
)

pdf.body_text(
    "The architecture prioritizes the 'minimum investment to go live' while meeting every stated "
    "requirement without compromise. No service is over-engineered for current scale, and no "
    "requirement is left unsatisfied."
)

# ═══════════════════════════════════════════
# OUTPUT
# ═══════════════════════════════════════════
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ShopCloud_Phase1_Report.pdf")
pdf.output(output_path)
print(f"Report generated: {output_path}")
