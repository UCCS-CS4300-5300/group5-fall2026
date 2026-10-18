// get Parent Element With Class List Name if it exists
function getParentWithClassListName(element, targetName) {
  let current = element.parentElement;
  console.log("   Checking ...   ")
  while (current) {
    console.log(current)
    if (current.classList.contains(targetName)) {
      console.log("Found")
      return current;
    }
    current = current.parentElement;
  }
  console.log("NOT Found! ")
  return null;
}

// Add drop Zone Listener. 
function addDropZoneListeners(dropZone) {
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
    body: JSON.stringify({
      item_id: elementId,
      target_zone: 'drop-zone'
    })
    })
    .then(response => response.json())
    .then(data => {
      console.log(data.status)
    
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
    console.log('Element clicked via delegation:', draggableCard);
  
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
