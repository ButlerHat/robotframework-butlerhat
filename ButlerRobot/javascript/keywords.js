
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
        let element = document.elementFromPoint(event.clientX, event.clientY);
        if (element instanceof HTMLIFrameElement)
          element = element.contentWindow.document.elementFromPoint(x, y);
  
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

  async function getTextFromBboxWithJsv2(args, page) {
    // args = [x1, y1, x2, y2]
    
  }

  async function examplePlaywrightToJS(page, args, logger) {
    const locator = page.locator(args[0]);
    const el_h = await locator.elementHandle();

    const elementHandle = await page.evaluateHandle((element) => {
      // let element = document.evaluate(locator, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;  // <- with xpath
      console.log(element)
      return element;
    }, el_h);

    logger("elementHandle: " + elementHandle)
    el_bbox = await elementHandle.boundingBox();
    logger("elementHandle Bbox: " + el_bbox.x + ", " + el_bbox.y + ", " + el_bbox.width + ", " + el_bbox.height);
  }
  
  async function scrollElementIfNeeded(page, args, logger) {
    // Function to scroll an element if needed. 
    // Returns an object that helps to record data for AI, so tries to set all elements visible.
    // Returns an object with the following properties:
    // is_element_scrolled: boolean, true if element has been scrolled
    // is_parent_scrolled: boolean, true if parent has been scrolled
    // el_bbox_after_scroll: object, bounding box of element after scroll
    // parent_bbox_before_scroll: object, bounding box of parent before scroll
    
    // Get element and parent
    logger("args[0]: " + args[0])
    // Check if has a frame locator. Locator: <iframe xpath> >>> <element xpath>
    let element;
    let frame;
    let frame_bbox;  // For delimiting the bbox of the parent
    let parent_is_frame = false;
    
    // Selector with iframe
    if (args[0].includes(">>>")) {
      const frame_locator = args[0].split(">>>")[0].trim();
      const element_locator = args[0].split(">>>")[1].trim();
      logger("frame_locator: " + frame_locator)
      logger("element_locator: " + element_locator)
      // Get element
      element = await page.frameLocator(frame_locator).locator(element_locator);
      logger("element: " + element)
      
      // Get frame
      frame_url = await page.locator(frame_locator).getAttribute("src");
      logger("frame_url: " + frame_url)
      // escape special characters
      if (!RegExp.escape) {
        RegExp.escape = function(s) {
          return s.replace(/[\\^$*+?.()|[\]{}]/g, '\\$&');
        };
      }
      const url_escaped = RegExp.escape(frame_url);      
      const url_regex = new RegExp(".*" + url_escaped + ".*");
      frame = page.frame({ url: url_regex });
      if (!frame) {
        throw new Error("Frame not found with url: " + frame_url + ". And regex: " + url_regex);
      }
      parent_is_frame = true;

      // Get frame bbox
      viewport = await page.viewportSize();
      frame_bbox = await page.locator(frame_locator).boundingBox();
      frame_bbox.width = Math.min(frame_bbox.width, viewport.width);
      frame_bbox.height = Math.min(frame_bbox.height, viewport.height);
      frame_bbox.x = Math.max(frame_bbox.x, 0);
      frame_bbox.y = Math.max(frame_bbox.y, 0);

    // Selector without iframe
    } else {
      element = await page.locator(args[0]);
      frame = page;
      frame_bbox = await page.viewportSize();
      frame_bbox.x = 0;
      frame_bbox.y = 0;
    }

    const elementHandle = await element.elementHandle();
    const scrollableParentHandle = await frame.evaluateHandle( (element) => {
      // let element = document.evaluate("//*[text()='Spain']", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;

      const isScrollable = function (ele) {
        const hasScrollableContent = ele.scrollHeight > ele.clientHeight;
      
        const overflowYStyle = window.getComputedStyle(ele).overflowY;
        const isOverflowHidden = overflowYStyle.indexOf('hidden') !== -1;
      
        return hasScrollableContent && !isOverflowHidden;
      };
      
      const getScrollableParent = function (ele) {
        return !ele || ele === document.body
            ? document.body
            : isScrollable(ele)
            ? ele
            : getScrollableParent(ele.parentNode);
      };

      parent = getScrollableParent(element);
      console.log(parent)
      return parent;

    }, elementHandle);

    const bbox_before = await element.boundingBox();
    const bbox_parent_before = await scrollableParentHandle.boundingBox();
    // parent_bbox is the min of the height and width of the viewport and the parent
    const return_parent_bbox = {
      x: Math.max(bbox_parent_before.x, frame_bbox.x),
      y: Math.max(bbox_parent_before.y, frame_bbox.y),
      width: Math.min(bbox_parent_before.width, frame_bbox.width),
      height: Math.min(bbox_parent_before.height, frame_bbox.height)
    }

    logger("Element bbox before scroll: " + JSON.stringify({x: bbox_before.x, y: bbox_before.y, width: bbox_before.width, height: bbox_before.height}));
    logger("Parent bbox before scroll: " + JSON.stringify({x: bbox_parent_before.x, y: bbox_parent_before.y, width: bbox_parent_before.width, height: bbox_parent_before.height}));
    logger("Returned parent bbox: " + JSON.stringify({x: frame_bbox.x, y: frame_bbox.y, width: frame_bbox.width, height: frame_bbox.height}));
  
    // ==== Scroll element if needed. ====
    await element.scrollIntoViewIfNeeded();
  
    // Check if element has been scrolled
    const bbox_after = await element.boundingBox();
    const bbox_parent_after = await scrollableParentHandle.boundingBox();

    logger("Element bbox after scroll: " + JSON.stringify({x: bbox_after.x, y: bbox_after.y, width: bbox_after.width, height: bbox_after.height}));
    logger("Parent bbox after scroll: " + JSON.stringify({x: bbox_parent_after.x, y: bbox_parent_after.y, width: bbox_parent_after.width, height: bbox_parent_after.height}));
    
    // Check if element has been scrolled
    const scrolled_element = bbox_before.y !== bbox_after.y;
    let scrolled_parent = false;
    // if parent is not frame, check if parent has been scrolled
    if (!parent_is_frame) {
      scrolled_parent = bbox_parent_before.y !== bbox_parent_after.y;
    }

    const is_scrolled_up = bbox_before.y < bbox_after.y;

    logger("Element scrolled: " + scrolled_element);
    logger("Parent scrolled: " + scrolled_parent);
    logger("Scrolled up: " + is_scrolled_up);
    logger("Element bbox after scroll: " + JSON.stringify({x: bbox_after.x, y: bbox_after.y, width: bbox_after.width, height: bbox_after.height}));
    logger("Parent bbox before scroll: " + JSON.stringify({x: bbox_parent_before.x, y: bbox_parent_before.y, width: bbox_parent_before.width, height: bbox_parent_before.height}));
    return Promise.resolve({
      is_element_scrolled: scrolled_element,
      is_parent_scrolled: scrolled_parent,
      is_scrolled_up: is_scrolled_up,
      el_bbox_after_scroll: {x: bbox_after.x, y: bbox_after.y, width: bbox_after.width, height: bbox_after.height},
      parent_bbox_before_scroll: {x: return_parent_bbox.x, y: return_parent_bbox.y, width: return_parent_bbox.width, height: return_parent_bbox.height}
    });
  }

  exports.__esModule = true;
  exports.getElementBboxHighlighted = getElementBboxHighlighted;
  exports.getTextFromBboxWithJs = getTextFromBboxWithJs;
  exports.scrollElementIfNeeded = scrollElementIfNeeded;