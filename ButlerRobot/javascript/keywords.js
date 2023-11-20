
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

  async function printBoundingBox(page, args, logger) {
    const bbox = args;  // [x1, y1, width, height]
    logger("bbox: " + bbox)
    return await page.evaluate((bbox) => {
      const highlightDiv = document.createElement("div");
      highlightDiv.style.position = "fixed";
      // highlightDiv.style.backgroundColor = "rgba(255, 255, 0, 0.5)";
      // highlightDiv.style.pointerEvents = "none";
      highlightDiv.style.zIndex = "9999";
      highlightDiv.id = "highlightDivBH";
      highlightDiv.className = "myClass";

      const style = document.createElement("style");
      style.innerHTML = `
      .myClass {
        background-color: rgba(255,165, 0, 0.2);
        border: 2px solid;
        border-image: linear-gradient(to right, blue, orange) 1;
        border-image-slice: 1;
      }

      .gradient-border {
        position: relative;
        overflow: hidden;
      }
      
      .gradient-border::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: -1;
        background: linear-gradient(to right, #ff0000, #00ff00);
      }
      
      .gradient-border::after {
        content: "";
        position: absolute;
        top: 2px; /* Adjust as needed */
        left: 2px; /* Adjust as needed */
        right: 2px; /* Adjust as needed */
        bottom: 2px; /* Adjust as needed */
        z-index: -1;
        background-color: rgba(255, 255, 255, 0.5);
      }
        

      `;

      highlightDiv.style.top = bbox[1] + "px";
      highlightDiv.style.left = bbox[0] + "px";
      highlightDiv.style.width = bbox[2] + "px";
      highlightDiv.style.height = bbox[3] + "px";

      document.head.appendChild(style);
      document.body.appendChild(highlightDiv);
      return Promise.resolve();
    }, bbox);
  }

  async function getTextFromBboxWithJs(args, page, logger) {
    const margin = 3;
    let frame;
    
    // Check if element is an iframe
    let elmenetHandle = await page.evaluateHandle( (boundingBox) => {
      let [x1, y1, x2, y2] = boundingBox;
      const middleX = Math.floor((x1 + x2) / 2);
      const middleY = Math.floor((y1 + y2) / 2);
      return document.elementFromPoint(middleX, middleY);
    }, args);

    let tagName = await elmenetHandle.$eval('xpath=.', node => node.tagName)
    if (tagName === "IFRAME") {
      logger("Element is an iframe")
      // Get frame
      frame_url = await elmenetHandle.getAttribute("src");
      logger("frame_url: " + frame_url)
      // escape special characters
      if (!RegExp.escape) {
        RegExp.escape = function(s) {
          return s.replace(/[\\^$*+?.()|[\]{}]/g, '\\$&');
        };
      }
      const url_escaped = RegExp.escape(frame_url);      
      const url_regex = new RegExp(".*" + url_escaped + ".*");
      logger("url_regex: " + url_regex)
      frame = page.frame({ url: url_regex });
      if (!frame) {
        throw new Error("Frame not found with url: " + frame_url + ". And regex: " + url_regex);
      }

      // Adjust bounding box
      let framePos = await elmenetHandle.boundingBox();
      // Convert all elements of the object to integers
      framePos = Object.keys(framePos).reduce((obj, key) => {
        obj[key] = Math.floor(framePos[key]);
        return obj;
      }, {});

      x1 = args[0] - framePos.x + margin;
      y1 = args[1] - framePos.y + margin;
      x2 = args[2] - framePos.x - margin;
      y2 = args[3] - framePos.y - margin;
      logger("Original bounding box: " + args)
      logger("Adjusted bounding box: " + [x1, y1, x2, y2])

    } else {
      x1 = args[0] + margin;
      y1 = args[1] + margin;
      x2 = args[2] - margin;
      y2 = args[3] - margin;
      frame = page;
    }

    let elementHandle =  await frame.evaluateHandle( (boundingBox) => {

      function getDistance(rect1, rect2) {
        const [x1, y1, x2, y2] = rect1;
        const [x3, y3, x4, y4] = rect2;
        const points1 = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]];
        const points2 = [[x3, y3], [x4, y3], [x4, y4], [x3, y4]];
        let distance = 0;
        for (let i = 0; i < 4; i++) {
          const [p1x, p1y] = points1[i];
          let minDistance = Infinity;
          for (let j = 0; j < 4; j++) {
            const [p2x, p2y] = points2[j];
            const d = Math.sqrt((p1x - p2x) ** 2 + (p1y - p2y) ** 2);
            minDistance = Math.min(minDistance, d);
          }
          distance += minDistance;
        }
        return distance;
      }

      const [x1, y1, x2, y2] = boundingBox;
      const middleX = Math.floor((x1 + x2) / 2);
      const middleY = Math.floor((y1 + y2) / 2);
      const middleElement = document.elementFromPoint(middleX, middleY);
      console.log("middleElement: ")
      console.log(middleElement)
      let bbox_element = middleElement.getBoundingClientRect();
      let bbox_list = [bbox_element.x, bbox_element.y, bbox_element.x + bbox_element.width, bbox_element.y + bbox_element.height];
      let closestDistance = getDistance(bbox_list, boundingBox);
      let closestElement = middleElement;

      const points = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]];

      for (const point of points) {
        const element = document.elementFromPoint(point[0], point[1]);
        console.log("element " + point[0] + ", " + point[1] + ": ")
        console.log(element)

        if (element && element !== closestElement) {
          bbox_element = element.getBoundingClientRect();
          console.log("element bbox: " + JSON.stringify(bbox_element))
          const bbox_element_list = [bbox_element.x, bbox_element.y, bbox_element.x + bbox_element.width, bbox_element.y + bbox_element.height]
          const distance = getDistance(bbox_element_list, boundingBox);
          console.log("distance: " + distance)
          console.log("closestDistance: " + closestDistance)
          if (distance < closestDistance) {
            closestDistance = distance;
            console.log("closestElement: ")
            console.log(element)
            console.log("element text: " + element.innerText)
            closestElement = element;
          }
        }
      }

      console.log("final closestElement: ");
      console.log(closestElement);
      console.log("element text: " + closestElement.innerText)
      return closestElement;

    }, [x1, y1, x2, y2]);

    let text = await elementHandle.innerText();
    // Find the first parent thata has text
    if (text === "") {
      // Try get input text with elementHandle.inputValue(). Catch error if not possible
      try {
        text = await elementHandle.inputValue();
      } catch (error) {} 
    }

    return text;
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

  async function getViewportSize(page, logger) {
    let viewport = await page.viewportSize();
    if (!viewport) {
      viewport_w = await page.evaluate(() => {
        return Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
      });
      logger("viewport_w: " + viewport_w)
      viewport_h = await page.evaluate(() => {
        return Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
      });
      logger("viewport_h: " + viewport_h)
      viewport = {width: viewport_w, height: viewport_h};
    }
    logger("viewport: " + viewport.width + ", " + viewport.height);
    return viewport;
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
      viewport = await getViewportSize(page, logger);
      frame_bbox = await page.locator(frame_locator).boundingBox();
      frame_bbox.width = Math.min(frame_bbox.width, viewport.width);
      frame_bbox.height = Math.min(frame_bbox.height, viewport.height);
      frame_bbox.x = Math.max(frame_bbox.x, 0);
      frame_bbox.y = Math.max(frame_bbox.y, 0);

    // Selector without iframe
    } else {
      element = await page.locator(args[0]);
      frame = page;
      frame_bbox = await getViewportSize(page, logger);
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
    logger("bbox_parent_before: " + JSON.stringify(bbox_parent_before))
    logger("frame_bbox: " + JSON.stringify(frame_bbox))
    // parent_bbox is the min of the height and width of the viewport and the parent
    const return_parent_bbox = {
      x: Math.max(bbox_parent_before.x, frame_bbox.x),
      y: Math.max(bbox_parent_before.y, frame_bbox.y),
      width: Math.min(bbox_parent_before.width, frame_bbox.width),
      height: Math.min(bbox_parent_before.height, frame_bbox.height)
    }

    logger("Element bbox before scroll: " + JSON.stringify({x: bbox_before.x, y: bbox_before.y, width: bbox_before.width, height: bbox_before.height}));
    logger("Parent bbox before scroll: " + JSON.stringify({x: bbox_parent_before.x, y: bbox_parent_before.y, width: bbox_parent_before.width, height: bbox_parent_before.height}));
    logger("Iframe bbox: " + JSON.stringify({x: frame_bbox.x, y: frame_bbox.y, width: frame_bbox.width, height: frame_bbox.height}));
  
    // ==== Scroll element if needed. ====
    await element.scrollIntoViewIfNeeded(true);
  
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
  exports.printBoundingBox = printBoundingBox;
  exports.getTextFromBboxWithJs = getTextFromBboxWithJs;
  exports.scrollElementIfNeeded = scrollElementIfNeeded;