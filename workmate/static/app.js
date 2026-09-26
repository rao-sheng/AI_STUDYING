const modeConfig = {
    knowledge: {
        endpoint: "/ask",
        label: "规则问答",
        title: "帮助你核对规则并回复买家",
        description: "基于商家知识库回答售后、商品和平台规则问题，并提供来源。",
        placeholder: "例如：商品支持七天无理由退货吗？",
        loadingText: "正在检索知识库并生成回答……",
        examples: [
            "商品支持七天无理由退货吗？",
            "库存不足时可以提现吗？",
        ],
    },
    operations: {
        endpoint: "/agent/chat",
        label: "运营分析",
        title: "基于真实数据辅助运营决策",
        description: "仅供商家内部使用，可查询库存、经营指标并获取补货建议。",
        placeholder: "例如：SKU-1001 的经营情况怎么样，是否需要补货？",
        loadingText: "正在查询商家数据并分析……",
        examples: [
            "哪些商品库存不足，需要优先补货？",
            "SKU-1001 的经营情况怎么样，是否需要补货？",
        ],
    },
};

let currentMode = "knowledge";
let isSending = false;

const histories = {
    knowledge: [],
    operations: [],
};

const modeButtons = document.querySelectorAll(".mode-button");
const modeLabel = document.querySelector("#mode-label");
const modeTitle = document.querySelector("#mode-title");
const modeDescription = document.querySelector("#mode-description");
const exampleList = document.querySelector("#example-list");
const messages = document.querySelector("#messages");
const questionForm = document.querySelector("#question-form");
const questionInput = document.querySelector("#question-input");
const clearButton = document.querySelector("#clear-button");
const sendButton = document.querySelector("#send-button");


function renderExamples() {
    const config = modeConfig[currentMode];

    exampleList.replaceChildren();

    for (const question of config.examples) {
        const button = document.createElement("button");

        button.type = "button";
        button.className = "example-button";
        button.textContent = question;

        button.addEventListener("click", () => {
            questionInput.value = question;
            questionInput.focus();
        });

        exampleList.append(button);
    }
}


function renderMessages() {
    const history = histories[currentMode];

    messages.replaceChildren();

    if (history.length === 0) {
        const emptyState = document.createElement("p");

        emptyState.className = "empty-state";
        emptyState.textContent = "输入一个问题，开始查询。";

        messages.append(emptyState);
        return;
    }

    for (const message of history) {
        const bubble = document.createElement("article");
        const content = document.createElement("div");

        bubble.className = `message message-${message.role}`;
        content.textContent = message.text;

        bubble.append(content);

        if (message.sources?.length) {
            const sourceLine = document.createElement("p");

            sourceLine.className = "message-meta";
            sourceLine.textContent = `参考来源：${message.sources
                .map((source) => `${source.id}（${source.source}）`)
                .join("、")}`;

            bubble.append(sourceLine);
        }

        messages.append(bubble);
    }

    messages.scrollTop = messages.scrollHeight;
}


function addMessage(mode, message) {
    histories[mode].push(message);

    if (currentMode === mode) {
        renderMessages();
    }
}


function removeLoadingMessage(mode) {
    histories[mode] = histories[mode].filter(
        (message) => !message.loading,
    );
}


function setSending(nextIsSending) {
    isSending = nextIsSending;

    questionInput.disabled = isSending;
    clearButton.disabled = isSending;
    sendButton.disabled = isSending;
    sendButton.textContent = isSending ? "正在处理……" : "发送问题";
}


function setMode(nextMode) {
    currentMode = nextMode;

    const config = modeConfig[currentMode];

    modeLabel.textContent = config.label;
    modeTitle.textContent = config.title;
    modeDescription.textContent = config.description;
    questionInput.placeholder = config.placeholder;

    for (const button of modeButtons) {
        const isActive = button.dataset.mode === currentMode;

        button.classList.toggle("is-active", isActive);
    }

    renderExamples();
    renderMessages();
}


async function sendQuestion(question) {
    const requestMode = currentMode;
    const config = modeConfig[requestMode];

    addMessage(requestMode, {
        role: "user",
        text: question,
    });

    questionInput.value = "";

    addMessage(requestMode, {
        role: "assistant",
        text: config.loadingText,
        loading: true,
    });

    setSending(true);

    try {
        const response = await fetch(config.endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                question,
            }),
        });

        let payload;

        try {
            payload = await response.json();
        } catch {
            throw new Error("服务返回了无法解析的响应。");
        }

        if (!response.ok) {
            throw new Error(
                typeof payload.detail === "string"
                    ? payload.detail
                    : "请求失败，请稍后重试。",
            );
        }

        if (typeof payload.answer !== "string" || !payload.answer.trim()) {
            throw new Error("服务未返回有效回答。");
        }

        removeLoadingMessage(requestMode);

        addMessage(requestMode, {
            role: "assistant",
            text: payload.answer,
            sources: Array.isArray(payload.sources) ? payload.sources : [],
        });
    } catch (error) {
        removeLoadingMessage(requestMode);

        addMessage(requestMode, {
            role: "error",
            text: error instanceof Error ? error.message : "请求失败，请稍后重试。",
        });
    } finally {
        setSending(false);

        if (currentMode === requestMode) {
            renderMessages();
        }
    }
}


for (const button of modeButtons) {
    button.addEventListener("click", () => {
        setMode(button.dataset.mode);
    });
}


clearButton.addEventListener("click", () => {
    histories[currentMode] = [];
    renderMessages();
});


questionForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const question = questionInput.value.trim();

    if (!question || isSending) {
        return;
    }

    sendQuestion(question);
});


setMode("knowledge");