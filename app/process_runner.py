from PySide6.QtCore import QObject, QProcess, Signal

class ProcessRunner(QObject):
	''' Runs commands inside specific CONDA environment '''

	# signals sent to main_window
	process_started = Signal()
	process_error = Signal()

	def __init__(self, parent=None):
		super().__init__(parent)

		self.process = QProcess(self)
		self.process.started.connect(self._on_started)
		self.process.errorOccurred.connect(self._on_error)


	def start(self, environment, command):

		if not environment:
			self.error.emit("No Conda environment was selected.")
			return

		if not command:
			self.error.emit("No command was specified.")
			return

		# QProcess needs the executable and arguments separately
		program = "conda"
		arguments = ["run","-n",environment,*command,]

		print("Launching:")
		print(" ".join([program, *arguments]))

		self.process.start(program, arguments)


	def _on_started(self):
		self.process_started.emit()

	def _on_error(self, process_error):
		self.process_error.emit(self.process.errorString())