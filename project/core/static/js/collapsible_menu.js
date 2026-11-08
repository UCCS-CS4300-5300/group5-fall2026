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

    // Check if the URL has a search query (e.g. ?q=apples). 
    // If it does, automatically open the sidebar and jump straight to the Pantry Organizer panel!
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('q') && urlParams.get('q').trim() !== '') {
        showPanel('panel-pantry');
        if (sideContainer) {
            sideContainer.classList.remove('collapsed');
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