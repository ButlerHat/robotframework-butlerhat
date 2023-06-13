var tabStatuses = {};

chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (request.action == "captureScreenshot") {
        chrome.tabs.captureVisibleTab(null, {format: "png", quality: 100}, function(dataUrl) {
            var image = new Image();
            image.onload = function() {
                var canvas = document.createElement('canvas');
                var context = canvas.getContext('2d');

                var devicePixelRatio = window.devicePixelRatio || 1;
                canvas.width = image.width / devicePixelRatio;
                canvas.height = image.height / devicePixelRatio;

                context.scale(1 / devicePixelRatio, 1 / devicePixelRatio);
                context.drawImage(image, 0, 0);
                var downscaledDataUrl = canvas.toDataURL('image/png');
                
                sendResponse({dataUrl: downscaledDataUrl});
            };
            image.src = dataUrl;
        });
    }

    return true;  // Will respond asynchronously.
});

chrome.webNavigation.onCompleted.addListener(function(details) {
    chrome.tabs.executeScript(details.tabId, {
        code: 'window.isContentScriptInjected'
    }, function(results) {
        // If isContentScriptInjected is not defined, the result is undefined, and we need to inject the script.
        if (chrome.runtime.lastError || !results[0]) {
            chrome.tabs.executeScript(details.tabId, {
                file: 'content.js'
            });
        }
    });
}, {url: [{urlMatches : 'http.*://*/*'}]});

