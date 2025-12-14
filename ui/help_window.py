"""
Help Window for Snapshot Decoder.

Provides a local HTML-based help system with a table of contents
navigation frame on the left and HTML content viewer on the right.
"""

import tkinter as tk
from tkinter import ttk, font as tkfont
import json
import os
import re
from html.parser import HTMLParser
from PIL import Image, ImageTk
from utils import resource_path


class SimpleHTMLParser(HTMLParser):
    """Simple HTML parser that converts HTML to styled text segments."""
    
    def __init__(self, help_dir=None):
        super().__init__()
        self.segments = []  # List of (text, tags) tuples or ('__IMAGE__', image_path)
        self.current_tags = []
        self.in_style = False
        self.in_list = False
        self.list_counter = 0
        self.is_ordered_list = False
        self.help_dir = help_dir
        
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == 'style':
            self.in_style = True
        elif tag in ('h1', 'h2'):
            # Add 2x newline before headings to ensure they start on a new line with a little space above
            self.segments.append(('\n\n', []))
            self.current_tags.append(tag)
        elif tag in ('h3'):
            # Olny add 1x newline before headings to ensure they start on a new line with a little space above
            self.segments.append(('\n', []))
            self.current_tags.append(tag)
        elif tag == 'strong' or tag == 'b':
            self.current_tags.append('bold')
        elif tag == 'em' or tag == 'i':
            self.current_tags.append('italic')
        elif tag == 'code' or tag == 'kbd':
            self.current_tags.append('code')
        elif tag == 'p':
            if self.segments and not self.segments[-1][0].endswith('\n\n'):
                self.segments.append(('\n', []))
        elif tag == 'br':
            self.segments.append(('\n', []))
        elif tag == 'ul':
            self.in_list = True
            self.is_ordered_list = False
            self.list_counter = 0
            self.segments.append(('\n', []))
        elif tag == 'ol':
            self.in_list = True
            self.is_ordered_list = True
            self.list_counter = 0
            self.segments.append(('\n', []))
        elif tag == 'li':
            self.list_counter += 1
            if self.is_ordered_list:
                self.segments.append((f'  {self.list_counter}. ', ['bold']))
            else:
                self.segments.append(('  • ', ['bold']))
        elif tag == 'div':
            # Check for styled divs
            class_attr = dict(attrs).get('class', '')
            if 'highlight' in class_attr or 'tip' in class_attr:
                self.current_tags.append('highlight')
            elif 'note' in class_attr or 'problem' in class_attr:
                self.current_tags.append('note')
            elif 'solution' in class_attr:
                self.current_tags.append('solution')
            elif 'step' in class_attr or 'info' in class_attr:
                self.current_tags.append('info')
            self.segments.append(('\n', []))
        elif tag == 'table':
            #self.segments.append(('\n', []))
            self.current_tags.append('table')
        elif tag == 'th':
            self.current_tags.append('bold')
        elif tag == 'td' or tag == 'th':
            self.segments.append(('  ', []))
        elif tag == 'tr':
            self.segments.append(('\n', []))
        elif tag == 'img':
            # Handle image tags
            attrs_dict = dict(attrs)
            src = attrs_dict.get('src', '')
            if src and self.help_dir:
                # Resolve relative path from help directory
                if src.startswith('../'):
                    img_path = os.path.normpath(os.path.join(self.help_dir, src))
                else:
                    img_path = os.path.join(self.help_dir, src)
                # Parse max-width from style if present
                style = attrs_dict.get('style', '')
                max_width = None
                if 'max-width' in style:
                    import re
                    match = re.search(r'max-width:\s*(\d+)px', style)
                    if match:
                        max_width = int(match.group(1))
                self.segments.append(('\n', []))
                self.segments.append(('__IMAGE__', img_path, max_width))
                self.segments.append(('\n', []))
            
    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == 'style':
            self.in_style = False
        elif tag in ('h1'):
            if tag in self.current_tags:
                self.current_tags.remove(tag)
            self.segments.append(('\n', []))
        elif tag in ('h2','h3'):
            if tag in self.current_tags:
                self.current_tags.remove(tag)
        elif tag == 'strong' or tag == 'b':
            if 'bold' in self.current_tags:
                self.current_tags.remove('bold')
        elif tag == 'em' or tag == 'i':
            if 'italic' in self.current_tags:
                self.current_tags.remove('italic')
        elif tag == 'code' or tag == 'kbd':
            if 'code' in self.current_tags:
                self.current_tags.remove('code')
        elif tag == 'p':
            self.segments.append(('\n', []))
        elif tag in ('ul', 'ol'):
            self.in_list = False
            self.segments.append(('\n', []))
        elif tag == 'li':
            self.segments.append(('\n', []))
        elif tag == 'div':
            for t in ['highlight', 'note', 'solution', 'info']:
                if t in self.current_tags:
                    self.current_tags.remove(t)
                    break
            #self.segments.append(('\n', []))
        elif tag == 'table':
            if 'table' in self.current_tags:
                self.current_tags.remove('table')
        elif tag == 'th':
            if 'bold' in self.current_tags:
                self.current_tags.remove('bold')
            self.segments.append(('\t', []))
        elif tag == 'td':
            self.segments.append(('\t', []))
            
    def handle_data(self, data):
        if self.in_style:
            return
        # Clean whitespace
        data = re.sub(r'\s+', ' ', data)
        if data.strip():
            self.segments.append((data, list(self.current_tags)))


class HelpWindow(tk.Toplevel):
    """
    Help window with table of contents navigation and HTML content display.
    
    Left pane: TreeView showing help topics hierarchy
    Right pane: Styled text widget displaying help content
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Snapshot Decoder Help")
        self.geometry("950x650")
        self.minsize(700, 400)
        
        # Center window on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")
        
        # Help content directory
        self.help_dir = resource_path("data/help")
        
        # Build UI
        self._build_ui()
        
        # Load table of contents
        self._load_toc()
        
        # Load initial page
        self._load_page("index.html")
    
    def _build_ui(self):
        """Build the help window UI with paned layout."""
        # Main paned window
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left frame - Table of Contents
        toc_frame = ttk.Frame(self.paned, width=220)
        toc_frame.pack_propagate(False)
        
        toc_label = ttk.Label(toc_frame, text="Contents", font=("Segoe UI", 11, "bold"))
        toc_label.pack(pady=(8, 4), padx=8, anchor="w")
        
        # TreeView for TOC
        self.toc_tree = ttk.Treeview(toc_frame, show="tree", selectmode="browse")
        toc_scroll = ttk.Scrollbar(toc_frame, orient="vertical", command=self.toc_tree.yview)
        self.toc_tree.configure(yscrollcommand=toc_scroll.set)
        
        self.toc_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=5)
        toc_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Bind selection event
        self.toc_tree.bind("<<TreeviewSelect>>", self._on_toc_select)
        
        self.paned.add(toc_frame, weight=1)
        
        # Right frame - Content
        content_frame = ttk.Frame(self.paned)
        
        # Text widget with scrollbar for content
        text_frame = ttk.Frame(content_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.scrollbar = ttk.Scrollbar(text_frame, orient="vertical")
        self.text_widget = tk.Text(
            text_frame, 
            wrap=tk.WORD, 
            font=("Segoe UI", 10),
            bg="white",
            padx=15,
            pady=15,
            yscrollcommand=self.scrollbar.set,
            cursor="arrow",
            state=tk.DISABLED
        )
        self.scrollbar.config(command=self.text_widget.yview)
        
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure text tags for styling
        self._configure_text_tags()
        
        self.paned.add(content_frame, weight=4)
    
    def _configure_text_tags(self):
        """Configure text tags for different HTML elements."""
        # Headers
        self.text_widget.tag_configure("h1", font=("Segoe UI", 18, "bold"), foreground="#2c5282", 
                                        spacing1=10, spacing3=5)
        self.text_widget.tag_configure("h2", font=("Segoe UI", 14, "bold"), foreground="#2d3748",
                                        spacing1=15, spacing3=5)
        self.text_widget.tag_configure("h3", font=("Segoe UI", 12, "bold"), foreground="#4a5568",
                                        spacing1=10, spacing3=3)
        
        # Text formatting
        self.text_widget.tag_configure("bold", font=("Segoe UI", 10, "bold"))
        self.text_widget.tag_configure("italic", font=("Segoe UI", 10, "italic"))
        self.text_widget.tag_configure("code", font=("Consolas", 9), background="#edf2f7", 
                                        foreground="#2d3748")
        
        # Callout boxes
        self.text_widget.tag_configure("highlight", background="#ebf8ff", lmargin1=20, lmargin2=20,
                                        rmargin=20, spacing1=5, spacing3=5)
        self.text_widget.tag_configure("note", background="#fefcbf", lmargin1=20, lmargin2=20,
                                        rmargin=20, spacing1=5, spacing3=5)
        self.text_widget.tag_configure("solution", background="#c6f6d5", lmargin1=20, lmargin2=20,
                                        rmargin=20, spacing1=5, spacing3=5)
        self.text_widget.tag_configure("info", background="#f7fafc", lmargin1=20, lmargin2=20,
                                        rmargin=20, spacing1=5, spacing3=5)
    
    def _load_toc(self):
        """Load table of contents from JSON file."""
        toc_path = os.path.join(self.help_dir, "toc.json")
        
        try:
            if os.path.exists(toc_path):
                with open(toc_path, "r", encoding="utf-8") as f:
                    toc_data = json.load(f)
                self._populate_toc(toc_data)
            else:
                # Default TOC if file not found
                self._populate_toc([
                    {"title": "Welcome", "page": "index.html"},
                    {"title": "Getting Started", "page": "getting_started.html"},
                    {"title": "Working with Snapshots", "page": "snapshots.html"},
                    {"title": "Using Charts", "page": "using_charts.html"},
                    {"title": "Keyboard Shortcuts", "page": "shortcuts.html"},
                    {"title": "Troubleshooting", "page": "troubleshooting.html"},
                ])
        except Exception as e:
            print(f"Error loading TOC: {e}")
            self.toc_tree.insert("", "end", text="Help", values=("index.html",))
    
    def _populate_toc(self, items, parent=""):
        """
        Recursively populate the TOC tree.
        
        Args:
            items: List of TOC items, each with 'title', 'page', and optional 'children'
            parent: Parent node ID for insertion
        """
        for item in items:
            title = item.get("title", "Untitled")
            page = item.get("page", "")
            children = item.get("children", [])
            
            # Insert node with page as value
            node_id = self.toc_tree.insert(parent, "end", text=title, values=(page,))
            
            # Recursively add children
            if children:
                self._populate_toc(children, node_id)
                # Expand parent nodes
                self.toc_tree.item(node_id, open=True)
    
    def _on_toc_select(self, event):
        """Handle TOC tree selection."""
        selection = self.toc_tree.selection()
        if selection:
            item = selection[0]
            values = self.toc_tree.item(item, "values")
            if values and values[0]:
                self._load_page(values[0])
    
    def _load_page(self, page_name):
        """
        Load an HTML page into the content viewer.
        
        Args:
            page_name: Name of the HTML file to load from help directory
        """
        page_path = os.path.join(self.help_dir, page_name)
        
        try:
            if os.path.exists(page_path):
                with open(page_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
            else:
                html_content = f"""
                <h1>Page Not Found</h1>
                <p>The help page <code>{page_name}</code> could not be found.</p>
                <p>Please ensure help files are installed in the data/help directory.</p>
                """
            
            self._render_html(html_content)
            
        except Exception as e:
            self._render_html(f"<h1>Error</h1><p>Failed to load page: {e}</p>")
    
    def _render_html(self, html_content):
        """
        Render HTML content to the text widget with styling.
        
        Args:
            html_content: HTML string to render
        """
        # Parse HTML
        parser = SimpleHTMLParser(self.help_dir)
        parser.feed(html_content)
        
        # Keep references to images to prevent garbage collection
        self._images = []
        
        # Enable editing
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete("1.0", tk.END)
        
        # Insert styled segments
        for segment in parser.segments:
            if len(segment) == 3 and segment[0] == '__IMAGE__':
                # Handle image
                _, img_path, max_width = segment
                try:
                    if os.path.exists(img_path):
                        img = Image.open(img_path)
                        # Resize if max_width specified
                        if max_width and img.width > max_width:
                            ratio = max_width / img.width
                            new_height = int(img.height * ratio)
                            img = img.resize((max_width, new_height), Image.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        self._images.append(photo)  # Keep reference
                        self.text_widget.image_create(tk.END, image=photo)
                except Exception as e:
                    self.text_widget.insert(tk.END, f"[Image: {img_path}]")
            else:
                text, tags = segment[0], segment[1] if len(segment) > 1 else []
                if tags:
                    self.text_widget.insert(tk.END, text, tuple(tags))
                else:
                    self.text_widget.insert(tk.END, text)
        
        # Disable editing and scroll to top
        self.text_widget.config(state=tk.DISABLED)
        self.text_widget.yview_moveto(0)
