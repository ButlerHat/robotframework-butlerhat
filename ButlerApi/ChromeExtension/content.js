chrome.storage.local.get(["recording", "paused", "setHover", "storeAfterClick", "taskID"], function(result) {
    let recording = result.recording || false;
    let taskID = result.taskID || null;
    let paused = result.paused || false;
    let setHover = result.setHover === undefined ? true : result.setHover;
    let storeAfterClick = result.storeAfterClick === undefined ? true : result.storeAfterClick;
    let lastClickedElement;
    let isWriting = false;
    let lastScreenshot = null;
    let lastWheelDirection = 1; 

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
            if (setHover) {
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
        async function(request, sender, sendResponse) {

            if (request.action == "startRecording") {
                console.log("Starting recording...");

                // Capture the screenshot before starting the recording
                chrome.runtime.sendMessage({action: "captureScreenshot"}, function(response) {
                    lastScreenshot = response.dataUrl;

                    // Create a new task
                    fetch("http://localhost:8000/start_root_task", {
                        method: "POST",
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({task_name: request.task_name})
                    // Store state and Update UI
                    }).then(response => response.json())
                    .then(data => {
                        console.log("Started ID: " + data.task_id + " with name " + data.task_name);
                        taskID = data.task_id;
                        recording = true;
                        paused = false;
                        window.addEventListener('scroll', handleScrollEvent, true);
                        chrome.storage.local.set({recording: recording, paused: paused, taskID: taskID});
                    });
                    sendResponse({recording:true, paused:false});
                });

            } else if (request.action == "createTask") {
                let instruction = request.instruction;
                fetch(`http://localhost:8000/add_task/${taskID}`, {
                    method: "POST",
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        task_name: instruction
                    })
                });
                console.log("Created task: " + instruction);
                
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
                    await new Promise(resolve => requestAnimationFrame(resolve));
                }
                // Remove the scroll event listener
                if (lastHighlightedElement) {
                    lastHighlightedElement.style.removeProperty("outline");
                    await new Promise(resolve => requestAnimationFrame(resolve));
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
                setHover = request.setHover;
                chrome.storage.local.set({setHover: setHover});
            
            } else if (request.action == "toggleStoreAfterClick") {
                // Store state
                storeAfterClick = request.storeAfterClick;
                chrome.storage.local.set({storeAfterClick: storeAfterClick});
            
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
                // Capture the screenshot before starting the recording
                chrome.runtime.sendMessage({action: "captureScreenshot"}, function(response) {
                    lastScreenshot = response.dataUrl;

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
                });
            }
        }
    );

    document.addEventListener("mousemove", function(event) {
        if (recording && !paused) highlightElementUnderMouse(event);
    });

    window.addEventListener(
        "click",
        async function (event) {
            if (!recording || paused) return;
            let overlay = document.getElementById("overlay");
            if (overlay) {
                overlay.style.display = 'none'; // Hide the overlay
            }
            let element = document.elementFromPoint(event.clientX, event.clientY);
            if (overlay) {
                overlay.style.display = 'block'; // Show the overlay
                await new Promise(resolve => requestAnimationFrame(resolve));
            }

            if (
                lastHighlightedElement &&
                lastHighlightedElement.contains(element)
            ) {
                // Stop propagation
                event.preventDefault();
                event.stopPropagation();
                event.stopImmediatePropagation();

                // Remove the highlight
                if (document.getElementById("highlightDiv")) {
                    document.getElementById("highlightDiv").remove();
                    await new Promise(resolve => requestAnimationFrame(resolve));
                }
                if (lastHighlightedElement) {
                    lastHighlightedElement.style.removeProperty("outline");
                    await new Promise(resolve => requestAnimationFrame(resolve));
                }

                // Get the bounding box of the element
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
                chrome.runtime.sendMessage({action: "captureScreenshot", bbox: bboxElement.bbox}, function(response) {

                    const screenshotDataUrl = response.dataUrl;
                    bboxElement.bbox = response.bbox;
                    
                    // Simulate a click on the element if is not writing
                    // REMOVED

                    // Store keyboad input if is writing
                    let text = "";
                    if (isWriting && lastClickedElement) {
                        if (lastClickedElement instanceof HTMLInputElement || lastClickedElement instanceof HTMLTextAreaElement) {
                            text = lastClickedElement.value;
                        } else {
                            text = lastClickedElement.textContent;
                        }
                    }
                    
                    // Store click or input text
                    if (!storeAfterClick) {
                        // Send keySequence to the API
                        if (isWriting && lastClickedElement) {
                            fetch(`http://localhost:8000/add_page_action/${taskID}`, {
                                method: "POST",
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    keySequence: text,
                                    action: ActionTypes.keyboard_input,
                                    screenshot: lastScreenshot
                                })
                            });
                            console.log("Sent keyboard input: " + text);
                            // After writing set storeAfterClick to true. 
                            // This is due to the fact that most of the time after writing you click on something and task ends.
                            storeAfterClick = true;
                            chrome.storage.local.set({storeAfterClick: storeAfterClick});
                            chrome.runtime.sendMessage({action: "updateUI", storeAfterClick: storeAfterClick}, function(response) {
                                console.log("Response from updateUI:");
                                console.log(response);
                              });
                        // Send click to the API
                        } else {
                            fetch(`http://localhost:8000/add_page_action/${taskID}`, {
                                method: "POST",
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    action: ActionTypes.click_at_bbox,
                                    screenshot: screenshotDataUrl,
                                    bbox: bboxElement.bbox
                                })
                            });
                            console.log("Sent click at bbox: " + JSON.stringify(bboxElement.bbox));
                        }
                    } else {
                        // Show a popup asking for the instruction
                        let instruction = prompt("Add the instruction to the action you did.");
                        console.log("Instruction: " + instruction);

                        // Send keySequence to the API
                        if (isWriting && lastClickedElement) {
                            fetch(`http://localhost:8000/add_task_and_action/${taskID}`, {
                                method: "POST",
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    keySequence: text,
                                    action: ActionTypes.keyboard_input,
                                    screenshot: lastScreenshot,
                                    task_instruction: instruction
                                })
                            });
                            console.log("Sent keyboard input: " + text);
                            // After writing set storeAfterClick to true. 
                            // This is due to the fact that most of the time after writing you click on something and task ends.
                            storeAfterClick = true;
                            chrome.storage.local.set({storeAfterClick: storeAfterClick});
                            chrome.runtime.sendMessage({action: "updateUI", storeAfterClick: storeAfterClick}, function(response) {
                                console.log("Response from updateUI:");
                                console.log(response);
                              });

                        // Send click to the API
                        } else {
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
                            console.log("Sent click at bbox: " + JSON.stringify(bboxElement.bbox));
                        }
                    }
                    
                    // Get the element for next keyboard input
                    if (lastHighlightedElement instanceof HTMLInputElement || lastHighlightedElement instanceof HTMLTextAreaElement) {
                        lastClickedElement = lastHighlightedElement;
                    } else {
                        // Find an input or textarea within the clicked element
                        let inputElement = lastHighlightedElement.querySelector("input, textarea");
                        if (inputElement) {
                            lastClickedElement = inputElement;
                        } else {
                            // If no input or textarea is found, set lastClickedElement to null
                            lastClickedElement = null;
                        }
                    }
                    console.log("Last clicked element: " + lastClickedElement);
                    // Reset the isWriting flag
                    
                    lastHighlightedElement = null;
                    paused = false;
                    isWriting = false;
                    lastScreenshot = screenshotDataUrl;
                });

                if (overlay) {
                    overlay.style.display = 'block';
                }
            }
        },
        true
    );

    document.addEventListener("keydown", function (event) {
        // Checking if the key pressed is a non-special key
        // (i.e., alphanumeric, space, or punctuation)
        // If the key pressed is the Escape key, pause the recording
        // if (event.key === "Escape") {
        //     paused = true;
        //     if (document.getElementById("highlightDiv") !== null) {
        //         document.getElementById("highlightDiv").remove();
        //     }
        //     lastHighlightedElement.style.removeProperty("outline");
        //     if (overlay) {
        //         overlay.style.display = 'none';
        //     }
        // }

        if (event.key.length === 1) {
            isWriting = true;
        }
    });

    window.addEventListener("wheel", (event) => {
        if (!recording || paused) return;
        lastWheelDirection = event.deltaY < 0 ? -1 : 1; // -1 means up, 1 means down
    }, true);

    async function handleScrollEvent(event) {
        if (!recording || paused) return;
        if (scrollTimeout !== null) {
            clearTimeout(scrollTimeout);
        }

        if (document.getElementById("highlightDiv") !== null) {
            document.getElementById("highlightDiv").remove();
            await new Promise(resolve => requestAnimationFrame(resolve));
        }
        if (lastHighlightedElement) {
            lastHighlightedElement.style.removeProperty("outline");
        }
        paused = true;

        scrollTimeout = setTimeout(async () => {
            if (document.getElementById("highlightDiv") !== null) {
                document.getElementById("highlightDiv").remove();
            }
            if (lastHighlightedElement) {
                lastHighlightedElement.style.removeProperty("outline");
            }
            await new Promise(resolve => requestAnimationFrame(resolve));
            paused = true;
            // Take screenshot

            let bbox = getScrollableParentBoundingBox(event.target);
        
            // Know if the user is scrolling up or down
            action = lastWheelDirection > 0 ? ActionTypes.scroll_down_at_bbox : ActionTypes.scroll_up_at_bbox;

            chrome.runtime.sendMessage({action: "captureScreenshot", bbox: bbox}, function(response) {

                if (document.getElementById("highlightDiv") !== null) {
                    console.log("highlightDiv is still in the DOM 4");
                }

                bbox = response.bbox;

                // Append step
                fetch(`http://localhost:8000/add_page_action/${taskID}`, {
                    method: "POST",
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        screenshot: lastScreenshot,
                        bbox: bbox,
                        action: action
                    })
                });
                console.log("scroll action added");
                console.log("Action: " + action);
                paused = false;
                lastScreenshot = response.dataUrl;
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
