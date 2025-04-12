# ConAir - File Selection and Concatenation Utility

ConAir (CONcatenate And Interactive Reorder) is a terminal-based utility for easily navigating directories, marking files for concatenation, and combining the contents of multiple text files into a single output.

## Features

- Interactive TUI (Text User Interface) for navigating directories
- Mark multiple files for concatenation
- Reorder selected files before concatenation
- Filter files by name or extension
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
   git clone https://github.com/yourusername/conair.git
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
   git clone https://github.com/yourusername/conair.git
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

1. Install pyperclip for clipboard support (optional but recommended):
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

### Navigation

- Use arrow keys (or `j`/`k`) to navigate up and down
- Press `Enter` to enter a directory
- Press `Backspace` or left arrow to go up a directory

### File Selection

- Press `m` to mark/unmark a file for concatenation
- Press `a` to mark all files in the current directory
- Press `u` to unmark all files

### Filtering

- Press `/` to enter filter mode
- Type part of a filename to filter the list
- Press `.` to filter by file extension
- Press `Escape` to exit filter mode

### Reordering

- Press `r` to enter reorder mode
- Use arrow keys to select files
- Press `j`/`k` or up/down arrows to move files up or down in the concatenation order
- Press `Escape` to exit reorder mode

### Concatenation

- Press `c` to concatenate marked files
- Press `o` to specify a custom output filename
- Press `y` to copy the concatenated content to clipboard

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

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.