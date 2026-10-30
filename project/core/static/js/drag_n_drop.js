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
    console.log(elementId)    
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
      if (data.success === true) {
        const droppedElement = document.getElementById(elementId);
        dropZone.appendChild(droppedElement);
      } else {
        alert('Error saving data');
      }
      if (data.redirect_url) {
          // Option 1: Redirect immediately
          window.location.href = data.redirect_url;
          
          // Option 2: Flash a message first, then redirect after 2 seconds
          // alert(data.message);
          // setTimeout(() => { window.location.href = data.redirect_url; }, 2000);
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
  } else {
    console.log("issue here")
  }
});

// Attach listener for the drop via the css class
const elements = document.querySelectorAll('.grid-lane');
elements.forEach(dropZone => {
  addDropZoneListeners(dropZone, dropZone.id)
});

// Attach listener for the drop via the css class
const pantryElements = document.querySelectorAll('.pantry-box')
pantryElements.forEach(dropZone => {
  addDropZoneListeners(dropZone, dropZone.id)
});


// dynamic search for global pantry
const searchInput = document.getElementById('search-input');
const searchForm = document.getElementById('search-form');
let timeout = null;

searchInput.addEventListener('keyup', function () {
  clearTimeout(timeout);
  timeout = setTimeout(function () {
    searchForm.submit();
  }, 500);
});
