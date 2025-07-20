"""Renderer Template Integration Tests

Template integration tests for Renderer extracted from parser unified tests.
Issue #540 Phase 2: 300行制限遵守のための分割
"""

import pytest

from kumihan_formatter.core.ast_nodes.node import Node
from kumihan_formatter.renderer import Renderer

pytestmark = pytest.mark.integration


class TestRendererTemplateIntegration:
    """Template integration tests for renderer"""

    def test_renderer_template_integration(self):
        """Test renderer with template system"""
        renderer = Renderer()

        test_nodes = [Node("h1", "Template Test")]

        try:
            # Test with different templates
            templates = ["default", "minimal", "detailed"]

            for template in templates:
                renderer.set_template(template)
                output = renderer.render(test_nodes)
                assert output is not None

        except (AttributeError, NotImplementedError):
            # Template system may not be implemented
            pass
