"""SES bounce and complaint handler that updates the suppression list."""

import json
import logging
import os

import psycopg2

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _get_db():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )


def _suppress(email: str, reason: str) -> None:
    conn = _get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE customers
                SET email_suppressed = TRUE,
                    suppressed_reason = %s,
                    suppressed_at = NOW()
                WHERE email = %s AND email_suppressed = FALSE
                """,
                (reason, email),
            )
            rows = cur.rowcount
        conn.commit()
        if rows:
            logger.info(f"Suppressed email={email} reason={reason} rows={rows}")
        else:
            logger.info(f"Email already suppressed or unknown: {email}")
    finally:
        conn.close()


def handler(event, context):
    for record in event.get("Records", []):
        try:
            sns_msg = json.loads(record["Sns"]["Message"])
        except (KeyError, ValueError):
            logger.warning(f"Skipping malformed SNS record: {record}")
            continue

        event_type = sns_msg.get("eventType") or sns_msg.get("notificationType")

        if event_type == "Bounce":
            bounce = sns_msg.get("bounce", {})
            bounce_type = bounce.get("bounceType")
            if bounce_type != "Permanent":
                logger.info(f"Ignoring non-permanent bounce: {bounce_type}")
                continue
            for recipient in bounce.get("bouncedRecipients", []):
                email = recipient.get("emailAddress")
                if email:
                    _suppress(email, "hard_bounce")

        elif event_type == "Complaint":
            complaint = sns_msg.get("complaint", {})
            for recipient in complaint.get("complainedRecipients", []):
                email = recipient.get("emailAddress")
                if email:
                    _suppress(email, "complaint")

        else:
            logger.info(f"Ignoring event type: {event_type}")

    return {"statusCode": 200}
