"""Reviewed local Wan workflows; no hosted nodes or arbitrary workflow overrides."""
from __future__ import annotations

import copy
import hashlib
import ipaddress
import json
from pathlib import Path
from urllib.parse import urlsplit


class LocalWorkflowPolicyError(ValueError):
    pass


_WORKFLOWS = Path(__file__).parent / "workflows"
# Hash canonical JSON, so Windows CRLF does not invalidate the review.
_REVIEWED_HASHES = {
    "wan22-t2v-4step.json": "2b4017403bd753ce26b1301931fd155db4be985af9266888daedb17c14b1d95b",
    "wan22-i2v-4step.json": "452056015f7950ebb0e0b28d1e6f9803c1632cdb37b636bbd057d29434a07d8c",
}


def local_server_url(value: str) -> str:
    """Accept literal loopback only; normalize localhost without a DNS lookup."""
    try:
        parts = urlsplit(value)
        host = parts.hostname
        if (parts.scheme != "http" or not host or parts.username is not None
                or parts.password is not None or parts.path not in ("", "/")
                or parts.query or parts.fragment):
            raise ValueError
        host = "127.0.0.1" if host.lower() == "localhost" else host
        address = ipaddress.ip_address(host)
        if not address.is_loopback:
            raise ValueError
        port = parts.port or 8188
        host = f"[{address}]" if address.version == 6 else str(address)
        return f"http://{host}:{port}"
    except (TypeError, ValueError):
        raise LocalWorkflowPolicyError(
            "Wan local requires an HTTP server on literal loopback (localhost, 127.0.0.1 or ::1)."
        ) from None


def _digest(workflow: dict) -> str:
    return hashlib.sha256(
        json.dumps(workflow, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _integer(value, low: int, high: int, name: str) -> None:
    if type(value) is not int or not low <= value <= high:
        raise LocalWorkflowPolicyError(f"Invalid local Wan {name}.")


def _filename(value, name: str) -> None:
    if (not isinstance(value, str) or not value or value in (".", "..")
            or any(c in value for c in ("/", "\\", ":", "\x00"))):
        raise LocalWorkflowPolicyError(f"Invalid local Wan {name}.")


def validate_wan_workflow(workflow: dict, output_node: str | None = None) -> str:
    """Compare every node, input, model and link with a reviewed template.

    Only prompt text, dimensions, frame count, seed, input image filename and
    output filename may change. Additional nodes/inputs/metadata are rejected.
    Returns the reviewed template name. No network or model loading occurs.
    """
    if not isinstance(workflow, dict):
        raise LocalWorkflowPolicyError("A local Wan API workflow must be an object.")
    for filename, expected_hash in _REVIEWED_HASHES.items():
        template = json.loads((_WORKFLOWS / filename).read_text(encoding="utf-8"))
        if _digest(template) != expected_hash:
            raise LocalWorkflowPolicyError("Bundled Wan workflow changed; review is required.")
        if set(workflow) != set(template):
            continue
        i2v = filename == "wan22-i2v-4step.json"
        expected_output = "108" if i2v else "16"
        if output_node is not None and str(output_node) != expected_output:
            continue
        prompt_id, latent_id, seed_id = ("93", "98", "86") if i2v else ("2", "11", "12")
        dynamic = {
            prompt_id: {"text"},
            latent_id: {"width", "height", "length"},
            seed_id: {"noise_seed"},
            expected_output: {"filename_prefix"},
        }
        if i2v:
            dynamic["97"] = {"image"}
        normalized = copy.deepcopy(workflow)
        try:
            for node_id, fields in dynamic.items():
                for field in fields:
                    value = workflow[node_id]["inputs"][field]
                    if field == "text":
                        if not isinstance(value, str) or not value.strip():
                            raise LocalWorkflowPolicyError("A nonempty prompt is required.")
                    elif field in ("width", "height"):
                        _integer(value, 16, 8192, field)
                        if value % 16:
                            raise LocalWorkflowPolicyError("Wan dimensions must be multiples of 16.")
                    elif field == "length":
                        _integer(value, 1, 4097, field)
                        if (value - 1) % 4:
                            raise LocalWorkflowPolicyError("Wan frame count must be 4n+1.")
                    elif field == "noise_seed":
                        _integer(value, 0, 2**64 - 1, field)
                    else:
                        _filename(value, field)
                    normalized[node_id]["inputs"][field] = template[node_id]["inputs"][field]
            if normalized == template:
                return filename
        except (KeyError, TypeError):
            continue
    raise LocalWorkflowPolicyError(
        "Only the reviewed bundled Wan 2.2 T2V/I2V graphs are allowed; custom/Partner Nodes are blocked."
    )
