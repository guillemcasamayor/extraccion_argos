document.getElementById("btn-summarize").addEventListener("click", () => {
    const engine = document.getElementById("engine").value;
    const model = document.getElementById("model").value;

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
            chrome.tabs.sendMessage(tabs[0].id, {
                action: "EXTRACT_AND_SUMMARIZE",
                engine: engine,
                model: model
            });
            window.close();
        }
    });
});
