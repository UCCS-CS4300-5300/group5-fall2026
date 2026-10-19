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

  // Add event listener for the drop action
  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    
    const elementId = e.dataTransfer.getData('text/plain');
    
    // Grab Django's CSRF token from the DOM
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

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
        target_zone: zoneName
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success') {
        const droppedElement = document.getElementById(elementId);
        dropZone.appendChild(droppedElement);
      } else {
        alert('Error saving data');
      }
    })
    .catch(error => console.error('Error:', error));
  });
}


// Attach one listener to the parent element or document looking for a food item
document.addEventListener('mousedown', (event) => {
  draggableCard = getParentWithClassListName(event.target, 'draggable-card') 
  if (draggableCard != null) {
    draggableCard.addEventListener('dragstart', (e) => {
      e.dataTransfer.setData('text/plain', e.target.id);
    });
  }
});

// Attach listener for the drop via the css class
document.querySelectorAll('.grid-lane').forEach(dropZone => {
  addDropZoneListeners(dropZone)
});

// Attach listener for the drop via the css class
document.querySelectorAll('.pantry-box').forEach(dropZone => {
  addDropZoneListeners(dropZone)
});

const elements = document.querySelectorAll('.grid-lane');
elements.forEach(dropZone => {
  addDropZoneListeners(dropZone, dropZone.id)
});

const pantryElements = document.querySelectorAll('.pantry-box')
pantryElements.forEach(dropZone => {
  addDropZoneListeners(dropZone, dropZone.id)
});
