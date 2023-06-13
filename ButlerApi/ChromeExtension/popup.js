chrome.storage.local.get(["recording", "disabelHover", "paused"], function(result) {
    
    let recording = result.recording || false;
    let paused = result.paused || false;
    let hoverDisabled = result.disableHover || true;

    // Update button display based on recording state
    function updateButtons() {
        document.getElementById("recordBtn").style.display = (!recording && !paused) ? "block" : "none";
        document.getElementById("pauseBtn").style.display = (recording && !paused) ? "block" : "none";
        document.getElementById("resumeBtn").style.display = (!recording && paused) ? "block" : "none";
        document.getElementById("stopBtn").style.display = (recording || paused) ? "block" : "none";
        document.getElementById('disableHover').checked = hoverDisabled;
    }

    document.getElementById('disableHover').addEventListener('change', (event) => {
        hoverDisabled = event.target.checked;
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            chrome.tabs.sendMessage(tabs[0].id, {action: "toggleHover", disableHover: hoverDisabled});
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