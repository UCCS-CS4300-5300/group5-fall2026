//const { use } = require("react");

// get Parent Element With Class List Name if it exists
function getParentWithClassListName(element, targetName) {
  let current = element.parentElement;
  while (current) {
    if (current.classList.contains(targetName)) {
      return current;
    }
    current = current.parentElement;
  }
  return null;
}

const validDropZones = new Set([
  'SHELF',
  'FRIDGE',
  'FREEZER',
  'BAG',
  'DELETE'
]);

// Add drop Zone Listener. 
function addDropZoneListeners(dropZone, zoneName) {
  // Add event listener for the drag over to prevent default behaviors
  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
  });

  dropZone.addEventListener("dragenter", (e) => {
    e.preventDefault();
    if (e.target.classList.contains("dropzone")) {
      e.target.classList.add("dragover");
    }
  });

  dropZone.addEventListener("dragleave", (e) => {
    if (e.target.classList.contains("dropzone")) {
      e.target.classList.remove("dragover");
    }
  });

  // Add event listener for the drop action
  dropZone.addEventListener('drop', (e) => {

    if (e.target.classList.contains("dropzone")) {
      e.target.classList.remove("dragover");
    }
    e.preventDefault();

    // Ignore anything that is not a valid drop zone
    if (!validDropZones.has(zoneName)) {
      console.warn(`Ignored invalid drop zone: ${zoneName}`);
      return;
    }
    
    const elementId = e.dataTransfer.getData('text/plain');

    // Grab Django's CSRF token from the DOM
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const queryString = window.location.search;

    const username = JSON.parse(document.getElementById('user-username').textContent);
    const isAuthenticated = JSON.parse(document.getElementById('user-is-authenticated').textContent);
    // Submit the fetch action (POST) to then move and update the data
    fetch('/submit-drag-drop/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',

        // Required by Django for security
        'X-CSRFToken': csrfToken 
      },

      // Post Payload. 
      body: JSON.stringify({
        username: username,
        isAuthenticated: isAuthenticated,
        item_id: elementId,
        raw_id: elementId.replace(/.*-/g, ""),
        target_zone: zoneName,
        query_string: queryString,
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success === true) {
        if (data.redirect_url) {
          window.location.href = data.redirect_url;
        } else {
          window.location.reload();
        }
      } else {
        alert('Error saving data');
      }
    })
    .catch(error => console.error('Error:', error));
  });
}


// ----------------------------------------------------------------------------------------
// Event listeners for the mouse down events
// ----------------------------------------------------------------------------------------
// Attach one listener to the parent element or document looking for a food item
document.addEventListener('mousedown', (event) => {
  draggableCard = getParentWithClassListName(event.target, 'draggable-card') 
  if (draggableCard != null) {
    draggableCard.addEventListener('dragstart', (e) => {
      e.dataTransfer.setData('text/plain', e.target.id);
    });
  } else {
    console.log("issue here")
  }
});


// ----------------------------------------------------------------------------------------------------
// Add event listeners for drop dragenter dragleave and dragover events concerning specific drop zones
// ----------------------------------------------------------------------------------------------------
const elements = document.querySelectorAll('.grid-lane');
elements.forEach(dropZone => {
  addDropZoneListeners(dropZone, dropZone.id)
});

// Attach listener for the drop via the css class
const pantryElements = document.querySelectorAll('.pantry-box')
pantryElements.forEach(dropZone => {
  addDropZoneListeners(dropZone, dropZone.id)
});

// Attach listener for the drop via the css class
const pantryElements1 = document.querySelectorAll('.pantry-box-delete')
pantryElements1.forEach(dropZone => {
  addDropZoneListeners(dropZone, dropZone.id)
});

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
// Find all elements
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