#!/usr/bin/env python3
"""Pruebas unitarias para el servidor MCP 'op-sandbox'."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

# Asegurar path para importar el modulo de scripts
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

import importlib.util

spec = importlib.util.spec_from_file_location(
    "mcp_op_sandbox", os.path.join(REPO_ROOT, "scripts", "mcp-op-sandbox.py")
)
mcp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp)


class TestOpSandbox(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.audit_log = os.path.join(self.temp_dir.name, "audit.log")
        os.environ["OP_SANDBOX_AUDIT_LOG"] = self.audit_log

    def tearDown(self):
        self.temp_dir.cleanup()
        if "OP_SANDBOX_AUDIT_LOG" in os.environ:
            del os.environ["OP_SANDBOX_AUDIT_LOG"]

    def test_allowlist_permits_localhost_and_testnet(self):
        valid_urls = [
            "http://127.0.0.1:3000/accounts/alice",
            "http://127.0.0.1:4000/accounts/bob",
            "http://localhost:3000/open-payments",
            "https://wallet.ilp.rafiki.money/alice",
            "https://test.interledger.org/peer",
        ]
        for url in valid_urls:
            allowed, reason = mcp.is_url_allowed(url)
            self.assertTrue(allowed, f"La URL debería ser permitida: {url} ({reason})")

    def test_allowlist_rejects_external_and_unauthorized_urls(self):
        invalid_urls = [
            "https://google.com/api",
            "https://paypal.com/checkout",
            "http://192.168.1.1/router",
            "ftp://127.0.0.1/resource",
            "https://attacker-rafiki.com",
            "",
            None,
        ]
        for url in invalid_urls:
            allowed, reason = mcp.is_url_allowed(url)
            self.assertFalse(allowed, f"La URL debería ser rechazada: {url}")

    def test_reject_float_amounts(self):
        res_float = mcp.handle_create_test_incoming_payment(
            {
                "wallet_address_url": "http://127.0.0.1:3000/accounts/alice",
                "amount": "100.50",
                "asset_code": "USD",
                "asset_scale": 2,
            }
        )
        self.assertTrue(res_float["isError"])
        self.assertIn("float", res_float["content"][0]["text"].lower())

        res_valid = mcp.handle_create_test_incoming_payment(
            {
                "wallet_address_url": "http://127.0.0.1:3000/accounts/alice",
                "amount": "10050",
                "asset_code": "USD",
                "asset_scale": 2,
            }
        )
        self.assertFalse(res_valid["isError"])
        payload = json.loads(res_valid["content"][0]["text"])
        self.assertEqual(payload["incomingAmount"]["value"], "10050")
        self.assertEqual(payload["state"], "PENDING")

    def test_audit_logging_writes_entries(self):
        mcp.handle_verify_wallet_address({"wallet_address_url": "https://malicious.com"})
        self.assertTrue(os.path.exists(self.audit_log))
        with open(self.audit_log, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertGreater(len(lines), 0)
        last_event = json.loads(lines[-1])
        self.assertEqual(last_event["tool"], "verify_wallet_address")
        self.assertFalse(last_event["allowlist_passed"])
        self.assertEqual(last_event["status"], "BLOCKED")

    def test_json_rpc_protocol_flow(self):
        script_path = os.path.join(REPO_ROOT, "scripts", "mcp-op-sandbox.py")
        p = subprocess.Popen(
            [sys.executable, script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ,
        )

        # 1. Initialize
        init_req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        # 2. Tools list
        tools_req = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        # 3. Tool call
        call_req = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "create_test_incoming_payment",
                    "arguments": {
                        "wallet_address_url": "http://127.0.0.1:3000/accounts/alice",
                        "amount": "5000",
                        "asset_code": "USD",
                        "asset_scale": 2,
                    },
                },
            }
        )

        input_data = f"{init_req}\n{tools_req}\n{call_req}\n"
        stdout_data, stderr_data = p.communicate(input=input_data, timeout=5)

        responses = [json.loads(line) for line in stdout_data.strip().splitlines() if line.strip()]
        self.assertEqual(len(responses), 3)
        self.assertEqual(responses[0]["id"], 1)
        self.assertEqual(responses[1]["id"], 2)
        tools = responses[1]["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        self.assertIn("verify_wallet_address", tool_names)
        self.assertIn("create_test_incoming_payment", tool_names)
        self.assertIn("inspect_payment_state", tool_names)

        self.assertEqual(responses[2]["id"], 3)
        self.assertFalse(responses[2]["result"]["isError"])


if __name__ == "__main__":
    unittest.main()
