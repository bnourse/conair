#!/usr/bin/env python3
"""
File Selection and Concatenation Utility

A curses-based utility for navigating directories, marking files for concatenation,
filtering files by name or extension, and concatenating selected text files.
"""

import curses
import os
import re
import sys
from typing import Dict, List, Set, Tuple

class FileConcatenator:
    def __init__(self, start_path: str = os.getcwd()):
        self.current_path = os.path.abspath(start_path)
        self.marked_files: Dict[str, str] = {}  # Dict of absolute paths to filenames
        self.current_filter = ""
        self.filter_mode = False
        self.filter_by_extension = False
        self.current_index = 0
        self.scroll_offset = 0
        self.status_message = ""
        self.help_visible = False
        self.quit_flag = False
        self.custom_output_filename = ""  # Store custom output filename

    def run(self, stdscr):
        """Main entry point for the curses application"""
        curses.curs_set(0)  # Hide cursor
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)  # Marked files
        curses.init_pair(2, curses.COLOR_YELLOW, -1)  # Directories
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)  # Selected item
        curses.init_pair(4, curses.COLOR_CYAN, -1)  # Filter mode
        curses.init_pair(5, curses.COLOR_RED, -1)  # Status messages

        while not self.quit_flag:
            self.draw_screen(stdscr)
            self.handle_input(stdscr)

    def draw_screen(self, stdscr):
        """Draw the main interface"""
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Draw header
        header = f" Current Dir: {self.current_path} "
        filter_status = f" Filter: {self.current_filter}" if self.filter_mode else ""
        stdscr.addstr(0, 0, header + filter_status)
        stdscr.addstr(1, 0, "=" * (width - 1))
        
        # Get directory contents
        try:
            contents = self.get_filtered_directory_contents()
        except Exception as e:
            self.status_message = f"Error: {str(e)}"
            contents = []

        # Adjust current_index if needed
        if contents and self.current_index >= len(contents):
            self.current_index = len(contents) - 1
        
        # Calculate visible range
        max_items = height - 7  # Reserve lines for header, footer, status
        if max_items < 1:
            max_items = 1
        
        if self.current_index - self.scroll_offset >= max_items:
            self.scroll_offset = self.current_index - max_items + 1
        elif self.current_index < self.scroll_offset:
            self.scroll_offset = self.current_index
        
        end_idx = min(len(contents), self.scroll_offset + max_items)
        visible_contents = contents[self.scroll_offset:end_idx]
        
        # Display directory contents
        for i, item in enumerate(visible_contents):
            idx = i + self.scroll_offset
            is_dir = os.path.isdir(os.path.join(self.current_path, item))
            is_marked = os.path.abspath(os.path.join(self.current_path, item)) in self.marked_files
            
            prefix = ""
            if is_marked:
                prefix = "[*] "
            elif is_dir:
                prefix = "[d] "
            else:
                prefix = "    "
            
            attr = 0
            if idx == self.current_index:
                attr = curses.color_pair(3)
            elif is_marked:
                attr = curses.color_pair(1)
            elif is_dir:
                attr = curses.color_pair(2)
                
            display_text = prefix + item
            if len(display_text) > width - 2:
                display_text = display_text[:width-5] + "..."
                
            try:
                stdscr.addstr(2 + i, 0, display_text, attr)
            except curses.error:
                # Catch potential out-of-bounds errors
                pass
        
        # Draw footer with marked files count
        marked_count = len(self.marked_files)
        footer_text = f" Marked: {marked_count} files "
        if self.filter_mode:
            mode_text = "FILTER MODE"
            stdscr.addstr(height - 4, 0, mode_text, curses.color_pair(4))
        
        try:
            stdscr.addstr(height - 3, 0, "=" * (width - 1))
            stdscr.addstr(height - 2, 0, footer_text)
            
            # Show help line
            help_text = "Press ? for help | q:Quit m:Mark f:Filter Enter:Open/Navigate c:Concatenate"
            if len(help_text) > width:
                help_text = help_text[:width-4] + "..."
            stdscr.addstr(height - 1, 0, help_text)
            
            # Show status message if any
            if self.status_message:
                stdscr.addstr(height - 5, 0, self.status_message, curses.color_pair(5))
        except curses.error:
            # Catch potential out-of-bounds errors
            pass
            
        # Display help if requested
        if self.help_visible:
            self.draw_help(stdscr)
            
        stdscr.refresh()

    def draw_help(self, stdscr):
        """Display help overlay"""
        height, width = stdscr.getmaxyx()
        help_height = 12
        help_width = 60
        start_y = (height - help_height) // 2
        start_x = (width - help_width) // 2
        
        # Create help window
        help_win = curses.newwin(help_height, help_width, start_y, start_x)
        help_win.box()
        
        help_texts = [
            "FILE CONCATENATOR HELP",
            "=============================================",
            "↑/↓/j/k: Navigate up and down",
            "Enter: Open directory or view file",
            "Backspace: Go up one directory",
            "m: Mark/unmark file (auto-advances to next)",
            "a: Mark all text files in current directory",
            "o: Set custom output filename",
            "f: Toggle filter mode (filter by name)",
            "e: Toggle filter by extension mode",
            "c: Concatenate all marked files",
            "q: Quit application",
            "?: Toggle this help"
        ]
        
        for i, text in enumerate(help_texts):
            if i == 0:  # Title
                help_win.addstr(i + 1, (help_width - len(text)) // 2, text)
            else:
                help_win.addstr(i + 1, 2, text)
        
        help_win.refresh()

    def handle_input(self, stdscr):
        """Process user input"""
        key = stdscr.getch()
        
        # Handle filter mode separately
        if self.filter_mode:
            if key == 27:  # ESC to exit filter mode
                self.filter_mode = False
                self.current_filter = ""
            elif key == 10 or key == curses.KEY_ENTER:  # Enter to apply filter
                self.filter_mode = False
            elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:  # Backspace
                self.current_filter = self.current_filter[:-1]
            elif key == 9:  # Tab to toggle filter by extension
                self.filter_by_extension = not self.filter_by_extension
                if self.filter_by_extension:
                    self.status_message = "Filtering by extension"
                else:
                    self.status_message = "Filtering by filename"
            elif 32 <= key <= 126:  # Printable characters
                self.current_filter += chr(key)
            return
        
        # Regular navigation and commands
        if key == curses.KEY_UP or key == ord('k'):
            self.current_index = max(0, self.current_index - 1)
        elif key == curses.KEY_DOWN or key == ord('j'):
            contents = self.get_filtered_directory_contents()
            self.current_index = min(len(contents) - 1 if contents else 0, self.current_index + 1)
        elif key == ord('g'):  # Go to top
            self.current_index = 0
        elif key == ord('G'):  # Go to bottom
            contents = self.get_filtered_directory_contents()
            self.current_index = len(contents) - 1 if contents else 0
        elif key == 10 or key == curses.KEY_ENTER:  # Enter
            self.open_selected_item()
        elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:  # Backspace
            self.navigate_up()
        elif key == ord('m'):
            self.toggle_mark_selected()
            # Auto-advance to next file after marking
            contents = self.get_filtered_directory_contents()
            if contents and self.current_index < len(contents) - 1:
                self.current_index += 1
        elif key == ord('a'):
            self.mark_all_files()
        elif key == ord('f'):
            self.filter_mode = True
            self.filter_by_extension = False
            self.status_message = "Filter mode: Type to filter by filename"
        elif key == ord('e'):
            self.filter_mode = True
            self.filter_by_extension = True
            self.status_message = "Filter mode: Type to filter by extension"
        elif key == ord('c'):
            self.concatenate_files()
        elif key == ord('o'):
            self.set_output_filename()
        elif key == ord('q'):
            self.quit_flag = True
        elif key == ord('?'):
            self.help_visible = not self.help_visible

    def get_filtered_directory_contents(self) -> List[str]:
        """Get directory contents with filtering applied"""
        try:
            all_contents = sorted(os.listdir(self.current_path))
            
            # Move directories to the top
            dirs = [item for item in all_contents if os.path.isdir(os.path.join(self.current_path, item))]
            files = [item for item in all_contents if not os.path.isdir(os.path.join(self.current_path, item))]
            
            # Add parent directory entry '..' at the very top, but not for the root directory
            parent_dir = os.path.dirname(self.current_path)
            if parent_dir != self.current_path:  # Check if not at root directory
                sorted_contents = [".."] + dirs + files
            else:
                sorted_contents = dirs + files
            
            # Apply filter if needed
            if self.current_filter:
                if self.filter_by_extension:
                    # Filter by file extension
                    filter_pattern = self.current_filter.lower()
                    return [item for item in sorted_contents if 
                           (os.path.isdir(os.path.join(self.current_path, item)) or
                            os.path.splitext(item.lower())[1].endswith(filter_pattern))]
                else:
                    # Filter by filename
                    filter_pattern = self.current_filter.lower()
                    return [item for item in sorted_contents if filter_pattern in item.lower()]
            
            return sorted_contents
        except Exception as e:
            self.status_message = f"Error listing directory: {str(e)}"
            return []

    def open_selected_item(self):
        """Open the currently selected item (navigate to dir or view file)"""
        contents = self.get_filtered_directory_contents()
        if not contents or self.current_index >= len(contents):
            return
        
        selected = contents[self.current_index]
        
        # Handle special case for parent directory navigation
        if selected == "..":
            self.navigate_up()
            return
            
        full_path = os.path.join(self.current_path, selected)
        
        if os.path.isdir(full_path):
            # Navigate to directory
            self.current_path = full_path
            self.current_index = 0
            self.scroll_offset = 0
        else:
            # Preview text file
            if self.is_text_file(full_path):
                self.preview_file(full_path)
            else:
                self.status_message = "Not a text file"

    def is_text_file(self, filepath: str) -> bool:
        """Check if a file is likely a text file by trying to read it as text"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                f.read(4096)  # Read first 4KB
            return True
        except Exception:
            return False

    def preview_file(self, filepath: str):
        """Show a preview of a text file"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(4096)  # Read first 4KB
                
            # Create a temporary window for preview
            lines = content.split('\n')
            height, width = curses.LINES, curses.COLS
            preview_height = min(len(lines) + 4, height - 4)
            preview_width = width - 4
            
            preview_win = curses.newwin(preview_height, preview_width, 2, 2)
            preview_win.box()
            
            filename = os.path.basename(filepath)
            title = f" {filename} Preview "
            preview_win.addstr(0, (preview_width - len(title)) // 2, title)
            
            for i, line in enumerate(lines[:preview_height-4]):
                truncated_line = line[:preview_width-6]
                preview_win.addstr(i + 1, 2, truncated_line)
                
            preview_win.addstr(preview_height - 2, 2, "Press any key to close preview")
            preview_win.refresh()
            preview_win.getch()
            
        except Exception as e:
            self.status_message = f"Error previewing file: {str(e)}"

    def navigate_up(self):
        """Navigate to parent directory"""
        parent = os.path.dirname(self.current_path)
        if parent != self.current_path:
            self.current_path = parent
            self.current_index = 0
            self.scroll_offset = 0

    def toggle_mark_selected(self):
        """Mark/unmark the currently selected file for concatenation"""
        contents = self.get_filtered_directory_contents()
        if not contents or self.current_index >= len(contents):
            return
        
        selected = contents[self.current_index]
        full_path = os.path.abspath(os.path.join(self.current_path, selected))
        
        if os.path.isdir(full_path):
            self.status_message = "Cannot mark directories"
            return
        
        if not self.is_text_file(full_path):
            self.status_message = "Can only mark text files"
            return
            
        # Toggle mark status
        if full_path in self.marked_files:
            del self.marked_files[full_path]
            self.status_message = f"Unmarked: {selected}"
        else:
            self.marked_files[full_path] = selected
            self.status_message = f"Marked: {selected}"

    def mark_all_files(self):
        """Toggle marking all text files in the current directory"""
        contents = self.get_filtered_directory_contents()
        text_files = []
        
        # Get all text files in the current directory
        for item in contents:
            if not os.path.isdir(os.path.join(self.current_path, item)):
                full_path = os.path.abspath(os.path.join(self.current_path, item))
                if self.is_text_file(full_path):
                    text_files.append((full_path, item))
        
        # Check if all text files are already marked
        all_marked = True
        for full_path, _ in text_files:
            if full_path not in self.marked_files:
                all_marked = False
                break
        
        # If all files are already marked, unmark them all
        if all_marked and text_files:
            for full_path, _ in text_files:
                if full_path in self.marked_files:
                    del self.marked_files[full_path]
            self.status_message = f"Unmarked all {len(text_files)} files"
        # Otherwise mark all unmarked text files
        else:
            marked_count = 0
            for full_path, item in text_files:
                if full_path not in self.marked_files:
                    self.marked_files[full_path] = item
                    marked_count += 1
            
            self.status_message = f"Marked {marked_count} files"

    def concatenate_files(self):
        """Concatenate all marked files into a single output file"""
        if not self.marked_files:
            self.status_message = "No files marked for concatenation"
            return
        
        # Use custom filename if set, otherwise use timestamp
        if self.custom_output_filename:
            output_file = os.path.join(self.current_path, self.custom_output_filename)
        else:
            # Create output filename based on current time
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.current_path, f"concatenated_{timestamp}.txt")
        
        try:
            with open(output_file, 'w', encoding='utf-8') as outfile:
                for filepath, filename in self.marked_files.items():
                    outfile.write(f"\n{'='*80}\n")
                    outfile.write(f"FILE: {filename}\n")
                    outfile.write(f"{'='*80}\n\n")
                    
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
                        outfile.write(infile.read())
                    
                    outfile.write("\n\n")
                    
            self.status_message = f"Concatenated {len(self.marked_files)} files to {os.path.basename(output_file)}"
        except Exception as e:
            self.status_message = f"Error during concatenation: {str(e)}"

    def set_output_filename(self):
        """Set a custom output filename"""
        height, width = curses.LINES, curses.COLS
        win_height = 5
        win_width = 60
        start_y = (height - win_height) // 2
        start_x = (width - win_width) // 2
        
        # Create input window
        input_win = curses.newwin(win_height, win_width, start_y, start_x)
        input_win.box()
        title = " Set Output Filename "
        input_win.addstr(0, (win_width - len(title)) // 2, title)
        
        # Initialize cursor position
        curses.echo()
        curses.curs_set(1)
        
        # Show current filename or default
        current = self.custom_output_filename if self.custom_output_filename else ""
        prompt = "Enter filename: "
        input_win.addstr(2, 2, prompt)
        input_win.refresh()
        
        # Get user input
        input_text = input_win.getstr(2, 2 + len(prompt), 40).decode('utf-8')
        
        # Reset cursor
        curses.noecho()
        curses.curs_set(0)
        
        if input_text:
            self.custom_output_filename = input_text
            self.status_message = f"Output filename set to: {input_text}"
        else:
            self.status_message = "Output filename unchanged"

def main():
    """Entry point for the application"""
    start_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    app = FileConcatenator(start_path)
    curses.wrapper(app.run)

if __name__ == "__main__":
    main()
