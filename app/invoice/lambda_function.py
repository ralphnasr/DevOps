"""Invoice generator: SQS → PDF → S3 → RDS → SES.

Flow per message:
  1. Check the customer's email isn't suppressed (hard-bounced / complained).
     If it is, skip the send step but still generate + store the PDF and write
     invoice_url to the order — the customer can still download from the
     confirmation page.
  2. Generate PDF with fpdf2.
  3. Upload to the invoices S3 bucket.
  4. Presign a 7-day URL and write it to orders.invoice_url.
  5. Send the email via SES using our configuration set (so bounces /
     complaints flow to the SNS topic → bounce-handler Lambda → auto-suppress).
     Transient errors (Throttling, ServiceUnavailable) retry with exponential
     backoff; hard rejects fail fast and are logged (no retry, no DLQ —
     invoice_url is persisted and the user can re-trigger from the UI).
"""

import json
import logging
import os
import time
from datetime import datetime

import boto3
import psycopg2
from botocore.exceptions import ClientError
from fpdf import FPDF

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
ses = boto3.client("ses")

S3_INVOICE_BUCKET = os.environ.get("S3_INVOICE_BUCKET", "shopcloud-invoices")
SES_SENDER_EMAIL = os.environ.get("SES_SENDER_EMAIL", "noreply@shopcloud.example.com")
SES_CONFIG_SET = os.environ.get("SES_CONFIG_SET")

# SES errors that are worth retrying — transient capacity / throttling issues.
_RETRYABLE_SES_ERRORS = {
    "Throttling",
    "ThrottlingException",
    "TooManyRequestsException",
    "ServiceUnavailable",
    "InternalFailure",
    "RequestTimeout",
}


def _get_db_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


def _is_suppressed(conn, email: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT email_suppressed FROM customers WHERE email = %s LIMIT 1",
            (email,),
        )
        row = cur.fetchone()
    return bool(row and row[0])


def generate_invoice_pdf(
    order_id: int, items: list, total_amount: float, created_at: str
) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 15, "ShopCloud", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "Your Cloud Shopping Destination", ln=True, align="C")
    pdf.ln(10)

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

    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(90, 8, "Product", border=1, fill=True)
    pdf.cell(30, 8, "Quantity", border=1, align="C", fill=True)
    pdf.cell(35, 8, "Unit Price", border=1, align="R", fill=True)
    pdf.cell(35, 8, "Subtotal", border=1, align="R", fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    for item in items:
        subtotal = item["quantity"] * item["unit_price"]
        pdf.cell(90, 8, item["product_name"][:40], border=1)
        pdf.cell(30, 8, str(item["quantity"]), border=1, align="C")
        pdf.cell(35, 8, f"${item['unit_price']:.2f}", border=1, align="R")
        pdf.cell(35, 8, f"${subtotal:.2f}", border=1, align="R")
        pdf.ln()

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(155, 10, "Total:", align="R")
    pdf.cell(35, 10, f"${total_amount:.2f}", align="R")
    pdf.ln(15)

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


def _send_email_with_retry(*, to_email: str, order_id: int, invoice_url: str) -> None:
    """Send via SES with exponential backoff on transient errors."""
    kwargs = dict(
        Source=SES_SENDER_EMAIL,
        Destination={"ToAddresses": [to_email]},
        Message={
            "Subject": {"Data": f"ShopCloud Invoice - Order #{order_id}"},
            "Body": {"Html": {"Data": invoice_html_template(order_id, invoice_url)}},
        },
    )
    if SES_CONFIG_SET:
        kwargs["ConfigurationSetName"] = SES_CONFIG_SET

    last_err: Exception | None = None
    for attempt in range(3):
        try:
            ses.send_email(**kwargs)
            return
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in _RETRYABLE_SES_ERRORS and attempt < 2:
                sleep_for = 2**attempt  # 1s, 2s
                logger.warning(
                    f"SES transient error {code} on attempt {attempt + 1}, "
                    f"retrying in {sleep_for}s"
                )
                time.sleep(sleep_for)
                last_err = e
                continue
            raise
    if last_err:
        raise last_err


def handler(event, context):
    for record in event["Records"]:
        message = json.loads(record["body"])
        order_id = message["order_id"]
        customer_email = message["customer_email"]
        items = message["items"]
        total_amount = message["total_amount"]
        created_at = message.get("created_at", "")

        logger.info(f"Processing invoice for order {order_id}")

        pdf_bytes = generate_invoice_pdf(order_id, items, total_amount, created_at)
        logger.info(f"Generated PDF for order {order_id} ({len(pdf_bytes)} bytes)")

        s3_key = f"invoices/{order_id}.pdf"
        s3.put_object(
            Bucket=S3_INVOICE_BUCKET,
            Key=s3_key,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )
        logger.info(f"Uploaded invoice to s3://{S3_INVOICE_BUCKET}/{s3_key}")

        invoice_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_INVOICE_BUCKET, "Key": s3_key},
            ExpiresIn=604800,
        )

        conn = _get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE orders SET invoice_url = %s, updated_at = NOW() WHERE id = %s",
                    (invoice_url, order_id),
                )
            conn.commit()
            logger.info(f"Updated order {order_id} with invoice URL")

            if _is_suppressed(conn, customer_email):
                logger.info(
                    f"Skipping send: email {customer_email} is suppressed "
                    f"(order {order_id} invoice still saved and downloadable)"
                )
                continue
        finally:
            conn.close()

        try:
            _send_email_with_retry(
                to_email=customer_email,
                order_id=order_id,
                invoice_url=invoice_url,
            )
            logger.info(f"Sent invoice email to {customer_email} for order {order_id}")
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            logger.error(
                f"Permanent SES failure for order {order_id} (code={code}): {e}"
            )
            # Don't re-raise — PDF is stored and invoice_url is in RDS, so the
            # customer can still download from the order confirmation page.
            # Bounce/complaint events (if any) will flow through SNS to the
            # bounce-handler Lambda independently.

    return {"statusCode": 200, "body": json.dumps("Invoices processed")}
