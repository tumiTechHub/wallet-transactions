"""
Unit tests for the MeridianPay wallet-transactions API.
Run with: pytest tests/ -v --cov=app --cov-report=term-missing
"""

import pytest
from app import app, WALLETS, TRANSACTIONS


@pytest.fixture(autouse=True)
def reset_state():
    """Reset in-memory state before each test to ensure test isolation."""
    WALLETS.clear()
    WALLETS.update({
        "wallet-001": {"owner": "Alice Dlamini", "balance": 5000.00, "currency": "ZAR"},
        "wallet-002": {"owner": "Bob Nkosi", "balance": 1200.50, "currency": "ZAR"},
    })
    TRANSACTIONS.clear()
    yield


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ── Health Check ──────────────────────────────────────────────────────────────

def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert "timestamp" in data


# ── Get Wallet ────────────────────────────────────────────────────────────────

def test_get_wallet_found(client):
    resp = client.get("/wallets/wallet-001")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["wallet_id"] == "wallet-001"
    assert data["owner"] == "Alice Dlamini"
    assert data["balance"] == 5000.00


def test_get_wallet_not_found(client):
    resp = client.get("/wallets/wallet-999")
    assert resp.status_code == 404
    assert "error" in resp.get_json()


# ── List Transactions ─────────────────────────────────────────────────────────

def test_list_transactions_empty(client):
    resp = client.get("/wallets/wallet-001/transactions")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["transactions"] == []


def test_list_transactions_invalid_wallet(client):
    resp = client.get("/wallets/wallet-999/transactions")
    assert resp.status_code == 404


# ── Create Transaction ────────────────────────────────────────────────────────

def test_credit_transaction_success(client):
    resp = client.post(
        "/wallets/wallet-001/transactions",
        json={"type": "credit", "amount": 500.0, "description": "Top-up"},
        content_type="application/json"
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["type"] == "credit"
    assert data["amount"] == 500.0
    assert data["balance_after"] == 5500.0


def test_debit_transaction_success(client):
    resp = client.post(
        "/wallets/wallet-001/transactions",
        json={"type": "debit", "amount": 100.0, "description": "Purchase"},
        content_type="application/json"
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["balance_after"] == 4900.0


def test_debit_insufficient_funds(client):
    resp = client.post(
        "/wallets/wallet-001/transactions",
        json={"type": "debit", "amount": 99999.0, "description": "Too much"},
        content_type="application/json"
    )
    assert resp.status_code == 422
    assert "Insufficient funds" in resp.get_json()["error"]


def test_transaction_invalid_type(client):
    resp = client.post(
        "/wallets/wallet-001/transactions",
        json={"type": "transfer", "amount": 100.0},
        content_type="application/json"
    )
    assert resp.status_code == 400


def test_transaction_negative_amount(client):
    resp = client.post(
        "/wallets/wallet-001/transactions",
        json={"type": "credit", "amount": -50.0},
        content_type="application/json"
    )
    assert resp.status_code == 400


def test_transaction_missing_body(client):
    resp = client.post("/wallets/wallet-001/transactions", content_type="application/json")
    assert resp.status_code == 400


def test_transaction_wallet_not_found(client):
    resp = client.post(
        "/wallets/wallet-999/transactions",
        json={"type": "credit", "amount": 100.0},
        content_type="application/json"
    )
    assert resp.status_code == 404


# ── Wallet Summary ────────────────────────────────────────────────────────────

def test_wallet_summary_empty(client):
    resp = client.get("/wallets/wallet-001/summary")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["transaction_count"] == 0
    assert data["total_credit"] == 0
    assert data["total_debit"] == 0


def test_wallet_summary_after_transactions(client):
    client.post("/wallets/wallet-001/transactions",
                json={"type": "credit", "amount": 300.0}, content_type="application/json")
    client.post("/wallets/wallet-001/transactions",
                json={"type": "debit", "amount": 100.0}, content_type="application/json")

    resp = client.get("/wallets/wallet-001/summary")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["transaction_count"] == 2
    assert data["total_credit"] == 300.0
    assert data["total_debit"] == 100.0


def test_wallet_summary_not_found(client):
    resp = client.get("/wallets/wallet-999/summary")
    assert resp.status_code == 404
