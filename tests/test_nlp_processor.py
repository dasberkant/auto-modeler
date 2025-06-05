"""Tests for the NLP processor module."""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.nlp_processor import NLPProcessor


class TestNLPProcessor(unittest.TestCase):
    """Test cases for NLPProcessor class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.processor = NLPProcessor()

    def test_initialization(self):
        """Test that NLPProcessor initializes correctly."""
        self.assertIsInstance(self.processor, NLPProcessor)

    @patch('app.nlp_processor.genai')
    def test_process_problem_statement(self, mock_genai):
        """Test processing of a simple problem statement."""
        # Mock the API response
        mock_response = Mock()
        mock_response.text = "Test problem analysis"
        mock_genai.generate_text.return_value = mock_response
        
        problem_statement = "Maximize profit from producing widgets."
        result = self.processor.process_problem_statement(problem_statement)
        
        self.assertIsNotNone(result)
        # Add more specific assertions based on your implementation

    def test_empty_problem_statement(self):
        """Test handling of empty problem statement."""
        with self.assertRaises(ValueError):
            self.processor.process_problem_statement("")

    def test_invalid_problem_statement(self):
        """Test handling of invalid problem statement."""
        with self.assertRaises(ValueError):
            self.processor.process_problem_statement(None)


if __name__ == '__main__':
    unittest.main() 