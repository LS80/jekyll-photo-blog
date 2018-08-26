from collections import defaultdict

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QGridLayout, QDialogButtonBox,
                             QLabel, QLineEdit, QGroupBox)

class SettingsDialog(QDialog):
    def __init__(self, settings, labels, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.settings = settings

        self.setWindowTitle("Settings")
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.widgets = defaultdict(list)
        for group_name, keys in labels.items():
            grid_layout = QGridLayout()
            group_box = QGroupBox(group_name)

            for i, key in enumerate(keys):
                value = self.settings.value('/'.join((group_name, key)))
                grid_layout.addWidget(QLabel(key), i, 0)
                widget = QLineEdit(value)
                grid_layout.addWidget(widget, i, 1)
                self.widgets[group_name].append((key, widget))

            group_box.setLayout(grid_layout)
            main_layout.addWidget(group_box)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        main_layout.addWidget(button_box)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def accept(self):
        for group_name, keys in self.widgets.items():
            for key, widget in keys:
                self.settings.setValue('/'.join((group_name, key)), widget.text())

        QDialog.accept(self)
