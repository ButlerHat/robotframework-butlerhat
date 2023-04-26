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

  
  async function getTextFromBboxWithJs(args, page) {
    // args = [x1, y1, x2, y2]
    return new Promise(async (resolve, reject) => {
      try {
        let text_array = await page.evaluate((args) => {
          let [x1, y1, x2, y2] = args;
          let elements = [];
          let text_array = [];
          
          for (let x = x1; x < x2; x=x+5) {
            for (let y = y1; y < y2; y=y+5) {
              const element = document.elementFromPoint(x, y);
              if (element && !elements.includes(element)) {
                elements.push(element);
              }
            }
          }

          function getTextArray(element) {
            if (element.nodeType === Node.TEXT_NODE) {
              //trim whitespace
              let text_content = element.textContent.trim();
              console.log("Adding text: " + text_content)
              //check if text array has the text already
              if (text_array.indexOf(text_content) === -1)
                text_array.push(text_content);
            } else {
              for (let child of element.childNodes) {
                getTextArray(child);
              }
            }
          }
          
          for (let i = 0; i < elements.length; i++) {
            getTextArray(elements[i]);
          }
          return text_array;
        }, args);
  
        resolve(text_array);
      } catch (error) {
        reject(error);
      }
    });
  }
  

  exports.__esModule = true;
  exports.getElementBboxHighlighted = getElementBboxHighlighted;
  exports.getTextFromBboxWithJs = getTextFromBboxWithJs;