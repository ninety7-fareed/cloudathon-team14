"""CounterGuide application tier.

One process serves Guide chat and Shiftlead. It listens on 8080, which is the
container port in design/cloudformation/application.yaml. The load balancer
health check is GET /health. GET /api/health is the same check.

Guide chat retrieves from the product knowledge base before it answers. An
empty retrieval does not call the foundation model. Catalog rows and the
request log live in Aurora. Shiftlead is read-only and only proposes an action.

Missing Bedrock or database settings do not fail startup. The health check
still returns 200.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "8080"))
AWS_REGION = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
DB_HOST = os.environ.get("DB_HOST", "")
DB_READER_HOST = os.environ.get("DB_READER_HOST", "") or DB_HOST
DB_NAME = os.environ.get("DB_NAME", "counterguide")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_USERNAME = os.environ.get("DB_USERNAME", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
PRODUCT_KB_ID = os.environ.get("PRODUCT_KB_ID", "")
RUNBOOK_KB_ID = os.environ.get("RUNBOOK_KB_ID", "")
SHIFTLEAD_AGENT_ID = os.environ.get("SHIFTLEAD_AGENT_ID", "")
SHIFTLEAD_AGENT_ALIAS_ID = os.environ.get("SHIFTLEAD_AGENT_ALIAS_ID", "")
FOUNDATION_MODEL_ID = os.environ.get("FOUNDATION_MODEL_ID", "")

CLUSTER_NAME = "counterguide"
SERVICE_NAME = "counterguide"
DB_CLUSTER_ID = "counterguide"

READ_ONLY_TOOLS = {
    "read_load_balancer_target_health",
    "read_service_status",
    "read_database_status",
    "read_knowledge_base_sync_status",
    "read_cloudwatch_alarms",
    "read_request_log",
}

CATALOG_SEED = (
    ("BAT-LIPO-2S", "2S LiPo flight pack", "batteries", "Pack for the beginner RC car."),
    ("BAT-AA-LOOSE", "Loose AA cells", "batteries", "Loose AA cells. Not part of a beginner RC kit."),
    ("HOB-RC-CAR", "Beginner RC car", "hobby equipment", "Ready-to-run beginner car."),
    ("HOB-RC-TX", "Beginner RC transmitter", "hobby equipment", "Transmitter sold with the beginner car."),
    ("ELE-USB-C", "USB-C charge cable", "electronics", "Charge cable for the pack charger."),
    ("PHN-CASE-01", "Phone case", "cell phones", "Basic phone case."),
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("counterguide")

_schema_ready = False
_schema_lock = threading.Lock()


def configured(value: str) -> bool:
    return bool(value and value.strip())


def db_configured() -> bool:
    return configured(DB_HOST) and configured(DB_USERNAME) and configured(DB_PASSWORD)


def model_configured() -> bool:
    return configured(FOUNDATION_MODEL_ID)


def product_kb_configured() -> bool:
    return configured(PRODUCT_KB_ID)


def agent_configured() -> bool:
    return configured(SHIFTLEAD_AGENT_ID) and configured(SHIFTLEAD_AGENT_ALIAS_ID)


def json_bytes(payload: dict) -> bytes:
    return json.dumps(payload).encode("utf-8")


def connect(host: str):
    import psycopg

    return psycopg.connect(
        host=host,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USERNAME,
        password=DB_PASSWORD,
        connect_timeout=3,
        autocommit=True,
    )


def ensure_schema() -> bool:
    global _schema_ready
    if _schema_ready or not db_configured():
        return _schema_ready
    with _schema_lock:
        if _schema_ready:
            return True
        try:
            with connect(DB_HOST) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS catalog (
                      sku text PRIMARY KEY,
                      name text NOT NULL,
                      category text NOT NULL,
                      description text NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS request_log (
                      id bigserial PRIMARY KEY,
                      kind text NOT NULL,
                      question text NOT NULL,
                      outcome text NOT NULL,
                      created_at timestamptz NOT NULL DEFAULT now()
                    )
                    """
                )
                with conn.cursor() as cur:
                    cur.executemany(
                        """
                        INSERT INTO catalog (sku, name, category, description)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (sku) DO NOTHING
                        """,
                        CATALOG_SEED,
                    )
            _schema_ready = True
        except Exception as exc:
            log.warning("schema init skipped: %s", type(exc).__name__)
            return False
    return True


def read_catalog() -> list[dict]:
    if not ensure_schema():
        return []
    host = DB_READER_HOST or DB_HOST
    try:
        with connect(host) as conn:
            rows = conn.execute(
                "SELECT sku, name, category, description FROM catalog ORDER BY category, sku"
            ).fetchall()
        return [
            {"sku": row[0], "name": row[1], "category": row[2], "description": row[3]}
            for row in rows
        ]
    except Exception as exc:
        log.warning("catalog read skipped: %s", type(exc).__name__)
        return []


def write_request_log(kind: str, question: str, outcome: str) -> None:
    if not ensure_schema():
        return
    try:
        with connect(DB_HOST) as conn:
            conn.execute(
                "INSERT INTO request_log (kind, question, outcome) VALUES (%s, %s, %s)",
                (kind, question[:2000], outcome[:200]),
            )
    except Exception as exc:
        log.warning("request log skipped: %s", type(exc).__name__)


def is_kit_question(question: str) -> bool:
    text = question.lower()
    return (
        "rc kit" in text
        or ("beginner" in text and "kit" in text)
        or "loose aa" in text
        or "aa cell" in text
    )


def retrieve_documents(question: str) -> tuple[list[dict], str]:
    """Return (documents, status). Status is ok, empty, unconfigured, or error.

    The caller must not invoke the model when documents is empty.
    """
    if not product_kb_configured():
        return [], "unconfigured"
    try:
        import boto3

        client = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)
        response = client.retrieve(
            knowledgeBaseId=PRODUCT_KB_ID,
            retrievalQuery={"text": question},
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 4}},
        )
    except Exception as exc:
        log.warning("retrieve failed: %s", type(exc).__name__)
        return [], "error"

    documents = []
    for item in response.get("retrievalResults", []):
        excerpt = (item.get("content") or {}).get("text") or ""
        excerpt = excerpt.strip()
        if not excerpt:
            continue
        location = item.get("location") or {}
        uri = ""
        if "s3Location" in location:
            uri = (location.get("s3Location") or {}).get("uri") or ""
        elif "webLocation" in location:
            uri = (location.get("webLocation") or {}).get("url") or ""
        metadata = item.get("metadata") or {}
        title = str(metadata.get("title") or metadata.get("x-amz-bedrock-kb-source-uri") or uri or "product guide")
        documents.append({"title": title, "uri": uri, "excerpt": excerpt[:1500]})
    if not documents:
        return [], "empty"
    return documents, "ok"


def guide_forbids_loose_aa(documents: list[dict]) -> bool:
    text = " ".join(doc["excerpt"].lower() for doc in documents)
    mentions_aa = "loose aa" in text or "aa cell" in text or "aa cells" in text
    forbids = any(word in text for word in ("forbid", "forbidden", "do not", "don't", "must not", "not allowed", "never"))
    return mentions_aa and forbids


def refused_skus(documents: list[dict], catalog: list[dict]) -> list[str]:
    if not guide_forbids_loose_aa(documents):
        return []
    refused = []
    for row in catalog:
        blob = f"{row['sku']} {row['name']} {row['description']}".lower()
        if row["sku"] == "BAT-AA-LOOSE" or "loose aa" in blob or "aa cell" in blob:
            refused.append(row["sku"])
    return refused


def cited_from_documents(documents: list[dict], offered: list[dict], refused: list[str], kit: bool) -> str:
    lines = ["Answer grounded in the retrieved product guides."]
    for doc in documents:
        source = doc["uri"] or doc["title"]
        lines.append(f"From {source}: {doc['excerpt']}")
    if kit:
        if offered:
            skus = ", ".join(f"{row['sku']} ({row['name']})" for row in offered)
            lines.append(f"Catalog SKUs: {skus}.")
        else:
            lines.append("The catalog did not return SKUs.")
        if refused:
            lines.append(
                "The safety guide forbids loose AA cells in this kit. "
                f"Refused SKUs: {', '.join(refused)}."
            )
    return "\n".join(lines)


def call_model(question: str, documents: list[dict], offered: list[dict], refused: list[str]) -> str:
    import boto3

    passages = "\n\n".join(
        f"Document: {doc['uri'] or doc['title']}\n{doc['excerpt']}" for doc in documents
    )
    catalog_text = "\n".join(
        f"{row['sku']} | {row['name']} | {row['category']} | {row['description']}" for row in offered
    ) or "(no catalog rows)"
    refused_text = ", ".join(refused) or "(none)"
    prompt = (
        "Use only the retrieved documents and catalog rows below. "
        "Do not use general knowledge. Cite the document sources you use. "
        "If this is a kit, recommend only the listed catalog SKUs. "
        "If the documents forbid loose AA cells, refuse that combination and do not recommend a refused SKU.\n\n"
        f"Question: {question}\n\n"
        f"Retrieved documents:\n{passages}\n\n"
        f"Catalog rows:\n{catalog_text}\n\n"
        f"Refused SKUs: {refused_text}"
    )
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    response = client.converse(
        modelId=FOUNDATION_MODEL_ID,
        system=[{"text": "You answer only from the documents and catalog rows in the user message."}],
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 400, "temperature": 0.1},
    )
    content = response["output"]["message"]["content"]
    return "".join(part.get("text", "") for part in content).strip()


def guide(question: str) -> dict:
    documents, status = retrieve_documents(question)
    kit = is_kit_question(question)
    if not documents:
        catalog = read_catalog() if kit else []
        if status == "unconfigured":
            answer = "Retrieval found nothing. The product knowledge base is not configured, so the model was not called."
        elif status == "error":
            answer = "Retrieval found nothing. The product knowledge base did not return documents, so the model was not called."
        else:
            answer = "Retrieval found nothing in the product guides. The model was not called."
        if kit and catalog:
            answer += " Catalog rows are listed as stored SKUs only. No combination was judged without a retrieved guide."
        write_request_log("guide", question, "retrieval_empty")
        return {
            "answer": answer,
            "documents": [],
            "calledModel": False,
            "retrievalEmpty": True,
            "catalog": catalog,
            "refused": [],
        }

    catalog = read_catalog()
    refused = refused_skus(documents, catalog) if kit else []
    offered = [row for row in catalog if row["sku"] not in refused] if kit else catalog
    called_model = False
    if model_configured():
        try:
            answer = call_model(question, documents, offered if kit else catalog, refused)
            called_model = True
        except Exception as exc:
            log.warning("model call skipped: %s", type(exc).__name__)
            answer = cited_from_documents(documents, offered, refused, kit)
    else:
        answer = cited_from_documents(documents, offered, refused, kit)
    if kit and (refused or guide_forbids_loose_aa(documents)) and "aa" not in answer.lower():
        answer += " The safety guide forbids loose AA cells in this kit. Those SKUs are not included."
    outcome = "kit_refused" if kit and (refused or guide_forbids_loose_aa(documents)) else "cited"
    write_request_log("guide", question, outcome)
    return {
        "answer": answer,
        "documents": documents,
        "calledModel": called_model,
        "retrievalEmpty": False,
        "catalog": offered if kit else catalog,
        "refused": refused,
    }


def tool_result(payload: dict) -> dict:
    return payload


def read_service_status() -> dict:
    import boto3

    ecs = boto3.client("ecs", region_name=AWS_REGION)
    response = ecs.describe_services(cluster=CLUSTER_NAME, services=[SERVICE_NAME])
    services = response.get("services") or []
    if not services:
        return tool_result({"seen": False, "detail": "service not found"})
    service = services[0]
    target_group = ""
    load_balancers = service.get("loadBalancers") or []
    if load_balancers:
        target_group = load_balancers[0].get("targetGroupArn") or ""
    return tool_result(
        {
            "seen": True,
            "status": service.get("status"),
            "desiredCount": service.get("desiredCount"),
            "runningCount": service.get("runningCount"),
            "pendingCount": service.get("pendingCount"),
            "targetGroupArn": target_group,
        }
    )


def read_load_balancer_target_health() -> dict:
    import boto3

    service = read_service_status()
    arn = service.get("targetGroupArn") or ""
    if not arn:
        return tool_result({"seen": False, "detail": "target group not visible"})
    elb = boto3.client("elbv2", region_name=AWS_REGION)
    health = elb.describe_target_health(TargetGroupArn=arn)
    states = []
    unhealthy = 0
    for item in health.get("TargetHealthDescriptions", []):
        state = (item.get("TargetHealth") or {}).get("State") or "unknown"
        states.append(state)
        if state != "healthy":
            unhealthy += 1
    return tool_result({"seen": True, "states": states, "unhealthy": unhealthy})


def read_database_status() -> dict:
    import boto3

    rds = boto3.client("rds", region_name=AWS_REGION)
    clusters = rds.describe_db_clusters(DBClusterIdentifier=DB_CLUSTER_ID).get("DBClusters") or []
    if not clusters:
        return tool_result({"seen": False, "detail": "cluster not found"})
    cluster = clusters[0]
    instances = []
    described = rds.describe_db_instances(
        Filters=[{"Name": "db-cluster-id", "Values": [DB_CLUSTER_ID]}]
    ).get("DBInstances", [])
    for item in described:
        instances.append(
            {
                "id": item.get("DBInstanceIdentifier"),
                "status": item.get("DBInstanceStatus"),
                "availabilityZone": item.get("AvailabilityZone"),
            }
        )
    return tool_result({"seen": True, "status": cluster.get("Status"), "instances": instances})


def read_knowledge_base_sync_status() -> dict:
    import boto3

    client = boto3.client("bedrock-agent", region_name=AWS_REGION)
    bases = []
    failed = False
    for name, kb_id in (("product", PRODUCT_KB_ID), ("runbook", RUNBOOK_KB_ID)):
        if not configured(kb_id):
            bases.append({"name": name, "seen": False, "detail": "not configured"})
            continue
        info = client.get_knowledge_base(knowledgeBaseId=kb_id)["knowledgeBase"]
        status = info.get("status")
        if status not in ("ACTIVE", None):
            failed = True
        bases.append({"name": name, "seen": True, "status": status})
    if not any(item.get("seen") for item in bases):
        return tool_result({"seen": False, "bases": bases, "failed": False})
    return tool_result({"seen": True, "bases": bases, "failed": failed})


def read_cloudwatch_alarms() -> dict:
    import boto3

    cloudwatch = boto3.client("cloudwatch", region_name=AWS_REGION)
    response = cloudwatch.describe_alarms(AlarmNamePrefix="counterguide-", MaxRecords=20)
    alarms = []
    in_alarm = []
    for alarm in response.get("MetricAlarms", []):
        name = alarm.get("AlarmName")
        state = alarm.get("StateValue")
        alarms.append({"name": name, "state": state})
        if state == "ALARM":
            in_alarm.append(name)
    return tool_result({"seen": True, "alarms": alarms, "inAlarm": in_alarm})


def read_request_log() -> dict:
    if not ensure_schema():
        return tool_result({"seen": False, "detail": "request log unavailable"})
    host = DB_READER_HOST or DB_HOST
    with connect(host) as conn:
        rows = conn.execute(
            """
            SELECT id, kind, outcome, created_at
            FROM request_log
            ORDER BY id DESC
            LIMIT 20
            """
        ).fetchall()
    return tool_result(
        {
            "seen": True,
            "rows": [
                {
                    "id": row[0],
                    "kind": row[1],
                    "outcome": row[2],
                    "createdAt": row[3].isoformat() if row[3] else None,
                }
                for row in rows
            ],
        }
    )


def run_read_tool(name: str) -> dict:
    if name not in READ_ONLY_TOOLS:
        return {"seen": False, "detail": "refused: not a read-only CounterGuide tool"}
    functions = {
        "read_load_balancer_target_health": read_load_balancer_target_health,
        "read_service_status": read_service_status,
        "read_database_status": read_database_status,
        "read_knowledge_base_sync_status": read_knowledge_base_sync_status,
        "read_cloudwatch_alarms": read_cloudwatch_alarms,
        "read_request_log": read_request_log,
    }
    try:
        return functions[name]()
    except Exception as exc:
        log.warning("read tool %s skipped: %s", name, type(exc).__name__)
        return {"seen": False, "detail": type(exc).__name__}


def tier_for_alarm(name: str) -> str:
    if "aurora" in name or "knowledge" in name:
        return "data"
    return "application"


def proposal_from(observations: dict) -> dict:
    notes = []
    tier = None

    targets = observations.get("read_load_balancer_target_health") or {}
    if targets.get("seen") and targets.get("unhealthy", 0):
        tier = "application"
        notes.append(f"{targets['unhealthy']} load balancer targets are not healthy.")

    service = observations.get("read_service_status") or {}
    if service.get("seen") and service.get("runningCount") is not None and service["runningCount"] < 2:
        tier = "application"
        notes.append("Fewer than two application tasks are running.")

    database = observations.get("read_database_status") or {}
    if database.get("seen") and database.get("status") not in (None, "available"):
        tier = "data"
        notes.append(f"Aurora status is {database.get('status')}.")

    knowledge = observations.get("read_knowledge_base_sync_status") or {}
    if knowledge.get("seen") and knowledge.get("failed"):
        tier = "data"
        notes.append("A knowledge base is not active.")

    alarms = observations.get("read_cloudwatch_alarms") or {}
    if alarms.get("seen"):
        for name in alarms.get("inAlarm") or []:
            alarm_tier = tier_for_alarm(name)
            if tier is None:
                tier = alarm_tier
            notes.append(f"Alarm {name} is in ALARM.")

    if tier is None:
        unseen = [name for name, value in observations.items() if not value.get("seen")]
        if unseen and not any(value.get("seen") for value in observations.values()):
            proposal = (
                "Shiftlead could not read health, the request log, or the runbooks. "
                "No fault was named. No change was applied. A person ships any CloudFormation change."
            )
        else:
            proposal = (
                "The read-only checks did not show a fault. "
                "No change was applied. A person ships any CloudFormation change."
            )
        return {"tier": None, "proposal": proposal, "applied": False, "readOnly": True}

    proposal = " ".join(notes)
    proposal += (
        f" The tier at fault is {tier}. "
        "Next action: a person ships the change with CloudFormation. Shiftlead did not apply it."
    )
    return {"tier": tier, "proposal": proposal, "applied": False, "readOnly": True}


def invoke_shiftlead(question: str, observations: dict) -> str:
    import boto3

    client = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)
    session_id = str(uuid.uuid4())
    response = client.invoke_agent(
        agentId=SHIFTLEAD_AGENT_ID,
        agentAliasId=SHIFTLEAD_AGENT_ALIAS_ID,
        sessionId=session_id,
        inputText=question,
        endSession=False,
    )
    text = ""
    for _ in range(4):
        invocation = None
        for event in response.get("completion") or []:
            if "chunk" in event:
                text += event["chunk"]["bytes"].decode("utf-8", errors="replace")
            elif "returnControl" in event:
                invocation = event["returnControl"]
        if not invocation:
            break
        results = []
        for item in invocation.get("invocationInputs") or []:
            function_input = item.get("functionInvocationInput") or {}
            name = function_input.get("function") or ""
            observation = run_read_tool(name)
            observations[name] = observation
            results.append(
                {
                    "functionResult": {
                        "actionGroup": function_input.get("actionGroup") or "read-health",
                        "function": name,
                        "responseBody": {"TEXT": {"body": json.dumps(observation)}},
                    }
                }
            )
        response = client.invoke_agent(
            agentId=SHIFTLEAD_AGENT_ID,
            agentAliasId=SHIFTLEAD_AGENT_ALIAS_ID,
            sessionId=session_id,
            sessionState={
                "invocationId": invocation.get("invocationId"),
                "returnControlInvocationResults": results,
            },
            endSession=False,
        )
    return text.strip()


def shiftlead(question: str) -> dict:
    observations = {}
    if not agent_configured():
        for name in (
            "read_load_balancer_target_health",
            "read_service_status",
            "read_database_status",
            "read_knowledge_base_sync_status",
            "read_cloudwatch_alarms",
            "read_request_log",
        ):
            observations[name] = run_read_tool(name)
        body = proposal_from(observations)
        body["answer"] = body["proposal"]
        body["agentInvoked"] = False
        write_request_log("shiftlead", question, "proposal")
        return body

    agent_text = ""
    try:
        agent_text = invoke_shiftlead(question, observations)
    except Exception as exc:
        log.warning("shiftlead invoke skipped: %s", type(exc).__name__)
        for name in READ_ONLY_TOOLS:
            if name not in observations:
                observations[name] = run_read_tool(name)
    body = proposal_from(observations)
    if agent_text:
        if "not applied" not in agent_text.lower() and "cloudformation" not in agent_text.lower():
            agent_text += " This proposal was not applied. A person ships any change with CloudFormation."
        body["answer"] = agent_text
        body["proposal"] = agent_text
    else:
        body["answer"] = body["proposal"]
    body["agentInvoked"] = bool(agent_text)
    body["applied"] = False
    body["readOnly"] = True
    write_request_log("shiftlead", question, "proposal")
    return body


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:
        log.info("%s %s", self.command, self.path.split("?", 1)[0])

    def _send(self, status: int, payload: dict) -> None:
        body = json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict | None:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        if length > 65536:
            return None
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        if not isinstance(data, dict):
            return None
        return data

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in ("/health", "/api/health"):
            self._send(200, {"status": "ok"})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        if path not in ("/api/guide", "/api/chat", "/api/shiftlead"):
            self._send(404, {"error": "not found"})
            return
        data = self._read_json()
        if data is None:
            self._send(400, {"error": "invalid json"})
            return
        question = str(data.get("question") or data.get("message") or "").strip()
        if not question:
            self._send(400, {"error": "question is required"})
            return
        if path == "/api/shiftlead":
            self._send(200, shiftlead(question))
            return
        self._send(200, guide(question))


def main() -> None:
    log.info(
        "listening on %s db=%s product_kb=%s model=%s shiftlead=%s",
        PORT,
        db_configured(),
        product_kb_configured(),
        model_configured(),
        agent_configured(),
    )
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
