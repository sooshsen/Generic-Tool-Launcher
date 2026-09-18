from pathlib import Path
from PySide6.QtWidgets import (
	QComboBox,
	QMainWindow,
	QWidget,
	QVBoxLayout,
	QLabel,
	QPushButton,
	QMessageBox,
	QFrame
	)

from .conda_manager import find_conda_environments
from .tool_registry import ToolRegistry
from .process_runner import ProcessRunner


class MainWindow(QMainWindow):

	def __init__(self):
		super().__init__()  # ??

		self.setWindowTitle('Generic Tool Launcher')
		self.resize(600, 450)


		''' Tool Registry '''
		self.registry = ToolRegistry(Path(__file__).parent.parent / "programs")

		# load tool definitions
		self.tools = self.registry.load_tools()

		
		''' Process Runner '''
		self.process_runner = ProcessRunner(self)

		self.process_runner.process_started.connect(self.tool_started)
		self.process_runner.process.finished.connect(self.tool_finished)
		self.process_runner.process_error.connect(self.tool_error)


		''' Main Widget '''
		central_widget = QWidget()
		self.setCentralWidget(central_widget)
		self.layout = QVBoxLayout(central_widget)



		''' Title '''
		title = QLabel('Generic Tool Launcher')
		title.setStyleSheet('''
				font-size: 24px;
				font-weight: bold; 
				padding: 10px;
				''')
		self.layout.addWidget(title)



		''' Subtitle '''
		subtitle = QLabel('Launch scientific analysis tools from their respective Conda environments.')
		subtitle.setStyleSheet('''
				font-size: 14px;
				color: #666666; 
				padding: 0 10px 15px 10px;
			''')
		self.layout.addWidget(subtitle)



		''' Conda environment selector '''
		environment_label = QLabel("Conda Environment")
		self.environment_dropdown = QComboBox()
		self.environment_dropdown.addItem("Select an environment...")
		
		environments = find_conda_environments()
		self.environment_dropdown.addItems(environments)

		self.environment_dropdown.currentTextChanged.connect(self.environment_changed)
		self.layout.addWidget(environment_label)
		self.layout.addWidget(self.environment_dropdown)

		

		''' Program card container '''
		self.program_container = QVBoxLayout()
		self.layout.addLayout(self.program_container)
        
		# Show initial message
		self.show_no_program_message("Select a Conda environment to continue.")
		self.layout.addStretch()


	# ======================================================
	# Environment changed
	# ======================================================
	def environment_changed(self, environment):

		# Remove current card
		self.clear_program_card()

		if (not environment or environment == "Select an environment..."):
			self.show_no_program_message("Select a Conda environment to continue.")
			return
		
		# Find matching tool
		matching_tool = None

		for tool in self.tools:
			if tool.get("environment") == environment:
				matching_tool = tool
				break

		# No matching program
		if matching_tool is None:
			self.show_no_program_message(
				"No program is configured for "
				f"the '{environment}' environment."
				)
			return

		# Show program
		self.show_program_card(matching_tool)


	# ======================================================
	# Show program card
	# ======================================================
	def show_program_card(self, tool):

		card = QFrame()
		card.setFrameShape(QFrame.StyledPanel)

		card.setStyleSheet("""
			border: 1px solid #cccccc;
			border-radius: 8px;
			padding: 10px;
			"""
			)

		layout = QVBoxLayout(card)

		# Program title
		name_label = QLabel(tool["name"])
		name_label.setStyleSheet("""
			font-size: 20px;
			font-weight: bold;
			"""
			)
		layout.addWidget(name_label)


		# Description
		description_label = QLabel(tool.get("description",""))
		description_label.setWordWrap(True)
		layout.addWidget(description_label)


		# Selected environment
		environment_label = QLabel(f"Environment: {tool['environment']}")
		layout.addWidget(environment_label)


		# Status
		self.status_label = QLabel("Status: Stopped")
		layout.addWidget(self.status_label)


		# Launch button
		self.launch_button = QPushButton(f"Launch {tool['name']}")
		self.launch_button.clicked.connect(lambda: self.launch_tool(tool))
		layout.addWidget(self.launch_button)
		self.program_container.addWidget(card)


		# Store current tool
		self.current_tool = tool


	# ======================================================
	# No program message
	# ======================================================
	def show_no_program_message(self, message):

		label = QLabel(message)
		label.setWordWrap(True)
		label.setStyleSheet("""
			color: #666666;
			padding: 20px;
			"""
			)

		self.program_container.addWidget(label)
		self.current_tool = None
		self.status_label = None
		self.launch_button = None

	# ======================================================
	# Clear program card
	# ======================================================
	def clear_program_card(self):

		while self.program_container.count():
			item = self.program_container.takeAt(0)
			widget = item.widget()

			if widget is not None: widget.deleteLater()

		self.current_tool = None
		self.status_label = None
		self.launch_button = None

	# ======================================================
	# Launch tool
	# ======================================================
	def launch_tool(self, tool):

		environment = (self.environment_dropdown.currentText())
		if not environment:
			QMessageBox.warning(self, "No Environment", "Please select a Conda environment.")
			return

		command = tool["launch"]["command"]

		self.process_runner.start(environment, command)


	# ======================================================
	# Process started
	# ======================================================
	def tool_started(self):

		if self.status_label is not None:
			self.status_label.setText("Status: Running")

		if self.launch_button is not None:
			self.launch_button.setEnabled(False)


	# ======================================================
	# Process finished
	# ======================================================
	def tool_finished(self, return_code):

		if self.status_label is not None:

			if return_code == 0:
				self.status_label.setText("Status: Stopped")
			else:
				self.status_label.setText(f"Status: Exited ({return_code})")

		if self.launch_button is not None:
			self.launch_button.setEnabled(True)

	# ======================================================
	# Process error
	# ======================================================
	def tool_error(self, message):

		if self.status_label is not None:
			self.status_label.setText("Status: Error")

		if self.launch_button is not None:
			self.launch_button.setEnabled(True)

		QMessageBox.critical(self, "Launch Error", message)



