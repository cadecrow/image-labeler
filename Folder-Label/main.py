import csv
import os
import shutil
import sys

import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIntValidator, QKeySequence
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QCheckBox, QFileDialog, QDesktopWidget, QLineEdit, \
    QRadioButton, QShortcut, QScrollArea, QVBoxLayout, QGroupBox, QFormLayout
from xlsxwriter.workbook import Workbook


def get_img_paths(dir, extensions=('.jpg', '.png', '.jpeg')):
    '''
    :param dir: folder with files
    :param extensions: tuple with file endings. e.g. ('.jpg', '.png'). Files with these endings will be added to img_paths
    :return: list of all filenames
    '''

    img_paths = []

    for filename in os.listdir(dir):
        if filename.lower().endswith(extensions):
            img_paths.append(os.path.join(dir, filename))

    return img_paths


def make_folder(directory):
    """
    Make folder if it doesn't already exist
    :param directory: The folder destination path
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


class SetupWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Window variables
        self.width = 800
        self.height = 940

        # State variables
        self.selected_folder = ''
        self.folder_headlines = []
        self.selected_labels = ''
        self.label = ''
        self.label_inputs = []
        self.label_headlines = []
        self.mode = 'csv'  # default option
        self.csv_generated_message = ''
        self.assigned_labels = {}
        self.output_filename = ''

        # QLabels
        self.headline_folder = QLabel('1. Select folder containing images you want to label', self)
        self.headline_label = QLabel('3. Specify label', self)
        self.headline_filename = QLabel('4. Set Output Filename (note: ".csv" extension will be added to filename)', self)

        self.selected_folder_label = QLabel(self)
        self.error_message = QLabel(self)


        # Buttons
        self.browse_button = QtWidgets.QPushButton("Browse", self)
        self.confirm_label = QtWidgets.QPushButton("Ok", self)
        self.set_filename_button = QtWidgets.QPushButton("Set Filename", self)
        self.output_button = QtWidgets.QPushButton("Generate Output", self)

        # Inputs
        self.labelInput = QLineEdit(self)
        self.filenameInput = QLineEdit(self)

        #layouts
        self.formLayout =QFormLayout()

        #GroupBoxs
        self.groupBox = QGroupBox()

        #Scrolls
        self.scroll = QScrollArea(self)

        # Init
        self.init_ui()

    def init_ui(self):
        # self.selectFolderDialog = QFileDialog.getExistingDirectory(self, 'Select directory')
        self.setWindowTitle('PyQt5 - Annotation tool - Parameters setup')
        self.setGeometry(0, 0, self.width, self.height)
        self.centerOnScreen()

        self.headline_folder.setGeometry(60, 30, 500, 20)
        self.headline_folder.setObjectName("headline")

        self.selected_folder_label.setGeometry(60, 60, 550, 26)
        self.selected_folder_label.setObjectName("selectedFolderLabel")

        self.browse_button.setGeometry(611, 59, 80, 28)
        self.browse_button.clicked.connect(self.pick_new)

        # Label Input
        self.headline_label.setGeometry(60, 270, 500, 20)
        self.headline_label.setObjectName("headline")

        self.labelInput.setGeometry(60, 300, 180, 26)

        self.confirm_label.setGeometry(241, 300, 80, 28)
        self.confirm_label.clicked.connect(self.set_label)

        # Filename Input
        self.headline_filename.setGeometry(60, 338, 500, 20)
        self.headline_filename.setObjectName("headline")

        self.filenameInput.setGeometry(60, 360, 180, 26)

        self.set_filename_button.setGeometry(241, 360, 140, 28)
        self.set_filename_button.clicked.connect(self.set_filename)

        # Generate Output Button (previously next_button)
        self.output_button.move(360, 630)
        self.output_button.clicked.connect(self.generate_output)
        self.output_button.setObjectName("blueButton")

        # Erro message
        self.error_message.setGeometry(20, 810, self.width - 20, 20)
        self.error_message.setAlignment(Qt.AlignCenter)
        self.error_message.setStyleSheet('color: red; font-weight: bold')

        self.init_radio_buttons()

        #initiate the ScrollArea
        self.scroll.setGeometry(60, 400, 650, 200)

        # apply custom styles
        try:
            styles_path = "./styles.qss"
            with open(styles_path, "r") as fh:
                self.setStyleSheet(fh.read())
        except:
            print("Can't load custom stylesheet.")

    def init_radio_buttons(self):
        """
        Creates section with mode selection
        """

        top_margin = 115
        radio_label = QLabel('2. Select mode', self)
        radio_label.setObjectName("headline")
        radio_label.move(60, top_margin)

        radiobutton = QRadioButton(
            "csv (Images in selected folder are labeled and then csv file with assigned labels is generated.)", self)
        radiobutton.setChecked(True)
        radiobutton.mode = "csv"
        radiobutton.toggled.connect(self.mode_changed)
        radiobutton.move(60, top_margin + 35)

        radiobutton = QRadioButton(
            "copy (Creates folder for each label. Labeled images are copied to these folders. Csv is also generated)",
            self)
        radiobutton.mode = "copy"
        radiobutton.toggled.connect(self.mode_changed)
        radiobutton.move(60, top_margin + 65)

        radiobutton = QRadioButton(
            "move (Creates folder for each label. Labeled images are moved to these folders. Csv is also generated)",
            self)
        radiobutton.mode = "move"
        radiobutton.toggled.connect(self.mode_changed)
        radiobutton.move(60, top_margin + 95)

# Show information
    def show_folder_input(self):
        # show headline for this step
            self.groupBox.setTitle('Your currently set folder and label is:')
            self.groupBox.setStyleSheet('font-weight: bold')

            # display current label fields
            self.folder_headlines.append(QLabel(f'folder: \"{self.selected_folder}\"', self))
            self.formLayout.addRow(self.folder_headlines[-1])

            self.groupBox.setLayout(self.formLayout)
            self.scroll.setWidget(self.groupBox)
            self.scroll.setWidgetResizable(True)

    def show_label_input(self):
        """
        Display current label in scroll area. The layout depends on the number of labels.
        """

        # check that label input is not empty
        if self.labelInput.text().strip() != '':

            # initialize values
            self.label_headlines = []  # labels to label input fields
            margin_top = 400

            # show headline for this step
            self.groupBox.setTitle('Your currently set folder and label is:')
            self.groupBox.setStyleSheet('font-weight: bold')

            # display current label fields
            self.label_headlines.append(QLabel(f'label: \"{self.label}\"', self))
            self.formLayout.addRow(self.label_headlines[-1])
                #self.formLayout.addRow(self.label_headlines[i], self.label_inputs[i])

            self.groupBox.setLayout(self.formLayout)
            self.scroll.setWidget(self.groupBox)
            self.scroll.setWidgetResizable(True)
    
    def show_output_message(self):
        # show headline for this step
            self.groupBox.setTitle('csv saved to:')
            self.groupBox.setStyleSheet('font-weight: bold')

            # diplsay current label fields
            self.formLayout.addRow(QLabel(self.csv_generated_message))

            self.groupBox.setLayout(self.formLayout)
            self.scroll.setWidget(self.groupBox)
            self.scroll.setWidgetResizable(True)

    def show_output_filename(self):
        # show headline for this step
            self.groupBox.setTitle('filename set as:')
            self.groupBox.setStyleSheet('font-weight: bold')

            self.formLayout.addRow(QLabel(f'filename: \"{self.output_filename}\"'))

            self.groupBox.setLayout(self.formLayout)
            self.scroll.setWidget(self.groupBox)
            self.scroll.setWidgetResizable(True)

# other Utility functions
    def mode_changed(self):
        """
        Sets new mode (one of: csv, copy, move)
        """
        radioButton = self.sender()
        if radioButton.isChecked():
            self.mode = radioButton.mode

    def pick_new(self):
        """
        shows a dialog to choose folder with images to label
        """
        dialog = QFileDialog()
        folder_path = dialog.getExistingDirectory(None, "Select Folder")

        self.selected_folder_label.setText(folder_path)
        self.selected_folder = folder_path
        self.show_folder_input()
    
    def centerOnScreen(self):
        """
        Centers the window on the screen.
        """
        resolution = QDesktopWidget().screenGeometry()
        self.move(int((resolution.width() / 2) - (self.width / 2)),
                  int((resolution.height() / 2) - (self.height / 2)) - 40)

    def check_validity(self):
        """
        :return: if all the necessary information is provided for proper run of application. And error message
        """
        if self.selected_folder == '':
            return False, 'Input folder has to be selected (step 1)'

        label_input = self.labelInput.text().strip()
        if label_input == '':
            return False, 'Must set a label (step 3).'

        return True, 'Form ok'

# Set Functions
    def set_label(self):
        self.label = self.labelInput.text().strip()
        self.show_label_input()

    def set_filename(self):
        self.output_filename = self.filenameInput.text().strip()
        self.show_output_filename()

    
    def set_labels(self, label):
        """
        Sets the label for every image in the folder
        :param label: selected label
        """
        img_paths = get_img_paths(self.selected_folder)

        for i in range(len(img_paths)):
            # get image filename from path (./data/images/img1.jpg → img1.jpg)
            img_path = img_paths[i]
            img_name = os.path.split(img_path)[-1]

            # if the img has some label already
            if img_name in self.assigned_labels.keys():

                # label is already there = means tht user want's to remove label
                if label in self.assigned_labels[img_name]:
                    self.assigned_labels[img_name].remove(label)

                    # remove key from dictionary if no labels are assigned to this image
                    if len(self.assigned_labels[img_name]) == 0:
                        self.assigned_labels.pop(img_name, None)

                    # remove image from appropriate folder
                    if self.mode == 'copy':
                        os.remove(os.path.join(self.selected_folder, label, img_name))

                    elif self.mode == 'move':
                        # label was in assigned labels, so I want to remove it from label folder,
                        # but this was the last label, so move the image to input folder.
                        # Don't remove it, because it it not save anywehre else
                        if img_name not in self.assigned_labels.keys():
                            shutil.move(os.path.join(self.selected_folder, label, img_name), self.selected_folder)
                        else:
                            # label was in assigned labels and the image is store in another label folder,
                            # so I want to remove it from current label folder
                            os.remove(os.path.join(self.selected_folder, label, img_name))

                # label is not there yet. But the image has some labels already
                else:
                    self.assigned_labels[img_name].append(label)

                    # path to copy/move images
                    copy_to = os.path.join(self.selected_folder, label)

                    # copy/move the image into appropriate label folder
                    if self.mode == 'copy':
                        # the image is stored in selected_folder, so i can copy it from there (differs from 'move' option)
                        shutil.copy(img_path, copy_to)

                    elif self.mode == 'move':
                        # the image doesn't have to be stored in selected_folder anymore.
                        # get the path where the image is stored
                        copy_from = os.path.join(self.selected_folder, self.assigned_labels[img_name][0], img_name)
                        shutil.copy(copy_from, copy_to)

            else:
                # Image has no labels yet. Set new label and copy/move

                self.assigned_labels[img_name] = [label]
                # move copy images to appropriate directories
                copy_to = os.path.join(self.selected_folder, label)

                if self.mode == 'copy':
                    shutil.copy(img_path, copy_to)
                elif self.mode == 'move':
                    shutil.move(img_path, copy_to)

            path = img_paths[i]
            filename = os.path.split(path)[-1]

            # If we have already assigned label to this image and mode is 'move', change the input path.
            # The reason is that the image was moved from '.../selected_folder' to '.../selected_folder/label'
            if self.mode == 'move' and filename in self.assigned_labels.keys():
                path = os.path.join(self.selected_folder, self.assigned_labels[filename][0], filename)

# CSV functions
    def generate_csv(self):
        """
        Generates and saves csv file with assigned labels.
        Assigned label is represented as one-hot vector.
        :param out_filename: name of csv file to be generated
        """
        self.csv_generated_message = ''

        path_to_save = os.path.join(self.selected_folder, 'Labeled-Output')
        make_folder(path_to_save)
        csv_file_path = os.path.join(path_to_save, self.output_filename) + '.csv'

        with open(csv_file_path, "w", newline='') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')

            # write header
            writer.writerow(['img'] + ['label'])

            #write labels
            for img_name in self.assigned_labels.keys():
                writer.writerow([img_name] + [self.label])

        self.csv_generated_message = f'csv saved to: {csv_file_path}'
        print(self.csv_generated_message)

        '''
        if self.generate_xlsx_checkbox.isChecked():
            try:
                self.csv_to_xlsx(csv_file_path)
            except:
                print('Generating xlsx file failed.')
        '''

    def generate_output(self):
        if self.label == '' or self.output_filename == '' or self.selected_folder == '':
            print('Must enter information or select data to generate csv')
            return
        self.set_labels(self.label)
        self.generate_csv()
        self.show_output_message()

############################################################################

    def csv_to_xlsx(self, csv_file_path):
        """
        converts csv file to xlsx file
        :param csv_file_path: path to csv file which we want to convert to lsx
        """
        workbook = Workbook(csv_file_path[:-4] + '.xlsx')
        worksheet = workbook.add_worksheet()

        with open(csv_file_path, 'rt', encoding='utf8') as f:
            reader = csv.reader(f)
            for r, row in enumerate(reader):
                for c, col in enumerate(row):
                    worksheet.write(r, c, col)

        workbook.close()

    def closeEvent(self, event):
        """
        This function is executed when the app is closed.
        It automatically generates csv file in case the user forgot to do that
        """
        print("closing the App..")
        if self.label != '' and self.output_filename != '' and self.selected_folder != '':
            print('assigned_classes_automatically_generated')
            self.generate_csv()

##########################################################################################

if __name__ == '__main__':
    # run the application
    app = QApplication(sys.argv)
    ex = SetupWindow()
    ex.show()
    sys.exit(app.exec_())
