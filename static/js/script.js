// ==================== PAGE LOAD AND MAIN SCRIPT SETUP ==================== // This main section waits for the HTML page to finish loading before the JavaScript starts working properly.
document.addEventListener("DOMContentLoaded", function () { // This makes sure the script only runs after all the page elements are available in the browser.

    // -------------------- Reusable Message Helper -------------------- // This helper function is used to show feedback messages to the user in a clean and consistent way.
    function setMessage(element, message, type = "info") { // This function receives the message area, the message text, and the type of message such as info, success, or error.
        if (!element) return; // This protects the code from breaking if the message element does not exist on the current page.
        element.className = `trade-message ${type}`; // This updates the CSS class so the message can be styled differently depending on whether it is an error, success, or information.
        element.innerHTML = Array.isArray(message) ? message.join("<br>") : message; // This allows the message to be shown as one line or as multiple lines if an array of messages is passed.
    } // This ends the reusable message helper function.

    // ==================== ACCORDION FUNCTIONALITY ==================== // This section controls the expandable and collapsible accordion panels used on the portfolio page.

    // -------------------- Attach Accordion Behaviour -------------------- // This function adds click behaviour to each accordion button.
    function attachAccordion(button) { // This function receives one accordion button and prepares it so the user can open and close the related panel.
        if (!button || button.dataset.bound === "true") return; // This prevents errors if the button is missing and also avoids attaching the same event listener more than once.
        button.dataset.bound = "true"; // This marks the accordion as already connected to JavaScript so duplicate event listeners are avoided.
        button.addEventListener("click", function () { // This listens for a click on the accordion button.
            this.classList.toggle("active"); // This adds or removes the active class so the button can visually show whether it is open.
            const panel = this.nextElementSibling; // This finds the panel directly after the button, which is the content area that should open or close.
            if (!panel) return; // This safely stops the function if there is no panel after the button.
            panel.style.display = panel.style.display === "block" ? "none" : "block"; // This switches the panel between visible and hidden each time the user clicks.
        }); // This ends the click event listener for the accordion.
    } // This ends the attachAccordion function.

    // -------------------- Activate Existing Accordions -------------------- // This connects the accordion function to any accordion buttons already on the page.
    document.querySelectorAll(".accordion").forEach(attachAccordion); // This finds every element with the accordion class and gives each one the open and close behaviour.

    // ==================== PORTFOLIO GROUP RENDERING ==================== // This section builds the saved portfolio groups dynamically using data returned from the Flask backend.

    // -------------------- Render Portfolio Groups On Page -------------------- // This function displays portfolio summaries and holdings inside accordion panels.
    function renderPortfolioGroups(grouped) { // This function receives grouped portfolio data from the backend and displays it in the portfolio section.
        const container = document.getElementById("portfolio-groups"); // This finds the main container where all portfolio groups will be inserted.
        if (!container) return; // This stops the function if the portfolio container does not exist on the current page.

        container.innerHTML = ""; // This clears the old portfolio content so the page does not show duplicated or outdated information.

        Object.entries(grouped).forEach(([, data]) => { // This loops through each portfolio group returned from the backend.
            const button = document.createElement("button"); // This creates a new button element for the accordion heading of the portfolio.
            button.className = "accordion portfolio-group-button"; // This gives the button the correct CSS classes for styling and accordion behaviour.
            button.type = "button"; // This makes sure the button does not accidentally submit a form.
            button.textContent = data.portfolio_name; // This displays the portfolio name as the clickable accordion title.

            const panel = document.createElement("div"); // This creates the panel that will contain the portfolio summary and holdings table.
            panel.className = "panel"; // This gives the panel the correct CSS class so it can be styled and hidden or shown.

            // -------------------- Portfolio Summary Box -------------------- // This subsection creates the summary information for each portfolio.
            const summary = data.summary || {}; // This safely stores the summary data, or uses an empty object if no summary is available.
            const summaryBox = document.createElement("div"); // This creates a new div to hold the summary information.
            summaryBox.className = "portfolio-summary"; // This applies the portfolio summary CSS class for styling.
            summaryBox.innerHTML = ` 
                <p><strong>Positions:</strong> ${summary.position_count ?? 0}</p>
                <p><strong>Total Allocated:</strong> ${summary.total_allocated_percent ?? 0}%</p>
                <p><strong>Remaining Cash:</strong> ${summary.remaining_cash_percent ?? 100}%</p>
                <p><strong>Average Score:</strong> ${summary.average_score ?? "N/A"}</p>
                <p><strong>Average Beta:</strong> ${summary.average_beta ?? "N/A"}</p>
                <p><strong>Status:</strong> ${summary.status ?? "N/A"}</p>
            `; 
            panel.appendChild(summaryBox); // This adds the summary box inside the accordion panel.

            // -------------------- Empty Portfolio Message -------------------- // This subsection shows a message when no holdings have been saved yet.
            if (!data.stocks || data.stocks.length === 0) { // This checks whether the portfolio has no stock holdings.
                const empty = document.createElement("p"); // This creates a paragraph element for the empty message.
                empty.className = "muted"; // This applies a muted style so the message looks secondary and not too strong.
                empty.textContent = "No holdings saved yet."; // This tells the user that the portfolio currently has no saved holdings.
                panel.appendChild(empty); // This adds the empty message into the portfolio panel.
            } else { // This runs when the portfolio does have saved stocks.
                const table = document.createElement("table"); // This creates a table element to display the saved holdings.
                table.className = "table"; // This applies the standard table CSS class.
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
                `; // This ends the holdings table and creates one row for every saved stock.
                panel.appendChild(table); // This adds the completed holdings table into the accordion panel.
            } // This ends the condition for showing either an empty message or a holdings table.

            container.appendChild(button); // This adds the portfolio accordion button to the page.
            container.appendChild(panel); // This adds the portfolio panel directly after the button.
            attachAccordion(button); // This activates the accordion behaviour for the newly created button.
        }); // This ends the loop through the grouped portfolio data.

        // -------------------- Delete Saved Holding -------------------- // This subsection lets the user delete a holding from a saved portfolio.
        document.querySelectorAll(".delete-holding-btn").forEach(button => { // This finds all delete buttons that were created inside the portfolio tables.
            button.addEventListener("click", async function () { // This adds a click event to each delete button and uses async because it calls the backend.
                const holdingId = this.dataset.holdingId; // This reads the saved holding ID from the button data attribute.

                try { // This starts the error handling block for the delete request.
                    const response = await fetch(`/delete-holding/${holdingId}`, { // This sends a request to the Flask route that deletes the selected holding.
                        method: "DELETE" // This tells the backend that the request is a delete operation.
                    }); // This ends the fetch request configuration.

                    const data = await response.json(); // This converts the backend response into JavaScript data.

                    if (!response.ok || data.error) { // This checks whether the backend returned an error or unsuccessful response.
                        alert(data.error || "Could not delete holding."); // This shows an error message to the user if the delete action failed.
                        return; // This stops the function so the page is not updated with bad data.
                    } // This ends the delete error check.

                    renderPortfolioGroups(data.portfolio); // This refreshes the portfolio display using the updated portfolio data returned by the backend.
                } catch (error) { // This catches unexpected errors, such as network problems or server issues.
                    console.error(error); // This logs the error in the browser console to help with debugging.
                    alert("Could not delete holding."); // This gives the user a simple message if the delete request could not be completed.
                } // This ends the try and catch block.
            }); // This ends the delete button click event listener.
        }); // This ends the loop through the delete holding buttons.
    } // This ends the renderPortfolioGroups function.

    // ==================== LOAD SAVED PORTFOLIO DATA ==================== // This section retrieves saved portfolio data from the Flask backend when the page opens.

    // -------------------- Fetch Portfolio Groups From Backend -------------------- // This function loads all saved portfolio holdings.
    async function loadPortfolioGroups() { // This async function fetches portfolio data from the backend.
        const container = document.getElementById("portfolio-groups"); // This checks whether the portfolio groups area exists on the page.
        if (!container) return; // This stops the function if the user is on a page that does not use portfolio groups.

        try { // This starts the safe request block for loading portfolio data.
            const response = await fetch("/portfolio-stocks"); // This calls the Flask route that returns the saved portfolio stocks as JSON.
            const data = await response.json(); // This converts the JSON response into JavaScript data.
            renderPortfolioGroups(data); // This sends the data to the rendering function so it can be displayed on the page.
        } catch (error) { // This catches any error that happens while loading the portfolio data.
            console.error("Could not load portfolio groups:", error); // This logs a clear debugging message in the browser console.
        } // This ends the try and catch block.
    } // This ends the loadPortfolioGroups function.

    // -------------------- Initial Portfolio Load -------------------- // This starts the portfolio loading process automatically.
    loadPortfolioGroups(); // This loads the saved portfolio groups as soon as the page has finished loading.

    // ==================== QUICK ADD PORTFOLIO FORM ==================== // This section controls the form used to quickly add a selected stock to a portfolio.

    // -------------------- Get Quick Add Form Elements -------------------- // This subsection selects the quick add form and message area from the page.
    const quickAddForm = document.getElementById("quick-add-form"); // This finds the quick add form used for saving a stock into a portfolio.
    const quickAddMessage = document.getElementById("quick-add-message"); // This finds the area where success or error messages will be displayed.

    // -------------------- Submit Quick Add Form -------------------- // This subsection handles the form submission for adding a holding.
    if (quickAddForm) { // This checks that the quick add form exists before adding the submit event.
        quickAddForm.addEventListener("submit", async function (event) { // This listens for the form submission and uses async because it sends data to the backend.
            event.preventDefault(); // This stops the browser from refreshing the page when the form is submitted.

            const ticker = document.getElementById("quick_ticker").value; // This gets the selected ticker value from the form input.
            const portfolioKey = document.getElementById("quick_portfolio_key").value; // This gets the selected portfolio key from the form input.

            if (!ticker || !portfolioKey) { // This checks whether the user forgot to select a stock or a portfolio.
                setMessage(quickAddMessage, "Please select both a stock and a portfolio.", "error"); // This shows a friendly validation error to the user.
                return; // This stops the form from being submitted because required information is missing.
            } // This ends the validation check.

            setMessage(quickAddMessage, "Analysing stock and saving holding...", "info"); // This shows the user that the system is processing the selected stock.

            try { // This starts the safe request block for saving the holding.
                const response = await fetch("/add-to-portfolio", { // This sends the selected stock and portfolio to the Flask backend.
                    method: "POST", // This uses POST because new data is being submitted to the server.
                    headers: {"Content-Type": "application/json"}, // This tells the backend that the request body is in JSON format.
                    body: JSON.stringify({ // This converts the JavaScript object into JSON so Flask can read it.
                        ticker: ticker, // This sends the selected stock ticker to the backend.
                        portfolio_key: portfolioKey // This sends the selected portfolio key to the backend.
                    }) // This ends the JSON object that is being sent to Flask.
                }); // This ends the fetch request for adding the holding.

                const data = await response.json(); // This converts the backend response into JavaScript data.

                if (!response.ok || data.error) { // This checks whether the save request failed or returned validation errors.
                    const errors = Array.isArray(data.error) ? data.error : [data.error || "Save failed."]; // This makes sure errors are stored as an array so they can be displayed neatly.
                    const warnings = Array.isArray(data.warnings) ? data.warnings : []; // This stores any warning messages from the backend, or an empty list if none exist.
                    setMessage(quickAddMessage, [...errors, ...warnings], "error"); // This displays both errors and warnings in the message area.
                    return; // This stops the function because the holding was not saved successfully.
                } // This ends the backend error check.

                const messages = [data.message || "Holding saved."]; // This prepares the success message to show after the holding is saved.
                if (Array.isArray(data.warnings) && data.warnings.length > 0) { // This checks whether the backend also returned warning messages.
                    messages.push(...data.warnings); // This adds the warnings after the success message so the user still sees important notes.
                } // This ends the warning check.

                setMessage(quickAddMessage, messages, "success"); // This displays the success message and any warnings to the user.
            } catch (error) { // This catches unexpected errors during the save request.
                console.error(error); // This logs the error in the console for debugging.
                setMessage(quickAddMessage, "Could not save holding.", "error"); // This shows a simple error message if the holding could not be saved.
            } // This ends the try and catch block for the quick add form.
        }); // This ends the quick add form submit event listener.
    } // This ends the quick add form check.

    // ==================== MARKET DASHBOARD TABLE SETUP ==================== // This section controls filtering, presets, sorting, and dashboard summary updates.

    // -------------------- Get Market Table Element -------------------- // This subsection selects the main dashboard table.
    const marketTable = document.getElementById("market-table"); // This finds the market dashboard table if it exists on the current page.

    // -------------------- Prepare Dashboard Controls -------------------- // This subsection prepares table rows, headers, filters, and summary text.
    if (marketTable) { // This checks whether the dashboard table exists before running dashboard-specific code.
        const tbody = marketTable.querySelector("tbody"); // This selects the table body where all stock rows are stored.
        const headers = marketTable.querySelectorAll("th[data-sort]"); // This selects table headers that are allowed to be clicked for sorting.

        const tickerFilter = document.getElementById("ticker-filter"); // This finds the ticker filter input or dropdown.
        const decisionFilter = document.getElementById("decision-filter"); // This finds the decision filter used to filter by recommendation or decision type.
        const scoreFilter = document.getElementById("score-filter"); // This finds the score filter used to show stocks above a minimum score.
        const volatilityFilter = document.getElementById("volatility-filter"); // This finds the volatility filter used to limit stocks by risk level.
        const sharpeFilter = document.getElementById("sharpe-filter"); // This finds the Sharpe ratio filter used to show stronger risk-adjusted returns.
        const summary = document.getElementById("dashboard-summary"); // This finds the summary text that tells the user how many securities are visible.

        let activePreset = ""; // This stores the currently selected preset filter, such as low-risk or high-conviction.

        // -------------------- Number Parsing Helper -------------------- // This helper safely converts text values into numbers for filtering.
        function parseNumber(value) { // This function receives a value from the table or filter input.
            const num = parseFloat(value); // This tries to convert the value into a decimal number.
            return isNaN(num) ? null : num; // This returns null if the value is not a valid number, which avoids broken comparisons.
        } // This ends the parseNumber helper function.

        // ==================== DASHBOARD FILTERING ==================== // This section applies manual filters and preset filters to the market dashboard.

        // -------------------- Apply Dashboard Filters -------------------- // This function decides which table rows should be visible.
        function applyDashboardFilters() { // This function reads all filters and updates the visible rows in the dashboard table.
            const rows = tbody.querySelectorAll("tr"); // This selects every row in the market table body.

            const tickerValue = tickerFilter ? tickerFilter.value.toUpperCase() : ""; // This gets the selected ticker filter and converts it to uppercase for consistent matching.
            const decisionValue = decisionFilter ? decisionFilter.value : ""; // This gets the selected decision filter value.
            const scoreValue = scoreFilter ? parseNumber(scoreFilter.value) : null; // This converts the score filter into a number if one was entered.
            const volatilityValue = volatilityFilter ? parseNumber(volatilityFilter.value) : null; // This converts the volatility filter into a number if one was entered.
            const sharpeValue = sharpeFilter ? parseNumber(sharpeFilter.value) : null; // This converts the Sharpe ratio filter into a number if one was entered.

            let visibleCount = 0; // This counts how many securities remain visible after all filters are applied.

            rows.forEach(row => { // This loops through each stock row in the dashboard.
                const rowTicker = (row.dataset.ticker || "").toUpperCase(); // This reads the ticker stored in the row data attribute.
                const rowDecision = row.dataset.decision || ""; // This reads the decision stored in the row data attribute.
                const rowScore = parseNumber(row.dataset.score); // This reads and converts the stock score from the row data attribute.
                const rowVolatility = parseNumber(row.dataset.volatility); // This reads and converts the stock volatility from the row data attribute.
                const rowSharpe = parseNumber(row.dataset.sharpe); // This reads and converts the stock Sharpe ratio from the row data attribute.

                let visible = true; // This assumes the row should be visible unless one of the filters excludes it.

                if (tickerValue && rowTicker !== tickerValue) visible = false; // This hides the row if it does not match the selected ticker.
                if (decisionValue && rowDecision !== decisionValue) visible = false; // This hides the row if it does not match the selected investment decision.
                if (scoreValue !== null && (rowScore === null || rowScore < scoreValue)) visible = false; // This hides the row if its score is missing or below the selected minimum score.
                if (volatilityValue !== null && (rowVolatility === null || rowVolatility > volatilityValue)) visible = false; // This hides the row if its volatility is missing or above the selected maximum volatility.
                if (sharpeValue !== null && (rowSharpe === null || rowSharpe < sharpeValue)) visible = false; // This hides the row if its Sharpe ratio is missing or below the selected minimum Sharpe ratio.

                if (activePreset === "low-risk" && row.dataset.lowRisk !== "true") visible = false; // This applies the low-risk preset by only showing rows marked as low risk.
                if (activePreset === "high-conviction" && row.dataset.highConviction !== "true") visible = false; // This applies the high-conviction preset by only showing strong investment candidates.
                if (activePreset === "core" && row.dataset.coreHolding !== "true") visible = false; // This applies the core holding preset by only showing stocks marked as suitable for the main portfolio.
                if (activePreset === "satellite" && row.dataset.satellite !== "true") visible = false; // This applies the satellite preset by only showing stocks marked as smaller supporting holdings.
                if (activePreset === "exploratory" && row.dataset.exploratory !== "true") visible = false; // This applies the exploratory preset by only showing stocks marked for further investigation.
                if (activePreset === "income" && row.dataset.incomeCandidate !== "true") visible = false; // This applies the income preset by only showing stocks marked as possible income candidates.
                if (activePreset === "best-ranked" && row.dataset.bestRanked !== "true") visible = false; // This applies the best-ranked preset by only showing securities marked as top-ranked.
                if (activePreset === "cash" && row.dataset.cashCandidate !== "true") visible = false; // This applies the cash candidate preset by only showing securities marked as cash-related or defensive choices.

                row.style.display = visible ? "" : "none"; // This shows or hides the row depending on whether it passed all filters.
                if (visible) visibleCount += 1; // This increases the visible count when a row remains visible.
            }); // This ends the loop through all table rows.

            if (summary) { // This checks whether the dashboard summary element exists.
                summary.textContent = `Showing ${visibleCount} securities after applying filters.`; // This updates the summary so the user knows how many securities are currently displayed.
            } // This ends the summary update.
        } // This ends the applyDashboardFilters function.

        // -------------------- Clear Dashboard Filters -------------------- // This function resets all manual and preset filters.
        function clearDashboardFilters() { // This function clears the dashboard so all securities can be shown again.
            if (tickerFilter) tickerFilter.value = ""; // This clears the ticker filter if it exists.
            if (decisionFilter) decisionFilter.value = ""; // This clears the decision filter if it exists.
            if (scoreFilter) scoreFilter.value = ""; // This clears the score filter if it exists.
            if (volatilityFilter) volatilityFilter.value = ""; // This clears the volatility filter if it exists.
            if (sharpeFilter) sharpeFilter.value = ""; // This clears the Sharpe ratio filter if it exists.
            activePreset = ""; // This removes any active preset filter.
            applyDashboardFilters(); // This reapplies the dashboard filters so the table updates immediately.
        } // This ends the clearDashboardFilters function.

        // ==================== DASHBOARD PRESET FILTERS ==================== // This section connects preset buttons to preset filter names.

        // -------------------- Preset Button Map -------------------- // This object links HTML button IDs to internal preset names.
        const presetMap = { // This object stores each preset button ID and the matching preset value used in the filtering logic.
            "preset-low-risk": "low-risk", // This connects the low-risk button to the low-risk preset.
            "preset-high-conviction": "high-conviction", // This connects the high-conviction button to the high-conviction preset.
            "preset-core": "core", // This connects the core button to the core holding preset.
            "preset-satellite": "satellite", // This connects the satellite button to the satellite preset.
            "preset-exploratory": "exploratory", // This connects the exploratory button to the exploratory preset.
            "preset-income": "income", // This connects the income button to the income candidate preset.
            "preset-best-ranked": "best-ranked", // This connects the best-ranked button to the best-ranked preset.
            "preset-cash": "cash" // This connects the cash button to the cash candidate preset.
        }; // This ends the preset map object.

        // -------------------- Activate Preset Buttons -------------------- // This subsection adds click events to each preset button.
        Object.entries(presetMap).forEach(([buttonId, presetName]) => { // This loops through each preset button ID and its matching preset name.
            const button = document.getElementById(buttonId); // This finds the preset button on the page.
            if (button) { // This checks that the button exists before adding the click event.
                button.addEventListener("click", function () { // This listens for the user clicking the preset button.
                    clearDashboardFilters(); // This clears any manual filters first so the preset works cleanly.
                    activePreset = presetName; // This stores the selected preset as the active preset.
                    applyDashboardFilters(); // This applies the selected preset to update the table rows.
                }); // This ends the preset button click event.
            } // This ends the button existence check.
        }); // This ends the loop through the preset map.

        // -------------------- Clear Filter Button -------------------- // This subsection connects the clear filters button.
        const clearButton = document.getElementById("clear-filters"); // This finds the button used to reset all dashboard filters.
        if (clearButton) clearButton.addEventListener("click", clearDashboardFilters); // This clears all filters when the user clicks the clear filters button.

        // -------------------- Manual Filter Inputs -------------------- // This subsection updates the dashboard when the user changes filter values.
        [tickerFilter, decisionFilter, scoreFilter, volatilityFilter, sharpeFilter].forEach(control => { // This loops through all manual filter controls.
            if (control) { // This checks that the filter control exists before adding events.
                control.addEventListener("input", function () { // This updates the dashboard while the user types or changes a value.
                    activePreset = ""; // This removes the preset because the user is now applying manual filters.
                    applyDashboardFilters(); // This applies the new manual filter values to the table.
                }); // This ends the input event listener.
                control.addEventListener("change", function () { // This updates the dashboard when a dropdown or input value is changed.
                    activePreset = ""; // This clears the active preset because manual filtering should take priority.
                    applyDashboardFilters(); // This applies the updated filters to the dashboard.
                }); // This ends the change event listener.
            } // This ends the filter control existence check.
        }); // This ends the loop through the manual filter controls.

        // ==================== DASHBOARD TABLE SORTING ==================== // This section allows the user to sort the market table by clicking table headers.

        // -------------------- Sort Table Columns -------------------- // This subsection adds sorting behaviour to each sortable table header.
        headers.forEach((header, index) => { // This loops through every table header that has a data-sort attribute.
            header.style.cursor = "pointer"; // This changes the cursor so the user can see the header is clickable.
            header.dataset.direction = "desc"; // This sets the default sorting direction for each header.

            header.addEventListener("click", function () { // This listens for clicks on a sortable table header.
                const rows = Array.from(tbody.querySelectorAll("tr")); // This converts all table rows into an array so they can be sorted.
                const direction = this.dataset.direction === "asc" ? "desc" : "asc"; // This switches the sorting direction between ascending and descending.
                this.dataset.direction = direction; // This saves the new sorting direction on the clicked header.

                rows.sort((a, b) => { // This sorts the table rows by comparing the values in the clicked column.
                    const aText = a.children[index].textContent.trim(); // This gets the text from the selected column in the first row.
                    const bText = b.children[index].textContent.trim(); // This gets the text from the selected column in the second row.

                    const aNum = parseFloat(aText.replace(/[^\d.-]/g, "")); // This tries to extract a number from the first value, even if it contains symbols like percent signs.
                    const bNum = parseFloat(bText.replace(/[^\d.-]/g, "")); // This tries to extract a number from the second value, even if it contains symbols like percent signs.

                    let comparison; // This variable stores the result of comparing the two row values.
                    if (!isNaN(aNum) && !isNaN(bNum)) comparison = aNum - bNum; // This compares the rows numerically if both values are valid numbers.
                    else comparison = aText.localeCompare(bText); // This compares the rows alphabetically if the values are text.

                    return direction === "asc" ? comparison : -comparison; // This returns the comparison in ascending or descending order depending on the selected direction.
                }); // This ends the row sorting logic.

                rows.forEach(row => tbody.appendChild(row)); // This re-adds the sorted rows back into the table body in the new order.
                applyDashboardFilters(); // This reapplies filters after sorting so hidden rows stay hidden.
            }); // This ends the table header click event.
        }); // This ends the loop through sortable headers.

        // -------------------- Initial Dashboard Filter Application -------------------- // This applies the dashboard filters once when the page first loads.
        applyDashboardFilters(); // This makes sure the dashboard summary and visible rows are correct when the page opens.
    } // This ends the market table section.
}); // This ends the DOMContentLoaded event and the full JavaScript script.