/* Table of Contents sidebar – auto-injected into every help page */
(function () {
    "use strict";

    var currentPage = location.pathname.split("/").pop() || "index.html";

    var toc = [
        {
            heading: "User Interface",
            items: [
                { title: "Snapshot Data Panel", href: "snapshot_panel.html" },
                { title: "Status Bar",          href: "status_bar.html" },
                { title: "Quick Charts",        href: "quick_charts.html" },
                { title: "Chart Controls",      href: "chart_controls.html" },
                { title: "Keyboard Shortcuts",  href: "shortcuts.html" }
            ]
        },
        {
            heading: "Working with Data",
            items: [
                { title: "Opening Files",     href: "opening_files.html" },
                { title: "Raw Data Table",    href: "raw_data_table.html" },
                { title: "Cleaned Data Table", href: "cleaned_data_table.html" }
            ]
        },
        {
            heading: "Getting Started",
            items: [
                { title: "Getting Started",              href: "getting_started.html" },
                { title: "Seven Step Diagnostic Process", href: "seven_step.html" },
                { title: "Troubleshooting",              href: "troubleshooting.html" }
            ]
        }
    ];

    /* ── Build sidebar HTML ── */
    var html = '<div class="toc-sidebar"><div class="toc-inner">';
    html += '<a class="toc-home' + (currentPage === "index.html" ? " toc-active" : "") +
            '" href="index.html">Home</a>';

    for (var s = 0; s < toc.length; s++) {
        var section = toc[s];
        html += '<h4 class="toc-heading">' + section.heading + '</h4><ul class="toc-list">';
        for (var i = 0; i < section.items.length; i++) {
            var item = section.items[i];
            var active = item.href === currentPage ? " toc-active" : "";
            html += '<li><a class="toc-link' + active + '" href="' + item.href + '">' +
                    item.title + '</a></li>';
        }
        html += '</ul>';
    }
    html += '</div></div>';

    /* ── Wrap existing body content ── */
    var wrapper = document.createElement("div");
    wrapper.className = "toc-layout";

    // Move all current body children into a main content div
    var main = document.createElement("div");
    main.className = "toc-content";
    while (document.body.firstChild) {
        main.appendChild(document.body.firstChild);
    }

    // Insert sidebar + main into wrapper, then into body
    var sidebarDiv = document.createElement("div");
    sidebarDiv.innerHTML = html;
    wrapper.appendChild(sidebarDiv.firstChild);
    wrapper.appendChild(main);
    document.body.appendChild(wrapper);
})();
