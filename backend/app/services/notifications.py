import json
from typing import Optional

import httpx
from structlog import get_logger

from app.models.alert import Alert
from app.models.job import FuzzJob
from app.models.schedule import JobSchedule

logger = get_logger(__name__)


def send_slack_alert(webhook_url: str, message: str, data: dict) -> bool:
    try:
        color = "danger" if data.get("severity") in ("critical", "high") else "warning"
        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": "🚨 FuzzGuard Alert"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": message}},
            {"type": "divider"},
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "value": f"*Job ID:*\n{data.get('job_id', '—')}"},
                    {"type": "mrkdwn", "value": f"*Severity:*\n{data.get('severity', 'warning')}"},
                    {"type": "mrkdwn", "value": f"*ASR:*\n{data.get('asr', 0)*100:.1f}%"},
                    {"type": "mrkdwn", "value": f"*Threshold:*\n{data.get('threshold', 0)*100:.1f}%"},
                ],
            },
        ]
        resp = httpx.post(webhook_url, json={"text": message, "blocks": blocks, "attachments": [{"color": color, "text": message}]}, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error("slack_alert_failed", error=str(e), webhook_url=webhook_url[:40])
        return False


def send_webhook_alert(url: str, message: str, data: dict) -> bool:
    try:
        payload = {
            "event": "asr_threshold_breach",
            "message": message,
            "severity": data.get("severity", "warning"),
            "job_id": data.get("job_id"),
            "schedule_id": data.get("schedule_id"),
            "project_id": data.get("project_id"),
            "asr": data.get("asr", 0),
            "threshold": data.get("threshold", 0),
            "timestamp": data.get("timestamp", ""),
        }
        resp = httpx.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error("webhook_alert_failed", error=str(e), webhook_url=url[:40])
        return False


def notify_threshold_breach(db, sched: JobSchedule, job: FuzzJob) -> Alert:
    from datetime import datetime, timezone
    import json as json_lib

    existing = db.query(Alert).filter(Alert.job_id == job.id, Alert.type == "asr_threshold").first()
    if existing:
        return existing

    alert = Alert(
        project_id=sched.project_id,
        schedule_id=sched.id,
        job_id=job.id,
        type="asr_threshold",
        severity="critical" if job.asr >= sched.asr_threshold * 1.5 else "warning",
        message=(
            f"Schedule '{sched.name}' exceeded ASR threshold: "
            f"{job.asr:.1%} >= {sched.asr_threshold:.1%}"
        ),
        data=json_lib.dumps({"asr": job.asr, "threshold": sched.asr_threshold}),
    )
    db.add(alert)
    db.flush()

    data = {
        "job_id": job.id,
        "schedule_id": sched.id,
        "project_id": sched.project_id,
        "asr": job.asr,
        "threshold": sched.asr_threshold,
        "severity": alert.severity,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if sched.slack_webhook_url:
        send_slack_alert(sched.slack_webhook_url, alert.message, data)

    if sched.webhook_url:
        send_webhook_alert(sched.webhook_url, alert.message, data)

    return alert
