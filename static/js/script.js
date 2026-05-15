document.addEventListener("DOMContentLoaded", function () { // waits until the full page is ready before any JavaScript tries to use the HTML elements

// =========================================================
// SHARED SECTION → PAGE CHECK + COMMON ELEMENTS
// I am storing the main page elements here once so I can
// reuse them later instead of querying the DOM repeatedly.
// =========================================================

const body = document.body; // keeps a reference to the full page in case I need page-level checks later
const form = document.getElementById("analyze-form"); // this is the form on criteria.html used to analyse a selected ticker
const addButton = document.getElementById("add-to-portfolio-btn"); // button used after analysis to add or update the stock in a portfolio
const portfolioSelect = document.getElementById("portfolio_key"); // dropdown where the user chooses which portfolio they are working with
const tradeMessage = document.getElementById("trade-message"); // message area for info, success, or error feedback to the user
const marketTable = document.getElementById("market-table"); // main table used on the market dashboard page
const tickerSelect = document.getElementById("ticker"); // ticker dropdown shown on the criteria page
const portfolioGroupsContainer = document.getElementById("portfolio-groups"); // container where grouped holdings are displayed on the page

let latestAnalysis = null; // stores the most recent successful analysis so it can be reused for the add/update step later

// =========================================================
// SHARED SECTION → TICKER UNIVERSE
// This is the grouped ticker list used to rebuild the
// dropdown dynamically instead of relying on only a few
// hardcoded options in the HTML.
// =========================================================

const tickerUniverse = { // object holding the full ticker universe grouped by investment type
    fixed_income: [ // bond and bond-like instruments that are usually lower risk than equities
        "SHY", "IEF", "TLT", "BND", "AGG", "TIP", "LQD", "HYG", "VGIT", "VCIT",
        "MINT", "BIL", "JPST", "SCHR", "SCHZ", "IGIB", "SPTI", "GOVT", "BSV", "VGSH"
    ],
    defensive_equities: [ // more defensive shares and sector ETFs that may be used in lower-risk allocations
        "XLP", "XLV", "XLU", "PG", "KO", "PEP", "JNJ", "MRK", "PFE",
        "WMT", "MCD", "CL", "KMB", "DUK", "SO", "NEE", "GIS", "MDT", "HSY", "EL"
    ],
    core_equities: [ // larger mainstream holdings that would often sit in the core part of a portfolio
        "AAPL", "MSFT", "AMZN", "GOOGL", "META", "JPM", "V", "MA", "UNH",
        "HD", "ADBE", "CRM", "ORCL", "CSCO", "INTU", "AVGO", "NFLX",
        "QCOM", "LIN", "TXN", "HON", "CAT", "IBM", "AMGN", "NOW", "BKNG",
        "AXP", "GS", "BLK", "SPGI"
    ],
    growth_equities: [ // higher-growth names which usually come with more volatility and more upside/downside
        "TSLA", "NVDA", "AMD", "SHOP", "SQ", "UBER", "PANW", "CRWD", "SNOW", "PLTR",
        "MDB", "DDOG", "NET", "ZS", "TEAM", "ABNB", "MELI", "SE", "TTD", "ROKU",
        "ARKK", "QQQ", "SMH", "SOXX", "IWF", "VUG", "XLK", "FTEC", "SCHG", "MGK"
    ],
    international_equities: [ // regional and international exposure for diversification outside one home market
        "VEA", "IEFA", "EWG", "EWQ", "EWI", "EWJ", "EWS", "EWA", "EWU", "EWP",
        "VGK", "EZU", "FEZ", "AAXJ", "VWO", "EEM", "INDA", "EWY", "MCHI", "FXI",
        "EWZ", "EWT", "EIDO", "EPHE", "EZA", "ERUS", "EWC", "EWL", "EWD", "EWN"
    ],
    alternatives: [ // non-traditional assets like commodities, real assets, FX-linked, thematic, or crypto-linked products
        "GLD", "SLV", "VNQ", "REET", "SCHH", "REM", "DBC", "PDBC", "USO", "IAU",
        "VNQI", "RWO", "FTGC", "COMT", "GSG", "DBA", "UUP", "FXE", "FXF", "FXY",
        "BITO", "ETHE", "PALL", "PLTM", "URA", "COPX", "WOOD", "HACK", "CIBR", "KWEB"
    ]
}; // closes the grouped ticker universe object

// =========================================================
// SHARED SECTION → SMALL HELPER FUNCTIONS
// These functions are reused in many places so the main
// logic stays shorter and easier to follow.
// =========================================================

function setText(id, value) { // small helper that updates text in one element by using its id
    const el = document.getElementById(id); // looks up the element first before trying to change it
    if (el) { // only runs the update if the element actually exists on that page
        el.textContent = value; // replaces the visible text content inside that element
    }
}

function fmtPercent(value) { // formats decimal values like 0.12 into a cleaner percentage for display
    return value === null || value === undefined || isNaN(value) // checks for missing or invalid values before formatting
        ? "N/A" // fallback shown when the value is not usable
        : `${(value * 100).toFixed(2)}%`; // converts decimal to percent and keeps two decimal places for consistency
}

function fmtNumber(value) { // formats regular numeric values such as beta, Sharpe-like ratio, or price
    return value === null || value === undefined || isNaN(value) // checks whether the input is missing or not a valid number
        ? "N/A" // fallback text when no real number is available
        : Number(value).toFixed(2); // forces a standard two-decimal display so values look neat on screen
}

function parseNumber(value) { // safely converts text input into a number that can be used in comparisons
    const num = parseFloat(value); // parseFloat is useful because many values arrive as strings from inputs or data attributes
    return isNaN(num) ? null : num; // returns null instead of NaN because null is easier to test later in the logic
}

function getSelectedPortfolioName() { // gets the visible label from the portfolio dropdown rather than just the hidden value
    if (!portfolioSelect) return "Unknown Portfolio"; // safe fallback in case the dropdown is not on the current page
    return portfolioSelect.options[portfolioSelect.selectedIndex].text; // returns the text the user actually sees in the dropdown
}

// =========================================================
// SHARED SECTION → MESSAGE BOX HELPERS
// These helpers are mostly used on the Criteria page so
// feedback messages are handled in one place.
// =========================================================

function showTradeMessage(message, type = "info") { // shows a message box with styling such as info, success, or error
    if (!tradeMessage) return; // stops quietly if the message box does not exist on the current page
    tradeMessage.className = `trade-message ${type}`; // swaps the CSS class so the message gets the right colour/style
    tradeMessage.innerHTML = Array.isArray(message) ? message.join("<br>") : message; // supports both one message and a list of messages
}

function clearTradeMessage() { // resets the message box back to a blank neutral state
    if (!tradeMessage) return; // stops safely if there is no message box on the page
    tradeMessage.className = "trade-message"; // removes any old info, success, or error styling
    tradeMessage.textContent = ""; // clears the visible text so old messages do not remain on screen
}

// =========================================================
// SHARED SECTION → ACCORDION / COLLAPSIBLE LOGIC
// This section is reused wherever content needs to open
// and close, like accordions or checklist panels.
// =========================================================

function attachAccordion(button) { // gives one accordion button its open/close behaviour
    if (!button || button.dataset.bound === "true") { // prevents errors and stops duplicate event listeners being attached
        return; // exits early if button is missing or already initialised
    }

    button.dataset.bound = "true"; // marks the button so I know its click event has already been attached once

    button.addEventListener("click", function () { // runs when that accordion button is clicked
        this.classList.toggle("active"); // toggles the active class so the open state can also be styled in CSS

        const panel = this.nextElementSibling; // assumes the matching panel sits directly after the button in the HTML
        if (!panel) return; // safety check in case the expected panel is missing

        panel.style.display = panel.style.display === "block" ? "none" : "block"; // simple show/hide toggle for the accordion content
    });
}

function initialiseStaticAccordions() { // activates all accordion buttons already written into the HTML
    document.querySelectorAll(".accordion").forEach(attachAccordion); // finds every accordion button and attaches the shared behaviour
}

function initialiseChecklistCollapsible() { // activates the collapsible checklist style buttons
    const buttons = document.querySelectorAll(".collapsible-btn"); // selects all buttons that should control collapsible checklist content

    buttons.forEach(button => { // loops through every matching checklist button
        if (button.dataset.bound === "true") return; // avoids attaching duplicate click handlers if the function runs again
        button.dataset.bound = "true"; // marks the button as already initialised

        button.addEventListener("click", function () { // runs when the checklist button is clicked
            const content = this.nextElementSibling; // assumes the collapsible content comes immediately after the button
            if (!content) return; // safety check if the expected content block is missing

            content.style.display = content.style.display === "block" ? "none" : "block"; // toggles the checklist content open and closed
        });
    });
}

// =========================================================
// INDEX.HTML LOGIC
// Placeholder section for any future homepage behaviour.
// =========================================================

function initialiseIndexPage() { // dedicated starter function for the homepage so page-specific logic stays grouped
    const isIndexPage = window.location.pathname === "/" || window.location.pathname.endsWith("index.html"); // checks whether the current page is the homepage
    if (!isIndexPage) return; // stops straight away if the user is not on the homepage
}

// =========================================================
// PORTFOLIO_PROFILES.HTML LOGIC
// This function exists because it is called at the bottom.
// =========================================================

function initialisePortfolioProfilesPage() { // keeps a dedicated place for portfolio_profiles page logic
    const isPortfolioProfilesPage = window.location.pathname.includes("portfolio_profiles"); // checks whether the current URL belongs to the portfolio profiles page
    if (!isPortfolioProfilesPage) return; // exits if the current page is not portfolio_profiles.html
}

// =========================================================
// CONTACT.HTML LOGIC
// Dedicated section for future contact page behaviour.
// =========================================================

function initialiseContactPage() { // keeps contact page logic separate from the rest of the file
    const isContactPage = window.location.pathname.includes("contact"); // checks if the current page is the contact page
    if (!isContactPage) return; // stops if the script is running on a different page
}

// =========================================================
// CRITERIA.HTML → TICKER DROPDOWN
// Rebuilds the ticker dropdown from the full universe.
// =========================================================

function populateTickerDropdown() { // builds the ticker dropdown dynamically instead of relying only on hardcoded HTML options
    if (!tickerSelect) return; // stops if the ticker dropdown does not exist on the current page

    tickerSelect.innerHTML = ""; // clears out any old options first so the dropdown does not duplicate entries

    const placeholder = document.createElement("option"); // creates the first placeholder option shown before a real ticker is selected
    placeholder.value = ""; // empty value makes it easy to validate when the user has not chosen a ticker yet
    placeholder.textContent = "-- Choose a ticker --"; // text shown to the user as the starting placeholder
    placeholder.selected = true; // makes the placeholder the default visible option
    placeholder.disabled = false; // keeps it selectable/visible at the top of the dropdown
    tickerSelect.appendChild(placeholder); // inserts the placeholder into the select element first

    Object.entries(tickerUniverse).forEach(([category, tickers]) => { // loops through each category and its ticker list inside the grouped universe
        const optgroup = document.createElement("optgroup"); // creates an optgroup so tickers appear grouped by category in the dropdown
        optgroup.label = category.replace(/_/g, " ").replace(/\b\w/g, char => char.toUpperCase()); // turns names like fixed_income into Fixed Income for cleaner display

        tickers.forEach(ticker => { // loops through each ticker inside the current category
            const option = document.createElement("option"); // creates one option element for one ticker
            option.value = ticker; // this is the value that gets submitted when the form is sent
            option.textContent = ticker; // this is the text the user sees in the dropdown
            optgroup.appendChild(option); // adds the ticker option into the current category group
        });

        tickerSelect.appendChild(optgroup); // after building one whole category group, adds it into the dropdown
    });
}

// =========================================================
// CRITERIA.HTML → RESETTING THE ANALYSIS AREA
// Clears old analysis so stale values do not remain.
// =========================================================

function clearAnalysisFields() { // resets all criteria result fields back to a neutral empty state
    [ // array of all result element ids that should be cleared when analysis is reset
        "beta-value",
        "score-value",
        "decision-value",
        "weight-value",
        "sector-value",
        "industry-value",
        "tag-value",
        "1y-er-value",
        "1y-vol-value",
        "1y-sharpe-value",
        "1y-latest-price-value",
        "1y-price-start-value",
        "1y-price-end-value",
        "1y-price-obs-value",
        "1y-return-start-value",
        "1y-return-end-value",
        "1y-return-obs-value",
        "1y-quarterly-return-value",
        "1y-q1-price-value",
        "1y-q2-price-value",
        "1y-q3-price-value",
        "1y-q4-price-value",
        "3m-er-value",
        "3m-vol-value",
        "3m-sharpe-value",
        "3m-latest-price-value",
        "3m-price-start-value",
        "3m-price-end-value",
        "3m-price-obs-value",
        "3m-return-start-value",
        "3m-return-end-value",
        "3m-return-obs-value",
        "3m-quarterly-return-value",
        "3m-q1-price-value",
        "3m-q2-price-value",
        "3m-q3-price-value",
        "3m-q4-price-value",
        "benchmark-ticker-value",
        "benchmark-start-value",
        "benchmark-end-value",
        "beta-obs-value"
    ].forEach(id => setText(id, "N/A")); // loops through all result fields and resets each one to N/A

    setText("result-ticker", "Select a stock to analyze"); // puts the main result heading back to the default message
    setText("portfolio-name", getSelectedPortfolioName()); // refreshes the displayed portfolio name based on the current dropdown selection

    if (addButton) { // only runs if the add/update button exists on this page
        addButton.disabled = true; // disables the button until a fresh valid analysis is completed
    }

    latestAnalysis = null; // clears the stored latest analysis so old data cannot be added by mistake
    clearTradeMessage(); // removes any old success/error/info message still showing
}

// =========================================================
// CRITERIA.HTML → CURRENT PORTFOLIO HOLDINGS DISPLAY
// Builds the grouped holdings section from Flask data.
// =========================================================

function renderPortfolioGroups(grouped) { // takes the grouped portfolio payload from Flask and turns it into visible HTML
    const container = document.getElementById("portfolio-groups"); // finds the holdings container where the grouped content should be inserted
    if (!container) return; // stops if that container does not exist on the current page

    container.innerHTML = ""; // clears previous content first so the screen does not duplicate holdings sections

    Object.entries(grouped).forEach(([, data]) => { // loops through each grouped portfolio entry returned by the backend
        const button = document.createElement("button"); // creates an accordion button for one portfolio group
        button.className = "accordion portfolio-group-button"; // gives the button the same styling/behaviour class as other accordions
        button.type = "button"; // keeps it as a normal button and stops it acting like a form submit button
        button.textContent = data.portfolio_name; // uses the portfolio name as the visible accordion label

        const panel = document.createElement("div"); // creates the hidden panel that will open under the button
        panel.className = "panel"; // applies the shared panel styling

        const summary = data.summary || {}; // safely reads the summary object or falls back to an empty object if missing

        const summaryBox = document.createElement("div"); // creates a small summary box for top-level portfolio stats
        summaryBox.className = "portfolio-summary"; // applies the summary grid styling
        summaryBox.innerHTML = ` 
            <p><strong>Positions:</strong> ${summary.position_count ?? 0}</p>
            <p><strong>Total Allocated:</strong> ${summary.total_allocated_percent ?? 0}%</p>
            <p><strong>Remaining Cash:</strong> ${summary.remaining_cash_percent ?? 100}%</p>
            <p><strong>Average Beta:</strong> ${summary.average_beta ?? "N/A"}</p>
        `;
        panel.appendChild(summaryBox); // inserts the summary box into the panel before the detailed stock list

        if (!data.stocks || data.stocks.length === 0) { // checks whether this portfolio currently has no saved holdings
            const empty = document.createElement("p"); // creates a simple paragraph for the empty state message
            empty.textContent = "No stocks added yet."; // message shown when the portfolio has no positions
            panel.appendChild(empty); // adds the empty state message into the panel
        } else { // if holdings exist, build the table instead of the empty message
            const table = document.createElement("table"); // creates a table element for the portfolio holdings
            table.className = "table"; // applies the site's main table styling

            table.innerHTML = ` 
                    <thead>
                    <tr><th>Ticker</th><th>Recommended Weight</th><th>Decision</th><th>Tag</th><th>Sector</th><th>Industry</th><th>Beta</th><th>Action</th></tr>
                    </thead>
                    <tbody>
                    ${data.stocks.map(stock => ` 
                        <tr><td>${stock.ticker}</td><td>${stock.recommended_weight}</td><td>${stock.decision}</td><td>${stock.tag}</td><td>${stock.sector || "Unknown"}</td><td>${stock.industry || "Unknown"}</td><td>${stock.beta !== null && stock.beta !== undefined ? Number(stock.beta).toFixed(2) : "N/A"}</td><td><button type="button" class="delete-holding-btn" data-holding-id="${stock.id}">Delete</button></td></tr>
                    `).join("")}
                    </tbody>
            `;

            panel.appendChild(table); // places the completed holdings table inside the accordion panel
        }

        container.appendChild(button); // adds the portfolio accordion button into the holdings container
        container.appendChild(panel); // adds the matching panel directly underneath that button
        attachAccordion(button); // attaches open/close behaviour to the new button that was just created
    });
}

// =========================================================
// CRITERIA.HTML → LOAD HOLDINGS FROM FLASK
// Pulls current saved holdings from the backend.
// =========================================================

async function loadPortfolioGroups() { // fetches the grouped portfolio holdings from Flask so they can be shown on screen
    const container = document.getElementById("portfolio-groups"); // finds the holdings container first
    if (!container) return; // stops if the current page does not contain that container

    try { // uses try/catch so a fetch failure does not break the whole page
        const res = await fetch("/portfolio-stocks"); // requests the grouped holdings JSON from the backend route
        const data = await res.json(); // converts the JSON response into a JavaScript object
        renderPortfolioGroups(data); // passes the returned data into the render function so the holdings appear on screen
    } catch (error) { // catches fetch or parsing problems
        console.error("Failed to load portfolio groups:", error); // logs the technical error in the console for debugging
    }
}

// =========================================================
// CRITERIA.HTML → ANALYSE TICKER FORM
// Sends the selected form data to /analyze with fetch.
// =========================================================

function initialiseCriteriaAnalysisForm() { // sets up the analyse form behaviour for the criteria page
    if (!form) return; // stops safely if the analysis form does not exist on the current page

    form.addEventListener("submit", async function (e) { // listens for the form submit and handles it with async logic
        e.preventDefault(); // stops the browser doing a normal page reload submit because fetch is being used instead
        console.log("Form submit handler is running"); // debug line so I can confirm in the browser console that the submit handler really fired
        clearTradeMessage(); // removes any previous message before starting a new analysis request

        const formData = new FormData(form); // collects all form values in a way Flask can read like a normal submitted form

        try { // uses try/catch so request failures do not break the whole UI
            const res = await fetch("/analyze", { // sends the selected ticker and portfolio to the Flask analyze route
                method: "POST", // POST is used because the form data is being sent to the backend
                body: formData, // sends the collected form values in the request body
                headers: { "X-Requested-With": "XMLHttpRequest" } // header often used to indicate this request came from JavaScript asynchronously
            });

            const data = await res.json(); // converts the JSON response from Flask into a JavaScript object

            if (!res.ok || data.error) { // checks for either an HTTP failure or an application-level error returned by Flask
                clearAnalysisFields(); // clears old analysis so the screen does not keep misleading stale data
                setText("result-ticker", "Analysis Error"); // updates the heading so the user can clearly see analysis failed
                setText("decision-value", data.error || "Could not load analysis."); // shows the error inside the result box
                showTradeMessage(data.error || "Could not load analysis.", "error"); // displays a visible error message to the user
                return; // stops here so the success logic below does not run
            }

            latestAnalysis = data; // saves the successful analysis payload so it can be reused by the add/update button

            if (addButton) { // checks that the add button exists before trying to use it
                addButton.disabled = false; // enables the add/update button because there is now a valid analysis to save
            }

            setText("result-ticker", `${data.ticker} — Analysis Summary`); // updates the result heading with the analysed ticker
            setText("portfolio-name", data.portfolio_name || getSelectedPortfolioName()); // shows the portfolio name returned by Flask or falls back to the dropdown label
            setText("beta-value", data.beta === null ? "N/A" : fmtNumber(data.beta)); // shows beta in a consistent number format
            setText("score-value", data.score ?? "N/A"); // displays the analysis score
            setText("decision-value", data.decision || "N/A"); // displays the final decision label
            setText("weight-value", data.recommended_weight || "N/A"); // displays the suggested position size
            setText("sector-value", data.sector || "Unknown"); // shows sector if available or a fallback if missing
            setText("industry-value", data.industry || "Unknown"); // shows industry if available or a fallback if missing
            setText("tag-value", data.tag || "N/A"); // shows the UI tag returned by the decision logic

            if (data.one_year) { // only fills the one-year block if Flask returned that section
                setText("1y-er-value", fmtPercent(data.one_year.annualised_expected_return)); // one-year expected return formatted as a percentage
                setText("1y-vol-value", fmtPercent(data.one_year.annualised_volatility)); // one-year volatility formatted as a percentage
                setText("1y-sharpe-value", fmtNumber(data.one_year.sharpe_like)); // one-year Sharpe-like value formatted as a number
                setText("1y-latest-price-value", fmtNumber(data.one_year.latest_price)); // latest price from the one-year analysis window
                setText("1y-price-start-value", data.one_year.price_start_date || "N/A"); // first date used in the one-year price series
                setText("1y-price-end-value", data.one_year.price_end_date || "N/A"); // last date used in the one-year price series
                setText("1y-price-obs-value", data.one_year.price_observations ?? "N/A"); // number of price observations in the one-year window
                setText("1y-return-start-value", data.one_year.return_start_date || "N/A"); // first date used in the one-year returns series
                setText("1y-return-end-value", data.one_year.return_end_date || "N/A"); // last date used in the one-year returns series
                setText("1y-return-obs-value", data.one_year.return_observations ?? "N/A"); // number of return observations in the one-year window

                if (data.one_year.forecast) { // only fills the forecast fields if the one-year forecast object exists
                    setText("1y-quarterly-return-value", fmtPercent(data.one_year.forecast.quarterly_return)); // implied quarterly return from the one-year forecast
                    setText("1y-q1-price-value", fmtNumber(data.one_year.forecast.q1_expected_price)); // forecasted expected Q1 price
                    setText("1y-q2-price-value", fmtNumber(data.one_year.forecast.q2_expected_price)); // forecasted expected Q2 price
                    setText("1y-q3-price-value", fmtNumber(data.one_year.forecast.q3_expected_price)); // forecasted expected Q3 price
                    setText("1y-q4-price-value", fmtNumber(data.one_year.forecast.q4_expected_price)); // forecasted expected Q4 price
                }
            }

            if (data.three_month) { // only fills the three-month block if Flask returned that section
                setText("3m-er-value", fmtPercent(data.three_month.annualised_expected_return)); // three-month expected return formatted as a percentage
                setText("3m-vol-value", fmtPercent(data.three_month.annualised_volatility)); // three-month volatility formatted as a percentage
                setText("3m-sharpe-value", fmtNumber(data.three_month.sharpe_like)); // three-month Sharpe-like value formatted as a number
                setText("3m-latest-price-value", fmtNumber(data.three_month.latest_price)); // latest price from the shorter analysis window
                setText("3m-price-start-value", data.three_month.price_start_date || "N/A"); // first date used in the three-month price series
                setText("3m-price-end-value", data.three_month.price_end_date || "N/A"); // last date used in the three-month price series
                setText("3m-price-obs-value", data.three_month.price_observations ?? "N/A"); // number of price observations in the three-month window
                setText("3m-return-start-value", data.three_month.return_start_date || "N/A"); // first date used in the three-month returns series
                setText("3m-return-end-value", data.three_month.return_end_date || "N/A"); // last date used in the three-month returns series
                setText("3m-return-obs-value", data.three_month.return_observations ?? "N/A"); // number of return observations in the three-month window

                if (data.three_month.forecast) { // only fills shorter-term forecast values if that forecast object exists
                    setText("3m-quarterly-return-value", fmtPercent(data.three_month.forecast.quarterly_return)); // implied quarterly return from the three-month forecast
                    setText("3m-q1-price-value", fmtNumber(data.three_month.forecast.q1_expected_price)); // forecasted Q1 expected price
                    setText("3m-q2-price-value", fmtNumber(data.three_month.forecast.q2_expected_price)); // forecasted Q2 expected price
                    setText("3m-q3-price-value", fmtNumber(data.three_month.forecast.q3_expected_price)); // forecasted Q3 expected price
                    setText("3m-q4-price-value", fmtNumber(data.three_month.forecast.q4_expected_price)); // forecasted Q4 expected price
                }
            }

            setText("benchmark-ticker-value", data.benchmark_ticker || "N/A"); // shows which benchmark ticker was used for beta calculation
            setText("benchmark-start-value", data.benchmark_start_date || "N/A"); // shows benchmark return series start date
            setText("benchmark-end-value", data.benchmark_end_date || "N/A"); // shows benchmark return series end date
            setText("beta-obs-value", data.beta_observations ?? "N/A"); // shows how many overlapping observations were used for beta

            showTradeMessage("Analysis completed. Review mandate fit before adding to portfolio.", "info"); // final info message shown after successful analysis
        } catch (error) { // catches network failures or unexpected technical issues
            clearAnalysisFields(); // resets the result area so broken requests do not leave stale values on screen
            setText("result-ticker", "Request Failed"); // updates the main heading to make the failure obvious
            setText("decision-value", "Could not load analysis."); // shows a fallback message in the decision field
            showTradeMessage("Could not load analysis.", "error"); // shows a visible error message to the user
            console.error(error); // logs the raw error in the console for debugging
        }
    });
}

// =========================================================
// CRITERIA.HTML → ADD / UPDATE PORTFOLIO
// Saves the analysed ticker into the chosen portfolio.
// =========================================================

function initialiseCriteriaAddToPortfolio() { // sets up the Add / Update Portfolio button behaviour
    if (!addButton) return; // stops if the add button does not exist on the current page

    addButton.addEventListener("click", async function () { // runs when the add/update button is clicked
        if (!latestAnalysis) return; // blocks the action if there is no saved analysis to work with

        const selectedPortfolioKey = portfolioSelect ? portfolioSelect.value : latestAnalysis.portfolio_key; // gets the chosen portfolio key or falls back to the key from the last analysis
        const selectedPortfolioName = getSelectedPortfolioName(); // gets the visible portfolio name from the dropdown

        try { // uses try/catch so save errors do not break the rest of the page
            const res = await fetch("/add-to-portfolio", { // sends the analysis data to the Flask route that validates and stores the holding
                method: "POST", // POST is used because new data is being sent to the backend
                headers: { "Content-Type": "application/json" }, // tells Flask that the request body is JSON
                body: JSON.stringify({ // converts the JavaScript object into JSON for the request body
                    ticker: latestAnalysis.ticker, // analysed ticker symbol
                    portfolio_key: selectedPortfolioKey, // selected portfolio key
                    portfolio_name: selectedPortfolioName, // selected portfolio display name
                    recommended_weight: latestAnalysis.recommended_weight, // suggested portfolio weight from the analysis
                    decision: latestAnalysis.decision, // model decision label
                    tag: latestAnalysis.tag, // short UI tag
                    sector: latestAnalysis.sector, // sector information from the analysis
                    industry: latestAnalysis.industry, // industry information from the analysis
                    beta: latestAnalysis.beta // beta from the analysis
                })
            });

            const data = await res.json(); // reads the backend response as JSON

            if (!res.ok || data.error) { // checks if the backend returned either an HTTP failure or a validation error
                const errors = Array.isArray(data.error) ? data.error : [data.error || "Failed to add stock."]; // normalises error output into an array
                const warnings = Array.isArray(data.warnings) ? data.warnings : []; // normalises warnings into an array too
                showTradeMessage([...errors, ...warnings], "error"); // shows errors and warnings together in the message box
                return; // stops here so success logic does not run after a failed save
            }

            renderPortfolioGroups(data.portfolio); // re-renders the grouped portfolio holdings using the updated backend data

            const messages = [data.message || "Portfolio updated."]; // starts a success message list with the backend success text
            if (Array.isArray(data.warnings) && data.warnings.length > 0) { // checks if the backend returned warnings together with a successful save
                messages.push(...data.warnings); // appends those warnings under the main success message
            }

            showTradeMessage(messages, "success"); // shows the final success message(s) to the user
        } catch (error) { // catches network failures or parsing problems during save
            showTradeMessage("Failed to add to portfolio.", "error"); // shows a simple visible error message
            console.error("Failed to add to portfolio:", error); // logs the technical error in the console for debugging
        }
    });
}

function initialiseCriteriaPage() { // main setup function for everything related to criteria.html
    const isCriteriaPage = window.location.pathname.includes("criteria"); // checks if the current page is the criteria page
    if (!isCriteriaPage) return; // stops if the user is on a different page

    populateTickerDropdown(); // rebuilds the ticker dropdown from the full grouped ticker universe
    initialiseCriteriaAnalysisForm(); // activates the form submission logic for analysis
    initialiseCriteriaAddToPortfolio(); // activates the add/update portfolio button logic
    loadPortfolioGroups(); // loads current saved holdings from Flask into the page

    if (portfolioSelect) { // only attaches this change handler if the portfolio dropdown exists
        portfolioSelect.addEventListener("change", function () { // runs whenever the selected portfolio changes
            clearAnalysisFields(); // clears old analysis because it may not match the newly selected portfolio anymore
            setText("portfolio-name", getSelectedPortfolioName()); // updates the displayed portfolio name immediately
        });
    }
}

// =========================================================
// MARKET_DASHBOARD.HTML → FILTERS, PRESETS, AND SORTING
// Keeps all dashboard screening logic in one section.
// =========================================================

function initialiseMarketDashboard() { // main setup function for the market dashboard page
    if (!marketTable) return; // stops if the market table does not exist on the current page

    const tbody = marketTable.querySelector("tbody"); // table body where all the market rows live
    const headers = marketTable.querySelectorAll("th[data-sort]"); // only selects headers that are meant to be sortable

    const tickerFilter = document.getElementById("ticker-filter"); // dropdown used to filter by specific ticker
    const decisionFilter = document.getElementById("decision-filter"); // dropdown used to filter by decision category
    const scoreFilter = document.getElementById("score-filter"); // dropdown used to set a minimum score threshold
    const volatilityFilter = document.getElementById("volatility-filter"); // numeric filter used to set a maximum volatility
    const sharpeFilter = document.getElementById("sharpe-filter"); // numeric filter used to set a minimum Sharpe-like ratio
    const summary = document.getElementById("dashboard-summary"); // summary text area showing how many securities remain visible

    const presetLowRisk = document.getElementById("preset-low-risk"); // quick filter button for low-risk names
    const presetHighConviction = document.getElementById("preset-high-conviction"); // quick filter button for high-conviction names
    const presetCore = document.getElementById("preset-core"); // quick filter button for core holdings
    const presetSatellite = document.getElementById("preset-satellite"); // quick filter button for satellite/diversifier holdings
    const presetExploratory = document.getElementById("preset-exploratory"); // quick filter button for exploratory/high-risk names
    const presetIncome = document.getElementById("preset-income"); // quick filter button for income/defensive names
    const presetBestRanked = document.getElementById("preset-best-ranked"); // quick filter button for best-ranked names
    const presetCash = document.getElementById("preset-cash"); // quick filter button for cash/risk-control names
    const clearFiltersBtn = document.getElementById("clear-filters"); // button that resets all filters back to blank

    let activePreset = ""; // stores which preset is currently active so filter logic can apply it

    function applyDashboardFilters() { // reads current filter values and shows/hides rows accordingly
        const rows = tbody.querySelectorAll("tr"); // selects all current dashboard rows

        const tickerValue = tickerFilter ? tickerFilter.value.toUpperCase() : ""; // reads the chosen ticker and normalises it to uppercase
        const decisionValue = decisionFilter ? decisionFilter.value : ""; // reads the selected decision filter
        const scoreValue = scoreFilter ? parseNumber(scoreFilter.value) : null; // reads and safely converts the score filter
        const volatilityValue = volatilityFilter ? parseNumber(volatilityFilter.value) : null; // reads and safely converts the volatility filter
        const sharpeValue = sharpeFilter ? parseNumber(sharpeFilter.value) : null; // reads and safely converts the Sharpe filter

        let visibleCount = 0; // counter used to track how many rows stay visible after filtering

        rows.forEach(row => { // checks every row one by one
            const rowTicker = (row.dataset.ticker || "").toUpperCase(); // reads the row ticker from the data attribute
            const rowDecision = row.dataset.decision || ""; // reads the row decision from the data attribute
            const rowScore = parseNumber(row.dataset.score); // reads and parses the row score
            const rowVolatility = parseNumber(row.dataset.volatility); // reads and parses the row volatility
            const rowSharpe = parseNumber(row.dataset.sharpe); // reads and parses the row Sharpe-like ratio

            const rowIsLowRisk = row.dataset.lowRisk === "true"; // converts low-risk flag into a true/false value
            const rowIsHighConviction = row.dataset.highConviction === "true"; // converts high-conviction flag into a true/false value
            const rowIsCoreHolding = row.dataset.coreHolding === "true"; // converts core-holding flag into a true/false value
            const rowIsSatellite = row.dataset.satellite === "true"; // converts satellite flag into a true/false value
            const rowIsExploratory = row.dataset.exploratory === "true"; // converts exploratory flag into a true/false value
            const rowIsCashCandidate = row.dataset.cashCandidate === "true"; // converts cash-candidate flag into a true/false value
            const rowIsIncomeCandidate = row.dataset.incomeCandidate === "true"; // converts income-candidate flag into a true/false value
            const rowIsBestRanked = row.dataset.bestRanked === "true"; // converts best-ranked flag into a true/false value

            let visible = true; // starts by assuming the row should remain visible

            if (tickerValue && rowTicker !== tickerValue) visible = false; // hides the row if its ticker does not match the selected ticker
            if (decisionValue && rowDecision !== decisionValue) visible = false; // hides the row if its decision does not match the selected decision
            if (scoreValue !== null && (rowScore === null || rowScore < scoreValue)) visible = false; // hides rows with missing score or too low a score
            if (volatilityValue !== null && (rowVolatility === null || rowVolatility > volatilityValue)) visible = false; // hides rows with missing volatility or too much volatility
            if (sharpeValue !== null && (rowSharpe === null || rowSharpe < sharpeValue)) visible = false; // hides rows with missing Sharpe or too low a Sharpe value

            if (activePreset === "low-risk" && !rowIsLowRisk) visible = false; // when low-risk preset is active, hide anything not flagged as low risk
            if (activePreset === "high-conviction" && !rowIsHighConviction) visible = false; // when high-conviction preset is active, keep only those rows
            if (activePreset === "core" && !rowIsCoreHolding) visible = false; // when core preset is active, keep only core holdings
            if (activePreset === "satellite" && !rowIsSatellite) visible = false; // when satellite preset is active, keep only satellite names
            if (activePreset === "exploratory" && !rowIsExploratory) visible = false; // when exploratory preset is active, keep only exploratory names
            if (activePreset === "cash" && !rowIsCashCandidate) visible = false; // when cash preset is active, keep only cash/risk-control rows
            if (activePreset === "income" && !rowIsIncomeCandidate) visible = false; // when income preset is active, keep only income/defensive rows
            if (activePreset === "best-ranked" && !rowIsBestRanked) visible = false; // when best-ranked preset is active, keep only best-ranked rows

            row.style.display = visible ? "" : "none"; // either shows or hides the row in the table

            if (visible) visibleCount += 1; // increments the visible row counter if the row passed all filters
        });

        if (summary) { // only updates the summary text if that element exists on the page
            let summaryText = `Showing ${visibleCount} securities after applying filters.`; // default summary text used when no special preset message applies

            if (activePreset === "low-risk") summaryText = `Showing ${visibleCount} low-risk securities. Filter logic: lower-volatility names that passed the model.`; // custom summary for low-risk preset
            else if (activePreset === "high-conviction") summaryText = `Showing ${visibleCount} high-conviction securities. Filter logic: names classified as YES — high conviction with score 7 or above.`; // custom summary for high-conviction preset
            else if (activePreset === "core") summaryText = `Showing ${visibleCount} core holdings. Filter logic: names classified as YES — core holding.`; // custom summary for core preset
            else if (activePreset === "satellite") summaryText = `Showing ${visibleCount} satellite / diversifier positions. Filter logic: names classified as YES — satellite.`; // custom summary for satellite preset
            else if (activePreset === "exploratory") summaryText = `Showing ${visibleCount} exploratory / high-risk positions. Filter logic: names classified as LIMITED — high risk / exploratory.`; // custom summary for exploratory preset
            else if (activePreset === "income") summaryText = `Showing ${visibleCount} income / defensive securities. Filter logic: defensive or bond-style instruments flagged by the model.`; // custom summary for income preset
            else if (activePreset === "best-ranked") summaryText = `Showing ${visibleCount} best-ranked securities. Filter logic: score 5 or above and Sharpe-like ratio of at least 0.3.`; // custom summary for best-ranked preset
            else if (activePreset === "cash") summaryText = `Showing ${visibleCount} cash / risk-control names. Filter logic: names classified as NO — hold as cash instead.`; // custom summary for cash preset

            summary.textContent = summaryText; // writes the summary text into the page
        }
    }

    function clearDashboardFilters() { // resets all manual filters and preset mode back to default state
        if (tickerFilter) tickerFilter.value = ""; // clears ticker filter
        if (decisionFilter) decisionFilter.value = ""; // clears decision filter
        if (scoreFilter) scoreFilter.value = ""; // clears score filter
        if (volatilityFilter) volatilityFilter.value = ""; // clears volatility filter
        if (sharpeFilter) sharpeFilter.value = ""; // clears Sharpe filter

        activePreset = ""; // clears whichever preset was active before
        applyDashboardFilters(); // re-runs filter logic immediately after reset
    }

    if (presetLowRisk) presetLowRisk.addEventListener("click", function () { clearDashboardFilters(); activePreset = "low-risk"; applyDashboardFilters(); }); // activates low-risk preset in one click
    if (presetHighConviction) presetHighConviction.addEventListener("click", function () { clearDashboardFilters(); activePreset = "high-conviction"; applyDashboardFilters(); }); // activates high-conviction preset in one click
    if (presetCore) presetCore.addEventListener("click", function () { clearDashboardFilters(); activePreset = "core"; applyDashboardFilters(); }); // activates core preset in one click
    if (presetSatellite) presetSatellite.addEventListener("click", function () { clearDashboardFilters(); activePreset = "satellite"; applyDashboardFilters(); }); // activates satellite preset in one click
    if (presetExploratory) presetExploratory.addEventListener("click", function () { clearDashboardFilters(); activePreset = "exploratory"; applyDashboardFilters(); }); // activates exploratory preset in one click
    if (presetIncome) presetIncome.addEventListener("click", function () { clearDashboardFilters(); activePreset = "income"; applyDashboardFilters(); }); // activates income/defensive preset in one click
    if (presetBestRanked) presetBestRanked.addEventListener("click", function () { clearDashboardFilters(); activePreset = "best-ranked"; applyDashboardFilters(); }); // activates best-ranked preset in one click
    if (presetCash) presetCash.addEventListener("click", function () { clearDashboardFilters(); activePreset = "cash"; applyDashboardFilters(); }); // activates cash/risk-control preset in one click
    if (clearFiltersBtn) clearFiltersBtn.addEventListener("click", clearDashboardFilters); // clear button resets every filter back to blank

    [tickerFilter, decisionFilter, scoreFilter, volatilityFilter, sharpeFilter].forEach(control => { // loops through all manual filter controls
        if (control) { // only attaches listeners if that control exists
            control.addEventListener("input", function () { // reacts immediately while the user types or changes values
                activePreset = ""; // clears preset mode when the user starts using manual filters
                applyDashboardFilters(); // reapplies the filter logic straight away
            });

            control.addEventListener("change", function () { // also reacts on standard change events for dropdowns and inputs
                activePreset = ""; // clears preset mode again to avoid conflict with manual filters
                applyDashboardFilters(); // reapplies filtering after the control changes
            });
        }
    });

    function getCellValue(row, index) { // helper used during sorting to read one cell value from a given row
        return row.children[index].textContent.trim(); // returns the cleaned visible text from the chosen column
    }

    headers.forEach((header, index) => { // loops through each sortable header cell
        header.style.cursor = "pointer"; // changes the cursor so the user can see the header is clickable
        header.dataset.direction = "desc"; // stores a default starting direction for sorting

        header.addEventListener("click", function () { // runs when the user clicks one sortable header
            const rows = Array.from(tbody.querySelectorAll("tr")); // converts current table rows into an array so they can be sorted
            const direction = this.dataset.direction === "asc" ? "desc" : "asc"; // toggles the sort direction each time the same header is clicked
            this.dataset.direction = direction; // saves the new sort direction on that header

            rows.sort((a, b) => { // sorts the rows array based on the clicked column
                const aText = getCellValue(a, index); // gets the cell text for row a in the selected column
                const bText = getCellValue(b, index); // gets the cell text for row b in the selected column

                const aNum = parseFloat(aText.replace(/[^\d.-]/g, "")); // tries to strip symbols like % and read a numeric value from row a
                const bNum = parseFloat(bText.replace(/[^\d.-]/g, "")); // tries to strip symbols like % and read a numeric value from row b

                let comparison; // holds the comparison result before the chosen direction is applied
                if (!isNaN(aNum) && !isNaN(bNum)) comparison = aNum - bNum; // uses numeric comparison when both cell values are valid numbers
                else comparison = aText.localeCompare(bText); // falls back to text comparison when the cells are not numeric

                return direction === "asc" ? comparison : -comparison; // applies ascending or descending direction to the comparison result
            });

            rows.forEach(row => tbody.appendChild(row)); // puts the sorted rows back into the table body in the new order
            applyDashboardFilters(); // reapplies filters after sorting so sorting and filtering stay consistent
        });
    });

    applyDashboardFilters(); // runs once on page load so the dashboard starts in a clean filtered state
}


// Delete a saved PostgreSQL-backed holding from the Criteria page.
document.addEventListener("click", async function (event) {
    const button = event.target.closest(".delete-holding-btn");
    if (!button) return;
    const holdingId = button.dataset.holdingId;
    try {
        const res = await fetch(`/delete-holding/${holdingId}`, { method: "DELETE" });
        const data = await res.json();
        if (!res.ok || data.error) { showTradeMessage(data.error || "Failed to delete holding.", "error"); return; }
        renderPortfolioGroups(data.portfolio);
        showTradeMessage(data.message || "Holding deleted.", "success");
    } catch (error) {
        showTradeMessage("Failed to delete holding.", "error");
        console.error("Failed to delete holding:", error);
    }
});

// =========================================================
// PAGE STARTUP / WHAT RUNS ON LOAD
// Starts the right logic depending on the current page.
// =========================================================

initialiseStaticAccordions(); // activates any accordion buttons already present in the HTML
initialiseChecklistCollapsible(); // activates collapsible checklist buttons and panels
initialiseIndexPage(); // runs homepage setup if the current page is index/home
initialisePortfolioProfilesPage(); // runs portfolio profiles setup if that page is open
initialiseCriteriaPage(); // runs criteria page setup if the current page is criteria.html
initialiseMarketDashboard(); // runs market dashboard setup if that page is open
initialiseContactPage(); // runs contact page setup if the current page is contact.html

}); // closes the DOMContentLoaded wrapper so all the code above only runs after the page is ready