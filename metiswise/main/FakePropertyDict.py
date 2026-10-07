class FakePropertyDict(dict):
    """Fake PropertyDict from oraclesupport.

    A classcache is also necessary when there is no database backend. For
    example, FITS files can include the class they represent as a header
    keyword. The classcache is used to lookup the Python class. However, this
    is not supported in DBFilebased, and thus implemented here.

    TODO: Implement this in DBFilebased.
    """

    def __init__(self, aclass):
        """Initialize: use dictionary key also as attribute.

        This mimics the behaviour of PropertyDict.
        """
        super().__init__()
        self.aclass = aclass
