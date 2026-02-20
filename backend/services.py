import random
import pdfplumber


class RuleBasedScorer:
    """
    A dummy scorer that mocks parsing a Turkish bank receipt PDF
    and returns a mock keycred_score and max_rent_limit.
    """

    def score(self, pdf_path: str) -> dict:
        # Attempt to open the PDF to prove pdfplumber works
        page_count = 0
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)
        except Exception:
            page_count = 0

        # Generate a realistic-looking mock score
        base_score = 780
        variation = random.randint(-30, 30)
        keycred_score = max(300, min(900, base_score + variation))

        # Derive max rent limit from score
        max_rent_limit = round((keycred_score / 900) * 30000, -2)

        return {
            "keycred_score": keycred_score,
            "max_rent_limit": max_rent_limit,
            "pages_parsed": page_count,
            "status": "completed",
        }
