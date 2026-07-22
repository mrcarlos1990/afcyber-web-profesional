const nav = document.getElementById("mainNav");
const topButton = document.getElementById("topButton");
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const waNumber = (window.AFCYBER && window.AFCYBER.whatsapp) || "18299198058";

function waUrl(message) {
  return `https://wa.me/${waNumber}?text=${encodeURIComponent(message || "Hola AFCyber Solutions, quiero información.")}`;
}

document.querySelectorAll(".js-wa").forEach((link) => {
  link.href = waUrl(link.dataset.message);
  link.target = "_blank";
  link.rel = "noopener";
});

const year = document.getElementById("year");
if (year) year.textContent = new Date().getFullYear();

const menu = document.getElementById("menu");
const collapse = menu && window.bootstrap ? bootstrap.Collapse.getOrCreateInstance(menu, { toggle: false }) : null;
document.querySelectorAll(".cyber-nav .nav-link").forEach((link) => {
  link.addEventListener("click", () => {
    if (window.innerWidth < 992 && collapse) collapse.hide();
  });
});

window.addEventListener("scroll", () => {
  nav && nav.classList.toggle("nav-scrolled", window.scrollY > 24);
  topButton && topButton.classList.toggle("show", window.scrollY > 650);
}, { passive: true });

topButton && topButton.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add("visible");
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.15 });
document.querySelectorAll(".reveal").forEach((el) => observer.observe(el));

const sections = [...document.querySelectorAll("header[id], section[id]")];
const navLinks = [...document.querySelectorAll(".cyber-nav .nav-link")];
const activeObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    const id = `#${entry.target.id}`;
    navLinks.forEach((link) => link.classList.toggle("active", link.getAttribute("href") === id));
  });
}, { rootMargin: "-30% 0px -55% 0px", threshold: 0.01 });
sections.forEach((section) => activeObserver.observe(section));

const counterObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    const el = entry.target;
    const target = Number(el.dataset.counter || 0);
    const start = performance.now();
    const tick = (now) => {
      const progress = Math.min((now - start) / 1300, 1);
      el.textContent = Math.round(target * (1 - Math.pow(1 - progress, 3)));
      if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
    counterObserver.unobserve(el);
  });
}, { threshold: 0.55 });
document.querySelectorAll("[data-counter]").forEach((el) => counterObserver.observe(el));

const canvas = document.getElementById("networkCanvas");
if (canvas && !prefersReducedMotion) {
  const ctx = canvas.getContext("2d");
  let points = [];
  let w = 0;
  let h = 0;
  function resize() {
    const ratio = window.devicePixelRatio || 1;
    w = canvas.offsetWidth;
    h = canvas.offsetHeight;
    canvas.width = w * ratio;
    canvas.height = h * ratio;
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    points = Array.from({ length: Math.min(80, Math.max(36, Math.floor(w / 18))) }, () => ({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - .5) * .32,
      vy: (Math.random() - .5) * .32,
      r: Math.random() * 1.8 + 1
    }));
  }
  function draw() {
    ctx.clearRect(0, 0, w, h);
    points.forEach((p, i) => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(0,212,255,.75)";
      ctx.fill();
      for (let j = i + 1; j < points.length; j++) {
        const o = points[j];
        const d = Math.hypot(p.x - o.x, p.y - o.y);
        if (d < 145) {
          ctx.strokeStyle = `rgba(0,212,255,${(1 - d / 145) * .16})`;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(o.x, o.y);
          ctx.stroke();
        }
      }
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0 || p.x > w) p.vx *= -1;
      if (p.y < 0 || p.y > h) p.vy *= -1;
    });
    requestAnimationFrame(draw);
  }
  resize();
  draw();
  window.addEventListener("resize", resize);
}
