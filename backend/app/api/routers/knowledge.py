from fastapi import APIRouter

router = APIRouter(prefix="/knowledge-base", tags=["knowledge"])

MOCK_ARTICLES = [
    {
        "id": "kb-1",
        "title": "How to triage vibration alarms",
        "summary": "Step-by-step triage checklist for high vibration events.",
        "tags": ["vibration", "alarms", "triage"],
    },
    {
        "id": "kb-2",
        "title": "Spare parts planning template",
        "summary": "Spreadsheet template and heuristics for spare parts prediction.",
        "tags": ["spares", "inventory"],
    },
]


@router.get("")
def list_articles():
    return MOCK_ARTICLES


@router.get("/chatops")
def chatops_stub():
    return {
        "status": "ready",
        "message": "ChatOps integration stub. Connect Slack or Teams bot here.",
        "supported_commands": ["/pm status", "/pm ack <alarm_id>", "/pm report daily"],
    }

