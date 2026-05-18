document.addEventListener("DOMContentLoaded", function () {
    function setMessage(element, message, type = "info") {
        if (!element) return;
        element.className = `trade-message ${type}`;
        element.innerHTML = Array.isArray(message) ? message.join("<br>") : message;
    }

    function attachAccordion(button) {
        if (!button || button.dataset.bound === "true") return;
        button.dataset.bound = "true";
        button.addEventListener("click", function () {
            this.classList.toggle("active");
            const panel = this.nextElementSibling;
            if (!panel) return;
            panel.style.display = panel.style.display === "block" ? "none" : "block";
        });
    }

    document.querySelectorAll(".accordion").forEach(attachAccordion);

    function renderPortfolioGroups(grouped) {
        const container = document.getElementById("portfolio-groups");
        if (!container) return;

        container.innerHTML = "";

        Object.entries(grouped).forEach(([, data]) => {
            const button = document.createElement("button");
            button.className = "accordion portfolio-group-button";
            button.type = "button";
            button.textContent = data.portfolio_name;

            const panel = document.createElement("div");
            panel.className = "panel";

            const summary = data.summary || {};
            const summaryBox = document.createElement("div");
            summaryBox.className = "portfolio-summary";
            summaryBox.innerHTML = `
                <p><strong>Positions:</strong> ${summary.position_count ?? 0}</p>
                <p><strong>Total Allocated:</strong> ${summary.total_allocated_percent ?? 0}%</p>
                <p><strong>Remaining Cash:</strong> ${summary.remaining_cash_percent ?? 100}%</p>
                <p><strong>Average Score:</strong> ${summary.average_score ?? "N/A"}</p>
                <p><strong>Average Beta:</strong> ${summary.average_beta ?? "N/A"}</p>
                <p><strong>Status:</strong> ${summary.status ?? "N/A"}</p>
            `;
            panel.appendChild(summaryBox);

            if (!data.stocks || data.stocks.length === 0) {
                const empty = document.createElement("p");
                empty.className = "muted";
                empty.textContent = "No holdings saved yet.";
                panel.appendChild(empty);
            } else {
                const table = document.createElement("table");
                table.className = "table";
                table.innerHTML = `
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>Weight</th>
                            <th>Decision</th>
                            <th>Score</th>
                            <th>Sector</th>
                            <th>Beta</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.stocks.map(stock => `
                            <tr>
                                <td>${stock.ticker}</td>
                                <td>${stock.recommended_weight}</td>
                                <td>${stock.decision}</td>
                                <td>${stock.score ?? "N/A"}</td>
                                <td>${stock.sector || "Unknown"}</td>
                                <td>${stock.beta !== null && stock.beta !== undefined ? Number(stock.beta).toFixed(2) : "N/A"}</td>
                                <td>
                                    <button type="button" class="delete-holding-btn" data-holding-id="${stock.id}">
                                        Delete
                                    </button>
                                </td>
                            </tr>
                        `).join("")}
                    </tbody>
                `;
                panel.appendChild(table);
            }

            container.appendChild(button);
            container.appendChild(panel);
            attachAccordion(button);
        });

        document.querySelectorAll(".delete-holding-btn").forEach(button => {
            button.addEventListener("click", async function () {
                const holdingId = this.dataset.holdingId;

                try {
                    const response = await fetch(`/delete-holding/${holdingId}`, {
                        method: "DELETE"
                    });

                    const data = await response.json();

                    if (!response.ok || data.error) {
                        alert(data.error || "Could not delete holding.");
                        return;
                    }

                    renderPortfolioGroups(data.portfolio);
                } catch (error) {
                    console.error(error);
                    alert("Could not delete holding.");
                }
            });
        });
    }

    async function loadPortfolioGroups() {
        const container = document.getElementById("portfolio-groups");
        if (!container) return;

        try {
            const response = await fetch("/portfolio-stocks");
            const data = await response.json();
            renderPortfolioGroups(data);
        } catch (error) {
            console.error("Could not load portfolio groups:", error);
        }
    }

    loadPortfolioGroups();

    const quickAddForm = document.getElementById("quick-add-form");
    const quickAddMessage = document.getElementById("quick-add-message");

    if (quickAddForm) {
        quickAddForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            const ticker = document.getElementById("quick_ticker").value;
            const portfolioKey = document.getElementById("quick_portfolio_key").value;

            if (!ticker || !portfolioKey) {
                setMessage(quickAddMessage, "Please select both a stock and a portfolio.", "error");
                return;
            }

            setMessage(quickAddMessage, "Analysing stock and saving holding...", "info");

            try {
                const response = await fetch("/add-to-portfolio", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        ticker: ticker,
                        portfolio_key: portfolioKey
                    })
                });

                const data = await response.json();

                if (!response.ok || data.error) {
                    const errors = Array.isArray(data.error) ? data.error : [data.error || "Save failed."];
                    const warnings = Array.isArray(data.warnings) ? data.warnings : [];
                    setMessage(quickAddMessage, [...errors, ...warnings], "error");
                    return;
                }

                const messages = [data.message || "Holding saved."];
                if (Array.isArray(data.warnings) && data.warnings.length > 0) {
                    messages.push(...data.warnings);
                }

                setMessage(quickAddMessage, messages, "success");
            } catch (error) {
                console.error(error);
                setMessage(quickAddMessage, "Could not save holding.", "error");
            }
        });
    }

    const marketTable = document.getElementById("market-table");

    if (marketTable) {
        const tbody = marketTable.querySelector("tbody");
        const headers = marketTable.querySelectorAll("th[data-sort]");

        const tickerFilter = document.getElementById("ticker-filter");
        const decisionFilter = document.getElementById("decision-filter");
        const scoreFilter = document.getElementById("score-filter");
        const volatilityFilter = document.getElementById("volatility-filter");
        const sharpeFilter = document.getElementById("sharpe-filter");
        const summary = document.getElementById("dashboard-summary");

        let activePreset = "";

        function parseNumber(value) {
            const num = parseFloat(value);
            return isNaN(num) ? null : num;
        }

        function applyDashboardFilters() {
            const rows = tbody.querySelectorAll("tr");

            const tickerValue = tickerFilter ? tickerFilter.value.toUpperCase() : "";
            const decisionValue = decisionFilter ? decisionFilter.value : "";
            const scoreValue = scoreFilter ? parseNumber(scoreFilter.value) : null;
            const volatilityValue = volatilityFilter ? parseNumber(volatilityFilter.value) : null;
            const sharpeValue = sharpeFilter ? parseNumber(sharpeFilter.value) : null;

            let visibleCount = 0;

            rows.forEach(row => {
                const rowTicker = (row.dataset.ticker || "").toUpperCase();
                const rowDecision = row.dataset.decision || "";
                const rowScore = parseNumber(row.dataset.score);
                const rowVolatility = parseNumber(row.dataset.volatility);
                const rowSharpe = parseNumber(row.dataset.sharpe);

                let visible = true;

                if (tickerValue && rowTicker !== tickerValue) visible = false;
                if (decisionValue && rowDecision !== decisionValue) visible = false;
                if (scoreValue !== null && (rowScore === null || rowScore < scoreValue)) visible = false;
                if (volatilityValue !== null && (rowVolatility === null || rowVolatility > volatilityValue)) visible = false;
                if (sharpeValue !== null && (rowSharpe === null || rowSharpe < sharpeValue)) visible = false;

                if (activePreset === "low-risk" && row.dataset.lowRisk !== "true") visible = false;
                if (activePreset === "high-conviction" && row.dataset.highConviction !== "true") visible = false;
                if (activePreset === "core" && row.dataset.coreHolding !== "true") visible = false;
                if (activePreset === "satellite" && row.dataset.satellite !== "true") visible = false;
                if (activePreset === "exploratory" && row.dataset.exploratory !== "true") visible = false;
                if (activePreset === "income" && row.dataset.incomeCandidate !== "true") visible = false;
                if (activePreset === "best-ranked" && row.dataset.bestRanked !== "true") visible = false;
                if (activePreset === "cash" && row.dataset.cashCandidate !== "true") visible = false;

                row.style.display = visible ? "" : "none";
                if (visible) visibleCount += 1;
            });

            if (summary) {
                summary.textContent = `Showing ${visibleCount} securities after applying filters.`;
            }
        }

        function clearDashboardFilters() {
            if (tickerFilter) tickerFilter.value = "";
            if (decisionFilter) decisionFilter.value = "";
            if (scoreFilter) scoreFilter.value = "";
            if (volatilityFilter) volatilityFilter.value = "";
            if (sharpeFilter) sharpeFilter.value = "";
            activePreset = "";
            applyDashboardFilters();
        }

        const presetMap = {
            "preset-low-risk": "low-risk",
            "preset-high-conviction": "high-conviction",
            "preset-core": "core",
            "preset-satellite": "satellite",
            "preset-exploratory": "exploratory",
            "preset-income": "income",
            "preset-best-ranked": "best-ranked",
            "preset-cash": "cash"
        };

        Object.entries(presetMap).forEach(([buttonId, presetName]) => {
            const button = document.getElementById(buttonId);
            if (button) {
                button.addEventListener("click", function () {
                    clearDashboardFilters();
                    activePreset = presetName;
                    applyDashboardFilters();
                });
            }
        });

        const clearButton = document.getElementById("clear-filters");
        if (clearButton) clearButton.addEventListener("click", clearDashboardFilters);

        [tickerFilter, decisionFilter, scoreFilter, volatilityFilter, sharpeFilter].forEach(control => {
            if (control) {
                control.addEventListener("input", function () {
                    activePreset = "";
                    applyDashboardFilters();
                });
                control.addEventListener("change", function () {
                    activePreset = "";
                    applyDashboardFilters();
                });
            }
        });

        headers.forEach((header, index) => {
            header.style.cursor = "pointer";
            header.dataset.direction = "desc";

            header.addEventListener("click", function () {
                const rows = Array.from(tbody.querySelectorAll("tr"));
                const direction = this.dataset.direction === "asc" ? "desc" : "asc";
                this.dataset.direction = direction;

                rows.sort((a, b) => {
                    const aText = a.children[index].textContent.trim();
                    const bText = b.children[index].textContent.trim();

                    const aNum = parseFloat(aText.replace(/[^\d.-]/g, ""));
                    const bNum = parseFloat(bText.replace(/[^\d.-]/g, ""));

                    let comparison;
                    if (!isNaN(aNum) && !isNaN(bNum)) comparison = aNum - bNum;
                    else comparison = aText.localeCompare(bText);

                    return direction === "asc" ? comparison : -comparison;
                });

                rows.forEach(row => tbody.appendChild(row));
                applyDashboardFilters();
            });
        });

        applyDashboardFilters();
    }
});
