chrome.storage.local.get(["recording", "paused", "hoverDisabled", "taskID"], function(result) {
    let recording = result.recording || false;
    let taskID = result.taskID || null;
    let paused = result.paused || false;
    let hoverDisabled = result.hoverDisabled || true;

    window.isContentScriptInjected = true;
    let lastHighlightedElement;
    let bboxElement;
    let highlightDiv = document.createElement("div");
    let scrollTimeout = null;
    const scrollTimeoutDuration = 2000; // 2 seconds

    // Enum to store the action types. This must be the same as RobotActions
    const ActionTypes = {
        click_at_bbox: 'click_at_bbox',
        keyboard_input: 'keyboard_input',
        scroll_down: 'scroll_down',
        scroll_up: 'scroll_up',
        scroll_down_at_bbox: 'scroll_down_at_bbox',
        scroll_up_at_bbox: 'scroll_up_at_bbox'
    };

    highlightDiv.id = "highlightDiv";
    highlightDiv.style.position = "fixed";
    highlightDiv.style.backgroundColor = "rgba(255, 255, 0, 0.2)";
    highlightDiv.style.pointerEvents = "none";
    highlightDiv.style.zIndex = "9999";

    function highlightElementUnderMouse(event) {
        // Remove the existing overlay if any
        let overlay = document.getElementById("overlay");
        if (overlay) {
            overlay.style.display = 'none';
        }

        // Now get the element
        let element = document.elementFromPoint(event.clientX, event.clientY);
        if (element instanceof HTMLIFrameElement)
            element = element.contentWindow.document.elementFromPoint(event.clientX, event.clientY);

        // Bring back the overlay
        if (overlay) {
            overlay.style.display = 'block';
        }

        if (element !== lastHighlightedElement) {
            if (lastHighlightedElement) {
                lastHighlightedElement.style.removeProperty("outline");
            }

            if (overlay) {
                overlay.remove();
            }

            // Create a new overlay
            if (hoverDisabled) {
                overlay = document.createElement("div");
                overlay.id = "overlay";
                overlay.style.position = "fixed";
                overlay.style.top = "0";
                overlay.style.left = "0";
                overlay.style.width = "100%";
                overlay.style.height = "100%";
                overlay.style.zIndex = "9998";
                overlay.style.pointerEvents = "auto";

                // Exclude the highlighted element from the overlay
                overlay.style.clipPath = `polygon(0 0, 100% 0, 100% 100%, 0 100%, 0 ${element.getBoundingClientRect().top}px, ${element.getBoundingClientRect().left}px ${element.getBoundingClientRect().top}px, ${element.getBoundingClientRect().left}px ${element.getBoundingClientRect().bottom}px, 0 ${element.getBoundingClientRect().bottom}px)`;

                document.body.appendChild(overlay);
            }

            highlightDiv.style.top = element.getBoundingClientRect().top + "px";
            highlightDiv.style.left = element.getBoundingClientRect().left + "px";
            highlightDiv.style.width = element.getBoundingClientRect().width + "px";
            highlightDiv.style.height = element.getBoundingClientRect().height + "px";
            
            if (!highlightDiv.parentNode) {
                if (document.getElementById("highlightDiv")) {
                    document.getElementById("highlightDiv").remove();
                }
                document.body.appendChild(highlightDiv);
            }

            element.addEventListener("mouseleave", function () {
                highlightDiv.remove();
            });

            element.style.outline = "2px solid red";
            lastHighlightedElement = element;
        }
    }

    chrome.runtime.onMessage.addListener(
        function(request, sender, sendResponse) {

            if (request.action == "startRecording") {
                console.log("Starting recording...");
                // Create a new task
                fetch("http://localhost:8000/start_root_task", {
                    method: "POST",
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({task_name: request.task_name})
                // Store state and Update UI
                }).then(response => response.json())
                .then(data => {
                    console.log("Started ID: " + data.task_id);
                    taskID = data.task_id;
                    recording = true;
                    paused = false;
                    window.addEventListener('scroll', handleScrollEvent, true);
                    chrome.storage.local.set({recording: recording, paused: paused, taskID: taskID});
                });
                sendResponse({recording:true, paused:false});
                
            } else if (request.action == "stopRecording") {
                // Store state
                recording = false;
                paused = false;
                chrome.storage.local.set({recording: recording, paused:paused, taskID: null});
                // Remove the overlay
                let overlay = document.getElementById("overlay");
                if (overlay) {
                    overlay.remove();
                }
                // Remove the highlight
                if (document.getElementById("highlightDiv")) {
                    document.getElementById("highlightDiv").remove();
                }
                // Remove the scroll event listener
                if (lastHighlightedElement) {
                    lastHighlightedElement.style.removeProperty("outline");
                }
                paused = true;

                // Remove the scroll event listener
                window.removeEventListener('scroll', handleScrollEvent, true);

                // Take screenshot
                chrome.runtime.sendMessage({action: "captureScreenshot"}, function(response) {
                    const screenshotDataUrl = response.dataUrl;
                    // End task
                    fetch(`http://localhost:8000/save_task/${taskID}`, {
                        method: "POST",
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({screenshot: screenshotDataUrl})
                    // Update UI
                    }).then(response => response.json())
                    .then(data => {
                        console.log("Recording stopped");
                        console.log(data);
                    });
                });

                sendResponse({recording:recording, paused:paused});

            } else if (request.action == "toggleHover") {
                // Store state
                hoverDisabled = request.disableHover;
                chrome.storage.local.set({hoverDisabled: hoverDisabled});

            } else if (request.action == "pauseRecording") {
                // Store state
                recording = false;
                paused = true;
                chrome.storage.local.set({recording: recording, paused:paused});
                // Remove the overlay
                highlightDiv.style.display = "none";
                let overlay = document.getElementById("overlay");
                if (overlay) {
                    overlay.style.display = 'none';
                }
                // Update UI
                sendResponse({recording:recording, paused:paused});

            } else if (request.action == "resumeRecording") {
                recording = true;
                paused = false;
                chrome.storage.local.set({recording: recording, paused:paused});
                highlightDiv.style.display = "block";
                let overlay = document.getElementById("overlay");
                if (overlay) {
                    overlay.style.display = 'block';
                }
                // Update UI
                sendResponse({recording:recording, paused:paused});
            }
        }
    );

    document.addEventListener("mousemove", function(event) {
        if (recording && !paused) highlightElementUnderMouse(event);
    });

    window.addEventListener(
        "click",
        function (event) {
            if (!recording || paused) return;
            let overlay = document.getElementById("overlay");
            if (overlay) {
                overlay.style.display = 'none'; // Hide the overlay
            }
            let element = document.elementFromPoint(event.clientX, event.clientY);


            if (
                lastHighlightedElement &&
                lastHighlightedElement.contains(element)
            ) {
                event.preventDefault();
                event.stopPropagation();
                event.stopImmediatePropagation();
                paused = true;
                document.getElementById("highlightDiv").remove();
                // Check if the element highlightDiv is still in the DOM
                if (document.getElementById("highlightDiv")) {
                    console.log("highlightDiv is still in the DOM");
                }
                lastHighlightedElement.style.removeProperty("outline");

                const bbox = lastHighlightedElement.getBoundingClientRect();
                bboxElement = {
                    element: lastHighlightedElement,
                    bbox: {
                        left: Math.round(bbox.left),
                        top: Math.round(bbox.top),
                        width: Math.round(bbox.width),
                        height: Math.round(bbox.height)
                    }
                };

                // Request a screenshot from the background script
                if (document.getElementById("highlightDiv")) {
                    console.log("highlightDiv is still in the DOM 2");
                }

                chrome.runtime.sendMessage({action: "captureScreenshot"}, function(response) {
                    if (document.getElementById("highlightDiv")) {
                        console.log("highlightDiv is still in the DOM 3");
                    }
                    
                    const screenshotDataUrl = response.dataUrl;
                    // Simulate a click on the element
                    let clickableElement = bboxElement.element;
                    if (typeof clickableElement.click !== 'function') {
                        clickableElement = bboxElement.element.querySelector('button, a, input[type="button"], input[type="submit"], input[type="checkbox"], input[type="radio"]');
                    }
                    
                    // If a clickable element is found, simulate a click
                    if (clickableElement && typeof clickableElement.click === 'function') {
                        recording = false;
                        clickableElement.click();
                        recording = true;
                    }

                    // Show a popup asking for the instruction
                    let instruction = prompt("Add the instruction to the action you did.");

                    console.log(ActionTypes.click_at_bbox);
                    console.log(bboxElement.bbox);
                    console.log(instruction)

                    // Add step
                    fetch(`http://localhost:8000/add_task_and_action/${taskID}`, {
                        method: "POST",
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            action: ActionTypes.click_at_bbox,
                            screenshot: screenshotDataUrl,
                            bbox: bboxElement.bbox,
                            task_instruction: instruction
                        })
                    });

                    lastHighlightedElement = null;
                    paused = false;

                });

                if (overlay) {
                    overlay.style.display = 'block';
                }
            }
        },
        true
    );

    async function handleScrollEvent(event) {
        if (!recording || paused) return;
        if (scrollTimeout !== null) {
            clearTimeout(scrollTimeout);
        }

        scrollTimeout = setTimeout(() => {
            if (document.getElementById("highlightDiv") !== null) {
                document.getElementById("highlightDiv").remove();
            }
            lastHighlightedElement.style.removeProperty("outline");
            paused = true;
            // Take screenshot
            chrome.runtime.sendMessage({action: "captureScreenshot"}, function(response) {
                const screenshotDataUrl = response.dataUrl;

                // Get bounding box of the scrollable parent
                let bbox = getScrollableParentBoundingBox(event.target);
                
                let action = event.deltaY < 0 ? ActionTypes.scroll_up_at_bbox : ActionTypes.scroll_down_at_bbox;

                // Append step
                fetch(`http://localhost:8000/add_page_action/${taskID}`, {
                    method: "POST",
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        screenshot: screenshotDataUrl,
                        bbox: bbox,
                        action: action
                    })
                });
                console.log("scroll action added");
                paused = false;
            });

            scrollTimeout = null;
        }, scrollTimeoutDuration);
    }

    function getScrollableParentBoundingBox(element) {
        let parent = element;

        while (parent && !(parent.scrollHeight > parent.clientHeight) && getComputedStyle(parent).overflowY !== "hidden") {
            parent = parent.parentNode;
        }

        let bbox = parent.getBoundingClientRect();
        // Set the bounging box to be in the viewport
        bbox = {
            left: Math.max(bbox.left, 0),
            top: Math.max(bbox.top, 0),
            width: Math.min(bbox.width, window.innerWidth),
            height: Math.min(bbox.height, window.innerHeight)
        };

        return {
            left: Math.round(bbox.left),
            top: Math.round(bbox.top),
            width: Math.round(bbox.width),
            height: Math.round(bbox.height),
        };
    }
});
