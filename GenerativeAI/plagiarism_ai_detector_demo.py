import math
import re
from collections import Counter
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Ensure NLTK tokenizers are downloaded
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)


# ==========================================
# 1. PLAGIARISM DETECTOR
# ==========================================
class PlagiarismChecker:
    def __init__(self, threshold=0.7):
        self.threshold = threshold

    def _preprocess(self, text: str) -> str:
        """Clean and normalize text."""
        text = text.lower()
        text = re.sub(r"[^\w\s]", "", text)
        return text

    def check_similarity(self, doc_a: str, doc_b: str) -> dict:
        """Calculates Cosine Similarity between two texts using TF-IDF."""
        clean_a = self._preprocess(doc_a)
        clean_b = self._preprocess(doc_b)

        vectorizer = TfidfVectorizer().fit_transform([clean_a, clean_b])
        vectors = vectorizer.toarray()

        # Calculate cosine similarity score
        similarity_score = float(cosine_similarity([vectors[0]], [vectors[1]])[0][0])
        is_plagiarized = similarity_score >= self.threshold

        return {
            "source_text": doc_a,
            "test_text": doc_b,
            "similarity_score": round(similarity_score * 100, 2),
            "is_plagiarized": is_plagiarized,
            "threshold": self.threshold * 100,
        }


# ==========================================
# 2. HEURISTIC AI GENERATION DETECTOR
# ==========================================
class AIDetector:
    """Analyzes Perplexity (predictability) and Burstiness (variance in sentence complexity)

    to flag likely AI-generated text.
    """

    def _calculate_perplexity(self, text: str) -> float:
        """Estimates text perplexity using unigram word distribution entropy.

        Lower score = predictable vocabulary (typical of AI).
        """
        words = word_tokenize(text.lower())
        words = [w for w in words if w.isalnum()]

        if not words:
            return 0.0

        total_words = len(words)
        freqs = Counter(words)

        # Shannon Entropy formula
        entropy = -sum(
            (count / total_words) * math.log2(count / total_words)
            for count in freqs.values()
        )
        perplexity = 2**entropy
        return perplexity

    def _calculate_burstiness(self, text: str) -> float:
        """Measures variance in sentence length.

        Lower variance = uniform sentence structure (typical of AI).
        """
        sentences = sent_tokenize(text)
        if len(sentences) <= 1:
            return 0.0

        lengths = [len(word_tokenize(s)) for s in sentences]
        mean_length = sum(lengths) / len(lengths)

        if mean_length == 0:
            return 0.0

        variance = sum((x - mean_length) ** 2 for x in lengths) / len(lengths)
        std_dev = math.sqrt(variance)

        # Coefficient of Variation (Burstiness metric)
        burstiness = std_dev / mean_length
        return burstiness

    def analyze_text(self, text: str) -> dict:
        perplexity = self._calculate_perplexity(text)
        burstiness = self._calculate_burstiness(text)

        # Heuristic scoring threshold based on statistical norms
        # AI text generally scores lower in both perplexity and burstiness
        is_ai_likely = perplexity < 45.0 and burstiness < 0.45

        return {
            "analyzed_text": text,
            "perplexity_score": round(perplexity, 2),
            "burstiness_score": round(burstiness, 2),
            "is_ai_generated": is_ai_likely,
            "confidence_assessment": (
                "High probability of AI generation"
                if is_ai_likely
                else "Likely human-written"
            ),
        }


# ==========================================
# EXAMPLE USAGE
# ==========================================
if __name__ == "__main__":
    # Sample Documents for Plagiarism Check
    source_doc = "Artificial Intelligence is transforming how we write code, analyze data, and build applications."
    test_doc = ("Artificial Intelligence is completely transforming how developers write code, analyze data, "
                "and build web applications.")

    # Sample Document for AI Detection
    ai_sample = (
        "Artificial intelligence has revolutionized modern technology. "
        "\n\t\t\t\t   It provides efficient solutions to complex problems. "
        "\n\t\t\t\t   Many businesses adopt machine learning to optimize daily workflows. "
        "\n\t\t\t\t   Furthermore, automated systems improve overall productivity continuously."
    )

    print("=== 1. PLAGIARISM CHECK RESULTS ===")
    plag_checker = PlagiarismChecker(threshold=0.65)
    plag_result = plag_checker.check_similarity(source_doc, test_doc)
    print(f"Source Input:     \"{plag_result['source_text']}\"")
    print(f"Test Input:       \"{plag_result['test_text']}\"")
    print(f"Similarity Score: {plag_result['similarity_score']}%")
    print(f"Plagiarism Detected: {plag_result['is_plagiarized']}\n")

    print("=== 2. AI GENERATION DETECTION RESULTS ===")
    ai_detector = AIDetector()
    ai_result = ai_detector.analyze_text(ai_sample)
    print(f"Analyzed Input:   \"{ai_result['analyzed_text']}\"")
    print(f"Perplexity Score: {ai_result['perplexity_score']}")
    print(f"Burstiness Score: {ai_result['burstiness_score']}")
    print(f"Result:           {ai_result['confidence_assessment']}")