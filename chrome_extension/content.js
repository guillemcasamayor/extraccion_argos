// Content Script inyectado en Chrome (SAP & Copilot Chat)

console.log("RIS LLM Summarizer Content Script cargado en:", window.location.href);

// 1. AUTO-PEGADO EN COPILOT CHAT WEB (m365.cloud.microsoft)
if (window.location.hostname.includes("cloud.microsoft") || window.location.hostname.includes("copilot.microsoft.com")) {
    checkAndAutoPasteCopilotPrompt();
}

function checkAndAutoPasteCopilotPrompt() {
    chrome.storage.local.get("pending_copilot_prompt", (result) => {
        const promptText = result.pending_copilot_prompt;
        if (!promptText) return;

        console.log("Detectado Prompt pendiente para Copilot. Esperando a que el campo de chat esté listo...");

        // Copiamos inmediatamente al portapapeles
        navigator.clipboard.writeText(promptText).catch(() => {});

        // Reintentamos detectar y enfocar la caja de texto durante unos segundos hasta que cargue la interfaz
        let attempts = 0;
        const maxAttempts = 30; // 15 segundos máximo

        const interval = setInterval(() => {
            attempts++;
            const chatInput = findCopilotInput();

            if (chatInput) {
                clearInterval(interval);
                console.log("¡Caja de texto de Copilot encontrada! Pegando prompt...");

                // Enfocar la caja de texto
                chatInput.focus();

                // Insertar el texto
                if (chatInput.tagName === "TEXTAREA" || chatInput.tagName === "INPUT") {
                    chatInput.value = promptText;
                    chatInput.dispatchEvent(new Event("input", { bubbles: true }));
                    chatInput.dispatchEvent(new Event("change", { bubbles: true }));
                } else if (chatInput.isContentEditable) {
                    chatInput.innerText = promptText;
                    chatInput.dispatchEvent(new Event("input", { bubbles: true }));
                }

                // Notificación visual de éxito sobre la página de Copilot
                showCopilotSuccessNotification();

                // Limpiar el storage para no repetir en futuras cargas espontáneas
                chrome.storage.local.remove("pending_copilot_prompt");
            } else if (attempts >= maxAttempts) {
                clearInterval(interval);
                alert("⚠️ Se abrió Copilot Chat. El prompt está guardado en tu portapapeles. Presiona Ctrl + V en la caja de texto para pegarlo.");
                chrome.storage.local.remove("pending_copilot_prompt");
            }
        }, 500);
    });
}

function findCopilotInput() {
    // Buscar elemento enfocado actualmente o selectores comunes de la interfaz de Copilot
    if (document.activeElement && (document.activeElement.tagName === "TEXTAREA" || document.activeElement.isContentEditable)) {
        return document.activeElement;
    }

    const selectors = [
        "textarea",
        "div[contenteditable='true']",
        "#searchbox",
        "#cib-focused-element",
        "textarea[placeholder*='pregunt']",
        "textarea[placeholder*='ask']",
        "textarea[aria-label*='Copilot']"
    ];

    for (const selector of selectors) {
        const el = document.querySelector(selector);
        if (el) return el;
    }

    return null;
}

function showCopilotSuccessNotification() {
    let notif = document.getElementById("ris-copilot-notif");
    if (notif) notif.remove();

    notif = document.createElement("div");
    notif.id = "ris-copilot-notif";
    notif.style.position = "fixed";
    notif.style.top = "20px";
    notif.style.left = "50%";
    notif.style.transform = "translateX(-50%)";
    notif.style.zIndex = "999999";
    notif.style.backgroundColor = "#0284c7";
    notif.style.color = "#ffffff";
    notif.style.padding = "16px 30px";
    notif.style.borderRadius = "10px";
    notif.style.boxShadow = "0 10px 30px rgba(0,0,0,0.4)";
    notif.style.fontFamily = "system-ui, sans-serif";
    notif.style.fontSize = "15px";
    notif.style.fontWeight = "bold";
    notif.style.textAlign = "center";
    notif.style.border = "1px solid #38bdf8";
    notif.innerHTML = "📋 <strong>Prompt anonimizado listo en tu portapapeles</strong><br><span style='font-size:13px; font-weight:normal; opacity:0.95;'>Haz clic en la caja de chat de Copilot y presiona <strong>Ctrl + V</strong> y <strong>Enter</strong> para enviar.</span>";
    document.body.appendChild(notif);

    setTimeout(() => {
        if (notif) notif.remove();
    }, 10000);
}



// Función para extraer notas de Argos / SAP atravesando el Shadow DOM (<cc-item>)
function extractArgosNotesFromShadowDOM(doc = document) {
    let notes = [];

    function scanRoot(root) {
        if (!root) return;

        // 1. Buscar elementos <cc-item> (Web Components de Argos)
        const ccItems = root.querySelectorAll('cc-item');
        ccItems.forEach((item, idx) => {
            const shadow = item.shadowRoot;
            if (shadow) {
                // Extraer Fecha / Hora desde atributos del elemento <cc-item> o elementos internos del shadowRoot
                const attrDate = item.getAttribute('date') || item.getAttribute('data-date') || item.getAttribute('created') || item.getAttribute('timestamp') || item.getAttribute('fecha');
                const dateEl = shadow.querySelector('.content__date, .date, time, [class*="date"], [class*="time"], [class*="header__date"], .header__time, .item__date');
                const titleEl = shadow.querySelector('.content__title, .title, header, .content__header, .header');
                const descEl = shadow.querySelector('.content__description, .description, .content');

                const dateText = dateEl ? (dateEl.innerText || dateEl.textContent).trim() : (attrDate || "");
                const titleText = titleEl ? (titleEl.innerText || titleEl.textContent).trim() : "";
                const descText = descEl ? (descEl.innerText || descEl.textContent).trim() : (shadow.innerText || shadow.textContent).trim();

                // Búsqueda de patrón de fecha DD/MM/YYYY o YYYY-MM-DD o DD-MM-YYYY en cualquier parte del shadow header
                let fechaEncontrada = dateText;
                if (!fechaEncontrada) {
                    const fullHeaderText = (titleText + " " + (shadow.firstElementChild ? shadow.firstElementChild.innerText : "")).trim();
                    const matchFecha = fullHeaderText.match(/\b(0?[1-9]|[12][0-9]|3[01])[\/\.-](0?[1-9]|1[012])[\/\.-](19|20)\d\d(?:\s+(?:a\s+las\s+)?\d{1,2}:\d{2}(?::\d{2})?)?\b/i);
                    if (matchFecha) fechaEncontrada = matchFecha[0];
                }

                if (descText && descText.length > 5) {
                    let headerInfo = [];
                    if (fechaEncontrada) headerInfo.push(`FECHA: ${fechaEncontrada}`);
                    if (titleText && titleText !== fechaEncontrada) headerInfo.push(titleText);

                    const headerStr = headerInfo.length > 0 ? headerInfo.join(" | ") : `NOTA CLÍNICA ${idx + 1}`;
                    notes.push(`--- NOTA [${headerStr}] ---\n${descText}`);
                }

            }
        });

        // 2. Explorar otros elementos que puedan tener shadowRoot
        const allElements = root.querySelectorAll('*');
        allElements.forEach(el => {
            if (el.shadowRoot && el.tagName !== 'CC-ITEM') {
                scanRoot(el.shadowRoot);
            }
        });

        // 3. Explorar en iframes
        const iframes = root.querySelectorAll('iframe, frame');
        iframes.forEach(frame => {
            try {
                const frameDoc = frame.contentDocument || (frame.contentWindow && frame.contentWindow.document);
                if (frameDoc) scanRoot(frameDoc);
            } catch (e) {
                console.warn("Iframe mismo origen restringido:", e);
            }
        });
    }

    scanRoot(doc);
    return notes;
}


// Función global de extracción completa
function getFullArgosExtraction(doc = document) {
    // Intentar primero extracción en Shadow DOM (<cc-item>)
    const shadowNotes = extractArgosNotesFromShadowDOM(doc);
    
    if (shadowNotes.length > 0) {
        console.log(`✅ Extraídas ${shadowNotes.length} notas desde el Shadow DOM (<cc-item>).`);
        const fullText = shadowNotes.join("\n\n");
        return {
            text: fullText,
            html: `<div>${shadowNotes.map(n => `<article>${n.replace(/\n/g, '<br>')}</article>`).join('')}</div>`
        };
    }

    // Fallback: Si no hay Shadow DOM, extraer todo el innerText e iframes convencionales
    console.log("⚠️ No se encontraron elementos cc-item en Shadow DOM, recurriendo a extracción clásica...");
    let fallbackText = doc.body ? doc.body.innerText : "";
    let fallbackHtml = doc.body ? doc.body.innerHTML : "";
    return { text: fallbackText, html: fallbackHtml };
}

// 2. MANEJO DE PÁGINAS DE SAP / RIS (EXTRACCIÓN)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "EXTRACT_AND_SUMMARIZE") {
        let extractedContent = { text: "", html: "" };

        // Si el usuario seleccionó texto manualmente con el ratón, usamos ese texto
        const selection = window.getSelection().toString().trim();
        if (request.selectionText || selection) {
            extractedContent.text = request.selectionText || selection;
            extractedContent.html = `<p>${extractedContent.text}</p>`;
        } else {
            // Extracción avanzada de Argos con soporte Shadow DOM <cc-item>
            extractedContent = getFullArgosExtraction(document);
        }

        showLoadingOverlay();

        fetch("http://127.0.0.1:5000/summarize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                html: extractedContent.html,
                text: extractedContent.text,
                engine: request.engine || "local",
                model: request.model || "qwen2.5:7b-instruct"
            })
        })
        .then(response => response.json())
        .then(data => {
            removeLoadingOverlay();
            if (data.status === "success") {
                if (request.autoOpenCopilot && data.ready_prompt) {
                    chrome.runtime.sendMessage({
                        action: "OPEN_COPILOT_AND_PASTE",
                        readyPrompt: data.ready_prompt
                    });
                } else {
                    showSummarySidebar(data.summary, data.elapsed_seconds, data.engine, data.ready_prompt || null);
                }
                sendResponse({ status: "ok" });
            } else {
                alert("Error al procesar: " + (data.error_message || "Error desconocido"));
                sendResponse({ status: "error" });
            }
        })
        .catch(err => {
            removeLoadingOverlay();
            alert("No se pudo conectar con el servidor local Python (127.0.0.1:5000). Asegúrate de tener ejecutado 'iniciar_servidor.bat'.");
            sendResponse({ status: "error" });
        });

        return true;
    }
});



function showLoadingOverlay() {
    let overlay = document.getElementById("ris-llm-loading");
    if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "ris-llm-loading";
        overlay.style.position = "fixed";
        overlay.style.top = "20px";
        overlay.style.right = "20px";
        overlay.style.zIndex = "999999";
        overlay.style.backgroundColor = "#1e293b";
        overlay.style.color = "#ffffff";
        overlay.style.padding = "16px 24px";
        overlay.style.borderRadius = "8px";
        overlay.style.boxShadow = "0 10px 25px rgba(0,0,0,0.3)";
        overlay.style.fontFamily = "sans-serif";
        overlay.style.fontSize = "14px";
        overlay.style.fontWeight = "bold";
        overlay.innerHTML = "⏳ Extrayendo datos de SAP, anonimizando y abriendo Copilot...";
        document.body.appendChild(overlay);
    }
}

function removeLoadingOverlay() {
    const overlay = document.getElementById("ris-llm-loading");
    if (overlay) overlay.remove();
}

function showSummarySidebar(summaryText, elapsedSeconds, engineName, readyPrompt = null) {
    let sidebar = document.getElementById("ris-llm-sidebar");
    if (sidebar) sidebar.remove();

    sidebar = document.createElement("div");
    sidebar.id = "ris-llm-sidebar";
    sidebar.style.position = "fixed";
    sidebar.style.top = "0";
    sidebar.style.right = "0";
    sidebar.style.width = "450px";
    sidebar.style.height = "100vh";
    sidebar.style.zIndex = "999999";
    sidebar.style.backgroundColor = "#0f172a";
    sidebar.style.color = "#f8fafc";
    sidebar.style.padding = "24px";
    sidebar.style.boxShadow = "-5px 0 25px rgba(0,0,0,0.5)";
    sidebar.style.overflowY = "auto";
    sidebar.style.fontFamily = "system-ui, -apple-system, sans-serif";

    const formattedSummary = summaryText.replace(/\n/g, "<br>").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    const textToCopy = readyPrompt ? readyPrompt : summaryText;

    sidebar.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #334155; padding-bottom:12px; margin-bottom:16px;">
            <h3 style="margin:0; font-size:15px; color:#38bdf8;">🧠 RIS LLM (${engineName})</h3>
            <button id="ris-llm-close" style="background:transparent; border:none; color:#94a3b8; font-size:20px; cursor:pointer;">&times;</button>
        </div>
        <div style="font-size:13px; line-height:1.6; color:#e2e8f0; margin-bottom:20px;">
            ${formattedSummary}
        </div>
        <div style="font-size:11px; color:#64748b; border-top:1px solid #334155; padding-top:12px; display:flex; justify-content:space-between; align-items:center;">
            <span>⏱️ ${elapsedSeconds}s</span>
            <button id="ris-llm-copy" style="background:#0284c7; color:#fff; border:none; padding:8px 14px; border-radius:6px; cursor:pointer; font-size:12px; font-weight:bold;">📋 Copiar Prompt + Texto</button>
        </div>
    `;

    document.body.appendChild(sidebar);

    if (readyPrompt) {
        navigator.clipboard.writeText(readyPrompt).catch(() => {});
    }

    document.getElementById("ris-llm-close").onclick = () => sidebar.remove();
    document.getElementById("ris-llm-copy").onclick = () => {
        navigator.clipboard.writeText(textToCopy);
        alert("¡Copiado al portapapeles! Ya puedes pegarlo (Ctrl + V) en Microsoft Copilot Chat.");
    };
}
