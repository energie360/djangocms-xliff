from importlib.metadata import PackageNotFoundError, version
from packaging.version import parse


try:
    cms_version = version("django-cms")
    IS_CMS_V4_PLUS = parse(cms_version) >= parse("4.0.0")
except PackageNotFoundError:
    IS_CMS_V4_PLUS = False

try:
    IS_ALIAS_INSTALLED = bool(version("djangocms-alias"))
except PackageNotFoundError:
    IS_ALIAS_INSTALLED = False