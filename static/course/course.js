function setPanelActive(panel, active) {
    if (!panel) return;
    panel.classList.toggle("v-expansion-panel--active", active);
    panel.classList.toggle("v-item--active", active);
    panel
        .querySelector("button.v-expansion-panel-header")
        .classList.toggle("v-expansion-panel-header--active", active);
    panel
        .querySelector("button.v-expansion-panel-header")
        .parentElement.setAttribute("aria-expanded", active);
}

document.querySelectorAll("button.v-expansion-panel-header").forEach((el) => {
    // Bind click event to panel
    el.addEventListener("click", (e) => {
        e.stopPropagation();
        e.preventDefault();
        const active = el.classList.contains(
            "v-expansion-panel-header--active"
        );
        // Close current active panel
        setPanelActive(
            el.parentElement.parentElement.querySelector(
                ".v-expansion-panel--active.v-item--active"
            ),
            false
        );
        // Toggle clicked panel
        setPanelActive(el.parentElement, !active);
    });
});

// Open first panel
document.querySelectorAll(".v-expansion-panels").forEach((el) => {
    setPanelActive(el.children[0], true);
});

// if function "ready" exists, call it (swiperjs)
if (typeof ready === "function") {
    ready();
}
