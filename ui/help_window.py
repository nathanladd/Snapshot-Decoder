"""
Help Window for Snapshot Decoder.

Provides a local HTML-based help system with a table of contents
navigation frame on the left and HTML content viewer on the right.
"""

import tkinter as tk
from tkinter import ttk
import json
import os
from tkinterweb import HtmlFrame
from utils import resource_path


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
        
        # Right frame - Content using HtmlFrame for proper CSS rendering
        content_frame = ttk.Frame(self.paned)
        
        self.html_frame = HtmlFrame(content_frame, messages_enabled=False)
        self.html_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Disable link navigation to external sites
        self.html_frame.on_link_click(self._on_link_click)
        
        self.paned.add(content_frame, weight=4)
    
    def _on_link_click(self, url):
        """Handle link clicks within the HTML content."""
        # Only allow navigation to local help files
        if url.endswith('.html') and not url.startswith(('http://', 'https://')):
            # Extract just the filename
            page_name = os.path.basename(url)
            self._load_page(page_name)
    
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
                # Load the HTML file directly - tkinterweb handles CSS
                self.html_frame.load_file(page_path)
            else:
                html_content = f"""
                <html><body>
                <h1>Page Not Found</h1>
                <p>The help page <code>{page_name}</code> could not be found.</p>
                <p>Help files are under construction.</p>
                </body></html>
                """
                self.html_frame.load_html(html_content)
            
        except Exception as e:
            self.html_frame.load_html(f"<html><body><h1>Error</h1><p>Failed to load page: {e}</p></body></html>")
