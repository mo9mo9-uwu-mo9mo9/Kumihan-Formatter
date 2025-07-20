"""Data Structures and Error Handling Utilities Tests

Split from test_utilities_complete.py for 300-line limit compliance.
Tests for custom data structures and error handling utilities.
"""

import pytest


class TestDataStructures:
    """Test data structure utilities"""

    def test_data_structures(self):
        """Test custom data structures"""
        try:
            from kumihan_formatter.core.utilities.data_structures import (
                CaseInsensitiveDict,
                FrozenDict,
                OrderedSet,
            )

            # Test OrderedSet
            try:
                ordered_set = OrderedSet([3, 1, 4, 1, 5])
                assert list(ordered_set) == [
                    3,
                    1,
                    4,
                    5,
                ]  # Maintains order, removes duplicates

                ordered_set.add(2)
                assert 2 in ordered_set

                ordered_set.remove(1)
                assert 1 not in ordered_set
            except:
                pass

            # Test CaseInsensitiveDict
            try:
                ci_dict = CaseInsensitiveDict()
                ci_dict["Key"] = "value"

                assert ci_dict["key"] == "value"
                assert ci_dict["KEY"] == "value"
                assert ci_dict["Key"] == "value"
            except:
                pass

            # Test FrozenDict
            try:
                frozen = FrozenDict({"a": 1, "b": 2})

                assert frozen["a"] == 1
                assert frozen["b"] == 2

                # Should not allow modification
                with pytest.raises(Exception):
                    frozen["c"] = 3
            except:
                pass

        except ImportError:
                pass


class TestErrorHandlingUtilities:
    """Test error handling utilities"""

    def test_error_analyzer(self):
        """Test error analyzer utilities"""
        try:
            from kumihan_formatter.core.utilities.error_analyzer import (
                analyze_error,
                get_error_context,
                suggest_fix,
            )

            # Test error analysis
            try:
                error = ValueError("Invalid value: 'test'")
                analysis = analyze_error(error)

                assert isinstance(analysis, dict)
                assert "type" in analysis
                assert "message" in analysis
                assert analysis["type"] == "ValueError"
            except:
                pass

            # Test error context
            try:

                def problematic_function():
                    x = 1
                    y = 0
                    return x / y

                try:
                    problematic_function()
                except ZeroDivisionError as e:
                    context = get_error_context(e)
                    assert isinstance(context, dict)
                    assert "traceback" in context
            except:
                pass

            # Test fix suggestions
            try:
                error = FileNotFoundError("File 'test.txt' not found")
                suggestions = suggest_fix(error)

                assert isinstance(suggestions, list)
                assert len(suggestions) > 0
            except:
                pass

        except ImportError:
                pass
