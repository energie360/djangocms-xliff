class XliffError(Exception):
    pass


class XliffConfigurationError(XliffError):
    pass


class XliffImportError(XliffError):
    pass


class XliffExportError(XliffError):
    pass
