from PyQt6.QtGui import QUndoCommand

class AddDictItemCommand(QUndoCommand):
    def __init__(self, target_dict, key, value, description, signal=None):
        super().__init__(description)
        self.target_dict = target_dict
        self.key = key
        self.value = value
        self.signal = signal

    def redo(self):
        self.target_dict[self.key] = self.value
        if self.signal:
            self.signal.emit()

    def undo(self):
        if self.key in self.target_dict:
            del self.target_dict[self.key]
        if self.signal:
            self.signal.emit()

class RemoveDictItemCommand(QUndoCommand):
    def __init__(self, target_dict, key, description, signal=None):
        super().__init__(description)
        self.target_dict = target_dict
        self.key = key
        self.old_value = target_dict.get(key)
        self.signal = signal

    def redo(self):
        if self.key in self.target_dict:
            del self.target_dict[self.key]
        if self.signal:
            self.signal.emit()

    def undo(self):
        if self.old_value is not None:
            self.target_dict[self.key] = self.old_value
        if self.signal:
            self.signal.emit()

class ReplaceDictItemCommand(QUndoCommand):
    def __init__(self, target_dict, key, new_value, old_value, description, signal=None):
        super().__init__(description)
        self.target_dict = target_dict
        self.key = key
        self.new_value = new_value
        self.old_value = old_value
        self.signal = signal

    def redo(self):
        self.target_dict[self.key] = self.new_value
        if self.signal:
            self.signal.emit()

    def undo(self):
        self.target_dict[self.key] = self.old_value
        if self.signal:
            self.signal.emit()
