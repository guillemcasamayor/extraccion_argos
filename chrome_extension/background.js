// Background Service Worker: Registro de Menú Contextual y Auto-Apertura Copilot

chrome.runtime.onInstalled.addListener(() => {
    // Limpiar menús anteriores para evitar error de ID duplicado al recargar la extensión
    chrome.contextMenus.removeAll(() => {
        // Menú Principal al hacer Clic Derecho
        chrome.contextMenus.create({
            id: "RIS_LLM_PARENT",
            title: "🧠 Resumir Historia RIS con LLM",
            contexts: ["page", "selection", "frame"]
        });

        // Opción 1: LLM Local
        chrome.contextMenus.create({
            parentId: "RIS_LLM_PARENT",
            id: "SUMMARIZE_LOCAL",
            title: "🚀 Inferencia Local (Ollama - Qwen 2.5 / Llama 3.3)",
            contexts: ["page", "selection", "frame"]
        });

        // Opción 2: API Copilot
        chrome.contextMenus.create({
            parentId: "RIS_LLM_PARENT",
            id: "SUMMARIZE_API",
            title: "☁️ API Corporativa (Copilot / Azure OpenAI - RGPD)",
            contexts: ["page", "selection", "frame"]
        });

        // Opción 3: Abrir Copilot Chat Web y Autopegar Prompt
        chrome.contextMenus.create({
            parentId: "RIS_LLM_PARENT",
            id: "OPEN_AND_PASTE_COPILOT",
            title: "🚀 Abrir Copilot Chat Web y AUTOPEGAR Prompt Anonimizado",
            contexts: ["page", "selection", "frame"]
        });
    });
});

// Manejo del evento del Clic Derecho
chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (!tab || !tab.id) return;

    let engine = "local";
    let model = "qwen2.5:7b-instruct";

    if (info.menuItemId === "SUMMARIZE_API") {
        engine = "api";
        model = "gpt-4o";
    } else if (info.menuItemId === "OPEN_AND_PASTE_COPILOT") {
        engine = "copilot_manual";
        model = "copilot-chat";
    }

    // Comunicar con la pestaña activa (SAP) de forma segura
    chrome.tabs.sendMessage(tab.id, {
        action: "EXTRACT_AND_SUMMARIZE",
        engine: engine,
        model: model,
        selectionText: info.selectionText || "",
        autoOpenCopilot: (info.menuItemId === "OPEN_AND_PASTE_COPILOT")
    }, (response) => {
        if (chrome.runtime.lastError) {
            console.warn("Script de contenido no listo en esta página. Inyectando dinámicamente...");
            // Si la página se abrió antes de cargar la extensión, inyectamos content.js dinámicamente
            chrome.scripting.executeScript({
                target: { tabId: tab.id },
                files: ["content.js"]
            }).then(() => {
                setTimeout(() => {
                    chrome.tabs.sendMessage(tab.id, {
                        action: "EXTRACT_AND_SUMMARIZE",
                        engine: engine,
                        model: model,
                        selectionText: info.selectionText || "",
                        autoOpenCopilot: (info.menuItemId === "OPEN_AND_PASTE_COPILOT")
                    });
                }, 200);
            }).catch(err => console.error("Error al inyectar script:", err));
        }
    });
});

// Escuchar peticiones para abrir la pestaña de Copilot Chat Web
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "OPEN_COPILOT_AND_PASTE") {
        const promptText = request.readyPrompt;
        
        // Guardar el prompt en el almacenamiento de la extensión
        chrome.storage.local.set({ pending_copilot_prompt: promptText }, () => {
            // Abrir la pestaña de Copilot Chat Web
            const copilotUrl = "https://m365.cloud.microsoft/chat?auth=2&home=1&from=ShellLogo";
            chrome.tabs.create({ url: copilotUrl, active: true });
            sendResponse({ status: "ok" });
        });

        return true;
    }
});
