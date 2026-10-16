"""Compatibility entry: spirits live in the shared queue editor."""
class SpiritWindow(object):
    def __new__(cls, onChange=None):
        from uimetinqueuedesigneditor import MetinQueueDesignEditor
        return MetinQueueDesignEditor()
