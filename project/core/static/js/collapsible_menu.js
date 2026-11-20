document.addEventListener('DOMContentLoaded', () => {
    const menuDropdownToggle = document.getElementById('menu-dropdown-toggle');
    const sideContainer = document.getElementById('side-container');
    const menuArrow = document.getElementById('menu-arrow');
    const sidebarNavLinks = document.querySelectorAll('.sidebar-nav-link');
    const sidebarMainMenu = document.getElementById('sidebar-main-menu');
    const featurePanels = document.querySelectorAll('.sidebar-feature-panel');
    const backToMenuButtons = document.querySelectorAll('.back-to-menu-btn');

    // Helper function to switch to a specific panel
    function showPanel(panelId) {
        if (sidebarMainMenu) {
            sidebarMainMenu.style.display = 'none';
        }
        featurePanels.forEach(panel => {
            panel.style.display = 'none';
        });
        const targetPanel = document.getElementById(panelId);
        if (targetPanel) {
            targetPanel.style.display = 'block';
        }
    }

    // The sidebar renders open on every page load, and a drag and drop
    // does a full page reload, so it reopened after every single move.
    // Put it back where the user left it instead.
    const SIDEBAR_KEY = 'sidebarCollapsed';

    if (sideContainer) {
        try {
            if (sessionStorage.getItem(SIDEBAR_KEY) === 'true') {
                sideContainer.classList.add('collapsed');
            }
        } catch (err) {
            // Private browsing or blocked storage. Opening by default is
            // the old behaviour, so there is nothing to recover from.
        }
    }

    // Check if the URL has a search query (e.g. ?q=apples). 
    // If it does, automatically open the sidebar and jump straight to the Pantry Organizer panel!
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('q') && urlParams.get('q').trim() !== '') {
        showPanel('panel-pantry');
        if (sideContainer) {
            sideContainer.classList.remove('collapsed');

            // A search opens the sidebar on purpose, so record that or the
            // next reload would close it again underneath the results.
            try {
                sessionStorage.setItem(SIDEBAR_KEY, 'false');
            } catch (err) {
                // Nothing to do.
            }
        }
        if (menuArrow) {
            menuArrow.style.display = 'none'; // Ensure arrow is hidden when open on startup search
        }
    }

    // Toggle side container open/closed on Menu button click
    if (menuDropdownToggle && sideContainer) {
        menuDropdownToggle.addEventListener('click', (e) => {
            e.preventDefault();
            sideContainer.classList.toggle('collapsed');

            // Remember it so the next page load matches.
            try {
                sessionStorage.setItem(
                    SIDEBAR_KEY,
                    sideContainer.classList.contains('collapsed'));
            } catch (err) {
                // The toggle still worked, it just will not persist.
            }
        });
    }

    // Switch submenus inside the side container without refreshing
    sidebarNavLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetPanelId = link.getAttribute('data-target');
            showPanel(targetPanelId);
        });
    });

    // Return back to the main menu view from a feature panel
    backToMenuButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();

            // Hide all feature panels
            featurePanels.forEach(panel => {
                panel.style.display = 'none';
            });

            // Show main menu view again
            if (sidebarMainMenu) {
                sidebarMainMenu.style.display = 'block';
            }
        });
    });
});