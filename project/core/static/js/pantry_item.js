
// Ellipses menu JS helper functions

function togglePantryMenu(event, productId) {
    event.stopPropagation();
    // Close any other open submenus first
    document.querySelectorAll('.item-submenu').forEach(menu => {
        if (menu.id !== 'item-submenu-' + productId) {
            menu.classList.remove('show');
        }
    });
    const submenu = document.getElementById('item-submenu-' + productId);
    submenu.classList.toggle('show');
}

function closePantryMenu(productId) {
    const submenu = document.getElementById('item-submenu-' + productId);
    if (submenu) {
        submenu.classList.remove('show');
    }
}

// Close menus when clicking anywhere else on the page
window.addEventListener('click', () => {
    document.querySelectorAll('.item-submenu').forEach(menu => {
        menu.classList.remove('show');
    });
});

// dynamic search for global pantry
const searchInput = document.getElementById('search-input');
const searchForm = document.getElementById('search-form');
let timeout = null;

searchInput.addEventListener('keyup', function () {
  clearTimeout(timeout);
  timeout = setTimeout(function () {
    searchForm.submit();
  }, 1500);
});

// ----------------------------------------------------------------------------------------
// Highligting for the various circle items
// ----------------------------------------------------------------------------------------

const circles = document.querySelectorAll('.item-circle');
circles.forEach(circle => {

  // Add listener for entering the element
  circle.addEventListener('mouseenter', () => {
    circle.style.backgroundColor = '#cdcdcd';
  });

  // Add listener exiting the element
  circle.addEventListener('mouseleave', () => {
    circle.style.backgroundColor = '#ffffff';
  });
});