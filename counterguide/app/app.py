"""CounterGuide application tier.

Runs on ECS Fargate behind the load balancer (port 8080). CloudFront forwards
/api/* here. This is the only tier that calls Aurora and Bedrock.

Environment (set by design/cloudformation/application.yaml):
  DB_HOST, DB_READER_HOST, DB_NAME, DB_PORT, DB_USERNAME, DB_PASSWORD,
  AWS_REGION, PRODUCT_KB_ID, RUNBOOK_KB_ID, SHIFTLEAD_AGENT_ID,
  SHIFTLEAD_AGENT_ALIAS_ID, FOUNDATION_MODEL_ID
Optional: GUIDES_DATA_SOURCE_ID, RUNBOOKS_DATA_SOURCE_ID (enables ingestion-job
status in Shiftlead), ECS_CLUSTER (default counterguide), ECS_SERVICE
(default counterguide), DB_CLUSTER_ID (default counterguide).
"""

import json
import logging
import os
import re
import threading
import time
import uuid

import boto3
from botocore.config import Config
from flask import Flask, g, jsonify, request

from catalog import CATALOG_ROWS, SCHEMA_SQL

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("counterguide")

REGION = os.environ.get("AWS_REGION", "us-east-1")
PRODUCT_KB_ID = os.environ.get("PRODUCT_KB_ID", "")
RUNBOOK_KB_ID = os.environ.get("RUNBOOK_KB_ID", "")
AGENT_ID = os.environ.get("SHIFTLEAD_AGENT_ID", "")
AGENT_ALIAS_ID = os.environ.get("SHIFTLEAD_AGENT_ALIAS_ID", "")
MODEL_ID = os.environ.get("FOUNDATION_MODEL_ID", "us.amazon.nova-pro-v1:0")
# Direct regional model ID, used if the cross-region inference profile is denied.
FALLBACK_MODEL_ID = "amazon.nova-pro-v1:0"
GUIDES_DS_ID = os.environ.get("GUIDES_DATA_SOURCE_ID", "")
RUNBOOKS_DS_ID = os.environ.get("RUNBOOKS_DATA_SOURCE_ID", "")
ECS_CLUSTER = os.environ.get("ECS_CLUSTER", "counterguide")
ECS_SERVICE = os.environ.get("ECS_SERVICE", "counterguide")
DB_CLUSTER_ID = os.environ.get("DB_CLUSTER_ID", "counterguide")
# Minimum retrieval score. Below this, Guide chat says it found nothing.
MIN_SCORE = float(os.environ.get("MIN_RETRIEVAL_SCORE", "0.3"))

_cfg = Config(region_name=REGION, retries={"max_attempts": 3, "mode": "standard"})
_clients = {}


def client(name):
    if name not in _clients:
        _clients[name] = boto3.client(name, config=_cfg)
    return _clients[name]


app = Flask(__name__)

# --------------------------------------------------------------------------- #
# Database (Aurora PostgreSQL). Lazy connect: Aurora may still be starting when
# the first task launches, and /health must not depend on it.
# --------------------------------------------------------------------------- #
_db_ready = False
_db_lock = threading.Lock()


def _connect(host_env):
    import psycopg2  # imported lazily so /health works without a database

    host = os.environ.get(host_env) or os.environ.get("DB_HOST")
    if not host:
        raise RuntimeError("DB_HOST is not set")
    return psycopg2.connect(
        host=host,
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ.get("DB_NAME", "counterguide"),
        user=os.environ.get("DB_USERNAME", "counterguide"),
        password=os.environ.get("DB_PASSWORD", ""),
        connect_timeout=5,
        sslmode="require",
    )


def ensure_schema():
    """Create tables and seed the sample catalog once. Safe to call repeatedly."""
    global _db_ready
    if _db_ready:
        return
    with _db_lock:
        if _db_ready:
            return
        conn = _connect("DB_HOST")
        try:
            with conn, conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)
                cur.execute("SELECT count(*) FROM products")
                if cur.fetchone()[0] == 0:
                    cur.executemany(
                        "INSERT INTO products (sku, name, category, description, price, stock, tags)"
                        " VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (sku) DO NOTHING",
                        CATALOG_ROWS,
                    )
            _db_ready = True
            log.info("database schema ready")
        finally:
            conn.close()


def db_query(sql, params=(), reader=True):
    ensure_schema()
    conn = _connect("DB_READER_HOST" if reader else "DB_HOST")
    try:
        with conn, conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.description is None:
                return []
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def db_execute(sql, params=()):
    ensure_schema()
    conn = _connect("DB_HOST")
    try:
        with conn, conn.cursor() as cur:
            cur.execute(sql, params)
    finally:
        conn.close()


def write_request_log(path, status, tier, latency_ms, detail="", simulated=False):
    """Best effort. A logging failure must not break the response."""
    try:
        db_execute(
            "INSERT INTO request_log (request_id, path, status, tier, latency_ms, detail, simulated)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (getattr(g, "request_id", str(uuid.uuid4())), path, status, tier, latency_ms,
             (detail or "")[:500], simulated),
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("request log write failed: %s", exc)


@app.before_request
def _start():
    g.request_id = str(uuid.uuid4())
    g.start = time.time()


def _elapsed_ms():
    return int((time.time() - g.start) * 1000)


def _json_safe(value):
    return json.loads(json.dumps(value, default=str))


# --------------------------------------------------------------------------- #
# Health (target group health check). No database or Bedrock dependency.
# --------------------------------------------------------------------------- #
@app.get("/health")
def health():
    return jsonify(status="ok"), 200


@app.get("/api/health")
def api_health():
    """Deeper check for people: reports whether the database answers."""
    out = {"app": "ok", "region": REGION}
    try:
        db_query("SELECT 1 AS ok")
        out["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        out["database"] = f"error: {type(exc).__name__}"
    return jsonify(out)


# --------------------------------------------------------------------------- #
# Product page (catalog). This is the "product page" Shiftlead troubleshoots.
# --------------------------------------------------------------------------- #
@app.get("/api/products")
def products():
    category = request.args.get("category")
    try:
        if category:
            rows = db_query(
                "SELECT sku, name, category, description, price, stock FROM products"
                " WHERE category = %s ORDER BY sku", (category,))
        else:
            rows = db_query(
                "SELECT sku, name, category, description, price, stock FROM products ORDER BY category, sku")
        write_request_log("/api/products", 200, "application", _elapsed_ms())
        return jsonify(products=_json_safe(rows))
    except Exception as exc:  # noqa: BLE001
        log.exception("product page failed")
        write_request_log("/api/products", 500, "data", _elapsed_ms(), f"{type(exc).__name__}: {exc}")
        return jsonify(error="The product page could not read the catalog."), 500


# --------------------------------------------------------------------------- #
# Guide chat: retrieve first, answer only from documents + catalog.
# --------------------------------------------------------------------------- #
GUIDE_SYSTEM = (
    "You are Guide chat, an assistant for AnyCompany store associates. "
    "Answer ONLY from the DOCUMENTS and CATALOG provided in the user message. "
    "Do not use general knowledge. If the documents do not answer the question, say so. "
    "When you recommend products, use only SKUs that appear in CATALOG, and write each SKU exactly. "
    "If a requested combination is forbidden by the documents (for example a battery type that the "
    "safety guide says must not be used), refuse that combination clearly, say which guide forbids it, "
    "and offer the safe catalog alternative. Cite the document names you used in square brackets, "
    "for example [battery-safety.md]. Keep answers short: at most 8 sentences or a short list."
)


def _doc_name(ref):
    loc = (ref.get("location") or {})
    uri = (loc.get("s3Location") or {}).get("uri", "")
    return uri.rsplit("/", 1)[-1] if uri else "document"


def converse(system, user_text, max_tokens=700):
    br = client("bedrock-runtime")
    kwargs = dict(
        system=[{"text": system}],
        messages=[{"role": "user", "content": [{"text": user_text}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": 0.2},
    )
    try:
        resp = br.converse(modelId=MODEL_ID, **kwargs)
    except br.exceptions.AccessDeniedException:
        log.warning("access denied for %s, retrying with %s", MODEL_ID, FALLBACK_MODEL_ID)
        resp = br.converse(modelId=FALLBACK_MODEL_ID, **kwargs)
    parts = resp["output"]["message"]["content"]
    return "".join(p.get("text", "") for p in parts).strip()


@app.post("/api/chat")
def chat():
    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()
    if not question:
        return jsonify(error="Ask a question."), 400
    if len(question) > 1000:
        return jsonify(error="Keep the question under 1000 characters."), 400

    # 1. Retrieve from the product knowledge base.
    try:
        resp = client("bedrock-agent-runtime").retrieve(
            knowledgeBaseId=PRODUCT_KB_ID,
            retrievalQuery={"text": question},
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 5}},
        )
        results = [r for r in resp.get("retrievalResults", []) if (r.get("score") or 0) >= MIN_SCORE]
    except Exception as exc:  # noqa: BLE001
        log.exception("retrieve failed")
        write_request_log("/api/chat", 502, "data", _elapsed_ms(), f"retrieve: {type(exc).__name__}: {exc}")
        return jsonify(error="The product guides are not reachable right now."), 502

    if not results:
        write_request_log("/api/chat", 200, "application", _elapsed_ms(), "no retrieval results")
        return jsonify(
            answer="I couldn't find that in the product guides, so I won't guess. "
                   "Please check with a supervisor.",
            sources=[], skus=[], retrieved=0)

    # 2. Read the catalog (small sample catalog, so read it all).
    try:
        catalog = db_query(
            "SELECT sku, name, category, description, price, stock, tags FROM products ORDER BY category, sku")
    except Exception as exc:  # noqa: BLE001
        log.exception("catalog read failed")
        write_request_log("/api/chat", 500, "data", _elapsed_ms(), f"catalog: {type(exc).__name__}: {exc}")
        return jsonify(error="The catalog is not reachable right now."), 500

    docs_text = "\n\n".join(
        f"--- {_doc_name(r)} ---\n{(r.get('content') or {}).get('text', '')}" for r in results)
    catalog_text = "\n".join(
        f"{p['sku']} | {p['name']} | {p['category']} | ${p['price']} | stock {p['stock']} | {p['description']}"
        for p in catalog)
    user_text = f"QUESTION:\n{question}\n\nDOCUMENTS:\n{docs_text}\n\nCATALOG:\n{catalog_text}"

    # 3. Answer with the model, grounded in what was retrieved.
    try:
        answer = converse(GUIDE_SYSTEM, user_text)
    except Exception as exc:  # noqa: BLE001
        log.exception("model call failed")
        write_request_log("/api/chat", 502, "application", _elapsed_ms(), f"model: {type(exc).__name__}: {exc}")
        return jsonify(error="The model is not reachable right now."), 502

    known = {p["sku"]: p for p in catalog}
    skus = [known[s] for s in dict.fromkeys(re.findall(r"[A-Z]{2}-[A-Z0-9-]+", answer)) if s in known]
    sources = sorted({_doc_name(r) for r in results})
    write_request_log("/api/chat", 200, "application", _elapsed_ms())
    return jsonify(answer=answer, sources=sources, skus=_json_safe(skus), retrieved=len(results))


# --------------------------------------------------------------------------- #
# Shiftlead: Bedrock Agent with RETURN_CONTROL. The agent picks a read-only
# tool; this tier runs it and returns the observation. No writes.
# --------------------------------------------------------------------------- #
def tool_target_health():
    svc = client("ecs").describe_services(cluster=ECS_CLUSTER, services=[ECS_SERVICE])["services"]
    tgs = [lb["targetGroupArn"] for s in svc for lb in s.get("loadBalancers", [])]
    out = []
    for tg in tgs:
        th = client("elbv2").describe_target_health(TargetGroupArn=tg)["TargetHealthDescriptions"]
        out.append({"targetGroup": tg.rsplit(":", 1)[-1], "targets": [
            {"id": t["Target"]["Id"], "state": t["TargetHealth"]["State"],
             "reason": t["TargetHealth"].get("Reason", ""), "description": t["TargetHealth"].get("Description", "")}
            for t in th]})
    return {"tier": "application (load balancer targets)", "targetGroups": out}


def tool_service_status():
    svc = client("ecs").describe_services(cluster=ECS_CLUSTER, services=[ECS_SERVICE])["services"]
    return {"tier": "application", "services": [{
        "name": s["serviceName"], "status": s["status"], "desired": s["desiredCount"],
        "running": s["runningCount"], "pending": s["pendingCount"],
        "deployments": [{"status": d["status"], "rollout": d.get("rolloutState"),
                         "running": d["runningCount"], "desired": d["desiredCount"]} for d in s.get("deployments", [])],
        "recentEvents": [e["message"] for e in s.get("events", [])[:5]],
    } for s in svc]}


def tool_database_status():
    rds = client("rds")
    cl = rds.describe_db_clusters(DBClusterIdentifier=DB_CLUSTER_ID)["DBClusters"][0]
    members = []
    for m in cl.get("DBClusterMembers", []):
        try:
            inst = rds.describe_db_instances(DBInstanceIdentifier=m["DBInstanceIdentifier"])["DBInstances"][0]
            members.append({"id": m["DBInstanceIdentifier"], "writer": m["IsClusterWriter"],
                            "status": inst["DBInstanceStatus"], "az": inst.get("AvailabilityZone")})
        except Exception as exc:  # noqa: BLE001
            members.append({"id": m["DBInstanceIdentifier"], "error": type(exc).__name__})
    try:
        db_query("SELECT 1 AS ok")
        reachable = "yes"
    except Exception as exc:  # noqa: BLE001
        reachable = f"no ({type(exc).__name__})"
    return {"tier": "data", "cluster": cl["DBClusterIdentifier"], "status": cl["Status"],
            "multiAZ": cl.get("MultiAZ"), "members": members, "reachableFromApplication": reachable}


def tool_kb_sync():
    ba = client("bedrock-agent")
    out = []
    for name, kb, ds in (("product-guides", PRODUCT_KB_ID, GUIDES_DS_ID),
                         ("operations-runbooks", RUNBOOK_KB_ID, RUNBOOKS_DS_ID)):
        item = {"knowledgeBase": name}
        try:
            item["status"] = ba.get_knowledge_base(knowledgeBaseId=kb)["knowledgeBase"]["status"]
        except Exception as exc:  # noqa: BLE001
            item["status"] = f"unreadable ({type(exc).__name__})"
        if ds:
            try:
                jobs = ba.list_ingestion_jobs(
                    knowledgeBaseId=kb, dataSourceId=ds, maxResults=1,
                    sortBy={"attribute": "STARTED_AT", "order": "DESCENDING"})["ingestionJobSummaries"]
                if jobs:
                    j = jobs[0]
                    item["lastIngestion"] = {"status": j["status"], "statistics": j.get("statistics", {})}
                else:
                    item["lastIngestion"] = "none - documents were never ingested"
            except Exception as exc:  # noqa: BLE001
                item["lastIngestion"] = f"unreadable ({type(exc).__name__})"
        else:
            item["lastIngestion"] = "not visible (data source ID not configured)"
        out.append(item)
    return {"tier": "data (knowledge bases)", "knowledgeBases": out}


def tool_alarms():
    alarms = client("cloudwatch").describe_alarms(AlarmNamePrefix="counterguide")["MetricAlarms"]
    return {"alarms": [{"name": a["AlarmName"], "state": a["StateValue"],
                        "reason": a.get("StateReason", "")[:200]} for a in alarms]}


def tool_request_log():
    rows = db_query(
        "SELECT created_at, path, status, tier, latency_ms, detail, simulated FROM request_log"
        " ORDER BY created_at DESC LIMIT 20")
    errors = [r for r in rows if r["status"] >= 500]
    return {"recentRequests": len(rows), "recentErrors": len(errors), "rows": _json_safe(rows)}


TOOLS = {
    "read_load_balancer_target_health": tool_target_health,
    "read_service_status": tool_service_status,
    "read_database_status": tool_database_status,
    "read_knowledge_base_sync_status": tool_kb_sync,
    "read_cloudwatch_alarms": tool_alarms,
    "read_request_log": tool_request_log,
}


def run_tool(name):
    fn = TOOLS.get(name)
    if fn is None:
        return {"error": f"unknown tool {name}"}
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        log.exception("tool %s failed", name)
        return {"error": f"{type(exc).__name__}: {exc}"[:300]}


@app.post("/api/shiftlead")
def shiftlead():
    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()
    if not question:
        return jsonify(error="Ask a question."), 400
    session_id = body.get("sessionId") or str(uuid.uuid4())
    rt = client("bedrock-agent-runtime")
    trace = []
    answer = ""
    kwargs = {"inputText": question[:1000]}
    try:
        for _ in range(8):  # bounded number of tool rounds
            resp = rt.invoke_agent(agentId=AGENT_ID, agentAliasId=AGENT_ALIAS_ID,
                                   sessionId=session_id, **kwargs)
            control = None
            for event in resp["completion"]:
                if "chunk" in event:
                    answer += event["chunk"]["bytes"].decode("utf-8")
                elif "returnControl" in event:
                    control = event["returnControl"]
            if not control:
                break
            results = []
            for inv in control.get("invocationInputs", []):
                fi = inv.get("functionInvocationInput", {})
                observation = run_tool(fi.get("function", ""))
                trace.append({"tool": fi.get("function"), "result": observation})
                results.append({"functionResult": {
                    "actionGroup": fi.get("actionGroup"),
                    "function": fi.get("function"),
                    "responseBody": {"TEXT": {"body": json.dumps(observation, default=str)[:20000]}},
                }})
            kwargs = {"sessionState": {"invocationId": control["invocationId"],
                                       "returnControlInvocationResults": results}}
    except Exception as exc:  # noqa: BLE001
        log.exception("shiftlead failed")
        write_request_log("/api/shiftlead", 502, "application", _elapsed_ms(), f"{type(exc).__name__}: {exc}")
        return jsonify(error=f"Shiftlead could not run: {type(exc).__name__}", toolsRun=trace), 502
    write_request_log("/api/shiftlead", 200, "application", _elapsed_ms())
    return jsonify(answer=answer.strip() or "Shiftlead returned no text.", toolsRun=_json_safe(trace),
                   sessionId=session_id, note="Proposal only. A person ships any change through CloudFormation.")


# --------------------------------------------------------------------------- #
# Demo helper, clearly labelled: records SIMULATED failed product-page requests
# in the request log so Shiftlead has a fault to diagnose without breaking real
# infrastructure. It changes no AWS resource. Rows are marked simulated=true.
# --------------------------------------------------------------------------- #
@app.post("/api/demo/simulate-product-page-errors")
def simulate_errors():
    for _ in range(5):
        write_request_log("/api/products", 500, "data", 5003,
                          "SIMULATED: OperationalError: connection to Aurora writer timed out (port 5432)",
                          simulated=True)
    return jsonify(recorded=5, simulated=True,
                   note="Five SIMULATED product-page failures were written to the request log. No AWS resource changed.")


@app.post("/api/demo/clear-simulated")
def clear_simulated():
    db_execute("DELETE FROM request_log WHERE simulated = true")
    return jsonify(cleared=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
