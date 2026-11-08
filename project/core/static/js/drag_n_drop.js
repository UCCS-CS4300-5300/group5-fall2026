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
    
    const elementId = e.dataTransfer.getData('text/plain');
    // Grab Django's CSRF token from the DOM
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const queryString = window.location.search;

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
        item_id: elementId,
        raw_id: elementId.replace(/.*-/g, ""),
        target_zone: zoneName,
        query_string: queryString
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success === true) {
        const droppedElement = document.getElementById(elementId);
        dropZone.appendChild(droppedElement);
      } else {
        alert('Error saving data');
      }
      if (data.redirect_url) {
          window.location.href = data.redirect_url;
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

// ----------------------------------------------------------------------------------------
// Dynamic search for global pantry
// ----------------------------------------------------------------------------------------
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
