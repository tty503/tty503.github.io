// tty503.com — UI behavior (nav, reveal, TOC, copy, year, back-to-top)
(function () {
  "use strict";

  // Year
  document.querySelectorAll("[data-year]").forEach((el) => {
    el.textContent = new Date().getFullYear();
  });

  // Nav scrolled + back-to-top
  var nav = document.querySelector(".site-nav");
  var toTop = document.querySelector(".to-top");
  function onScroll() {
    var y = window.scrollY;
    if (nav) nav.classList.toggle("scrolled", y > 10);
    if (toTop) toTop.classList.toggle("show", y > 600);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
  if (toTop) {
    toTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
  }

  // Mobile nav toggle
  var toggleBtn = document.querySelector(".nav-toggle");
  var navLinks = document.querySelector(".nav-links");
  if (toggleBtn && navLinks) {
    toggleBtn.addEventListener("click", () => navLinks.classList.toggle("open"));
    navLinks.querySelectorAll("a").forEach((a) =>
      a.addEventListener("click", () => navLinks.classList.remove("open"))
    );
  }

  // Reveal on scroll
  var revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && revealEls.length) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    revealEls.forEach((el) => io.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("in"));
  }

  // Copy code button
  document.querySelectorAll("pre.code").forEach(function (pre) {
    var wrap = pre.parentElement;
    if (!wrap || !wrap.classList.contains("code-wrap")) return;
    var btn = document.createElement("button");
    btn.className = "copy-btn";
    btn.type = "button";
    btn.textContent = "copy";
    btn.addEventListener("click", function () {
      var code = pre.innerText;
      var done = function () {
        btn.textContent = "copied";
        setTimeout(function () { btn.textContent = "copy"; }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(code).then(done).catch(function () {
          fallbackCopy(code);
          done();
        });
      } else {
        fallbackCopy(code);
        done();
      }
    });
    wrap.appendChild(btn);
  });
  function fallbackCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); } catch (e) {}
    document.body.removeChild(ta);
  }

  // TOC current-section highlight
  var tocAnchors = Array.prototype.slice.call(document.querySelectorAll(".toc-card a[href^='#']"));
  if (tocAnchors.length && "IntersectionObserver" in window) {
    var map = new Map();
    var io2 = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) map.set(e.target.id, true);
          else map.delete(e.target.id);
        });
        var active = null;
        [...map.keys()].forEach(function (id) {
          var a = tocAnchors.find(function (x) { return x.getAttribute("href") === "#" + id; });
          if (a) {
            tocAnchors.forEach(function (x) { x.style.color = ""; });
            if (a.closest(".toc-card")) a.style.color = "var(--lime)";
          }
        });
      },
      { rootMargin: "-15% 0px -70% 0px" }
    );
    tocAnchors.forEach(function (a) {
      var id = a.getAttribute("href").slice(1);
      var el = document.getElementById(id);
      if (el) io2.observe(el);
    });
  }
})();