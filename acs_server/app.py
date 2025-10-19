import logging
import os
from typing import Tuple

from flask import Flask, Response, request

from .soap import (
    build_envelope,
    build_fault,
    build_get_rpc_methods_response,
    build_inform_response,
    parse_cwmp_request,
)


def create_app() -> Flask:
    app = Flask(__name__)

    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    logger = logging.getLogger("acs")

    @app.get("/")
    def index() -> Tuple[str, int, dict]:
        return (
            "TR-069 ACS is running. POST CWMP SOAP to /acs",
            200,
            {"Content-Type": "text/plain; charset=utf-8"},
        )

    @app.route("/acs", methods=["POST", "GET"])  # Allow GET health-checks
    def acs_endpoint():
        if request.method == "GET":
            return (
                "OK",
                200,
                {"Content-Type": "text/plain; charset=utf-8"},
            )

        raw: bytes = request.get_data() or b""
        if not raw:
            # No body -> per TR-069 flows this could be end of session; 204 is acceptable
            return Response(status=204)

        try:
            parsed = parse_cwmp_request(raw)
        except Exception as exc:  # noqa: BLE001 - surface parsing errors to client
            logger.exception("Failed to parse CWMP request")
            fault_el = build_fault("Client", "Bad Request", str(exc))
            envelope = build_envelope(fault_el, cwmp_id=None)
            return Response(envelope, status=400, mimetype="text/xml; charset=utf-8")

        method_name = parsed.get("method_name")
        cwmp_id = parsed.get("cwmp_id")
        logger.info("Received CWMP RPC: %s (ID=%s)", method_name, cwmp_id)

        if method_name == "Inform":
            body_child = build_inform_response(max_envelopes=1)
        elif method_name == "GetRPCMethods":
            body_child = build_get_rpc_methods_response()
        else:
            body_child = build_fault(
                "Client",
                "Method Not Supported",
                f"Unsupported CWMP method: {method_name}",
            )

        envelope = build_envelope(body_child, cwmp_id=cwmp_id)
        return Response(envelope, status=200, mimetype="text/xml; charset=utf-8")

    return app
