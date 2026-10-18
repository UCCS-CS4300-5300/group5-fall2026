
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

function addDropZoneListeners(dropZone) {
  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    
    const elementId = e.dataTransfer.getData('text/plain');
    // console.log(e.dataTransfer)
    
    // Grab Django's CSRF token from the DOM
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

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

// Attach one listener to the parent element or document
document.addEventListener('mousedown', (event) => {
    draggableCard = getParentWithClassListName(event.target, 'draggable-card') 
  if (draggableCard != null) {
    console.log('Element clicked via delegation:', draggableCard);
  
    draggableCard.addEventListener('dragstart', (e) => {
      e.dataTransfer.setData('text/plain', e.target.id);
    });
  }
});

document.querySelectorAll('.grid-lane').forEach(dropZone => {
  addDropZoneListeners(dropZone)
});

document.querySelectorAll('.pantry-box').forEach(dropZone => {
  addDropZoneListeners(dropZone)
});
