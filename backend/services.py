import random
import pdfplumber


class RuleBasedScorer:
    """
    Production-ready rule-based creditworthiness scorer for KeyCred.

    Phase 1: Mock data extraction from PDF, robust mathematical scoring.
    The algorithm evaluates a tenant's financial reliability based on
    income, balance, payment behaviour, and risk indicators.
    """

    BASE_SCORE = 400
    MAX_SCORE = 1000
    MIN_SCORE = 0
    DEFAULT_TARGET_RENT = 15_000  # TRY

    # ── Mock data generation ──────────────────────────────────────────

    @staticmethod
    def _generate_mock_data() -> dict:
        """Generate realistic mock financial parameters."""
        monthly_income = round(random.uniform(12_000, 65_000), 2)
        current_balance = round(random.uniform(2_000, 120_000), 2)
        regular_support_income = random.choice([True, False])
        utility_bills_paid = random.randint(0, 3)
        credit_card_repayment_ratio = round(random.uniform(0.1, 1.0), 2)
        overdraft_usage = random.choices([True, False], weights=[15, 85])[0]
        high_risk_transactions = random.choices([True, False], weights=[5, 95])[0]
        cash_advance_reliance = random.choices([True, False], weights=[10, 90])[0]

        return {
            "monthly_income": monthly_income,
            "current_balance": current_balance,
            "regular_support_income": regular_support_income,
            "utility_bills_paid": utility_bills_paid,
            "credit_card_repayment_ratio": credit_card_repayment_ratio,
            "overdraft_usage": overdraft_usage,
            "high_risk_transactions": high_risk_transactions,
            "cash_advance_reliance": cash_advance_reliance,
        }

    # ── Scoring rules ─────────────────────────────────────────────────

    @staticmethod
    def _score_income_vs_rent(income: float, target_rent: float) -> int:
        ratio = income / target_rent if target_rent > 0 else 0
        if ratio >= 3:
            return 200
        elif ratio >= 2:
            return 100
        else:
            return -150

    @staticmethod
    def _score_balance(balance: float, target_rent: float) -> int:
        return 100 if balance > 3 * target_rent else 0

    @staticmethod
    def _score_support(has_support: bool) -> int:
        return 100 if has_support else 0

    @staticmethod
    def _score_utility_bills(bills_paid: int) -> int:
        return min(bills_paid, 3) * 30  # max +90

    @staticmethod
    def _score_cc_repayment(ratio: float) -> int:
        if ratio > 0.8:
            return 100
        elif ratio < 0.4:
            return -100
        return 0

    @staticmethod
    def _score_overdraft(usage: bool) -> int:
        return -150 if usage else 0

    @staticmethod
    def _score_cash_advance(reliance: bool) -> int:
        return -100 if reliance else 0

    @staticmethod
    def _score_high_risk(has_risk: bool) -> int:
        return -300 if has_risk else 0

    # ── Max rent limit ────────────────────────────────────────────────

    @staticmethod
    def _calculate_max_rent_limit(income: float, balance: float) -> float:
        limit = income * 0.40
        if balance > 50_000:
            limit += balance * 0.05
        return round(limit, 2)

    # ── Risk level ────────────────────────────────────────────────────

    @staticmethod
    def _determine_risk_level(score: int) -> str:
        if score >= 750:
            return "LOW"
        elif score >= 500:
            return "MEDIUM"
        return "HIGH"

    # ── Main scoring method ───────────────────────────────────────────

    def score(self, pdf_path: str, target_rent: float | None = None) -> dict:
        """
        Analyse a bank receipt PDF and return a creditworthiness report.

        Parameters
        ----------
        pdf_path : str
            Path to the uploaded PDF.
        target_rent : float, optional
            Target rent amount in TRY. Defaults to 15 000.
        """
        if target_rent is None:
            target_rent = self.DEFAULT_TARGET_RENT

        # Attempt to open the PDF (proves pdfplumber works)
        page_count = 0
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)
        except Exception:
            page_count = 0

        # Phase 1: mock extraction
        params = self._generate_mock_data()

        # ── Apply scoring rules ──
        adjustments = {
            "income_vs_rent": self._score_income_vs_rent(params["monthly_income"], target_rent),
            "balance": self._score_balance(params["current_balance"], target_rent),
            "support_income": self._score_support(params["regular_support_income"]),
            "utility_bills": self._score_utility_bills(params["utility_bills_paid"]),
            "cc_repayment": self._score_cc_repayment(params["credit_card_repayment_ratio"]),
            "overdraft": self._score_overdraft(params["overdraft_usage"]),
            "cash_advance": self._score_cash_advance(params["cash_advance_reliance"]),
            "high_risk": self._score_high_risk(params["high_risk_transactions"]),
        }

        total_adjustment = sum(adjustments.values())
        raw_score = self.BASE_SCORE + total_adjustment
        keycred_score = max(self.MIN_SCORE, min(self.MAX_SCORE, raw_score))

        # ── Derived fields ──
        max_rent_limit = self._calculate_max_rent_limit(
            params["monthly_income"], params["current_balance"]
        )
        is_approved = keycred_score >= 650
        risk_level = self._determine_risk_level(keycred_score)

        return {
            "keycred_score": keycred_score,
            "max_rent_limit": max_rent_limit,
            "is_approved": is_approved,
            "risk_level": risk_level,
            "pages_parsed": page_count,
            "status": "completed",
            "score_breakdown": adjustments,
            "mocked_parameters": params,
        }
