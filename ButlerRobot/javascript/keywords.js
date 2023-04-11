async function getElementBboxHighlighted(page) {
    return await page.evaluate(() => {
      let lastHighlightedElement;
      let highlightDiv = document.createElement("div");
  
      // Set the styles for the highlight div
      highlightDiv.style.position = "fixed";
      highlightDiv.style.backgroundColor = "rgba(255, 255, 0, 0.5)";
      highlightDiv.style.pointerEvents = "none";
      highlightDiv.style.zIndex = "9999";
  
      function highlightElementUnderMouse() {
        // Get the element that is currently under the mouse pointer
        const element = document.elementFromPoint(event.clientX, event.clientY);
  
        // Check if the element is different from the last highlighted element
        if (element !== lastHighlightedElement) {
          // Remove the highlight div from the last highlighted element, if any
          if (lastHighlightedElement) {
            lastHighlightedElement.style.removeProperty("outline");
          }
  
          // Update the position and size of the highlight div
          highlightDiv.style.top = element.getBoundingClientRect().top + "px";
          highlightDiv.style.left = element.getBoundingClientRect().left + "px";
          highlightDiv.style.width = element.getBoundingClientRect().width + "px";
          highlightDiv.style.height = element.getBoundingClientRect().height + "px";
  
          // Add the highlight div to the document, if it hasn't been added yet
          if (!highlightDiv.parentNode) {
            document.body.appendChild(highlightDiv);
          }
  
          // Remove the highlight div when the mouse moves away from the element
          element.addEventListener("mouseleave", function () {
            highlightDiv.remove();
          });
  
          // Add an outline to the element to indicate that it is highlighted
          element.style.outline = "2px solid red";
  
          // Set the last highlighted element to the current element
          lastHighlightedElement = element;
        }
      }
  
      // Listen for click events on the window
      return new Promise((resolve, reject) => {
        window.addEventListener(
          "click",
          function (event) {
            // Check if the click is within the bounds of the last highlighted element
            if (
              lastHighlightedElement &&
              lastHighlightedElement.contains(event.target)
            ) {
              // Prevent the default behavior of the event
              event.preventDefault();
              event.stopPropagation();
  
              // Remove the highlight div
              highlightDiv.remove();
  
              // Get the bounding box of the last highlighted element
              const bbox = lastHighlightedElement.getBoundingClientRect();
  
              // Reset the last highlighted element
              lastHighlightedElement.style.removeProperty("outline");
              lastHighlightedElement = null;

              document.removeEventListener("mousemove", highlightElementUnderMouse);
  
              // Resolve the promise with the bounding box
              resolve({
                left: bbox.left,
                top: bbox.top,
                right: bbox.right,
                bottom: bbox.bottom,
                width: bbox.width,
                height: bbox.height,
              });
            } else {
              reject("No element was clicked.");
            }
          },
          true
        );
  
        // Listen for mousemove events on the document
        document.addEventListener("mousemove", highlightElementUnderMouse);
      });
    });
  }
  

  exports.__esModule = true;
  exports.getElementBboxHighlighted = getElementBboxHighlighted;