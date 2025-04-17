# ConAir - File Selection and Concatenation Utility

ConAir (CONcatenate And Interactive Reorder) is a terminal-based utility for easily navigating directories, marking files for concatenation, and combining the contents of multiple text files into a single output.

## Features

- Interactive TUI (Text User Interface) for navigating directories
- Mark multiple files for concatenation
- Reorder selected files before concatenation
- Filter files by name
- Copy concatenated text to clipboard
- Custom output file naming
- Intuitive keyboard shortcuts

## Installation

### Prerequisites

- Python 3.6 or higher
- Optional: `pyperclip` library for clipboard support

### Linux/macOS Installation

1. Clone the repository:
   ```
   git clone https://github.com/bnourse/conair.git
   cd conair
   ```

2. Make the script executable:
   ```
   chmod +x conair.py
   ```

3. Optional: Install pyperclip for clipboard support:
   ```
   pip install pyperclip
   ```

4. Optional: Create a symlink to use ConAir from anywhere:
   ```
   ln -s $(pwd)/conair.py /usr/local/bin/conair
   ```

### Windows Installation

#### 1. Install Python (if not already installed)

1. Download the latest Python installer from [python.org](https://www.python.org/downloads/windows/)
2. Run the installer
   - Make sure to check "Add Python to PATH" during installation
   - Click "Install Now" for a standard installation
3. Verify the installation by opening Command Prompt and typing:
   ```
   python --version
   ```

#### 2. Get the ConAir Code

**Option A: Clone using Git**

1. Open Command Prompt
2. Navigate to the directory where you want to install ConAir
3. Clone the repository:
   ```
   git clone https://github.com/bnourse/conair.git
   cd conair
   ```

**Option B: Download ZIP file**

1. Download the repository as a ZIP file
2. Extract the ZIP file to your desired location
3. Open Command Prompt and navigate to the extracted folder:
   ```
   cd path\to\extracted\conair
   ```

#### 3. Install Required Dependencies

1. Install the windows-curses package (required for Windows):
   ```
   pip install windows-curses
   ```

2. Install pyperclip for clipboard support (optional but recommended):
   ```
   pip install pyperclip
   ```

#### 4. Create a Batch File for Easy Access (Optional)

To run ConAir from anywhere in your system, you can create a batch file:

1. Create a new text file named `conair.bat` in a directory that's in your system PATH (e.g., `C:\Windows`)
2. Add the following content to the file (replace the path with your actual installation path):
   ```batch
   @echo off
   python C:\path\to\conair\conair.py %*
   ```
3. Save the file

#### 5. Running ConAir on Windows

**Method 1: Direct Python execution**

1. Open Command Prompt
2. Navigate to the ConAir directory:
   ```
   cd path\to\conair
   ```
3. Run the script:
   ```
   python conair.py
   ```

**Method 2: Using the batch file (if created)**

1. Open Command Prompt
2. Navigate to any directory you want to work in
3. Simply type:
   ```
   conair
   ```

#### Windows Troubleshooting

1. **Python not recognized as a command**
   - Make sure Python is added to your PATH environment variable
   - Try reinstalling Python with the "Add Python to PATH" option checked

2. **Clipboard functionality not working**
   - Ensure pyperclip is installed: `pip install pyperclip`
   - If using Windows Terminal with elevated privileges, clipboard access may be restricted

3. **Display issues in Windows Terminal**
   - ConAir uses curses for its TUI; try using a different terminal emulator if you encounter display problems
   - Adjust terminal window size if the interface appears corrupted

## Usage

### Basic Usage

Run the script from the directory where you want to start:

**Linux/macOS:**
```
./conair.py
```

Or if you've created the symlink:
```
conair
```

**Windows:**
```
python conair.py
```

Or if you've created the batch file:
```
conair
```

Specify a starting directory as a command-line argument:
```
conair /path/to/directory
```

### Navigation

- Use arrow keys (or `j`/`k`) to navigate up and down
- Press `Enter` to enter a directory or preview a file
- Press `Backspace` to go up a directory
- Press `g` to jump to the top of the file list
- Press `G` to jump to the bottom of the file list

### File Selection

- Press `m` to mark/unmark a file for concatenation (cursor auto-advances to next file)
- Press `a` to toggle marking all text files in the current directory
  - If all files are already marked, this will unmark them all
  - Otherwise, it will mark all unmarked text files
- Press `u` to unmark the currently selected file and move up in the list

### Filtering

- Press `/` to enter filter mode
- Type part of a filename to filter the list
- Press `Escape` or `Enter` to exit filter mode

### Reordering

- Press `r` to enter reorder mode
- Use arrow keys (or `j`/`k`) to select files
- Press `u`/`d` to move files up or down in the concatenation order
- Press `Escape` to exit reorder mode

### Concatenation

- Press `c` to concatenate marked files
  - If no custom filename is set, files are concatenated to "concatenated_YYYYMMDD_HHMMSS.txt"
- Press `o` to specify a custom output filename
- Press `y` to copy the concatenated content to clipboard
- Press `Y` to copy the current file's contents to clipboard
- Press `p` to copy the current file's path to clipboard

### Other Commands

- Press `?` to show/hide help
- Press `q` to quit the application

## Examples

### Combining multiple configuration files

1. Navigate to your configuration directory
2. Mark the files you want to combine with `m`
3. Press `r` to reorder them if needed
4. Press `c` to concatenate and specify an output file

### Concatenating code snippets

1. Navigate to your source code directory
2. Use `/` to filter for specific files
3. Mark relevant files with `m`
4. Press `y` to concatenate and copy to clipboard

### Creating a combined log file

1. Navigate to your logs directory
2. Mark the log files you want to analyze together
3. Use `r` to arrange them in chronological order if needed
4. Press `c` to concatenate and specify an output file

### Sharing multiple file contents

1. Navigate to the relevant directory
2. Mark all the files you want to share with `m`
3. Press `y` to copy all contents to clipboard
4. Paste into your document or communication tool

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request at https://github.com/bnourse/conair.