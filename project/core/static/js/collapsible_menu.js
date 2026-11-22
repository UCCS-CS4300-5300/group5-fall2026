document.addEventListener('DOMContentLoaded', () => {
    const menuDropdownToggle = document.getElementById('menu-dropdown-toggle');
    const sideContainer = document.getElementById('side-container');
    const menuArrow = document.getElementById('menu-arrow');
    const sidebarNavLinks = document.querySelectorAll('.sidebar-nav-link');
    const sidebarMainMenu = document.getElementById('sidebar-main-menu');
    const featurePanels = document.querySelectorAll('.sidebar-feature-panel');
    const backToMenuButtons = document.querySelectorAll('.back-to-menu-btn');

    // A drag and drop does a full page reload, so anything the sidebar
    // remembers has to survive that or the user fights it on every move.
    const SIDEBAR_KEY = 'sidebarCollapsed';
    const VIEW_KEY = 'sidebarView';

    function remember(key, value) {
        try {
            sessionStorage.setItem(key, value);
        } catch (err) {
            // Private browsing or blocked storage. The click still worked,
            // it just will not survive the next load.
        }
    }

    function recall(key) {
        try {
            return sessionStorage.getItem(key);
        } catch (err) {
            return null;
        }
    }

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

    function showMainMenu() {
        featurePanels.forEach(panel => {
            panel.style.display = 'none';
        });
        if (sidebarMainMenu) {
            sidebarMainMenu.style.display = 'block';
        }
    }

    // Open or closed. home.html also applies this before paint, so the
    // sidebar does not render open and then snap shut; this is the copy
    // that keeps working if that inline script is ever removed.
    if (sideContainer && recall(SIDEBAR_KEY) === 'true') {
        sideContainer.classList.add('collapsed');
    }

    // Which view was showing. Without this, pressing the back arrow and
    // then dragging an item would drop you back in the panel you just left.
    const storedView = recall(VIEW_KEY);
    if (storedView && storedView !== 'menu') {
        showPanel(storedView);
    }

    // Landing on a ?q= URL should open the sidebar on the Pantry Organizer
    // so the results are visible. A drag and drop reload keeps ?q= in the
    // URL though, so this runs on every move. Only steer the user on the
    // first load, when nothing is remembered; after that their own choices
    // win, whether that is collapsing the sidebar or going back to the menu.
    const urlParams = new URLSearchParams(window.location.search);
    const firstVisit = storedView === null;

    if (urlParams.has('q') && urlParams.get('q').trim() !== '' && firstVisit) {
        showPanel('panel-pantry');
        remember(VIEW_KEY, 'panel-pantry');

        if (sideContainer && recall(SIDEBAR_KEY) !== 'true') {
            sideContainer.classList.remove('collapsed');
            remember(SIDEBAR_KEY, 'false');
        }
        if (menuArrow) {
            menuArrow.style.display = 'none';
        }
    }

    // Toggle side container open/closed on Menu button click
    if (menuDropdownToggle && sideContainer) {
        menuDropdownToggle.addEventListener('click', (e) => {
            e.preventDefault();
            sideContainer.classList.toggle('collapsed');
            remember(SIDEBAR_KEY, sideContainer.classList.contains('collapsed'));
        });
    }

    // Switch submenus inside the side container without refreshing
    sidebarNavLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetPanelId = link.getAttribute('data-target');

            // A nav link with no data-target would hide the menu and then
            // find no panel to show, leaving the sidebar blank with no way
            // back. The About / Manual link opens a dialog and has none.
            if (!targetPanelId) {
                return;
            }

            showPanel(targetPanelId);
            remember(VIEW_KEY, targetPanelId);
        });
    });

    // Return back to the main menu view from a feature panel
    backToMenuButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            showMainMenu();
            remember(VIEW_KEY, 'menu');
        });
    });
});