"""
Test suite for rule engine
"""
import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from modules.rule_engine import RuleEngine


@pytest.fixture
def rule_engine():
    """Create rule engine instance"""
    return RuleEngine(
        rules_path="data/rules.json",
        faqs_path="data/faqs.json"
    )


def test_exact_match(rule_engine):
    """Test exact FAQ matching"""
    result = rule_engine.match("What is Doc QA Bot?")
    assert result is not None
    answer, confidence, sources = result
    assert confidence == 1.0
    assert len(answer) > 0


def test_keyword_match(rule_engine):
    """Test keyword-based matching"""
    result = rule_engine.match("how to start the system")
    assert result is not None
    answer, confidence, sources = result
    assert confidence > 0.7


def test_pattern_match(rule_engine):
    """Test regex pattern matching"""
    result = rule_engine.match("how to install this thing")
    assert result is not None
    answer, confidence, sources = result
    assert confidence >= 0.8


def test_no_match(rule_engine):
    """Test query with no match"""
    result = rule_engine.match("ksjdhfksjdhf xyz 123")
    assert result is None


def test_add_faq(rule_engine):
    """Test adding new FAQ"""
    rule_engine.add_faq(
        questions=["Test question?"],
        answer="Test answer",
        keywords=["test"],
        source="test"
    )
    
    result = rule_engine.match("Test question?")
    assert result is not None


def test_stats(rule_engine):
    """Test getting stats"""
    stats = rule_engine.get_stats()
    assert stats['total_faqs'] > 0
    assert 'total_rules' in stats
    assert 'keywords_indexed' in stats
