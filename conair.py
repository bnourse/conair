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
import subprocess
from typing import Dict, List, Set, Tuple

# Check if we can use pyperclip, otherwise use platform-specific clipboard commands
try:
    import pyperclip
    HAVE_PYPERCLIP = True
except ImportError:
    HAVE_PYPERCLIP = False

class FileConcatenator:
    def __init__(self, start_path: str = os.getcwd()):
        self.current_path = os.path.abspath(start_path)
        self.marked_files: Dict[str, str] = {}  # Dict of absolute paths to filenames
        self.marked_files_order: List[str] = []  # List of absolute paths in concatenation order
        self.current_filter = ""
        self.filter_mode = False
        self.search_mode = False
        self.search_term = ""
        self.search_results: List[int] = []  # Indices of items matching search
        self.current_search_index = 0
        self.current_index = 0
        self.scroll_offset = 0
        self.status_message = ""
        self.help_visible = False
        self.quit_flag = False
        self.custom_output_filename = ""  # Store custom output filename
        self.reorder_mode = False  # Flag for reorder mode
        self.column_count = 2  # Number of columns for file list
        self.page = 0  # Current page for pagination
        self.quick_mark_mode = False  # Flag for quick-mark mode
        self.quick_mark_files = []  # List of all text files for quick-mark mode
        self.quick_mark_page = 0  # Current page in quick-mark mode

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
        if self.quick_mark_mode:
            header = f" QUICK-MARK MODE - Press letters to mark/unmark files "
        elif self.reorder_mode:
            header = f" REORDER MODE - Concatenation Order "
        else:
            header = f" Current Dir: {self.current_path} "
            
        # Always show filter status if there's an active filter, not just in filter mode
        filter_status = f" Filter: {self.current_filter}" if self.current_filter else ""
        
        # Show search status if search is active
        search_status = f" Search: {self.search_term}" if self.search_term else ""
        if self.search_term and self.search_results:
            search_status += f" ({self.current_search_index + 1}/{len(self.search_results)})"
            
        status_text = filter_status + search_status
        stdscr.addstr(0, 0, header + status_text)
        stdscr.addstr(1, 0, "=" * (width - 1))
        
        # If in quick-mark mode, show files with letter labels
        if self.quick_mark_mode:
            self.draw_quick_mark_mode(stdscr)
        # If in reorder mode, show marked files in current order (single column view)
        elif self.reorder_mode:
            visible_contents = []
            contents = self.marked_files_order
            
            # Adjust current_index if needed for reorder mode
            if contents and self.current_index >= len(contents):
                self.current_index = len(contents) - 1
            
            # Calculate visible range for reorder mode
            max_items = height - 7  # Reserve lines for header, footer, status
            if max_items < 1:
                max_items = 1
            
            if self.current_index - self.scroll_offset >= max_items:
                self.scroll_offset = self.current_index - max_items + 1
            elif self.current_index < self.scroll_offset:
                self.scroll_offset = self.current_index
            
            end_idx = min(len(contents), self.scroll_offset + max_items)
            
            # Show marked files in current order for reordering
            for i in range(self.scroll_offset, end_idx):
                filepath = contents[i]
                if filepath in self.marked_files:
                    filename = self.marked_files[filepath]
                    visible_contents.append((i, filepath, filename))
                    
            # Display the reorder list
            for idx, (i, filepath, item) in enumerate(visible_contents):
                prefix = f"[{i+1}] "
                attr = curses.color_pair(3) if i == self.current_index else curses.color_pair(1)
                display_text = prefix + item
                if len(display_text) > width - 2:
                    display_text = display_text[:width-5] + "..."
                    
                try:
                    stdscr.addstr(2 + idx, 0, display_text, attr)
                except curses.error:
                    # Catch potential out-of-bounds errors
                    pass
        else:
            # Get directory contents (normal mode)
            try:
                contents = self.get_filtered_directory_contents()
            except Exception as e:
                self.status_message = f"Error: {str(e)}"
                contents = []

            # Adjust current_index if needed
            if contents and self.current_index >= len(contents):
                self.current_index = len(contents) - 1
            
            # Multi-column layout calculations
            total_items = len(contents)
            if total_items == 0:
                # No items to display
                stdscr.addstr(3, 0, "  (No files or directories)")
            else:
                # Calculate column width based on terminal width
                available_width = width - 2  # Leave margin
                col_padding = 2  # Space between columns
                
                # Dynamically adjust column count based on terminal width
                # Make sure we have at least one column
                self.column_count = max(1, min(4, available_width // 30))  # Limit to max 4 columns
                
                col_width = available_width // self.column_count - col_padding
                
                # Calculate items per page
                items_per_column = height - 7  # Reserve lines for header, footer, status
                if items_per_column < 1:
                    items_per_column = 1
                    
                items_per_page = items_per_column * self.column_count
                
                # Calculate total pages
                total_pages = (total_items + items_per_page - 1) // items_per_page
                
                # Make sure current_index is on the current page
                page_of_current = self.current_index // items_per_page
                if self.page != page_of_current:
                    self.page = page_of_current
                
                # Calculate start and end indices for current page
                start_idx = self.page * items_per_page
                end_idx = min(total_items, start_idx + items_per_page)
                
                # Display page indicator
                page_indicator = f" Page {self.page + 1}/{total_pages} "
                try:
                    stdscr.addstr(height - 6, 0, page_indicator)
                except curses.error:
                    pass
                
                # Display directory contents in columns
                for i in range(start_idx, end_idx):
                    item = contents[i]
                    is_dir = os.path.isdir(os.path.join(self.current_path, item))
                    is_marked = os.path.abspath(os.path.join(self.current_path, item)) in self.marked_files
                    
                    # Calculate column and row position
                    relative_idx = i - start_idx
                    col = relative_idx // items_per_column
                    row = relative_idx % items_per_column
                    
                    # Calculate horizontal position
                    x_pos = col * (col_width + col_padding)
                    
                    prefix = ""
                    if is_marked:
                        prefix = "[*] "
                    elif is_dir:
                        prefix = "[d] "
                    else:
                        prefix = "    "
                    
                    attr = 0
                    if i == self.current_index:
                        attr = curses.color_pair(3)
                    elif is_marked:
                        attr = curses.color_pair(1)
                    elif is_dir:
                        attr = curses.color_pair(2)
                        
                    display_text = prefix + item
                    if len(display_text) > col_width:
                        display_text = display_text[:col_width-3] + "..."
                        
                    try:
                        stdscr.addstr(2 + row, x_pos, display_text, attr)
                    except curses.error:
                        # Catch potential out-of-bounds errors
                        pass
        
        # Draw footer with marked files count or reorder instructions
        marked_count = len(self.marked_files)
        if self.reorder_mode:
            footer_text = f" Use u/d or arrow keys to move files up/down | ESC to exit reorder mode "
        else:
            footer_text = f" Marked: {marked_count} files "
            
        if self.filter_mode:
            mode_text = "FILTER MODE"
            stdscr.addstr(height - 4, 0, mode_text, curses.color_pair(4))
        elif self.reorder_mode:
            mode_text = "REORDER MODE"
            stdscr.addstr(height - 4, 0, mode_text, curses.color_pair(4))
        
        try:
            stdscr.addstr(height - 3, 0, "=" * (width - 1))
            stdscr.addstr(height - 2, 0, footer_text)
            
            # Show help line
            if self.reorder_mode:
                help_text = "u/k:Move Up | d/j:Move Down | ESC:Exit Reorder | q:Quit"
            else:
                help_text = "Press ? for help | q:Quit | m:Mark | r:Reorder | Enter:Open/Navigate | c:Concatenate"
                
            if len(help_text) > width:
                help_text = help_text[:width-4] + "..."
            stdscr.addstr(height - 1, 0, help_text)
            
            # Show status message if any
            if self.status_message:
                stdscr.addstr(height - 5, 0, self.status_message, curses.color_pair(5))
            
            # Show search mode indicator
            if self.search_mode:
                search_prompt = f"/{self.search_term}"
                stdscr.addstr(height - 5, 0, search_prompt, curses.color_pair(4))
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
        help_height = 15
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
            "←/→/h/l: Navigate left and right (multi-column)",
            "Enter: Open directory or view file",
            "Backspace: Go up one directory",
            "g: Go to top | G: Go to bottom",
            "]/PgDn: Next page | [/PgUp: Previous page",
            "m: Mark/unmark file (auto-advances to next)",
            "Q: Toggle quick-mark mode (letter shortcuts for marking)",
            "u: Unmark file and move up in list",
            "y: Copy concatenated content to clipboard",
            "Y: Copy current file contents to clipboard",
            "p: Copy file path to clipboard",
            "a: Mark all text files in current directory",
            "o: Set custom output filename",
            "f: Toggle filter mode (filter by name)",
            "/: Enter search mode (search for files by name)",
            "n: Go to next search result",
            "N: Go to previous search result",
            "r: Toggle reorder mode (change concatenation order)",
            "  - In reorder mode: u/d to move files up/down",
            "  - ESC: Exit reorder mode",
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
                self.current_filter = self.current_filter[:-1]            # Tab toggle functionality removed
            elif 32 <= key <= 126:  # Printable characters
                self.current_filter += chr(key)
            return
        # Search mode handling
        elif self.search_mode:
            if key == 27:  # ESC to exit search mode
                self.search_mode = False
                self.status_message = "Search canceled"
            elif key == 10 or key == curses.KEY_ENTER:  # Enter to execute search
                self.search_mode = False
                self.execute_search()
            elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:  # Backspace
                self.search_term = self.search_term[:-1]
            elif 32 <= key <= 126:  # Printable characters
                self.search_term += chr(key)
            return
        # Quick-mark mode handling
        elif self.quick_mark_mode:
            if key == 27:  # ESC to exit quick-mark mode
                self.quick_mark_mode = False
                self.status_message = "Exited quick-mark mode"
                return
            elif 97 <= key <= 122:  # lowercase a-z (97-122)
                self.toggle_quick_mark_by_letter(chr(key))
                return
            elif 65 <= key <= 90:  # uppercase A-Z (65-90)
                self.toggle_quick_mark_by_letter(chr(key))
                return
            elif key == ord(']') or key == curses.KEY_NPAGE:  # Next page
                self.next_quick_mark_page()
                return
            elif key == ord('[') or key == curses.KEY_PPAGE:  # Previous page
                self.prev_quick_mark_page()
                return
            return  # Ignore other keys in quick-mark mode
        # When not in filter, search, or quick-mark mode but ESC is pressed
        elif key == 27:
            # Clear filter if active
            if self.current_filter:
                self.current_filter = ""
                self.status_message = "Filter cleared"
                return
            # Clear search if active
            elif self.search_term:
                self.search_term = ""
                self.search_results = []
                self.status_message = "Search cleared"
                return
            
        # Handle reorder mode separately
        if self.reorder_mode:
            if key == 27:  # ESC to exit reorder mode
                self.reorder_mode = False
                self.status_message = "Exited reorder mode"
            elif key == ord('r'):  # Toggle reorder mode
                self.toggle_reorder_mode()
            elif key == ord('u'):  # Move file up in order
                self.move_file_up()
            elif key == ord('d'):  # Move file down in order
                self.move_file_down()
            elif key == ord('j') or key == curses.KEY_DOWN:  # Navigate down
                self.current_index = min(len(self.marked_files_order) - 1 if self.marked_files_order else 0, 
                                         self.current_index + 1)
            elif key == ord('k') or key == curses.KEY_UP:  # Navigate up
                self.current_index = max(0, self.current_index - 1)
            elif key == ord('q'):  # Quit
                self.quit_flag = True
            return
        
        # Regular navigation and commands
        if key == curses.KEY_UP or key == ord('k'):
            self.current_index = max(0, self.current_index - 1)
            self.update_page_for_current_index(stdscr)
        elif key == curses.KEY_DOWN or key == ord('j'):
            contents = self.get_filtered_directory_contents()
            self.current_index = min(len(contents) - 1 if contents else 0, self.current_index + 1)
            self.update_page_for_current_index(stdscr)
        elif key == curses.KEY_LEFT or key == ord('h'):
            # Move left in multi-column view
            items_per_column = self.get_items_per_column(stdscr)
            if items_per_column > 0 and self.current_index >= items_per_column:
                self.current_index -= items_per_column
                self.update_page_for_current_index(stdscr)
        elif key == curses.KEY_RIGHT or key == ord('l'):
            # Move right in multi-column view
            contents = self.get_filtered_directory_contents()
            items_per_column = self.get_items_per_column(stdscr)
            if items_per_column > 0 and self.current_index + items_per_column < len(contents):
                self.current_index += items_per_column
                self.update_page_for_current_index(stdscr)
        elif key == ord('g'):  # Go to top
            self.current_index = 0
            self.page = 0
        elif key == ord('G'):  # Go to bottom
            contents = self.get_filtered_directory_contents()
            self.current_index = len(contents) - 1 if contents else 0
            
            # Update page for the bottom item
            items_per_page = self.get_items_per_page(stdscr)
            if items_per_page > 0:
                self.page = self.current_index // items_per_page
                
        elif key == curses.KEY_NPAGE or key == ord(']'):  # Page Down
            self.next_page(stdscr)
        elif key == curses.KEY_PPAGE or key == ord('['):  # Page Up
            self.prev_page(stdscr)
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
            self.status_message = "Filter mode: Type to filter by filename"
        elif key == ord('/'):
            self.search_mode = True
            self.search_term = ""
            self.status_message = "Search mode: Type to search for files"
        elif key == ord('n'):
            self.navigate_to_next_search_result()
        elif key == ord('N'):
            self.navigate_to_previous_search_result()
        elif key == ord('Q'):  # Capital Q for quick-mark mode
            self.toggle_quick_mark_mode()
        elif key == ord('c'):
            self.concatenate_files()
        elif key == ord('o'):
            self.set_output_filename()
        elif key == ord('r'):  # Toggle reorder mode
            self.toggle_reorder_mode()
        elif key == ord('q'):
            self.quit_flag = True
        elif key == ord('?'):
            self.help_visible = not self.help_visible
        elif key == ord('u'):  # Unmark and move up
            self.unmark_and_move_up()
        elif key == ord('y'):  # Copy concatenated content to clipboard
            self.copy_concatenated_content_to_clipboard()
        elif key == ord('Y'):  # Copy file contents to clipboard (like vim's "yank")
            self.copy_file_contents_to_clipboard()
        elif key == ord('p'):  # Copy file path to clipboard
            self.copy_file_path_to_clipboard()

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
            # Remove from order list as well
            if full_path in self.marked_files_order:
                self.marked_files_order.remove(full_path)
            self.status_message = f"Unmarked: {selected}"
        else:
            self.marked_files[full_path] = selected
            # Add to order list
            if full_path not in self.marked_files_order:
                self.marked_files_order.append(full_path)
            self.status_message = f"Marked: {selected}"

    def unmark_and_move_up(self):
        """Unmark the currently selected file and move up one item in the list"""
        contents = self.get_filtered_directory_contents()
        if not contents or self.current_index >= len(contents):
            return
        
        selected = contents[self.current_index]
        full_path = os.path.abspath(os.path.join(self.current_path, selected))
        
        # If the file is marked, unmark it
        if full_path in self.marked_files and not os.path.isdir(full_path):
            del self.marked_files[full_path]
            self.status_message = f"Unmarked: {selected}"
        
        # Move up in the list
        if self.current_index > 0:
            self.current_index -= 1
        else:
            # Already at top, give feedback
            self.status_message += " (Already at top of list)"

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
                # Use the ordered list instead of the dictionary directly
                # If a file is in marked_files but not in the order list, add it to the end
                files_to_process = list(self.marked_files_order)
                
                # Add any marked files that aren't in the order list (should be rare)
                for filepath in self.marked_files:
                    if filepath not in files_to_process:
                        files_to_process.append(filepath)
                        
                for filepath in files_to_process:
                    if filepath in self.marked_files:  # Ensure it's still marked
                        filename = self.marked_files[filepath]
                        outfile.write(f"\n{'='*80}\n")
                        outfile.write(f"FILE: {filename}\n")
                        outfile.write(f"{'='*80}\n\n")
                        
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
                            outfile.write(infile.read())
                        
                        outfile.write("\n\n")
                    
            self.status_message = f"Concatenated {len(self.marked_files)} files to {os.path.basename(output_file)}"
        except Exception as e:
            self.status_message = f"Error during concatenation: {str(e)}"

    def copy_to_clipboard(self, text: str) -> bool:
        """Copy text to system clipboard"""
        if HAVE_PYPERCLIP:
            try:
                pyperclip.copy(text)
                return True
            except Exception as e:
                self.status_message = f"Failed to copy to clipboard: {str(e)}"
                return False
        else:
            # Fallback to platform-specific commands
            try:
                # macOS pbcopy
                process = subprocess.Popen('pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
                process.communicate(text.encode('utf-8'))
                return process.returncode == 0
            except Exception as e:
                self.status_message = f"Failed to copy to clipboard: {str(e)}"
                return False

    def copy_file_contents_to_clipboard(self):
        """Copy the currently selected file's contents to clipboard"""
        contents = self.get_filtered_directory_contents()
        if not contents or self.current_index >= len(contents):
            return
        
        selected = contents[self.current_index]
        full_path = os.path.join(self.current_path, selected)
        
        if os.path.isdir(full_path):
            self.status_message = "Cannot copy directory contents to clipboard"
            return
        
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if self.copy_to_clipboard(content):
                self.status_message = f"Copied contents of {selected} to clipboard"
            
        except Exception as e:
            self.status_message = f"Error copying file contents: {str(e)}"

    def copy_file_path_to_clipboard(self):
        """Copy the currently selected file's full path to clipboard"""
        contents = self.get_filtered_directory_contents()
        if not contents or self.current_index >= len(contents):
            return
        
        selected = contents[self.current_index]
        full_path = os.path.abspath(os.path.join(self.current_path, selected))
        
        if self.copy_to_clipboard(full_path):
            self.status_message = f"Copied path of {selected} to clipboard"
            
    def copy_concatenated_content_to_clipboard(self):
        """Copy the concatenated content of all marked files to clipboard"""
        if not self.marked_files:
            self.status_message = "No files marked for concatenation"
            return
            
        try:
            concatenated_content = ""
            
            # Use the ordered list for concatenation
            files_to_process = list(self.marked_files_order)
            
            # Add any marked files that aren't in the order list (should be rare)
            for filepath in self.marked_files:
                if filepath not in files_to_process:
                    files_to_process.append(filepath)
                    
            for filepath in files_to_process:
                if filepath in self.marked_files:  # Ensure it's still marked
                    filename = self.marked_files[filepath]
                    concatenated_content += f"\n{'='*80}\n"
                    concatenated_content += f"FILE: {filename}\n"
                    concatenated_content += f"{'='*80}\n\n"
                    
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
                        concatenated_content += infile.read()
                    
                    concatenated_content += "\n\n"
                
            if self.copy_to_clipboard(concatenated_content):
                self.status_message = f"Copied concatenated content of {len(self.marked_files)} files to clipboard"
            
        except Exception as e:
            self.status_message = f"Error copying concatenated content: {str(e)}"

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

    def execute_search(self):
        """Execute search based on current search term"""
        if not self.search_term:
            self.search_results = []
            return
            
        contents = self.get_filtered_directory_contents()
        self.search_results = []
        
        # Find all matching indices
        for i, item in enumerate(contents):
            if self.search_term.lower() in item.lower():
                self.search_results.append(i)
                
        if self.search_results:
            self.current_search_index = 0
            self.current_index = self.search_results[0]
            self.status_message = f"Found {len(self.search_results)} matches for '{self.search_term}'"
        else:
            self.status_message = f"No matches found for '{self.search_term}'"
            
    def navigate_to_next_search_result(self):
        """Move to the next search result"""
        if not self.search_results:
            self.status_message = "No active search"
            return
            
        self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
        self.current_index = self.search_results[self.current_search_index]
        self.status_message = f"Match {self.current_search_index + 1} of {len(self.search_results)}"
        
    def navigate_to_previous_search_result(self):
        """Move to the previous search result"""
        if not self.search_results:
            self.status_message = "No active search"
            return
            
        self.current_search_index = (self.current_search_index - 1) % len(self.search_results)
        self.current_index = self.search_results[self.current_search_index]
        self.status_message = f"Match {self.current_search_index + 1} of {len(self.search_results)}"
            
    def toggle_reorder_mode(self):
        """Toggle reorder mode for marked files"""
        if not self.marked_files:
            self.status_message = "No files marked to reorder"
            return
            
        self.reorder_mode = not self.reorder_mode
        if self.reorder_mode:
            self.status_message = "REORDER MODE: Use j/k or arrow keys to select, u/d to move files up/down"
        else:
            self.status_message = "Exited reorder mode"
            
    def move_file_up(self):
        """Move the currently selected file up in the concatenation order"""
        if not self.reorder_mode or not self.marked_files_order:
            return
            
        # Use current_index as index into the order list
        if self.current_index > 0 and self.current_index < len(self.marked_files_order):
            # Swap with the previous item
            self.marked_files_order[self.current_index], self.marked_files_order[self.current_index-1] = \
                self.marked_files_order[self.current_index-1], self.marked_files_order[self.current_index]
            self.current_index -= 1
            self.status_message = f"Moved {os.path.basename(self.marked_files_order[self.current_index])} up"
    
    def get_items_per_column(self, stdscr):
        """Calculate how many items fit in one column"""
        height, _ = stdscr.getmaxyx()
        return max(1, height - 7)  # Reserve lines for header, footer, status
        
    def get_items_per_page(self, stdscr):
        """Calculate how many items fit on one page"""
        return self.get_items_per_column(stdscr) * self.column_count
        
    def next_page(self, stdscr):
        """Move to the next page"""
        contents = self.get_filtered_directory_contents()
        if not contents:
            return
            
        items_per_page = self.get_items_per_page(stdscr)
        total_pages = (len(contents) + items_per_page - 1) // items_per_page
        
        if self.page < total_pages - 1:
            self.page += 1
            # Update current_index to the first item on the new page
            self.current_index = min(self.page * items_per_page, len(contents) - 1)
            self.status_message = f"Page {self.page + 1}/{total_pages}"
        
    def prev_page(self, stdscr):
        """Move to the previous page"""
        contents = self.get_filtered_directory_contents()
        if not contents:
            return
            
        items_per_page = self.get_items_per_page(stdscr)
        total_pages = (len(contents) + items_per_page - 1) // items_per_page
        
        if self.page > 0:
            self.page -= 1
            # Update current_index to the first item on the new page
            self.current_index = self.page * items_per_page
            self.status_message = f"Page {self.page + 1}/{total_pages}"
            
    def toggle_quick_mark_mode(self):
        """Toggle quick-mark mode for rapid file marking"""
        if self.reorder_mode:
            self.status_message = "Exit reorder mode first"
            return
            
        # Toggle mode
        self.quick_mark_mode = not self.quick_mark_mode
        
        if self.quick_mark_mode:
            # Prepare the quick-mark file list (all text files)
            contents = self.get_filtered_directory_contents()
            self.quick_mark_files = []
            for item in contents:
                if not os.path.isdir(os.path.join(self.current_path, item)):
                    if self.is_text_file(os.path.join(self.current_path, item)):
                        self.quick_mark_files.append(item)
            
            # Reset to first page
            self.quick_mark_page = 0
            
            if not self.quick_mark_files:
                self.quick_mark_mode = False
                self.status_message = "No text files to mark"
            else:
                total_pages = (len(self.quick_mark_files) + 51) // 52  # Ceiling division for total pages
                if total_pages > 1:
                    self.status_message = f"QUICK-MARK MODE: Page 1/{total_pages} - [/] to navigate, ESC to exit"
                else:
                    self.status_message = "QUICK-MARK MODE: Press letters to mark/unmark files, ESC to exit"
        else:
            self.status_message = "Exited quick-mark mode"
            
    def draw_quick_mark_mode(self, stdscr):
        """Draw the quick-mark mode interface"""
        height, width = stdscr.getmaxyx()
        
        # Calculate layout
        max_filename_width = width - 10  # Allow for label and padding
        
        # Calculate pagination
        files_per_page = 52  # a-z + A-Z
        total_files = len(self.quick_mark_files)
        total_pages = (total_files + files_per_page - 1) // files_per_page  # Ceiling division
        
        # Show page indicator if multiple pages
        if total_pages > 1:
            page_indicator = f" Page {self.quick_mark_page + 1}/{total_pages} - '[' prev, ']' next "
            try:
                stdscr.addstr(height - 6, 0, page_indicator)
            except curses.error:
                pass
        
        # Calculate start and end indices for current page
        start_idx = self.quick_mark_page * files_per_page
        end_idx = min(total_files, start_idx + files_per_page)
        page_files = self.quick_mark_files[start_idx:end_idx]
        
        # First, draw lowercase letters (a-z)
        lower_count = min(26, len(page_files))
        for i in range(lower_count):
            letter = chr(97 + i)  # 'a' starts at 97
            filename = page_files[i]
            full_path = os.path.abspath(os.path.join(self.current_path, filename))
            is_marked = full_path in self.marked_files
            
            # Truncate filename if needed
            if len(filename) > max_filename_width:
                display_name = filename[:max_filename_width-3] + "..."
            else:
                display_name = filename
                
            # Prepare the display line
            if is_marked:
                label = f"[{letter}*]"
                attr = curses.color_pair(1)  # Marked color
            else:
                label = f"[{letter} ]"
                attr = 0  # Normal color
                
            # Display the line
            try:
                row = 2 + i
                if row < height - 6:  # Ensure we don't go off-screen
                    stdscr.addstr(row, 0, f"{label} {display_name}", attr)
            except curses.error:
                pass
                
        # Then, draw uppercase letters (A-Z) if we have more files
        upper_count = min(26, len(page_files) - 26)
        for i in range(upper_count):
            letter = chr(65 + i)  # 'A' starts at 65
            filename = page_files[26 + i]
            full_path = os.path.abspath(os.path.join(self.current_path, filename))
            is_marked = full_path in self.marked_files
            
            # Truncate filename if needed
            if len(filename) > max_filename_width:
                display_name = filename[:max_filename_width-3] + "..."
            else:
                display_name = filename
                
            # Prepare the display line
            if is_marked:
                label = f"[{letter}*]"
                attr = curses.color_pair(1)  # Marked color
            else:
                label = f"[{letter} ]"
                attr = 0  # Normal color
                
            # Display the line
            try:
                row = 2 + lower_count + i
                if row < height - 6:  # Ensure we don't go off-screen
                    stdscr.addstr(row, 0, f"{label} {display_name}", attr)
            except curses.error:
                pass
                
    def toggle_quick_mark_by_letter(self, letter):
        """Toggle mark status for a file in quick-mark mode based on its letter"""
        letter_index = -1
        
        # Calculate index based on letter
        if 'a' <= letter <= 'z':
            letter_index = ord(letter) - 97  # 'a' is 0
        elif 'A' <= letter <= 'Z':
            letter_index = ord(letter) - 65 + 26  # 'A' is 26
            
        # Calculate actual index in the full list, accounting for pagination
        files_per_page = 52
        start_idx = self.quick_mark_page * files_per_page
        actual_index = start_idx + letter_index
            
        # Check if file exists at this index
        if 0 <= letter_index < 52 and actual_index < len(self.quick_mark_files):
            filename = self.quick_mark_files[actual_index]
            full_path = os.path.abspath(os.path.join(self.current_path, filename))
            
            # Toggle mark status
            if full_path in self.marked_files:
                del self.marked_files[full_path]
                # Remove from order list as well
                if full_path in self.marked_files_order:
                    self.marked_files_order.remove(full_path)
                self.status_message = f"Unmarked: {filename}"
            else:
                self.marked_files[full_path] = filename
                # Add to order list
                if full_path not in self.marked_files_order:
                    self.marked_files_order.append(full_path)
                self.status_message = f"Marked: {filename}"
                
    def next_quick_mark_page(self):
        """Move to the next page in quick-mark mode"""
        files_per_page = 52
        total_pages = (len(self.quick_mark_files) + files_per_page - 1) // files_per_page
        
        if self.quick_mark_page < total_pages - 1:
            self.quick_mark_page += 1
            self.status_message = f"Page {self.quick_mark_page + 1}/{total_pages}"
        
    def prev_quick_mark_page(self):
        """Move to the previous page in quick-mark mode"""
        files_per_page = 52
        total_pages = (len(self.quick_mark_files) + files_per_page - 1) // files_per_page
        
        if self.quick_mark_page > 0:
            self.quick_mark_page -= 1
            self.status_message = f"Page {self.quick_mark_page + 1}/{total_pages}"
            
    def update_page_for_current_index(self, stdscr):
        """Update the page based on the current index"""
        items_per_page = self.get_items_per_page(stdscr)
        if items_per_page > 0:
            new_page = self.current_index // items_per_page
            if new_page != self.page:
                self.page = new_page
                
    def move_file_down(self):
        """Move the currently selected file down in the concatenation order"""
        if not self.reorder_mode or not self.marked_files_order:
            return
            
        # Use current_index as index into the order list
        if self.current_index < len(self.marked_files_order) - 1:
            # Swap with the next item
            self.marked_files_order[self.current_index], self.marked_files_order[self.current_index+1] = \
                self.marked_files_order[self.current_index+1], self.marked_files_order[self.current_index]
            self.current_index += 1
            self.status_message = f"Moved {os.path.basename(self.marked_files_order[self.current_index])} down"

def main():
    """Entry point for the application"""
    start_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    app = FileConcatenator(start_path)
    curses.wrapper(app.run)

if __name__ == "__main__":
    main()
