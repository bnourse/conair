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

### Basic Installation

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

## Usage

### Basic Usage

Run the script from the directory where you want to start:

```
./conair.py
```

Or if you've created the symlink:

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