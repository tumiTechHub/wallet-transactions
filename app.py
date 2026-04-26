"""
MeridianPay — wallet-transactions API
A minimal REST API demonstrating CI/CD pipeline practices.
"""

from flask import Flask, jsonify, request
from datetime import datetime
import uuid

app = Flask(__name__)

# In-memory store (for demo/testing purposes only)
WALLETS = {
    "wallet-001": {"owner": "Alice Dlamini", "balance": 5000.00, "currency": "ZAR"},
    "wallet-002": {"owner": "Bob Nkosi", "balance": 1200.50, "currency": "ZAR"},
}
TRANSACTIONS = []


# ── Health Check ──────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for load balancers and smoke tests."""
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()}), 200


# ── Get Wallet Balance ────────────────────────────────────────────────────────
@app.route("/wallets/<wallet_id>", methods=["GET"])
def get_wallet(wallet_id):
    """Return wallet details for a given wallet ID."""
    wallet = WALLETS.get(wallet_id)
    if not wallet:
        return jsonify({"error": "Wallet not found"}), 404
    return jsonify({"wallet_id": wallet_id, **wallet}), 200


# ── List Transactions ─────────────────────────────────────────────────────────
@app.route("/wallets/<wallet_id>/transactions", methods=["GET"])
def list_transactions(wallet_id):
    """Return all transactions for a wallet."""
    if wallet_id not in WALLETS:
        return jsonify({"error": "Wallet not found"}), 404
    txns = [t for t in TRANSACTIONS if t["wallet_id"] == wallet_id]
    return jsonify({"wallet_id": wallet_id, "transactions": txns}), 200


# ── Create Transaction ────────────────────────────────────────────────────────
@app.route("/wallets/<wallet_id>/transactions", methods=["POST"])
def create_transaction(wallet_id):
    """
    Create a debit or credit transaction on a wallet.
    Body: { "type": "debit"|"credit", "amount": float, "description": str }
    """
    wallet = WALLETS.get(wallet_id)
    if not wallet:
        return jsonify({"error": "Wallet not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    txn_type = data.get("type")
    amount = data.get("amount")
    description = data.get("description", "")

    if txn_type not in ("debit", "credit"):
        return jsonify({"error": "type must be 'debit' or 'credit'"}), 400
    if not isinstance(amount, (int, float)) or amount <= 0:
        return jsonify({"error": "amount must be a positive number"}), 400

    if txn_type == "debit" and wallet["balance"] < amount:
        return jsonify({"error": "Insufficient funds"}), 422

    # Apply transaction
    if txn_type == "debit":
        wallet["balance"] -= amount
    else:
        wallet["balance"] += amount

    txn = {
        "id": str(uuid.uuid4()),
        "wallet_id": wallet_id,
        "type": txn_type,
        "amount": amount,
        "description": description,
        "timestamp": datetime.utcnow().isoformat(),
        "balance_after": wallet["balance"],
    }
    TRANSACTIONS.append(txn)

    return jsonify(txn), 201


# ── Summary ───────────────────────────────────────────────────────────────────
@app.route("/wallets/<wallet_id>/summary", methods=["GET"])
def wallet_summary(wallet_id):
    """Return a summary: total credits, total debits, transaction count."""
    if wallet_id not in WALLETS:
        return jsonify({"error": "Wallet not found"}), 404

    txns = [t for t in TRANSACTIONS if t["wallet_id"] == wallet_id]
    total_credit = sum(t["amount"] for t in txns if t["type"] == "credit")
    total_debit = sum(t["amount"] for t in txns if t["type"] == "debit")

    return jsonify({
        "wallet_id": wallet_id,
        "transaction_count": len(txns),
        "total_credit": total_credit,
        "total_debit": total_debit,
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
