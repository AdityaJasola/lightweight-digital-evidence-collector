// Copy-to-clipboard and print buttons. No other scripting is needed.
(function () {
  "use strict";

  function setStatus(button, text) {
    var status = button.parentElement.querySelector(".copy-status");
    if (status) { status.textContent = text; }
  }

  function fallbackCopy(text) {
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    document.body.removeChild(area);
    return ok;
  }

  document.querySelectorAll("[data-copy]").forEach(function (button) {
    button.addEventListener("click", function () {
      var source = document.querySelector(button.getAttribute("data-copy"));
      if (!source) { return; }
      var text = source.textContent.trim();
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(
          function () { setStatus(button, "Hash copied"); },
          function () { setStatus(button, fallbackCopy(text) ? "Hash copied" : "Copy failed"); }
        );
      } else {
        setStatus(button, fallbackCopy(text) ? "Hash copied" : "Copy failed");
      }
    });
  });

  document.querySelectorAll("[data-print]").forEach(function (button) {
    button.addEventListener("click", function () { window.print(); });
  });
})();
