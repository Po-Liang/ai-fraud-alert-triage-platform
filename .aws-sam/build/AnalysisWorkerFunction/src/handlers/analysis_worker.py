import json
import logging
from json import JSONDecodeError

from src.services import alert_service

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _configure_logging() -> None:
    logging.basicConfig(level=logging.INFO)
    logging.getLogger().setLevel(logging.INFO)


def _record_identifier(record: dict, default: str) -> str:
    return str(record.get("messageId") or default)


def lambda_handler(event, context):
    del context
    _configure_logging()
    logger.info("analysis_worker_started")

    batch_item_failures = []

    for index, record in enumerate(event.get("Records", []), start=1):
        item_identifier = _record_identifier(record, default=f"record-{index}")

        try:
            logger.info("sqs_record_received messageId=%s", item_identifier)
            payload = json.loads(record.get("body") or "")
            if not isinstance(payload, dict):
                raise ValueError("SQS message body must be a JSON object")

            alert_id = str(payload.get("alertId") or "").strip()
            if not alert_id:
                raise ValueError("SQS message is missing alertId")

            logger.info(
                "analysis_started_for_alert alertId=%s messageId=%s",
                alert_id,
                item_identifier,
            )
            alert_service.analyze_alert(alert_id)
            logger.info(
                "analysis_completed_for_alert alertId=%s messageId=%s",
                alert_id,
                item_identifier,
            )
        except (JSONDecodeError, ValueError) as error:
            logger.error(
                "analysis_failed_for_alert alertId=unknown messageId=%s",
                item_identifier,
            )
            logger.error("Invalid analysis job %s: %s", item_identifier, error)
            batch_item_failures.append({"itemIdentifier": item_identifier})
        except Exception:
            logger.exception(
                "analysis_failed_for_alert alertId=unknown messageId=%s",
                item_identifier,
            )
            logger.exception("Failed to process analysis job %s", item_identifier)
            batch_item_failures.append({"itemIdentifier": item_identifier})

    return {"batchItemFailures": batch_item_failures}
