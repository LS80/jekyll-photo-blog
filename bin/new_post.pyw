import sys
import os
from datetime import date
from collections import OrderedDict

import cloudinary
import cloudinary.uploader
import ruamel.yaml
from slugify import slugify
from PyQt5.QtCore import QFileInfo, Qt, QSettings
from PyQt5.QtWidgets import (
    QAction, QApplication, QCalendarWidget, QFileDialog,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QPlainTextEdit, QPushButton, QVBoxLayout, QWidget
)

from settings import SettingsDialog

SETTINGS = OrderedDict(Cloudinary=['Cloud Name', 'API Key', 'API Secret'])

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        settings_menu = self.menuBar().addMenu('Menu')
        settings_action = QAction('Settings', self)
        settings_action.triggered.connect(self.show_settings)
        settings_menu.addAction(settings_action)

        self.setWindowTitle('Create New Post')
        layout = QVBoxLayout()
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.setFixedSize(self.size())
        self.statusBar().setSizeGripEnabled(False)

        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel('Title'))
        self.title_edit = QLineEdit()
        title_layout.addWidget(self.title_edit)

        calendar_layout = QHBoxLayout()
        label = QLabel('Date')
        calendar_layout.addWidget(label)
        self.calendar = QCalendarWidget()
        self.calendar.setMaximumDate(date.today())
        calendar_layout.addWidget(self.calendar)
        calendar_layout.addStretch()
        calendar_layout.setAlignment(label, Qt.AlignTop)

        images_layout = QVBoxLayout()
        select_images_button = QPushButton('Add Images')
        button_layout = QHBoxLayout()
        button_layout.addWidget(select_images_button)
        button_layout.addStretch()
        images_layout.addLayout(button_layout)
        self.image_paths_edit = QPlainTextEdit()
        self.image_paths_edit.textChanged.connect(self.enable_button)
        images_layout.addWidget(self.image_paths_edit)

        self.generate_button = QPushButton('Create')
        self.generate_button.setEnabled(False)

        layout.addLayout(title_layout)
        layout.addLayout(calendar_layout)
        layout.addLayout(images_layout)
        layout.addWidget(self.generate_button)

        select_images_button.clicked.connect(self.add_images)
        self.title_edit.textEdited.connect(self.enable_button)
        self.generate_button.clicked.connect(self.create_post)

        self.statusBar().showMessage(None)

        self.show()

        self.settings = QSettings()

        self.image_paths = []

    def enable_button(self):
        if self.title_edit.text() and self.image_paths_edit.toPlainText():
            self.generate_button.setEnabled(True)
        else:
            self.generate_button.setEnabled(False)

    def show_settings(self):
        SettingsDialog(self.settings, labels=SETTINGS, parent=self).exec_()

    def configure_cloudinary(self):
        if not all(self.settings.value('/'.join(('Cloudinary', key))) for key in SETTINGS['Cloudinary']):
            self.show_settings()

        d = dict((key.lower().replace(' ', '_'), self.settings.value('/'.join(('Cloudinary', key))))
                 for key in SETTINGS['Cloudinary'])
        cloudinary.config(**d)

    def add_images(self):
        image_paths, _ = QFileDialog.getOpenFileNames(
            self,
            directory=self.settings.value('Image Path'),
            filter='Photos (*.jpg)'
        )
        self.image_paths.extend(image_paths)
        self.image_paths_edit.setPlainText('\n'.join(self.image_paths))
        self.settings.setValue('Image Path', QFileInfo(self.image_paths[0]).path())

    def upload_images(self, files):
        self.configure_cloudinary()
        for filename in files:
            self.statusBar().showMessage('Uploading {}...'.format(filename))
            try:
                result = cloudinary.uploader.upload(filename)
            except (cloudinary.api.Error, ValueError):
                self.statusBar().showMessage('Upload error')
                return
            except FileNotFoundError:
                self.statusBar().showMessage('File not found: {}'.format(filename))
                return
            self.statusBar().showMessage(None)
            yield dict(id=result['public_id'], effect=None, caption=None)

    def create_post(self):
        title = self.title_edit.text()
        post_date = self.calendar.selectedDate().toPyDate()

        posts_dir = os.path.join(os.path.dirname(__file__), '..', '_posts')
        os.makedirs(posts_dir, exist_ok=True)
        filename = os.path.join(posts_dir, '{}-{}.md'.format(post_date.isoformat(), slugify(str(title))))

        image_paths = self.image_paths_edit.toPlainText().split('\n')
        images = list(self.upload_images(image_paths))
        if not images:
            return

        front_matter = dict(title=title, images=images)

        with open(filename, 'w') as f:
            f.write('---\n')
            ruamel.yaml.round_trip_dump(front_matter, f, default_flow_style=False)
            f.write('---\n\n')
            f.write('Enter a description here.\n')

        self.title_edit.clear()
        self.image_paths_edit.clear()
        self.statusBar().showMessage('Saved {}'.format(filename))


app = QApplication(sys.argv)
win = Window()
sys.exit(app.exec_())
