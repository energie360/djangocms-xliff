#  type: ignore
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from tests.models import (
    TestChildModel,
    TestMultipleFieldsModel,
    TestOneFieldModel,
    TestParentModel,
)

TEST_TEMPLATE = "testing.html"


@plugin_pool.register_plugin
class TestOneFieldPlugin(CMSPluginBase):
    model = TestOneFieldModel
    name = "Test one field plugin"
    render_template = TEST_TEMPLATE


@plugin_pool.register_plugin
class TestMultipleFieldsPlugin(CMSPluginBase):
    model = TestMultipleFieldsModel
    name = "Test multiple fields plugin"
    render_template = TEST_TEMPLATE


@plugin_pool.register_plugin
class TestParentPlugin(CMSPluginBase):
    model = TestParentModel
    name = "Test parent plugin"
    render_template = "testing.html"
    allow_children = True
    child_classes = TEST_TEMPLATE


@plugin_pool.register_plugin
class TestChildPlugin(CMSPluginBase):
    model = TestChildModel
    name = "Test child plugin"
    render_template = "testing.html"
    require_parent = True
    parent_classes = TEST_TEMPLATE
