const siteConfig = {
  whatsappNumber: window.AF_SITE?.whatsapp || "18299198058",
  defaultWhatsappMessage: window.AF_SITE?.defaultMessage || "Hola AFCyber Solutions, quiero solicitar información sobre sus servicios tecnológicos."
};

document.addEventListener("DOMContentLoaded", () => {
  document.body.classList.add("loaded");

  const year = document.getElementById("currentYear");
  if (year) year.textContent = new Date().getFullYear();

  initAos();
  initNavbar();
  initWhatsappLinks();
  initCounters();
  initBackToTop();
  initNetworkCanvas();
  initSocParallax();
  initAssetReadyState();
  initAdminShortcut();
  initInteractiveTimeline();
  initVirtualAssistant();
});

function initAos() {
  if (!window.AOS) return;
  AOS.init({
    duration: 820,
    easing: "ease-out-cubic",
    once: true,
    offset: 70
  });
}

function initNavbar() {
  const nav = document.getElementById("mainNav");
  const menu = document.getElementById("navbarMenu");
  const links = document.querySelectorAll(".premium-nav .nav-link");
  const collapse = menu && window.bootstrap
    ? bootstrap.Collapse.getOrCreateInstance(menu, { toggle: false })
    : null;

  if (!nav) return;

  const updateNav = () => nav.classList.toggle("nav-scrolled", window.scrollY > 30);
  updateNav();
  window.addEventListener("scroll", updateNav, { passive: true });

  links.forEach((link) => {
    link.addEventListener("click", () => {
      links.forEach((item) => item.classList.remove("active"));
      link.classList.add("active");
      if (window.innerWidth < 1200 && collapse) collapse.hide();
    });
  });

  const targets = Array.from(links)
    .map((link) => document.querySelector(link.getAttribute("href") || ""))
    .filter(Boolean);

  if (!targets.length) return;

  const observer = new IntersectionObserver((entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

    if (!visible) return;
    links.forEach((link) => {
      link.classList.toggle("active", link.getAttribute("href") === `#${visible.target.id}`);
    });
  }, {
    threshold: [0.22, 0.45, 0.68],
    rootMargin: "-18% 0px -58% 0px"
  });

  targets.forEach((target) => observer.observe(target));
}

function buildWhatsappUrl(message) {
  return `https://wa.me/${siteConfig.whatsappNumber}?text=${encodeURIComponent(normalizeText(message || siteConfig.defaultWhatsappMessage))}`;
}

function normalizeText(text) {
  return String(text || "")
    .replaceAll("informaci\u00c3\u00b3n", "informaci\u00f3n")
    .replaceAll("tecnol\u00c3\u00b3gicos", "tecnol\u00f3gicos")
    .replaceAll("cotizaci\u00c3\u00b3n", "cotizaci\u00f3n")
    .replaceAll("c\u00c3\u00a1maras", "c\u00e1maras")
    .replaceAll("barber\u00c3\u00adas", "barber\u00edas");
}

function initWhatsappLinks() {
  document.querySelectorAll(".js-whatsapp").forEach((link) => {
    const service = link.dataset.service;
    const message = link.dataset.message || (service
      ? `Hola AFCyber Solutions, quiero información sobre el servicio: ${service}.`
      : siteConfig.defaultWhatsappMessage);
    link.setAttribute("href", buildWhatsappUrl(message));
    link.setAttribute("target", "_blank");
    link.setAttribute("rel", "noopener");
  });
}

function initAdminShortcut() {
  document.addEventListener("keydown", (event) => {
    if (event.ctrlKey && event.altKey && event.key.toLowerCase() === "a") {
      event.preventDefault();
      window.location.href = "/admin/login";
    }
  });
}

function initInteractiveTimeline() {
  const items = document.querySelectorAll(".interactive-timeline article");
  if (!items.length) return;

  items.forEach((item) => {
    item.addEventListener("mouseenter", () => {
      items.forEach((entry) => entry.classList.remove("active"));
      item.classList.add("active");
    });
    item.addEventListener("focusin", () => {
      items.forEach((entry) => entry.classList.remove("active"));
      item.classList.add("active");
    });
  });
}

function initVirtualAssistant() {
  const assistant = document.getElementById("virtualAssistant");
  if (!assistant) return;

  const toggle = assistant.querySelector(".assistant-toggle");
  if (!toggle) return;

  toggle.addEventListener("click", () => {
    const isOpen = assistant.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(isOpen));
  });
}

function initCounters() {
  const counters = document.querySelectorAll("[data-counter]");
  if (!counters.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      animateCounter(entry.target);
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.55 });

  counters.forEach((counter) => observer.observe(counter));
}

function animateCounter(element) {
  const target = Number(element.dataset.counter || "0");
  const duration = 1350;
  const start = performance.now();

  const tick = (now) => {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    element.textContent = Math.round(target * eased);
    if (progress < 1) requestAnimationFrame(tick);
  };

  requestAnimationFrame(tick);
}

function initBackToTop() {
  const button = document.getElementById("backToTop");
  if (!button) return;

  window.addEventListener("scroll", () => {
    button.classList.toggle("show", window.scrollY > 650);
  }, { passive: true });

  button.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
}

function initSocParallax() {
  const hero = document.querySelector(".hero-section");
  const layers = document.querySelectorAll("[data-parallax]");
  if (!hero || !layers.length || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  let pointerX = 0;
  let pointerY = 0;
  let scrollY = window.scrollY;
  let ticking = false;

  const update = () => {
    layers.forEach((layer) => {
      const speed = Number(layer.dataset.parallax || "0");
      const moveX = pointerX * speed * 38;
      const moveY = pointerY * speed * 26 + scrollY * speed * .28;
      layer.style.translate = `${moveX}px ${moveY}px`;
    });
    ticking = false;
  };

  const requestUpdate = () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(update);
  };

  hero.addEventListener("mousemove", (event) => {
    const rect = hero.getBoundingClientRect();
    pointerX = ((event.clientX - rect.left) / rect.width) - .5;
    pointerY = ((event.clientY - rect.top) / rect.height) - .5;
    requestUpdate();
  }, { passive: true });

  window.addEventListener("scroll", () => {
    scrollY = window.scrollY;
    requestUpdate();
  }, { passive: true });
}

function initAssetReadyState() {
  const hero = document.querySelector(".hero-section");
  if (!hero) return;

  const logo = document.querySelector(".hero-logo-img");
  if (!logo) {
    hero.classList.add("hero-assets-ready");
    return;
  }

  if (logo.complete) {
    hero.classList.add("hero-assets-ready");
    return;
  }

  logo.addEventListener("load", () => hero.classList.add("hero-assets-ready"), { once: true });
}

function initNetworkCanvas() {
  const canvas = document.getElementById("networkCanvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  let points = [];
  let width = 0;
  let height = 0;
  let animationFrame = null;

  const resize = () => {
    const ratio = window.devicePixelRatio || 1;
    width = canvas.offsetWidth;
    height = canvas.offsetHeight;
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    points = createPoints(width, height);
  };

  const animate = () => {
    ctx.clearRect(0, 0, width, height);
    drawNetwork(ctx, points);
    points.forEach((point) => {
      point.x += point.vx;
      point.y += point.vy;
      if (point.x < 0 || point.x > width) point.vx *= -1;
      if (point.y < 0 || point.y > height) point.vy *= -1;
    });
    animationFrame = requestAnimationFrame(animate);
  };

  resize();
  animate();

  window.addEventListener("resize", () => {
    cancelAnimationFrame(animationFrame);
    resize();
    animate();
  }, { passive: true });
}

function createPoints(width, height) {
  const amount = Math.min(95, Math.max(44, Math.floor(width / 15)));
  return Array.from({ length: amount }, () => ({
    x: Math.random() * width,
    y: Math.random() * height,
    vx: (Math.random() - .5) * .24,
    vy: (Math.random() - .5) * .24,
    r: Math.random() * 1.8 + .9
  }));
}

function drawNetwork(ctx, points) {
  ctx.lineWidth = 1;

  points.forEach((point, index) => {
    ctx.beginPath();
    ctx.arc(point.x, point.y, point.r, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(0, 168, 255, .72)";
    ctx.shadowColor = "rgba(0, 168, 255, .75)";
    ctx.shadowBlur = 8;
    ctx.fill();
    ctx.shadowBlur = 0;

    for (let i = index + 1; i < points.length; i += 1) {
      const other = points[i];
      const distance = Math.hypot(point.x - other.x, point.y - other.y);
      if (distance < 140) {
        const opacity = 1 - distance / 140;
        ctx.strokeStyle = `rgba(0, 168, 255, ${opacity * .18})`;
        ctx.beginPath();
        ctx.moveTo(point.x, point.y);
        ctx.lineTo(other.x, other.y);
        ctx.stroke();
      }
    }
  });
}
