# UI Testing and Debugging Protocol: Dark Mode Toggle

## 1. Reliable Clicking Strategy

To ensure consistent and reliable interaction with the "Dark Mode" toggle, we will use the `evaluate_script` tool provided by the Chrome DevTools MCP. This approach is more robust than relying on coordinates, as it directly targets the DOM element.

The toggle is a Streamlit `st.toggle` component with the label '🌓'. Streamlit renders this as a `label` element containing the emoji. We can target this element and trigger a click on its parent or associated input element.

### JavaScript Snippet for `evaluate_script`

The following JavaScript snippet will find the toggle element by its label and click it:

```javascript
() => {
  // Find all label elements on the page
  const labels = Array.from(document.querySelectorAll('label'));
  
  // Find the specific label that contains the moon emoji '🌓'
  const toggleLabel = labels.find(label => label.textContent.includes('🌓'));
  
  // If the label is found, click it to activate the toggle
  if (toggleLabel) {
    toggleLabel.click();
    return "Toggle clicked.";
  } else {
    return "Toggle not found.";
  }
}
```

This script is self-contained and directly executable by the `evaluate_script` tool.

## 2. Visual Verification Protocol

This protocol outlines the step-by-step procedure for verifying the "Dark Mode" toggle's functionality using screenshots as evidence.

1.  **Launch the Dashboard:**
    *   Ensure the Streamlit dashboard is running. The application is served at `http://localhost:8501`.
    *   Use the `browser_action` tool to launch a new browser instance and navigate to the dashboard's URL.

2.  **Take "Before" Screenshot (Dark Mode):**
    *   Once the page has loaded, take a screenshot of the initial state.
    *   The application should default to a dark theme.
    *   Save this screenshot as `before_toggle_dark.png`.

3.  **Execute the Click Strategy:**
    *   Use the `evaluate_script` tool with the JavaScript snippet defined in section 1 to click the '🌓' toggle.

4.  **Take "After" Screenshot (Light Mode):**
    *   After the script has been executed, take a second screenshot.
    *   This screenshot should show the dashboard in a proper light mode (e.g., white or light grey background).
    *   Save this screenshot as `after_toggle_light.png`.

5.  **Execute the Click Strategy Again:**
    *   Use the `evaluate_script` tool a second time with the same JavaScript snippet to toggle the theme back to dark mode.

6.  **Take Final Screenshot (Return to Dark Mode):**
    *   Take a final screenshot to verify that the dashboard has successfully returned to dark mode.
    *   Save this screenshot as `final_return_to_dark.png`.

## 3. Debugging Strategy for "Black Screen" Bug

If the "light mode" appears as a black screen, the following steps will be used to diagnose the issue using browser developer tools.

1.  **Navigate to Light Mode:**
    *   Follow steps 1-3 from the Visual Verification Protocol to switch the dashboard to the buggy light mode state.

2.  **Inspect Page Elements:**
    *   Use the browser's developer tools (accessible by right-clicking and selecting "Inspect") to examine the HTML and CSS of the page.
    *   Focus on the main container or `body` element to identify the styles being applied.

3.  **Analyze CSS Rules:**
    *   In the "Styles" or "Computed" tab of the developer tools, look for CSS rules that set the `background-color` to black or a dark color.
    *   Identify the source of these styles. They may be coming from the `dark_theme_css` string in [`src/vertex_benchmark/dashboard.py`](src/vertex_benchmark/dashboard.py:171) and are not being correctly overridden or removed when switching to light mode.

4.  **Hypothesize and Test:**
    *   The most likely cause is that the `light_theme_css` is not sufficient to reset the styles applied by `dark_theme_css`. The `light_theme_css` is currently empty.
    *   Live-edit the CSS in the browser to test potential fixes. For example, explicitly set `background-color: white !important;` on the `.stApp` class.
    *   If a fix is identified, implement it in the [`src/vertex_benchmark/dashboard.py`](src/vertex_benchmark/dashboard.py) file.