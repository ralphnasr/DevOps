import json
import logging
import os
from datetime import datetime

import boto3
import psycopg2
from fpdf import FPDF

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
ses = boto3.client("ses")

S3_INVOICE_BUCKET = os.environ.get("S3_INVOICE_BUCKET", "shopcloud-invoices")
SES_SENDER_EMAIL = os.environ.get("SES_SENDER_EMAIL", "noreply@shopcloud.example.com")


def _get_db_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


def generate_invoice_pdf(
    order_id: int, items: list, total_amount: float, created_at: str
) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 15, "ShopCloud", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Your Cloud Shopping Destination", ln=True, align="C")
    pdf.ln(10)

    # Invoice details
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"Invoice - Order #{order_id}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(
        0,
        6,
        f"Date: {created_at[:10] if created_at else datetime.utcnow().strftime('%Y-%m-%d')}",
        ln=True,
    )
    pdf.ln(8)

    # Separator
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # Items table header
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(90, 8, "Product", border=1, fill=True)
    pdf.cell(30, 8, "Quantity", border=1, align="C", fill=True)
    pdf.cell(35, 8, "Unit Price", border=1, align="R", fill=True)
    pdf.cell(35, 8, "Subtotal", border=1, align="R", fill=True)
    pdf.ln()

    # Items rows
    pdf.set_font("Helvetica", "", 10)
    for item in items:
        subtotal = item["quantity"] * item["unit_price"]
        pdf.cell(90, 8, item["product_name"][:40], border=1)
        pdf.cell(30, 8, str(item["quantity"]), border=1, align="C")
        pdf.cell(35, 8, f"${item['unit_price']:.2f}", border=1, align="R")
        pdf.cell(35, 8, f"${subtotal:.2f}", border=1, align="R")
        pdf.ln()

    # Total
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(155, 10, "Total:", align="R")
    pdf.cell(35, 10, f"${total_amount:.2f}", align="R")
    pdf.ln(15)

    # Footer
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 6, "Thank you for shopping with ShopCloud!", ln=True, align="C")

    return pdf.output()


def invoice_html_template(order_id: int, invoice_url: str) -> str:
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #1a1a2e;">ShopCloud - Order Confirmation</h2>
        <p>Your order <strong>#{order_id}</strong> has been confirmed.</p>
        <p>Your invoice is ready. You can download it using the link below:</p>
        <p style="margin: 20px 0;">
            <a href="{invoice_url}"
               style="background: #4a90d9; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">
                Download Invoice
            </a>
        </p>
        <p style="color: #888; font-size: 12px;">This link expires in 7 days.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #888; font-size: 12px;">ShopCloud - Your Cloud Shopping Destination</p>
    </body>
    </html>
    """


def handler(event, context):
    for record in event["Records"]:
        message = json.loads(record["body"])
        order_id = message["order_id"]
        customer_email = message["customer_email"]
        items = message["items"]
        total_amount = message["total_amount"]
        created_at = message.get("created_at", "")

        logger.info(f"Processing invoice for order {order_id}")

        # 1. Generate PDF
        pdf_bytes = generate_invoice_pdf(order_id, items, total_amount, created_at)
        logger.info(f"Generated PDF for order {order_id} ({len(pdf_bytes)} bytes)")

        # 2. Upload to S3
        s3_key = f"invoices/{order_id}.pdf"
        s3.put_object(
            Bucket=S3_INVOICE_BUCKET,
            Key=s3_key,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )
        logger.info(f"Uploaded invoice to s3://{S3_INVOICE_BUCKET}/{s3_key}")

        # 3. Generate presigned URL (7 days)
        invoice_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_INVOICE_BUCKET, "Key": s3_key},
            ExpiresIn=604800,
        )

        # 4. Update order in RDS
        conn = _get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE orders SET invoice_url = %s, updated_at = NOW() WHERE id = %s",
                    (invoice_url, order_id),
                )
            conn.commit()
            logger.info(f"Updated order {order_id} with invoice URL")
        finally:
            conn.close()

        # 5. Send email via SES
        try:
            ses.send_email(
                Source=SES_SENDER_EMAIL,
                Destination={"ToAddresses": [customer_email]},
                Message={
                    "Subject": {"Data": f"ShopCloud Invoice - Order #{order_id}"},
                    "Body": {
                        "Html": {"Data": invoice_html_template(order_id, invoice_url)}
                    },
                },
            )
            logger.info(f"Sent invoice email to {customer_email} for order {order_id}")
        except Exception as e:
            logger.error(f"Failed to send email for order {order_id}: {e}")
            # Don't re-raise — invoice is saved, email failure is non-fatal

    return {"statusCode": 200, "body": json.dumps("Invoices processed")}
