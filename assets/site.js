"use strict";

document.documentElement.classList.add("js");
const menuButton = document.querySelector(".nav-toggle");
const menu = document.querySelector(".nav-links");
if (menuButton && menu) {
  menuButton.addEventListener("click", () => {
    const open = menuButton.getAttribute("aria-expanded") !== "true";
    menuButton.setAttribute("aria-expanded", String(open));
    menu.classList.toggle("open", open);
  });
}

const launch = document.querySelector("[data-launch]");
if (launch) {
  const frame = document.querySelector(".viewer-frame");
  const preview = document.querySelector(".preview-stage");
  const status = document.querySelector(".loading-status");

  launch.addEventListener("click", () => {
    launch.disabled = true;
    launch.textContent = "Loading graph…";
    status.textContent = "Loading the interactive graph. You can also open the standalone version above.";

    const onLoad = () => {
      try {
        const doc = frame.contentDocument;
        const graph = doc && doc.querySelector(".plotly-graph-div");
        if (!graph || !frame.contentWindow.Plotly) {
          throw new Error("The interactive graph did not load.");
        }
        // Adapt presentation in the same-origin frame; retain the saved artifact's bytes.
        const style = doc.createElement("style");
        style.textContent = "body>header,body>main,body>footer,body>section{display:none!important}html,body{margin:0!important;padding:0!important;background:white!important}";
        doc.head.appendChild(style);
        frame.hidden = false;
        preview.hidden = true;
        const resize = () => frame.contentWindow.Plotly.Plots.resize(graph);
        requestAnimationFrame(resize);
        status.textContent = "Graph loaded. Drag to rotate, scroll to zoom, and use the date slider or playback controls.";
      } catch (error) {
        frame.hidden = true;
        status.textContent = "The embedded graph could not load. Please use Open standalone above.";
        launch.disabled = false;
        launch.textContent = "Try loading again";
      }
    };

    frame.addEventListener("load", onLoad, { once: true });
    frame.src = frame.dataset.src;
  });
}
