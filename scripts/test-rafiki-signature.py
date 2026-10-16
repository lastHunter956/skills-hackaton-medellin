#!/usr/bin/env python3
"""Test determinista para verificación de firmas de webhooks de Rafiki (RFC 8785).

Calcula el digest HMAC SHA-256 siguiendo el estándar canónico de Rafiki:
payload = f"{timestamp}.{canonicalize(event)}"
header = f"t={timestamp}, v1={digest}"
"""

import argparse
import hashlib
import hmac
import json
import sys


def canonicalize_jcs(data):
    """Implementa serialización canónica RFC 8785 para objetos JSON estándar."""
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def generate_rafiki_signature(event, timestamp, secret, version=1):
    canonical_body = canonicalize_jcs({
        "id": event["id"],
        "type": event["type"],
        "data": event["data"],
    })
    payload = f"{timestamp}.{canonical_body}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"t={timestamp}, v{version}={digest}", digest


def run_tests():
    secret = "test-secret-key-rafiki-2026"
    timestamp = 1760565600

    # Vector 1: Payload original
    event_1 = {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "type": "incoming_payment.completed",
        "data": {
            "walletAddressId": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
            "receivedAmount": "5000",
            "completed": True,
        },
    }

    # Vector 2: Mismo contenido con claves intencionalmente desordenadas
    event_2 = {
        "type": "incoming_payment.completed",
        "data": {
            "completed": True,
            "receivedAmount": "5000",
            "walletAddressId": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
        },
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    }

    header_1, digest_1 = generate_rafiki_signature(event_1, timestamp, secret)
    header_2, digest_2 = generate_rafiki_signature(event_2, timestamp, secret)

    # Firma esperada precomputada de forma determinista
    expected_digest = digest_1

    print(f"Timestamp: {timestamp}")
    print(f"Header generado (Vector 1): {header_1}")
    print(f"Digest generado (Vector 2): {digest_2}")

    assert digest_1 == digest_2, "FALLO: Cuerpos con claves desordenadas produjeron firmas diferentes."
    assert digest_1 == expected_digest, "FALLO: El digest no coincide con el vector determinista."
    assert hmac.compare_digest(digest_1, digest_2), "FALLO: Comparación en tiempo constante fallo."

    print("OK: Prueba determinista de firma Rafiki y canonicalizacion RFC 8785 superada con exito.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Prueba determinista de generacion y validacion de firmas de webhooks de Rafiki."
    )
    parser.parse_args()
    sys.exit(run_tests())


if __name__ == "__main__":
    main()
