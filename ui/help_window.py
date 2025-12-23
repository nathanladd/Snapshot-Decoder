"""
Help Window for Snapshot Decoder.

Provides a local HTML-based help system with a table of contents
navigation frame on the left and HTML content viewer on the right.
"""

import tkinter as tk
from tkinter import ttk
import json
import os
import urllib.request
import threading
import webbrowser
from tkinterweb import HtmlFrame
from utils import resource_path
from version import APP_VERSION
from domain.constants import UPDATE_URL


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
        # Open external links in system browser
        if url.startswith(('http://', 'https://')):
            webbrowser.open(url)
        # Navigate to local help files
        elif url.endswith('.html'):
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
            items: List of TOC items, each with 'title', 'page', and optional 'children', 'expanded'
            parent: Parent node ID for insertion
        """
        for item in items:
            title = item.get("title", "Untitled")
            page = item.get("page", "")
            children = item.get("children", [])
            expanded = item.get("expanded", True)  # Default to expanded for backward compatibility
            
            # Insert node with page as value
            node_id = self.toc_tree.insert(parent, "end", text=title, values=(page,))
            
            # Recursively add children
            if children:
                self._populate_toc(children, node_id)
                # Expand parent nodes based on expanded flag
                self.toc_tree.item(node_id, open=expanded)
    
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
        # Special handling for updating page - inject version info
        if page_name == "updating.html":
            self._load_updating_page()
            return
        
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
    
    def _load_updating_page(self):
        """Load the updating page with dynamic version information."""
        # Load the base HTML
        page_path = os.path.join(self.help_dir, "updating.html")
        css_path = os.path.join(self.help_dir, "styles.css")
        
        # Read CSS for inline use
        css_content = ""
        try:
            with open(css_path, "r", encoding="utf-8") as f:
                css_content = f.read()
        except:
            pass
        
        # Show initial content with "checking..." status
        html = self._build_updating_html(css_content, APP_VERSION, "Checking...", None)
        self.html_frame.load_html(html)
        
        # Fetch latest version in background thread
        thread = threading.Thread(target=self._fetch_latest_version, args=(css_content,), daemon=True)
        thread.start()
    
    def _fetch_latest_version(self, css_content):
        """Fetch the latest version from GitHub releases API."""
        latest_version = None
        download_url = UPDATE_URL
        
        try:
            url = "https://api.github.com/repos/nathanladd/Snapshot-Decoder/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "Snapshot-Decoder"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                latest_version = data.get("tag_name", "").lstrip("v")
                # Get direct download URL from release assets if available
                assets = data.get("assets", [])
                if assets:
                    download_url = assets[0].get("browser_download_url", download_url)
        except Exception as e:
            latest_version = "Unable to check"
        
        # Update UI on main thread
        self.after(0, lambda: self._update_version_display(css_content, latest_version, download_url))
    
    def _update_version_display(self, css_content, latest_version, download_url):
        """Update the updating page with fetched version info."""
        html = self._build_updating_html(css_content, APP_VERSION, latest_version, download_url)
        self.html_frame.load_html(html)
    
    def _build_updating_html(self, css_content, current_version, latest_version, download_url):
        """Build the updating page HTML with version information."""
        # Determine update status
        if latest_version == "Checking...":
            status_class = "info"
            status_msg = "Checking for updates..."
        elif latest_version == "Unable to check":
            status_class = "note"
            status_msg = "Unable to check for updates. Please visit the download page manually."
        elif latest_version and current_version:
            try:
                # Simple version comparison
                current_parts = [int(x) for x in current_version.split(".")]
                latest_parts = [int(x) for x in latest_version.split(".")]
                if latest_parts > current_parts:
                    status_class = "tip"
                    status_msg = f"A new version is available! ({latest_version})"
                else:
                    status_class = "tip"
                    status_msg = "You are running the latest version."
            except:
                status_class = "info"
                status_msg = f"Latest version: {latest_version}"
        else:
            status_class = "info"
            status_msg = ""
        
        download_link = download_url or UPDATE_URL
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <style>{css_content}</style>
</head>
<body>
    <h1>Updating Snapshot Decoder</h1>
    
    <p>Keep Snapshot Decoder up to date to get the latest features, bug fixes, and support for new snapshot types.</p>
    
    <h2>Version Information</h2>
    <table>
        <tr><th>Location</th><th>Version</th></tr>
        <tr><td><strong>Your Software Version</strong></td><td>{current_version}</td></tr>
        <tr><td><strong>Latest Official Version</strong></td><td>{latest_version}</td></tr>
    </table>
    
    <div class="{status_class}">
        <strong>{status_msg}</strong>
    </div>
    
    <h2>Download</h2>
    <p>Visit the official download page to get the latest version:</p>
    <p><a href="{download_link}" target="_blank"><strong>{download_link}</strong></a></p>
    
    <h2>How to Update</h2>
    <ol>
        <li>Download the latest version from the link above</li>
        <li>Close Snapshot Decoder if it is currently running</li>
        <li>Run the new installer</li>
        <li>When prompted, install to the same location as your existing installation</li>
        <li>The new version will replace the old files automatically</li>
        <li>Launch Snapshot Decoder to verify the update</li>
    </ol>
    
    <div class="info">
        <strong>Tip:</strong> Your settings and preferences are preserved when updating. 
        You do not need to uninstall the old version first.
    </div>
</body>
</html>
"""
