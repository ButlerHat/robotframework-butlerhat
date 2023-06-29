chrome.storage.local.get(["recording", "setHover", "storeAfterClick", "paused"], function(result) {
    
    let recording = result.recording || false;
    let paused = result.paused || false;
    let setHover = result.setHover === undefined ? true : result.setHover;
    let storeAfterClick = result.storeAfterClick === undefined ? true : result.storeAfterClick;

    // Add listener to update buttons when recording state changes
    chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
        if (request.action == "updateUI") {
            recording = request.recording || recording;
            paused = request.paused || paused;
            setHover = request.setHover || setHover;
            storeAfterClick = request.storeAfterClick === undefined ? storeAfterClick : request.storeAfterClick;
            updateButtons();
            sendResponse({message: "UI updated"});
        }
      });

    // Update button display based on recording state
    function updateButtons() {
        document.getElementById("recordBtn").style.display = (!recording && !paused) ? "block" : "none";
        document.getElementById("createTaskBtn").style.display = recording ? "block" : "none";
        document.getElementById("pauseBtn").style.display = (recording && !paused) ? "block" : "none";
        document.getElementById("resumeBtn").style.display = (!recording && paused) ? "block" : "none";
        document.getElementById("stopBtn").style.display = (recording || paused) ? "block" : "none";
        document.getElementById('setHover').checked = setHover;
        document.getElementById('storeAfterClick').checked = storeAfterClick;
    }

    document.getElementById('setHover').addEventListener('change', (event) => {
        setHover = event.target.checked;
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            chrome.tabs.sendMessage(tabs[0].id, {action: "toggleHover", setHover: setHover});
        });
    });

    document.getElementById('storeAfterClick').addEventListener('change', (event) => {
        storeAfterClick = event.target.checked;
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            chrome.tabs.sendMessage(tabs[0].id, {action: "toggleStoreAfterClick", storeAfterClick: storeAfterClick});
        });
    });

    document.getElementById("recordBtn").addEventListener("click", function() {
        // Log to console
        let taskName = prompt("Enter the name of the task:");
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            chrome.tabs.sendMessage(tabs[0].id, {action: "startRecording", task_name: taskName}, function(response) {
                console.log("Response from startRecording:");
                console.log(response);
                recording = response.recording;
                paused = response.paused;
                updateButtons();
                document.getElementById("loadingLabel").style.display = "none";
            });
        });
        document.getElementById("loadingLabel").style.display = "block";
    });

    document.getElementById("createTaskBtn").addEventListener("click", function() {
        let instruction = prompt("Enter the instruction for the task:");
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            chrome.tabs.sendMessage(tabs[0].id, {action: "createTask", instruction: instruction});
        });
    });

    document.getElementById("pauseBtn").addEventListener("click", function() {
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            chrome.tabs.sendMessage(tabs[0].id, {action: "pauseRecording"}, function(response) {
                if (chrome.runtime.lastError) {
                    // Handle error
                    console.error(chrome.runtime.lastError.message);
                    return;
                }
                recording = response.recording;
                paused = response.paused;
                updateButtons();
                document.getElementById("loadingLabel").style.display = "none";
            });
        });
        document.getElementById("loadingLabel").style.display = "block";
    });

    document.getElementById("resumeBtn").addEventListener("click", function() {
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            chrome.tabs.sendMessage(tabs[0].id, {action: "resumeRecording"}, function(response) {
                recording = response.recording;
                paused = response.paused;
                updateButtons();
                document.getElementById("loadingLabel").style.display = "none";
            });
        });
        document.getElementById("loadingLabel").style.display = "block";
    });

    document.getElementById('stopBtn').addEventListener('click', function() {
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            chrome.tabs.sendMessage(tabs[0].id, {action: "stopRecording"}, function(response) {
                if (chrome.runtime.lastError) {
                    // Handle error
                    console.error(chrome.runtime.lastError.message);
                    return;
                }
                recording = response.recording;
                paused = response.paused;
                updateButtons();
                document.getElementById("loadingLabel").style.display = "none";
            });
        });
        document.getElementById("loadingLabel").style.display = "block";
    });

    updateButtons();
});