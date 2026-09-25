"""Fixed provider child. Start only through the separately approved authority host.

No SQL writer, provider retry, discovery, arbitrary endpoint or credential argument
is accepted over IPC. Creation requires the separate protected enrollment profile.
Importing the module performs no external action.
"""

import argparse
import json
from pathlib import Path
from urllib.parse import quote


def bootstrap(manifest_path):
    import runpy

    launcher = Path(__file__).absolute().with_name("run_export_authority.py")
    runpy.run_path(str(launcher))["bootstrap"](manifest_path, script=__file__)


def execute_http(request, *, session, credentials, refresh_request, enrollment=False):
    from services.export_execution_protocol import (
        ProtocolError,
        ProviderThrottled,
        validate_response,
    )

    arguments = request.arguments
    body = arguments.pop("body", None)
    target = quote(request.target, safe="")
    if request.operation == "sheets.create":
        if not enrollment:
            raise ProtocolError("Creation requires the separate enrollment credential profile.")
        arguments.pop("plan_id")
        arguments.pop("ordinal")
        url = "https://sheets.googleapis.com/v4/spreadsheets"
        method = "POST"
    elif request.operation.startswith("sheets."):
        url = "https://sheets.googleapis.com/v4/spreadsheets/" + target
        method = "GET"
        if request.operation == "sheets.batchUpdate":
            url += ":batchUpdate"
            method = "POST"
        elif request.operation == "sheets.values.batchGet":
            url += "/values:batchGet"
        elif request.operation.startswith("sheets.values."):
            url += "/values/" + quote(arguments.pop("range"), safe="")
            if request.operation == "sheets.values.update":
                method = "PUT"
            elif request.operation == "sheets.values.clear":
                url += ":clear"
                method = "POST"
        if request.operation == "sheets.get" and "fields" in arguments:
            arguments["fields"] += ",spreadsheetId"
    else:
        url = "https://www.googleapis.com/drive/v3/files/" + target
        method = "GET"
        if request.operation == "drive.files.update":
            method = "PATCH"
        elif request.operation.startswith("drive.permissions."):
            url += "/permissions"
            if request.operation == "drive.permissions.create":
                method = "POST"
            elif request.operation == "drive.permissions.delete":
                url += "/" + quote(arguments.pop("permissionId"), safe="")
                method = "DELETE"
        if request.operation.startswith("drive.files.") and "fields" in arguments:
            arguments["fields"] += ",id"
    # Refresh authentication before the sole export send. Do not use an
    # AuthorizedSession/SDK that can replay a mutation after a 401 response.
    if not credentials.valid:
        credentials.refresh(refresh_request)
    if enrollment and set(credentials.granted_scopes or ()) != {
        "https://www.googleapis.com/auth/drive.file"
    }:
        raise ProtocolError("Narrow enrollment token scope was not confirmed; no provider send.")
    response = session.request(
        method,
        url,
        params=arguments,
        json=body,
        headers={"Authorization": "Bearer " + credentials.token},
        timeout=(10, 30),
        allow_redirects=False,
    )
    try:
        expected = 204 if request.operation == "drive.permissions.delete" else 200
        if response.status_code in (429, 503):
            raise ProviderThrottled.from_header(
                response.status_code, response.headers.get("Retry-After")
            )
        if response.status_code != expected:
            raise ProtocolError("Provider returned an unproven terminal outcome.")
        result = None if expected == 204 else response.json()
        validate_response(request, result)
        return result
    finally:
        response.close()


def provider_credentials(document, manifest):
    """Construct credentials from explicitly supplied bytes; this never reads a file."""
    if document.get("token_uri") != "https://oauth2.googleapis.com/token":
        raise ValueError("Unsupported token endpoint.")
    if "enrollment_profile" in manifest:
        from google.oauth2.credentials import Credentials

        from services.export_runtime_composition import enrollment_profile

        profile = enrollment_profile(manifest["enrollment_profile"])
        if (
            set(document)
            != {"type", "client_id", "client_secret", "refresh_token", "token_uri", "scopes"}
            or document["type"] != "authorized_user"
            or document["client_id"] != profile["client_id"]
            or document["scopes"] != profile["scopes"]
            or any(
                not isinstance(document[k], str) or not 0 < len(document[k]) <= 16384
                for k in ("client_secret", "refresh_token")
            )
        ):
            raise ValueError("Exact separately provisioned enrollment credential required.")
        return Credentials.from_authorized_user_info(document, scopes=profile["scopes"])
    from google.oauth2.service_account import Credentials

    identity = manifest["deployment_boundary"]["identity"]
    if any(document.get(k) != identity[k] for k in ("client_id", "private_key_id")):
        raise ValueError("Credential key differs from reviewed authority custody.")

    credentials = Credentials.from_service_account_info(
        document,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    if (
        credentials.service_account_email != manifest["service_account_email"]
        or credentials.project_id != manifest["project_id"]
    ):
        raise ValueError("Provider account differs from immutable registration.")
    return credentials


def main(argv=None):
    parser = argparse.ArgumentParser(description="Supervised K98 provider child; G4 only")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--pipe", required=True)
    parser.add_argument("--child-id", required=True)
    args = parser.parse_args(argv)
    bootstrap(args.manifest)
    from core.export_execution_host import (
        MessagePipe,
        assert_protected_path,
        current_sid,
        open_message_pipe,
    )
    from services.export_execution_protocol import (
        ProviderRequest,
        ProviderThrottled,
        decode,
        uuid_text,
    )

    manifest_path = assert_protected_path(args.manifest, private=True)
    assert_protected_path(Path(__file__).resolve())
    manifest = decode(manifest_path.read_bytes())
    expected_version = 1 if "enrollment_profile" in manifest else 2
    if (
        manifest.get("version") != expected_version
        or manifest.get("authority_sid") != current_sid()
    ):
        raise ValueError("Exact authority identity/protocol required.")
    uuid_text(args.child_id)
    if args.pipe != "\\\\.\\pipe\\K98Export-" + args.child_id:
        raise ValueError("Exact child pipe identity required.")
    credentials_path = assert_protected_path(manifest["credentials_file"], private=True)
    raw = credentials_path.read_bytes()
    if "enrollment_profile" not in manifest:
        import hashlib

        if (
            hashlib.sha256(raw).hexdigest()
            != manifest["deployment_boundary"]["identity"]["credential_sha256"]
        ):
            raise ValueError("Credential bytes differ from reviewed authority custody.")
    credential_document = json.loads(raw)
    from google.auth.transport.requests import Request
    import requests

    credentials = provider_credentials(credential_document, manifest)
    enrollment = "enrollment_profile" in manifest
    http = requests.Session()
    http.trust_env = False
    authentication = requests.Session()
    authentication.trust_env = False
    handle = open_message_pipe(args.pipe)
    pipe = MessagePipe(handle)
    pipe.send({"version": 1, "child_id": args.child_id})
    try:
        while True:
            message = pipe.receive()
            request = ProviderRequest.parse(message, enrollment=enrollment)
            try:
                result = execute_http(
                    request,
                    session=http,
                    credentials=credentials,
                    refresh_request=Request(session=authentication),
                    enrollment=enrollment,
                )
            except ProviderThrottled as exc:
                # Feedback only: exit without retrying or claiming non-delivery.
                pipe.send(exc.message(request.request_id))
                return 1
            except Exception:
                # No provider prose, token, content or automatic retry crosses
                # the boundary. Exit; the authority retains dispatch_intent.
                pipe.send({"request_id": request.request_id, "error": "unproven_outcome"})
                return 1
            pipe.send({"request_id": request.request_id, "result": result})
    finally:
        handle.Close()
        http.close()
        authentication.close()


if __name__ == "__main__":
    raise SystemExit(main())
